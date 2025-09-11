"""
Vistas para el módulo de impuestos.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from core.models import Company
from core.utils import get_current_company, require_company_access

from .models_tax_types import TaxType, TaxCalendar
from accounting.models_accounts import Account
from accounting.models_journal import JournalEntry, JournalEntryLine, JournalType


@login_required
@require_company_access
def taxes_dashboard(request):
    current_company = request.current_company

    """
    Dashboard principal de impuestos.
    """
    # Obtener empresas del usuario
    companies = Company.objects.filter(is_active=True)
    
    # Estadísticas de impuestos (simuladas por ahora)
    total_vat_generated = 2850000  # IVA generado mes actual
    total_withholdings = 425000   # Retenciones mes actual
    total_ica = 120000           # ICA mes actual
    pending_declarations = 3      # Declaraciones pendientes
    
    context = {
        'companies': companies,
        'total_vat_generated': total_vat_generated,
        'total_withholdings': total_withholdings,
        'total_ica': total_ica,
        'pending_declarations': pending_declarations,
    }
    
    return render(request, 'taxes/dashboard.html', context)


@login_required
@require_company_access
def iva_declaration(request):
    current_company = request.current_company

    """Vista para declaración de IVA."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/iva_declaration.html', context)


@login_required
@require_company_access
def retention_declaration(request):
    current_company = request.current_company

    """Vista para declaración de retenciones."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/retention_declaration.html', context)


@login_required
@require_company_access
def ica_declaration(request):
    current_company = request.current_company

    """Vista para declaración de ICA."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/ica_declaration.html', context)


@login_required
@require_company_access
def retention_certificates(request):
    current_company = request.current_company

    """Vista para certificados de retención."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/retention_certificates.html', context)


@login_required
@require_company_access
def magnetic_media(request):
    current_company = request.current_company

    """Vista para medios magnéticos."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/magnetic_media.html', context)


@login_required
@require_company_access
def tax_calendar(request):
    current_company = request.current_company

    """Vista para calendario tributario."""
    companies = Company.objects.filter(is_active=True)
    calendars = TaxCalendar.objects.all().order_by('due_date')
    
    context = {
        'companies': companies,
        'calendars': calendars,
    }
    
    return render(request, 'taxes/tax_calendar.html', context)


@login_required
@require_company_access
def iva_report(request):
    current_company = request.current_company

    """Vista para reportes de IVA."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/iva_report.html', context)


@login_required
@require_company_access
def renta_declaration(request):
    current_company = request.current_company

    """Vista para declaración de renta."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'taxes/renta_declaration.html', context)


@login_required
@require_company_access
def new_tax_declaration(request):
    current_company = request.current_company

    """Vista para crear nueva declaración de impuestos."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos de la declaración
                company_id = request.POST.get('company')
                tax_type_id = request.POST.get('tax_type')
                period_year = request.POST.get('period_year')
                period_month = request.POST.get('period_month')
                due_date = request.POST.get('due_date')
                
                company = Company.objects.get(id=company_id)
                tax_type = TaxType.objects.get(id=tax_type_id)
                
                # Crear una declaración simple (sin modelo completo por ahora)
                # En producción se usaría el modelo TaxDeclaration
                
                # Procesar conceptos de la declaración
                total_base = 0
                total_tax = 0
                
                for i in range(1, 21):  # Máximo 20 líneas
                    concept_code = request.POST.get(f'concept_code_{i}')
                    concept_name = request.POST.get(f'concept_name_{i}')
                    tax_base = request.POST.get(f'tax_base_{i}', 0)
                    tax_rate = request.POST.get(f'tax_rate_{i}', 0)
                    tax_amount = request.POST.get(f'tax_amount_{i}', 0)
                    
                    if concept_code and (tax_base or tax_amount):
                        tax_base = float(tax_base) if tax_base else 0
                        tax_rate = float(tax_rate) if tax_rate else 0
                        tax_amount = float(tax_amount) if tax_amount else 0
                        
                        # Si no se ingresó el impuesto, calcularlo
                        if tax_base > 0 and tax_rate > 0 and tax_amount == 0:
                            tax_amount = tax_base * (tax_rate / 100)
                        
                        total_base += tax_base
                        total_tax += tax_amount
                
                # Crear asiento contable si hay impuesto a pagar
                if total_tax > 0:
                    journal_type = JournalType.objects.filter(
                        company=company, code='CG'
                    ).first()
                    
                    if journal_type:
                        journal_entry = JournalEntry.objects.create(
                            company=company,
                            number=journal_type.get_next_sequence(),
                            journal_type=journal_type,
                            period=company.get_current_period(),
                            date=timezone.now().date(),
                            description=f"Declaración {tax_type.name} - {period_year}/{period_month or 'Anual'}",
                            currency=company.functional_currency,
                            created_by=request.user
                        )
                        
                        # Débito: Gasto por impuesto
                        tax_expense_account = Account.objects.filter(
                            company=company, code__startswith='5115'
                        ).first()
                        if tax_expense_account:
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=tax_expense_account,
                                description=f"Impuesto {tax_type.name}",
                                debit=total_tax,
                                credit=0,
                                created_by=request.user
                            )
                        
                        # Crédito: Impuesto por pagar
                        tax_payable_account = Account.objects.filter(
                            company=company, code__startswith='2367'
                        ).first()
                        if tax_payable_account:
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=tax_payable_account,
                                description=f"Por pagar {tax_type.name}",
                                debit=0,
                                credit=total_tax,
                                created_by=request.user
                            )
                
                messages.success(request, f'Declaración de {tax_type.name} creada exitosamente. Total: ${total_tax:,.2f}')
                return redirect('taxes:new_tax_declaration')
                
        except Exception as e:
            messages.error(request, f'Error al crear la declaración: {str(e)}')
    
    # Datos para el template
    context = {
        'current_company': current_company,
        'tax_types': TaxType.objects.filter(is_active=True),
        'current_year': timezone.now().year,
    }
    
    return render(request, 'taxes/new_tax_declaration.html', context)