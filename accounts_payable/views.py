from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models_supplier import Supplier
from .models_bill import PurchaseInvoice, PurchaseInvoiceLine
from .models_payment import SupplierPayment, PaymentAllocation
from accounting.models import Account, JournalEntry, JournalEntryLine, JournalType
from treasury.models import BankAccount
from core.models import Company
from core.utils import get_current_company, require_company_access

from taxes.models import TaxType


@login_required
@require_company_access
def new_purchase_invoice(request):
    current_company = request.current_company

    """Vista para crear nueva factura de compra."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos de la factura
                company_id = request.POST.get('company')
                supplier_id = request.POST.get('supplier')
                invoice_number = request.POST.get('invoice_number')
                date = request.POST.get('date')
                due_date = request.POST.get('due_date')
                description = request.POST.get('description', '')
                
                company = Company.objects.get(id=company_id)
                supplier = Supplier.objects.get(id=supplier_id)
                
                # Crear la factura
                invoice = PurchaseInvoice.objects.create(
                    company=company,
                    supplier=supplier,
                    invoice_number=invoice_number,
                    date=date,
                    due_date=due_date,
                    description=description,
                    created_by=request.user
                )
                
                # Procesar líneas de la factura
                subtotal = 0
                tax_amount = 0
                
                for i in range(1, 11):  # Máximo 10 líneas
                    account_id = request.POST.get(f'account_{i}')
                    quantity = request.POST.get(f'quantity_{i}', 0)
                    unit_price = request.POST.get(f'unit_price_{i}', 0)
                    tax_rate = request.POST.get(f'tax_rate_{i}', 0)
                    line_description = request.POST.get(f'line_description_{i}', '')
                    
                    if account_id and quantity and unit_price:
                        account = Account.objects.get(id=account_id)
                        quantity = float(quantity)
                        unit_price = float(unit_price)
                        tax_rate = float(tax_rate) if tax_rate else 0
                        
                        line_subtotal = quantity * unit_price
                        line_tax = line_subtotal * (tax_rate / 100)
                        line_total = line_subtotal + line_tax
                        
                        PurchaseInvoiceLine.objects.create(
                            invoice=invoice,
                            account=account,
                            description=line_description or f"Línea {i}",
                            quantity=quantity,
                            unit_price=unit_price,
                            tax_rate=tax_rate,
                            subtotal=line_subtotal,
                            tax_amount=line_tax,
                            total=line_total,
                            created_by=request.user
                        )
                        
                        subtotal += line_subtotal
                        tax_amount += line_tax
                
                # Actualizar totales de la factura
                invoice.subtotal = subtotal
                invoice.tax_amount = tax_amount
                invoice.total = subtotal + tax_amount
                invoice.save()
                
                # Crear asiento contable automático
                journal_type = JournalType.objects.filter(
                    company=company, code='CC'
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
                        description=f"Factura compra {invoice_number} - {supplier.name}",
                        currency=currency,
                        created_by=request.user
                    )
                    
                    # Líneas del asiento
                    for line in invoice.lines.all():
                        # Débito: Cuenta del gasto/activo
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=line.account,
                            description=line.description,
                            debit=line.subtotal,
                            credit=0,
                            line_number=1
                        )
                        
                        # Débito: IVA si aplica
                        if line.tax_amount > 0:
                            tax_account = Account.objects.filter(
                                company=company, code__startswith='2408'
                            ).first()
                            if tax_account:
                                JournalEntryLine.objects.create(
                                    journal_entry=journal_entry,
                                    account=tax_account,
                                    description=f"IVA {line.description}",
                                    debit=line.tax_amount,
                                    credit=0,
                                    line_number=2
                                )
                    
                    # Crédito: Cuenta por pagar al proveedor
                    supplier_account = Account.objects.filter(
                        company=company, code__startswith='2205'
                    ).first()
                    if supplier_account:
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=supplier_account,
                            description=f"Por pagar a {supplier.name}",
                            debit=0,
                            credit=invoice.total,
                            line_number=3
                        )
                
                messages.success(request, f'Factura de compra {invoice_number} creada exitosamente')
                return redirect('accounts_payable:new_purchase_invoice')
                
        except Exception as e:
            messages.error(request, f'Error al crear la factura: {str(e)}')
    
    # Datos para el template
    context = {
        'current_company': current_company,
        'suppliers': Supplier.objects.filter(is_active=True),
        'accounts': Account.objects.filter(is_detail=True, is_active=True),
        'tax_types': TaxType.objects.filter(is_active=True),
    }
    
    return render(request, 'accounts_payable/new_purchase_invoice.html', context)


@login_required
@require_company_access
def supplier_payment(request):
    current_company = request.current_company

    """Vista para pagar proveedores."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos del pago
                company_id = request.POST.get('company')
                supplier_id = request.POST.get('supplier')
                payment_method = request.POST.get('payment_method')
                bank_account_id = request.POST.get('bank_account')
                amount = request.POST.get('amount')
                date = request.POST.get('date')
                reference = request.POST.get('reference', '')
                description = request.POST.get('description', '')
                
                company = Company.objects.get(id=company_id)
                supplier = Supplier.objects.get(id=supplier_id)
                amount = float(amount)
                
                # Crear el pago
                payment = SupplierPayment.objects.create(
                    company=company,
                    supplier=supplier,
                    payment_method=payment_method,
                    amount=amount,
                    date=date,
                    reference=reference,
                    description=description or f"Pago a {supplier.name}",
                    created_by=request.user
                )
                
                # Procesar aplicación a facturas
                remaining_amount = amount
                
                for i in range(1, 11):  # Máximo 10 facturas
                    invoice_id = request.POST.get(f'invoice_{i}')
                    applied_amount = request.POST.get(f'applied_amount_{i}', 0)
                    
                    if invoice_id and applied_amount:
                        applied_amount = float(applied_amount)
                        if applied_amount > 0 and applied_amount <= remaining_amount:
                            invoice = PurchaseInvoice.objects.get(id=invoice_id)
                            
                            PaymentAllocation.objects.create(
                                payment=payment,
                                invoice=invoice,
                                amount=applied_amount,
                                created_by=request.user
                            )
                            
                            # Actualizar saldo de la factura
                            invoice.paid_amount += applied_amount
                            if invoice.paid_amount >= invoice.total:
                                invoice.status = 'paid'
                            else:
                                invoice.status = 'partial'
                            invoice.save()
                            
                            remaining_amount -= applied_amount
                
                # Crear asiento contable automático
                journal_type = JournalType.objects.filter(
                    company=company, code='CE'
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
                        description=f"Pago a {supplier.name} - {reference}",
                        currency=currency,
                        created_by=request.user
                    )
                    
                    # Débito: Cuenta por pagar al proveedor
                    supplier_account = Account.objects.filter(
                        company=company, code__startswith='2205'
                    ).first()
                    if supplier_account:
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=supplier_account,
                            description=f"Pago a {supplier.name}",
                            debit=amount,
                            credit=0,
                            line_number=1
                        )
                    
                    # Crédito: Cuenta de banco o caja
                    if payment_method == 'bank_transfer' and bank_account_id:
                        bank_account = BankAccount.objects.get(id=bank_account_id)
                        JournalEntryLine.objects.create(
                            journal_entry=journal_entry,
                            account=bank_account.account,
                            description=f"Transferencia a {supplier.name}",
                            debit=0,
                            credit=amount,
                            line_number=2
                        )
                    else:
                        # Cuenta de caja por defecto
                        cash_account = Account.objects.filter(
                            company=company, code__startswith='1105'
                        ).first()
                        if cash_account:
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=cash_account,
                                description=f"Pago efectivo a {supplier.name}",
                                debit=0,
                                credit=amount,
                                line_number=2
                            )
                
                messages.success(request, f'Pago de ${amount:,.2f} a {supplier.name} registrado exitosamente')
                return redirect('accounts_payable:supplier_payment')
                
        except Exception as e:
            messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    # Datos para el template
    context = {
        'current_company': current_company,
        'suppliers': Supplier.objects.filter(is_active=True),
        'bank_accounts': BankAccount.objects.filter(status='active'),
        'pending_invoices': PurchaseInvoice.objects.filter(
            status__in=['pending', 'partial']
        ).order_by('due_date'),
    }
    
    return render(request, 'accounts_payable/supplier_payment.html', context)
