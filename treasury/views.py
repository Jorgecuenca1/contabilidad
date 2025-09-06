from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models_bank import BankAccount
from .models_movement import BankMovement
from .models_reconciliation import BankReconciliation
from accounting.models import Account, JournalEntry, JournalEntryLine, JournalType
from core.models import Company


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
                    company=company,
                    bank_account=bank_account,
                    movement_type=movement_type,
                    amount=amount,
                    date=date,
                    reference=reference,
                    description=description or f"Movimiento {movement_type}",
                    third_party=third_party,
                    created_by=request.user
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
                from .models import BankReconciliation
                reconciliation = BankReconciliation.objects.create(
                    company=company,
                    bank_account=bank_account,
                    statement_date=statement_date,
                    statement_balance=statement_balance,
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
                            company=company,
                            bank_account=bank_account,
                            movement_type='deposit' if adjustment_type == 'add' else 'withdrawal',
                            amount=adjustment_amount,
                            date=statement_date,
                            reference=f"CONC-{reconciliation.id}",
                            description=f"Ajuste conciliación: {adjustment_description}",
                            created_by=request.user
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
                reconciliation.adjusted_balance = bank_account.current_balance
                reconciliation.difference = abs(statement_balance - bank_account.current_balance)
                reconciliation.is_balanced = reconciliation.difference < 0.01
                reconciliation.save()
                
                if reconciliation.is_balanced:
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
    }
    
    return render(request, 'treasury/bank_reconciliation.html', context)
