"""
Vistas para el módulo de contabilidad.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator

from core.models import Company
from core.utils import get_current_company, require_company_access

from .models_accounts import Account, ChartOfAccounts, AccountType, CostCenter
from .models_journal import JournalEntry, JournalEntryLine, JournalType


@login_required
@require_company_access
def new_journal_entry(request):
    current_company = request.current_company

    """
    Página para crear nuevo asiento contable.
    """
    companies = Company.objects.filter(is_active=True)
    journal_types = JournalType.objects.filter(is_active=True)
    accounts = Account.objects.filter(is_detail=True, is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Procesar el formulario
        company_id = request.POST.get('company')
        journal_type_id = request.POST.get('journal_type')
        date = request.POST.get('date')
        reference = request.POST.get('reference')
        description = request.POST.get('description')
        
        # Crear el asiento
        try:
            company = Company.objects.get(id=company_id)
            journal_type = JournalType.objects.get(id=journal_type_id)
            
            # Obtener período y moneda
            from core.models import Period, Currency
            current_period = Period.objects.filter(
                fiscal_year__company=company, 
                status='open'
            ).first()
            currency = Currency.objects.filter(code='COP').first()
            
            journal_entry = JournalEntry.objects.create(
                company=company,
                number=journal_type.get_next_sequence(),
                journal_type=journal_type,
                period=current_period,
                date=date,
                reference=reference,
                description=description,
                currency=currency,
                created_by=request.user
            )
            
            # Procesar las líneas del asiento
            total_debit = 0
            total_credit = 0
            
            for i in range(1, 11):  # Máximo 10 líneas
                account_id = request.POST.get(f'account_{i}')
                cost_center_id = request.POST.get(f'cost_center_{i}')
                debit = request.POST.get(f'debit_{i}', 0)
                credit = request.POST.get(f'credit_{i}', 0)
                line_description = request.POST.get(f'line_description_{i}', '')
                
                if account_id and (debit or credit):
                    account = Account.objects.get(id=account_id)
                    cost_center = CostCenter.objects.get(id=cost_center_id) if cost_center_id else None
                    debit = float(debit) if debit else 0
                    credit = float(credit) if credit else 0
                    
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        account=account,
                        cost_center=cost_center,
                        description=line_description or description,
                        debit=debit,
                        credit=credit,
                        line_number=i
                    )
                    
                    total_debit += debit
                    total_credit += credit
            
            # Validar que el asiento esté balanceado
            if abs(total_debit - total_credit) < 0.01:  # Permitir diferencias mínimas por redondeo
                journal_entry.total_debit = total_debit
                journal_entry.total_credit = total_credit
                journal_entry.save()
                
                messages.success(request, f'Asiento contable #{journal_entry.number} creado exitosamente.')
                return redirect('accounting:new_journal_entry')
            else:
                journal_entry.delete()
                messages.error(request, f'El asiento no está balanceado. Débitos: ${total_debit:,.2f}, Créditos: ${total_credit:,.2f}')
                
        except Exception as e:
            messages.error(request, f'Error al crear el asiento: {str(e)}')
    
    context = {
        'companies': companies,
        'journal_types': journal_types,
        'accounts': accounts,
        'cost_centers': cost_centers,
    }
    
    return render(request, 'accounting/new_journal_entry.html', context)


@login_required
@require_company_access
def chart_of_accounts(request):
    current_company = request.current_company

    """
    Página para ver el plan de cuentas.
    Muestra el PUC colombiano estándar sin duplicados.
    """
    search = request.GET.get('search', '')
    
    # Obtener todas las cuentas sin duplicados (agrupadas por código)
    # Solo mostramos una cuenta por código único
    from django.db.models import Min
    
    # Obtener los IDs de las primeras cuentas por cada código único
    unique_account_ids = Account.objects.values('code').annotate(
        first_id=Min('id')
    ).values_list('first_id', flat=True)
    
    # Obtener las cuentas únicas
    accounts = Account.objects.filter(
        id__in=unique_account_ids,
        is_active=True
    ).order_by('code')
    
    if search:
        accounts = accounts.filter(
            Q(code__icontains=search) | 
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(accounts, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_accounts': accounts.count(),
        'is_standard_puc': True,  # Indicar que es el PUC estándar
    }
    
    return render(request, 'accounting/chart_of_accounts.html', context)


@login_required
@require_company_access
def get_accounts_json(request):
    current_company = request.current_company

    """
    API para obtener cuentas en formato JSON (para AJAX).
    """
    try:
        company_id = request.GET.get('company')
        search = request.GET.get('search', '').strip()
        
        # Validate company_id if provided
        if company_id:
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                # Check if user has access to this company
                if not request.user.companies.filter(id=company_id).exists() and not request.user.is_superuser:
                    return JsonResponse({'error': 'No tiene permisos para acceder a esta empresa'}, status=403)
            except Company.DoesNotExist:
                return JsonResponse({'error': 'Empresa no encontrada'}, status=404)
        
        accounts = Account.objects.filter(is_detail=True, is_active=True)
        
        if company_id:
            accounts = accounts.filter(chart_of_accounts__company_id=company_id)
        
        if search:
            accounts = accounts.filter(
                Q(code__icontains=search) | 
                Q(name__icontains=search)
            )[:20]  # Limitar resultados
        
        accounts_data = [
            {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'full_name': f"{account.code} - {account.name}"
            }
            for account in accounts
        ]
        
        return JsonResponse({'accounts': accounts_data})
        
    except Exception as e:
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)