"""
Vistas para el Sistema de Presupuesto Público
CDP, RP, Obligaciones, PAC y gestión presupuestal
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, date

from .models import (
    BudgetPeriod, BudgetRubro, CDP, CDPDetail,
    RP, RPDetail, BudgetObligation, PAC,
    BudgetModification, BudgetModificationDetail, BudgetExecution
)
from core.models import Company
from accounting.models import JournalEntry, JournalEntryLine, JournalType, ChartOfAccounts


def get_user_company(request):
    """Función auxiliar para obtener la empresa del usuario"""
    company_id = request.GET.get('company_id') or request.session.get('selected_company_id')
    
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
            request.session['selected_company_id'] = str(company.id)
            return company
        except Company.DoesNotExist:
            pass
    
    # Si no hay empresa en sesión, usar la primera disponible
    if request.user.is_superuser:
        company = Company.objects.filter(is_active=True).first()
    else:
        company = request.user.companies.filter(is_active=True).first()
    
    if company:
        request.session['selected_company_id'] = str(company.id)
    return company


@login_required
def budget_dashboard(request):
    """Dashboard principal del módulo de presupuesto"""
    company = get_user_company(request)
    
    if not company:
        messages.error(request, 'No tiene ninguna empresa asignada')
        return redirect('core:dashboard')
    
    current_year = timezone.now().year
    
    # Obtener o crear período presupuestal actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company,
        year=current_year,
        defaults={
            'name': f'Vigencia {current_year}',
            'status': 'active',
            'created_by': request.user
        }
    )
    
    # Estadísticas generales
    stats = {
        'total_budget': period.current_budget,
        'cdp_total': CDP.objects.filter(company=company, period=period, state='approved').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'rp_total': RP.objects.filter(company=company, period=period, state='approved').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'obligations_total': BudgetObligation.objects.filter(company=company, period=period, state='approved').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
        'payments_total': BudgetObligation.objects.filter(company=company, period=period, state='paid').aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0,
    }
    
    # CDPs recientes
    recent_cdps = CDP.objects.filter(
        company=company,
        period=period
    ).order_by('-created_at')[:5]
    
    # RPs recientes
    recent_rps = RP.objects.filter(
        company=company,
        period=period
    ).order_by('-created_at')[:5]
    
    # Rubros con mayor ejecución
    top_rubros = BudgetRubro.objects.filter(
        company=company,
        period=period,
        rubro_type='expense'
    ).order_by('-cdp_amount')[:10]
    
    # Obtener todas las empresas disponibles para el selector
    if request.user.is_superuser:
        all_companies = Company.objects.filter(is_active=True)
    else:
        all_companies = request.user.companies.filter(is_active=True)
    
    context = {
        'company': company,
        'companies': all_companies,
        'period': period,
        'stats': stats,
        'recent_cdps': recent_cdps,
        'recent_rps': recent_rps,
        'top_rubros': top_rubros,
    }
    
    return render(request, 'budget/dashboard.html', context)


@login_required
def cdp_create(request):
    """Crear nuevo CDP"""
    company = get_user_company(request)
    
    if not company:
        messages.error(request, 'Seleccione una empresa primero')
        return redirect('budget:budget_dashboard')
    
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        try:
            # Crear CDP
            cdp = CDP.objects.create(
                company=company,
                period=period,
                date=request.POST.get('date'),
                concept=request.POST.get('concept'),
                request_area=request.POST.get('request_area'),
                request_person=request.POST.get('request_person'),
                project=request.POST.get('project', ''),
                contract_modality=request.POST.get('contract_modality', ''),
                total_amount=Decimal(request.POST.get('total_amount', 0)),
                state='draft',
                created_by=request.user,
                observations=request.POST.get('observations', '')
            )
            
            # Crear detalles por rubro
            rubros = request.POST.getlist('rubro_id[]')
            amounts = request.POST.getlist('rubro_amount[]')
            
            for rubro_id, amount in zip(rubros, amounts):
                if rubro_id and amount:
                    rubro = BudgetRubro.objects.get(id=rubro_id)
                    CDPDetail.objects.create(
                        cdp=cdp,
                        rubro=rubro,
                        amount=Decimal(amount)
                    )
                    
                    # Actualizar ejecución del rubro
                    rubro.cdp_amount += Decimal(amount)
                    rubro.save()
            
            # Si se solicita aprobar directamente
            if request.POST.get('approve') == 'true':
                cdp.state = 'approved'
                cdp.approved_by = request.user
                cdp.approved_at = timezone.now()
                cdp.save()
            
            messages.success(request, f'CDP {cdp.number} creado exitosamente')
            return redirect('budget:cdp_detail', pk=cdp.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear CDP: {str(e)}')
    
    # Obtener rubros disponibles
    rubros = BudgetRubro.objects.filter(
        company=company,
        period=period,
        rubro_type='expense',
        is_active=True
    ).order_by('code')
    
    context = {
        'company': company,
        'period': period,
        'rubros': rubros,
        'today': timezone.now().date(),
    }
    
    return render(request, 'budget/cdp_create.html', context)


@login_required
def cdp_detail(request, pk):
    """Ver detalle de CDP"""
    company = get_user_company(request)
    cdp = get_object_or_404(CDP, pk=pk, company=company)
    
    # RPs asociados
    rps = RP.objects.filter(
        details__cdp=cdp
    ).distinct()
    
    context = {
        'cdp': cdp,
        'rps': rps,
    }
    
    return render(request, 'budget/cdp_detail.html', context)


@login_required
def rp_create(request):
    """Crear nuevo RP"""
    company = get_user_company(request)
    
    if not company:
        messages.error(request, 'Seleccione una empresa primero')
        return redirect('budget:budget_dashboard')
    
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        try:
            # Crear RP
            rp = RP.objects.create(
                company=company,
                period=period,
                date=request.POST.get('date'),
                beneficiary_type=request.POST.get('beneficiary_type'),
                beneficiary_id=request.POST.get('beneficiary_id'),
                beneficiary_name=request.POST.get('beneficiary_name'),
                contract_type=request.POST.get('contract_type'),
                contract_number=request.POST.get('contract_number', ''),
                concept=request.POST.get('concept'),
                total_amount=Decimal(request.POST.get('total_amount', 0)),
                state='draft',
                created_by=request.user,
                observations=request.POST.get('observations', '')
            )
            
            # Crear detalles por CDP
            cdp_ids = request.POST.getlist('cdp_id[]')
            cdp_detail_ids = request.POST.getlist('cdp_detail_id[]')
            amounts = request.POST.getlist('amount[]')
            
            for cdp_id, detail_id, amount in zip(cdp_ids, cdp_detail_ids, amounts):
                if cdp_id and detail_id and amount:
                    cdp = CDP.objects.get(id=cdp_id)
                    cdp_detail = CDPDetail.objects.get(id=detail_id)
                    
                    RPDetail.objects.create(
                        rp=rp,
                        cdp=cdp,
                        cdp_detail=cdp_detail,
                        amount=Decimal(amount)
                    )
                    
                    # Actualizar CDP
                    cdp.committed_amount += Decimal(amount)
                    cdp.save()
                    
                    # Actualizar detalle CDP
                    cdp_detail.committed_amount += Decimal(amount)
                    cdp_detail.save()
                    
                    # Actualizar rubro
                    cdp_detail.rubro.rp_amount += Decimal(amount)
                    cdp_detail.rubro.save()
            
            # Si se solicita aprobar directamente
            if request.POST.get('approve') == 'true':
                rp.state = 'approved'
                rp.approved_by = request.user
                rp.approved_at = timezone.now()
                rp.save()
            
            messages.success(request, f'RP {rp.number} creado exitosamente')
            return redirect('budget:rp_detail', pk=rp.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear RP: {str(e)}')
    
    # Obtener CDPs disponibles
    cdps = CDP.objects.filter(
        company=company,
        period=period,
        state='approved'
    ).exclude(
        available_amount=0
    ).order_by('-date')
    
    context = {
        'company': company,
        'period': period,
        'cdps': cdps,
        'today': timezone.now().date(),
    }
    
    return render(request, 'budget/rp_create.html', context)


@login_required
def rp_detail(request, pk):
    """Ver detalle de RP"""
    company = get_user_company(request)
    rp = get_object_or_404(RP, pk=pk, company=company)
    
    # Obligaciones asociadas
    obligations = BudgetObligation.objects.filter(rp=rp)
    
    context = {
        'rp': rp,
        'obligations': obligations,
    }
    
    return render(request, 'budget/rp_detail.html', context)


@login_required
def obligation_create(request):
    """Crear nueva Obligación Presupuestal"""
    company = get_user_company(request)
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        try:
            rp = get_object_or_404(RP, id=request.POST.get('rp_id'))
            
            # Crear Obligación
            obligation = BudgetObligation.objects.create(
                company=company,
                period=period,
                date=request.POST.get('date'),
                rp=rp,
                concept=request.POST.get('concept'),
                invoice_number=request.POST.get('invoice_number', ''),
                invoice_date=request.POST.get('invoice_date') or None,
                gross_amount=Decimal(request.POST.get('gross_amount', 0)),
                deductions=Decimal(request.POST.get('deductions', 0)),
                state='draft',
                created_by=request.user,
                observations=request.POST.get('observations', '')
            )
            
            # Actualizar RP
            rp.obligated_amount += obligation.net_amount
            rp.save()
            
            # Actualizar rubros
            for detail in rp.details.all():
                proportion = detail.amount / rp.total_amount
                obligated = obligation.net_amount * proportion
                detail.cdp_detail.rubro.obligations += obligated
                detail.cdp_detail.rubro.save()
            
            # Crear asiento contable si se solicita
            if request.POST.get('create_journal_entry') == 'true':
                journal_type = JournalType.objects.get(code='OB')  # Obligación
                
                journal_entry = JournalEntry.objects.create(
                    company=company,
                    date=obligation.date,
                    journal_type=journal_type,
                    number=obligation.number,
                    reference=f"Obligación {obligation.number}",
                    description=obligation.concept,
                    created_by=request.user
                )
                
                # Líneas del asiento (simplificado - ajustar según plan de cuentas)
                # Débito: Gasto
                # Crédito: CxP
                
                obligation.journal_entry = journal_entry
                obligation.save()
            
            # Si se solicita aprobar directamente
            if request.POST.get('approve') == 'true':
                obligation.state = 'approved'
                obligation.approved_by = request.user
                obligation.approved_at = timezone.now()
                obligation.save()
            
            messages.success(request, f'Obligación {obligation.number} creada exitosamente')
            return redirect('budget:obligation_detail', pk=obligation.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear Obligación: {str(e)}')
    
    # Obtener RPs disponibles
    rps = RP.objects.filter(
        company=company,
        period=period,
        state='approved'
    ).exclude(
        total_amount=F('obligated_amount')
    ).order_by('-date')
    
    context = {
        'company': company,
        'period': period,
        'rps': rps,
        'today': timezone.now().date(),
    }
    
    return render(request, 'budget/obligation_create.html', context)


@login_required
def obligation_detail(request, pk):
    """Ver detalle de Obligación"""
    obligation = get_object_or_404(BudgetObligation, pk=pk, company=get_user_company(request))
    
    context = {
        'obligation': obligation,
    }
    
    return render(request, 'budget/obligation_detail.html', context)


@login_required
def pac_management(request):
    """Gestión del PAC - Plan Anual de Caja"""
    company = get_user_company(request)
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        # Actualizar PAC
        for key in request.POST:
            if key.startswith('pac_'):
                parts = key.split('_')
                if len(parts) == 3:
                    rubro_id = parts[1]
                    month = parts[2]
                    value = Decimal(request.POST.get(key, 0))
                    
                    rubro = BudgetRubro.objects.get(id=rubro_id)
                    pac, created = PAC.objects.get_or_create(
                        company=company,
                        period=period,
                        rubro=rubro,
                        defaults={'created_by': request.user}
                    )
                    
                    setattr(pac, month, value)
                    pac.save()
        
        messages.success(request, 'PAC actualizado exitosamente')
        return redirect('budget:pac_management')
    
    # Obtener rubros y PAC
    rubros = BudgetRubro.objects.filter(
        company=company,
        period=period,
        is_active=True
    ).order_by('code')
    
    pacs = {}
    for rubro in rubros:
        pac, created = PAC.objects.get_or_create(
            company=company,
            period=period,
            rubro=rubro,
            defaults={'created_by': request.user}
        )
        pacs[rubro.id] = pac
    
    months = [
        ('january', 'Enero'), ('february', 'Febrero'), ('march', 'Marzo'),
        ('april', 'Abril'), ('may', 'Mayo'), ('june', 'Junio'),
        ('july', 'Julio'), ('august', 'Agosto'), ('september', 'Septiembre'),
        ('october', 'Octubre'), ('november', 'Noviembre'), ('december', 'Diciembre')
    ]
    
    context = {
        'company': company,
        'period': period,
        'rubros': rubros,
        'pacs': pacs,
        'months': months,
    }
    
    return render(request, 'budget/pac_management.html', context)


@login_required
def budget_execution_report(request):
    """Reporte de Ejecución Presupuestal"""
    company = get_user_company(request)
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    # Obtener rubros con ejecución
    rubros = BudgetRubro.objects.filter(
        company=company,
        period=period,
        is_active=True
    ).order_by('code')
    
    # Calcular totales
    totals = {
        'appropriation': rubros.filter(rubro_type='expense').aggregate(Sum('current_appropriation'))['current_appropriation__sum'] or 0,
        'cdp': rubros.filter(rubro_type='expense').aggregate(Sum('cdp_amount'))['cdp_amount__sum'] or 0,
        'rp': rubros.filter(rubro_type='expense').aggregate(Sum('rp_amount'))['rp_amount__sum'] or 0,
        'obligations': rubros.filter(rubro_type='expense').aggregate(Sum('obligations'))['obligations__sum'] or 0,
        'payments': rubros.filter(rubro_type='expense').aggregate(Sum('payments'))['payments__sum'] or 0,
    }
    
    context = {
        'company': company,
        'period': period,
        'rubros': rubros,
        'totals': totals,
    }
    
    return render(request, 'budget/execution_report.html', context)


@login_required
def budget_modifications(request):
    """Gestión de Modificaciones Presupuestales"""
    company = get_user_company(request)
    current_year = timezone.now().year
    
    # Obtener o crear el período presupuestal para el año actual
    period, created = BudgetPeriod.objects.get_or_create(
        company=company, 
        year=current_year,
        defaults={
            'name': f'Presupuesto {current_year}',
            'start_date': timezone.datetime(current_year, 1, 1).date(),
            'end_date': timezone.datetime(current_year, 12, 31).date(),
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        try:
            # Crear modificación
            modification = BudgetModification.objects.create(
                company=company,
                period=period,
                date=request.POST.get('date'),
                modification_type=request.POST.get('modification_type'),
                act_number=request.POST.get('act_number'),
                act_date=request.POST.get('act_date'),
                concept=request.POST.get('concept'),
                total_amount=Decimal(request.POST.get('total_amount', 0)),
                state='draft',
                created_by=request.user
            )
            
            # Crear detalles
            rubros = request.POST.getlist('rubro_id[]')
            movements = request.POST.getlist('movement_type[]')
            amounts = request.POST.getlist('amount[]')
            
            for rubro_id, movement, amount in zip(rubros, movements, amounts):
                if rubro_id and amount:
                    BudgetModificationDetail.objects.create(
                        modification=modification,
                        rubro_id=rubro_id,
                        movement_type=movement,
                        amount=Decimal(amount)
                    )
            
            messages.success(request, f'Modificación presupuestal {modification.number} creada')
            return redirect('budget:modifications')
            
        except Exception as e:
            messages.error(request, f'Error al crear modificación: {str(e)}')
    
    # Listar modificaciones
    modifications = BudgetModification.objects.filter(
        company=company,
        period=period
    ).order_by('-date')
    
    rubros = BudgetRubro.objects.filter(
        company=company,
        period=period,
        is_active=True
    ).order_by('code')
    
    context = {
        'company': company,
        'period': period,
        'modifications': modifications,
        'rubros': rubros,
        'today': timezone.now().date(),
    }
    
    return render(request, 'budget/modifications.html', context)


# API endpoints para obtener datos dinámicos
@login_required
def api_cdp_details(request, cdp_id):
    """API para obtener detalles de un CDP"""
    cdp = get_object_or_404(CDP, id=cdp_id, company=get_user_company(request))
    
    details = []
    for detail in cdp.details.all():
        details.append({
            'id': detail.id,
            'rubro_code': detail.rubro.code,
            'rubro_name': detail.rubro.name,
            'amount': float(detail.amount),
            'committed': float(detail.committed_amount),
            'available': float(detail.available_amount)
        })
    
    return JsonResponse({
        'cdp': {
            'id': cdp.id,
            'number': cdp.number,
            'total': float(cdp.total_amount),
            'available': float(cdp.available_amount)
        },
        'details': details
    })


@login_required
def api_rubro_availability(request, rubro_id):
    """API para obtener disponibilidad de un rubro"""
    rubro = get_object_or_404(BudgetRubro, id=rubro_id, company=get_user_company(request))
    
    return JsonResponse({
        'rubro': {
            'id': rubro.id,
            'code': rubro.code,
            'name': rubro.name,
            'appropriation': float(rubro.current_appropriation),
            'available_appropriation': float(rubro.available_appropriation),
            'cdp_amount': float(rubro.cdp_amount),
            'available_cdp': float(rubro.available_cdp),
            'rp_amount': float(rubro.rp_amount),
            'available_rp': float(rubro.available_rp)
        }
    })