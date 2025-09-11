from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal

from .models_bank import BankAccount, CashAccount, Bank
from .models_movement import BankMovement, CashMovement
from .models_reconciliation import BankReconciliation, CashFlow
from accounting.models_journal import JournalEntry, JournalEntryLine
from accounting.models_journal import JournalType
from accounting.models_accounts import Account
from core.models import Company, Period, Currency


@login_required
def bank_movement(request):
    """Vista para registrar movimientos bancarios."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos del movimiento
                company_id = request.POST.get('company')
                bank_account_id = request.POST.get('bank_account')
                movement_type = request.POST.get('movement_type')
                amount = request.POST.get('amount')
                date = request.POST.get('date')
                reference = request.POST.get('reference', '')
                description = request.POST.get('description', '')
                third_party = request.POST.get('third_party', '')
                
                company = Company.objects.get(id=company_id)
                bank_account = BankAccount.objects.get(id=bank_account_id)
                amount = float(amount)
                
                # Crear el movimiento bancario
                movement = BankMovement.objects.create(
                    bank_account=bank_account,
                    transaction_id=reference or '',
                    reference=reference or '',
                    date=date,
                    value_date=date,
                    movement_type='credit' if movement_type == 'deposit' else 'debit',
                    amount=amount,
                    balance=bank_account.current_balance + (amount if movement_type == 'deposit' else -amount),
                    description=description or f"Movimiento {movement_type}",
                    concept=third_party or 'Movimiento manual'
                )
                
                # Actualizar saldo de la cuenta bancaria
                if movement_type == 'deposit':
                    bank_account.current_balance += amount
                else:  # withdrawal
                    bank_account.current_balance -= amount
                bank_account.save()
                
                # Crear asiento contable automático
                journal_type = JournalType.objects.filter(
                    company=company, code='CB'
                ).first()
                
                if journal_type:
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
                        description=f"Movimiento bancario - {description}",
                        currency=currency,
                        created_by=request.user
                    )
                    
                    if movement_type == 'deposit':
                        # Débito: Cuenta bancaria
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=bank_account.accounting_account,
                            description=description,
                            debit=amount,
                            credit=0,
                            line_number=1
                        )
                        
                        # Crédito: Cuenta de ingresos varios (por defecto)
                        income_account = Account.objects.filter(
                            company=company, code__startswith='4295'
                        ).first()
                        if income_account:
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=income_account,
                                description=f"Ingreso bancario - {description}",
                                debit=0,
                                credit=amount,
                                line_number=2
                            )
                    else:  # withdrawal
                        # Débito: Cuenta de gastos varios (por defecto)
                        expense_account = Account.objects.filter(
                            company=company, code__startswith='5195'
                        ).first()
                        if expense_account:
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=expense_account,
                                description=f"Gasto bancario - {description}",
                                debit=amount,
                                credit=0,
                                line_number=1
                            )
                        
                        # Crédito: Cuenta bancaria
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=bank_account.accounting_account,
                            description=description,
                            debit=0,
                            credit=amount,
                            line_number=2
                        )
                
                messages.success(request, f'Movimiento bancario de ${amount:,.2f} registrado exitosamente')
                return redirect('treasury:bank_movement')
                
        except Exception as e:
            messages.error(request, f'Error al registrar el movimiento: {str(e)}')
    
    # Datos para el template
    context = {
        'companies': Company.objects.filter(is_active=True),
        'bank_accounts': BankAccount.objects.filter(status='active'),
        'recent_movements': BankMovement.objects.all().order_by('-date', '-created_at')[:10],
        'today': timezone.now().date(),
    }
    
    return render(request, 'treasury/bank_movement.html', context)


@login_required
def bank_reconciliation(request):
    """Vista para conciliación bancaria."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos de la conciliación
                company_id = request.POST.get('company')
                bank_account_id = request.POST.get('bank_account')
                statement_date = request.POST.get('statement_date')
                statement_balance = request.POST.get('statement_balance')
                
                company = Company.objects.get(id=company_id)
                bank_account = BankAccount.objects.get(id=bank_account_id)
                statement_balance = float(statement_balance)
                
                # Crear la conciliación
                reconciliation = BankReconciliation.objects.create(
                    company=company,
                    number=f"REC-{timezone.now().strftime('%Y%m%d')}-{BankReconciliation.objects.filter(company=company).count() + 1:03d}",
                    bank_account=bank_account,
                    period_start=statement_date,
                    period_end=statement_date,
                    bank_balance=statement_balance,
                    book_balance=bank_account.current_balance,
                    created_by=request.user
                )
                
                # Procesar ajustes
                total_adjustments = 0
                
                for i in range(1, 11):  # Máximo 10 ajustes
                    adjustment_type = request.POST.get(f'adjustment_type_{i}')
                    adjustment_amount = request.POST.get(f'adjustment_amount_{i}', 0)
                    adjustment_description = request.POST.get(f'adjustment_description_{i}', '')
                    
                    if adjustment_type and adjustment_amount:
                        adjustment_amount = float(adjustment_amount)
                        
                        # Crear movimiento de ajuste
                        BankMovement.objects.create(
                            bank_account=bank_account,
                            transaction_id=f"CONC-{reconciliation.id}",
                            reference=f"CONC-{reconciliation.id}",
                            date=statement_date,
                            value_date=statement_date,
                            movement_type='credit' if adjustment_type == 'add' else 'debit',
                            amount=adjustment_amount,
                            balance=bank_account.current_balance + (adjustment_amount if adjustment_type == 'add' else -adjustment_amount),
                            description=f"Ajuste conciliación: {adjustment_description}",
                            concept='Conciliación bancaria'
                        )
                        
                        # Actualizar saldo
                        if adjustment_type == 'add':
                            bank_account.current_balance += adjustment_amount
                            total_adjustments += adjustment_amount
                        else:
                            bank_account.current_balance -= adjustment_amount
                            total_adjustments -= adjustment_amount
                
                bank_account.save()
                
                # Actualizar conciliación
                reconciliation.reconciled_balance = bank_account.current_balance
                reconciliation.difference = abs(statement_balance - bank_account.current_balance)
                if reconciliation.difference < 0.01:
                    reconciliation.status = 'completed'
                else:
                    reconciliation.status = 'in_progress'
                reconciliation.save()
                
                if reconciliation.difference < 0.01:
                    messages.success(request, f'Conciliación completada exitosamente. Diferencia: ${reconciliation.difference:,.2f}')
                else:
                    messages.warning(request, f'Conciliación con diferencia de ${reconciliation.difference:,.2f}. Revise los ajustes.')
                
                return redirect('treasury:bank_reconciliation')
                
        except Exception as e:
            messages.error(request, f'Error en la conciliación: {str(e)}')
    
    # Datos para el template
    context = {
        'companies': Company.objects.filter(is_active=True),
        'bank_accounts': BankAccount.objects.filter(status='active'),
        'recent_movements': BankMovement.objects.all().order_by('-date')[:20],
        'today': timezone.now().date(),
    }
    
    return render(request, 'treasury/bank_reconciliation.html', context)
"""
Additional views for the treasury module.
These should be added to views.py
"""

@login_required
def treasury_dashboard(request):
    """Dashboard principal de tesorería."""
    # Obtener estadísticas generales
    total_bank_accounts = BankAccount.objects.filter(status='active').count()
    total_cash_accounts = CashAccount.objects.filter(status='active').count()
    
    # Saldos totales
    total_bank_balance = BankAccount.objects.filter(status='active').aggregate(
        total=Sum('current_balance'))['total'] or 0
    total_cash_balance = CashAccount.objects.filter(status='active').aggregate(
        total=Sum('current_balance'))['total'] or 0
    
    # Movimientos recientes
    recent_bank_movements = BankMovement.objects.all().order_by('-created_at')[:5]
    recent_cash_movements = CashMovement.objects.all().order_by('-created_at')[:5]
    
    # Conciliaciones pendientes
    pending_reconciliations = BankReconciliation.objects.filter(
        status__in=['draft', 'in_progress']).count()
    
    context = {
        'total_bank_accounts': total_bank_accounts,
        'total_cash_accounts': total_cash_accounts,
        'total_bank_balance': total_bank_balance,
        'total_cash_balance': total_cash_balance,
        'total_balance': total_bank_balance + total_cash_balance,
        'recent_bank_movements': recent_bank_movements,
        'recent_cash_movements': recent_cash_movements,
        'pending_reconciliations': pending_reconciliations,
    }
    
    return render(request, 'treasury/dashboard.html', context)


@login_required
def bank_account_list(request):
    """Lista de cuentas bancarias."""
    accounts = BankAccount.objects.all().order_by('code')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'treasury/bank_account_list.html', context)


@login_required
def bank_account_create(request):
    """Crear nueva cuenta bancaria."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                company_id = request.POST.get('company')
                bank_id = request.POST.get('bank')
                
                company = Company.objects.get(id=company_id)
                bank = Bank.objects.get(code=bank_id)
                
                account = BankAccount.objects.create(
                    company=company,
                    code=request.POST.get('code'),
                    name=request.POST.get('name'),
                    bank=bank,
                    account_number=request.POST.get('account_number'),
                    account_type=request.POST.get('account_type'),
                    currency=Currency.objects.get(code=request.POST.get('currency', 'COP')),
                    opening_balance=Decimal(request.POST.get('opening_balance', '0')),
                    current_balance=Decimal(request.POST.get('opening_balance', '0')),
                    accounting_account=Account.objects.get(id=request.POST.get('accounting_account')),
                    created_by=request.user
                )
                
                messages.success(request, f'Cuenta bancaria {account.name} creada exitosamente')
                return redirect('treasury:bank_account_list')
                
        except Exception as e:
            messages.error(request, f'Error al crear cuenta bancaria: {str(e)}')
    
    context = {
        'companies': Company.objects.filter(is_active=True),
        'banks': Bank.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'accounts': Account.objects.filter(account_type='asset', code__startswith='11').order_by('code'),
    }
    
    return render(request, 'treasury/bank_account_form.html', context)


@login_required
def bank_account_edit(request, pk):
    """Editar cuenta bancaria."""
    account = get_object_or_404(BankAccount, pk=pk)
    
    if request.method == 'POST':
        try:
            account.name = request.POST.get('name')
            account.account_type = request.POST.get('account_type')
            account.status = request.POST.get('status')
            account.save()
            
            messages.success(request, f'Cuenta bancaria {account.name} actualizada exitosamente')
            return redirect('treasury:bank_account_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar cuenta bancaria: {str(e)}')
    
    context = {
        'account': account,
        'banks': Bank.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
    }
    
    return render(request, 'treasury/bank_account_form.html', context)


@login_required
def cash_account_list(request):
    """Lista de cuentas de caja."""
    accounts = CashAccount.objects.all().order_by('code')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'treasury/cash_account_list.html', context)


@login_required
def cash_account_create(request):
    """Crear nueva cuenta de caja."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                company_id = request.POST.get('company')
                company = Company.objects.get(id=company_id)
                
                account = CashAccount.objects.create(
                    company=company,
                    code=request.POST.get('code'),
                    name=request.POST.get('name'),
                    location=request.POST.get('location', ''),
                    currency=Currency.objects.get(code=request.POST.get('currency', 'COP')),
                    opening_balance=Decimal(request.POST.get('opening_balance', '0')),
                    current_balance=Decimal(request.POST.get('opening_balance', '0')),
                    max_balance=Decimal(request.POST.get('max_balance', '0')),
                    accounting_account=Account.objects.get(id=request.POST.get('accounting_account')),
                    created_by=request.user
                )
                
                messages.success(request, f'Cuenta de caja {account.name} creada exitosamente')
                return redirect('treasury:cash_account_list')
                
        except Exception as e:
            messages.error(request, f'Error al crear cuenta de caja: {str(e)}')
    
    context = {
        'companies': Company.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'accounts': Account.objects.filter(account_type='asset', code__startswith='11').order_by('code'),
    }
    
    return render(request, 'treasury/cash_account_form.html', context)


@login_required
def cash_account_edit(request, pk):
    """Editar cuenta de caja."""
    account = get_object_or_404(CashAccount, pk=pk)
    
    if request.method == 'POST':
        try:
            account.name = request.POST.get('name')
            account.location = request.POST.get('location', '')
            account.max_balance = Decimal(request.POST.get('max_balance', '0'))
            account.status = request.POST.get('status')
            account.save()
            
            messages.success(request, f'Cuenta de caja {account.name} actualizada exitosamente')
            return redirect('treasury:cash_account_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar cuenta de caja: {str(e)}')
    
    context = {
        'account': account,
        'currencies': Currency.objects.filter(is_active=True),
    }
    
    return render(request, 'treasury/cash_account_form.html', context)


@login_required
def bank_movement_list(request):
    """Lista de movimientos bancarios."""
    movements = BankMovement.objects.all().order_by('-date', '-created_at')[:100]
    
    context = {
        'movements': movements,
    }
    
    return render(request, 'treasury/bank_movement_list.html', context)


@login_required
def cash_movement(request):
    """Vista para registrar movimientos de caja."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                company_id = request.POST.get('company')
                cash_account_id = request.POST.get('cash_account')
                movement_type = request.POST.get('movement_type')
                amount = Decimal(request.POST.get('amount'))
                date = request.POST.get('date')
                
                company = Company.objects.get(id=company_id)
                cash_account = CashAccount.objects.get(id=cash_account_id)
                
                # Crear el movimiento de caja
                movement = CashMovement.objects.create(
                    company=company,
                    number=f"{'RC' if movement_type == 'receipt' else 'EC'}-{timezone.now().strftime('%Y%m%d')}-{CashMovement.objects.filter(company=company).count() + 1:04d}",
                    cash_account=cash_account,
                    movement_type=movement_type,
                    date=date,
                    third_party_name=request.POST.get('third_party_name', ''),
                    third_party_document=request.POST.get('third_party_document', ''),
                    currency=cash_account.currency,
                    amount=amount,
                    concept=request.POST.get('concept', ''),
                    description=request.POST.get('description', ''),
                    created_by=request.user
                )
                
                # Actualizar saldo de la cuenta de caja
                if movement_type == 'receipt':
                    cash_account.current_balance += amount
                else:  # disbursement
                    cash_account.current_balance -= amount
                cash_account.save()
                
                messages.success(request, f'Movimiento de caja de ${amount:,.2f} registrado exitosamente')
                return redirect('treasury:cash_movement')
                
        except Exception as e:
            messages.error(request, f'Error al registrar movimiento de caja: {str(e)}')
    
    context = {
        'companies': Company.objects.filter(is_active=True),
        'cash_accounts': CashAccount.objects.filter(status='active'),
        'recent_movements': CashMovement.objects.all().order_by('-date', '-created_at')[:10],
        'today': timezone.now().date(),
    }
    
    return render(request, 'treasury/cash_movement.html', context)


@login_required
def cash_movement_list(request):
    """Lista de movimientos de caja."""
    movements = CashMovement.objects.all().order_by('-date', '-created_at')[:100]
    
    context = {
        'movements': movements,
    }
    
    return render(request, 'treasury/cash_movement_list.html', context)


@login_required
def bank_reconciliation_list(request):
    """Lista de conciliaciones bancarias."""
    reconciliations = BankReconciliation.objects.all().order_by('-period_end')[:50]
    
    context = {
        'reconciliations': reconciliations,
    }
    
    return render(request, 'treasury/bank_reconciliation_list.html', context)


@login_required
def cash_flow(request):
    """Vista para flujo de caja."""
    # Obtener flujos de caja del período actual
    current_period = Period.objects.filter(status='open').first()
    
    if current_period:
        flows = CashFlow.objects.filter(period=current_period).order_by('-date')
    else:
        flows = CashFlow.objects.none()
    
    # Totales por categoría
    operating_total = flows.filter(category='operating').aggregate(Sum('net_flow'))['net_flow__sum'] or 0
    investing_total = flows.filter(category='investing').aggregate(Sum('net_flow'))['net_flow__sum'] or 0
    financing_total = flows.filter(category='financing').aggregate(Sum('net_flow'))['net_flow__sum'] or 0
    
    context = {
        'flows': flows[:20],
        'current_period': current_period,
        'operating_total': operating_total,
        'investing_total': investing_total,
        'financing_total': financing_total,
        'total_flow': operating_total + investing_total + financing_total,
    }
    
    return render(request, 'treasury/cash_flow.html', context)


@login_required
def cash_flow_report(request):
    """Reporte de flujo de caja."""
    period_id = request.GET.get('period')
    
    if period_id:
        period = get_object_or_404(Period, pk=period_id)
        flows = CashFlow.objects.filter(period=period).order_by('category', 'date')
    else:
        current_period = Period.objects.filter(status='open').first()
        period = current_period
        flows = CashFlow.objects.filter(period=current_period).order_by('category', 'date') if current_period else CashFlow.objects.none()
    
    # Agrupar por categoría
    operating_flows = flows.filter(category='operating')
    investing_flows = flows.filter(category='investing')
    financing_flows = flows.filter(category='financing')
    
    context = {
        'period': period,
        'periods': Period.objects.all().order_by('-start_date')[:12],
        'operating_flows': operating_flows,
        'investing_flows': investing_flows,
        'financing_flows': financing_flows,
        'operating_total': operating_flows.aggregate(Sum('net_flow'))['net_flow__sum'] or 0,
        'investing_total': investing_flows.aggregate(Sum('net_flow'))['net_flow__sum'] or 0,
        'financing_total': financing_flows.aggregate(Sum('net_flow'))['net_flow__sum'] or 0,
    }
    
    return render(request, 'treasury/cash_flow_report.html', context)