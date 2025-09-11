"""
Vistas para el módulo de cuentas por cobrar.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from decimal import Decimal

from core.models import Company
from core.utils import get_current_company, require_company_access

from accounting.models_accounts import Account
from .models_customer import Customer, CustomerType
from .models_invoice import Invoice, InvoiceLine
from .models_payment import Payment, PaymentAllocation
from third_parties.models import ThirdParty


@login_required
@require_company_access
def new_invoice(request):
    """
    Página para crear nueva factura de venta.
    """
    current_company = request.current_company
    customers = Customer.objects.filter(company=current_company, is_active=True)
    customer_types = CustomerType.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Datos generales de la factura
            customer_id = request.POST.get('customer')
            invoice_date = request.POST.get('invoice_date')
            due_date = request.POST.get('due_date')
            reference = request.POST.get('reference')
            notes = request.POST.get('notes', '')
            
            company = current_company  # Usar la empresa del contexto
            customer = Customer.objects.get(id=customer_id, company=company)
            
            # Generar número de factura
            last_invoice = Invoice.objects.filter(company=company).order_by('-invoice_number').first()
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_number = int(last_invoice.invoice_number.split('-')[-1])
                    new_number = f"FV-{last_number + 1:06d}"
                except:
                    new_number = "FV-000001"
            else:
                new_number = "FV-000001"
            
            # Crear la factura
            invoice = Invoice.objects.create(
                company=company,
                customer=customer,
                invoice_number=new_number,
                invoice_date=invoice_date,
                due_date=due_date,
                reference=reference,
                notes=notes,
                created_by=request.user
            )
            
            # Procesar las líneas de la factura
            subtotal = Decimal('0.00')
            
            for i in range(1, 21):  # Máximo 20 líneas
                description = request.POST.get(f'line_description_{i}')
                quantity = request.POST.get(f'quantity_{i}')
                unit_price = request.POST.get(f'unit_price_{i}')
                
                if description and quantity and unit_price:
                    quantity = Decimal(quantity)
                    unit_price = Decimal(unit_price)
                    line_total = quantity * unit_price
                    
                    InvoiceLine.objects.create(
                        invoice=invoice,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=line_total,
                        created_by=request.user
                    )
                    
                    subtotal += line_total
            
            # Calcular impuestos
            tax_rate = Decimal('0.19')  # IVA 19%
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            # Actualizar totales de la factura
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_amount
            invoice.total_amount = total_amount
            invoice.save()
            
            messages.success(request, f'Factura #{invoice.number} creada exitosamente por ${total_amount:,.2f}')
            return redirect('accounts_receivable:new_invoice')
            
        except Exception as e:
            messages.error(request, f'Error al crear la factura: {str(e)}')
    
    context = {
        'customers': customers,
        'customer_types': customer_types,
        'current_company': current_company,
    }
    
    return render(request, 'accounts_receivable/new_invoice.html', context)


@login_required
@require_company_access
def new_payment(request):
    current_company = request.current_company

    """
    Página para registrar nuevo pago de cliente.
    """
    companies = Company.objects.filter(is_active=True)
    customers = Customer.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Datos del pago
            company_id = request.POST.get('company')
            customer_id = request.POST.get('customer')
            payment_date = request.POST.get('payment_date')
            amount = request.POST.get('amount')
            payment_method = request.POST.get('payment_method')
            reference = request.POST.get('reference')
            notes = request.POST.get('notes', '')
            
            company = Company.objects.get(id=company_id)
            customer = Customer.objects.get(id=customer_id)
            amount = Decimal(amount)
            
            # Crear el pago
            payment = Payment.objects.create(
                company=company,
                customer=customer,
                payment_date=payment_date,
                amount=amount,
                payment_method=payment_method,
                reference=reference,
                notes=notes,
                created_by=request.user
            )
            
            # Aplicar pago a facturas pendientes automáticamente
            pending_invoices = Invoice.objects.filter(
                company=company,
                customer=customer,
                status='pending'
            ).order_by('due_date')
            
            remaining_amount = amount
            
            for invoice in pending_invoices:
                if remaining_amount <= 0:
                    break
                
                pending_amount = invoice.total_amount - invoice.paid_amount
                
                if pending_amount > 0:
                    allocation_amount = min(remaining_amount, pending_amount)
                    
                    PaymentAllocation.objects.create(
                        payment=payment,
                        invoice=invoice,
                        amount=allocation_amount,
                        created_by=request.user
                    )
                    
                    # Actualizar monto pagado de la factura
                    invoice.paid_amount += allocation_amount
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.status = 'paid'
                    invoice.save()
                    
                    remaining_amount -= allocation_amount
            
            messages.success(request, f'Pago registrado exitosamente por ${amount:,.2f}')
            return redirect('accounts_receivable:new_payment')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
    
    context = {
        'companies': companies,
        'customers': customers,
    }
    
    return render(request, 'accounts_receivable/new_payment.html', context)


@login_required
@require_company_access
def get_customer_invoices(request):
    current_company = request.current_company

    """
    API para obtener facturas pendientes de un cliente.
    """
    customer_id = request.GET.get('customer_id')
    company_id = request.GET.get('company_id')
    
    if not customer_id or not company_id:
        return JsonResponse({'invoices': []})
    
    invoices = Invoice.objects.filter(
        customer_id=customer_id,
        company_id=company_id,
        status='pending'
    ).order_by('due_date')
    
    invoices_data = []
    for invoice in invoices:
        pending_amount = invoice.total_amount - invoice.paid_amount
        invoices_data.append({
            'id': invoice.id,
            'number': invoice.number,
            'date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'due_date': invoice.due_date.strftime('%Y-%m-%d'),
            'total_amount': float(invoice.total_amount),
            'paid_amount': float(invoice.paid_amount),
            'pending_amount': float(pending_amount),
            'days_overdue': (invoice.due_date - invoice.invoice_date).days if invoice.due_date < invoice.invoice_date else 0
        })
    
    return JsonResponse({'invoices': invoices_data})


@login_required
@require_company_access
def get_customers_json(request):
    current_company = request.current_company

    """
    API para obtener clientes en formato JSON.
    """
    company_id = request.GET.get('company')
    search = request.GET.get('search', '')
    
    customers = Customer.objects.filter(is_active=True)
    
    if company_id:
        customers = customers.filter(company_id=company_id)
    
    if search:
        customers = customers.filter(
            Q(name__icontains=search) | 
            Q(document_number__icontains=search) |
            Q(email__icontains=search)
        )[:20]
    
    customers_data = [
        {
            'id': customer.id,
            'name': customer.name,
            'document_number': customer.document_number,
            'email': customer.email,
            'full_name': f"{customer.document_number} - {customer.name}"
        }
        for customer in customers
    ]
    
    return JsonResponse({'customers': customers_data})


@login_required
@require_company_access
def index(request):
    current_company = request.current_company

    """Dashboard principal de Cuentas por Cobrar."""
    return dashboard(request)


@login_required
@require_company_access
def dashboard(request):
    current_company = request.current_company

    """Dashboard con estadísticas de CxC."""
    companies = Company.objects.filter(is_active=True)
    
    # Statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_invoices = Invoice.objects.count()
    pending_invoices = Invoice.objects.filter(status__in=['draft', 'sent', 'partial']).count()
    overdue_invoices = Invoice.objects.filter(status='overdue').count()
    
    # Recent activity
    recent_invoices = Invoice.objects.select_related('customer', 'company').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('customer', 'company').order_by('-created_at')[:5]
    
    context = {
        'companies': companies,
        'total_customers': total_customers,
        'total_invoices': total_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'recent_invoices': recent_invoices,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'accounts_receivable/dashboard.html', context)


@login_required
@require_company_access
def customer_list(request):
    current_company = request.current_company

    """Lista de clientes."""
    search = request.GET.get('search', '')
    company_filter = request.GET.get('company', '')
    
    customers = Customer.objects.filter(is_active=True).select_related('company', 'customer_type')
    
    if search:
        customers = customers.filter(
            Q(business_name__icontains=search) |
            Q(name__icontains=search) |
            Q(document_number__icontains=search) |
            Q(email__icontains=search)
        )
    
    if company_filter:
        customers = customers.filter(company_id=company_filter)
    
    # Paginate
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)
    
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'customers': customers_page,
        'companies': companies,
        'search': search,
        'company_filter': company_filter,
    }
    
    return render(request, 'accounts_receivable/customer_list.html', context)

@login_required
def customer_detail(request, customer_id):
    """Detalle del cliente."""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Get customer invoices
    invoices = customer.invoices.order_by('-invoice_date')[:10]
    
    # Get customer payments
    payments = customer.payments.order_by('-date')[:10]
    
    context = {
        'customer': customer,
        'invoices': invoices,
        'payments': payments,
    }
    
    return render(request, 'accounts_receivable/customer_detail.html', context)


@login_required
def edit_customer(request, customer_id):
    """Editar cliente."""
    customer = get_object_or_404(Customer, id=customer_id)
    companies = Company.objects.filter(is_active=True)
    customer_types = CustomerType.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Update customer fields
            customer.document_type = request.POST.get('document_type')
            customer.document_number = request.POST.get('document_number')
            customer.verification_digit = request.POST.get('verification_digit', '')
            customer.business_name = request.POST.get('business_name', '')
            customer.trade_name = request.POST.get('trade_name', '')
            customer.first_name = request.POST.get('first_name', '')
            customer.last_name = request.POST.get('last_name', '')
            customer.customer_type_id = request.POST.get('customer_type')
            customer.regime = request.POST.get('regime', 'common')
            customer.address = request.POST.get('address')
            customer.city = request.POST.get('city')
            customer.state = request.POST.get('state')
            customer.country = request.POST.get('country', 'Colombia')
            customer.postal_code = request.POST.get('postal_code', '')
            customer.phone = request.POST.get('phone', '')
            customer.mobile = request.POST.get('mobile', '')
            customer.email = request.POST.get('email', '')
            customer.website = request.POST.get('website', '')
            customer.credit_limit = Decimal(request.POST.get('credit_limit', '0'))
            customer.credit_days = int(request.POST.get('credit_days', '30'))
            customer.discount_percentage = Decimal(request.POST.get('discount_percentage', '0'))
            customer.is_tax_responsible = bool(request.POST.get('is_tax_responsible'))
            customer.is_active = bool(request.POST.get('is_active', True))
            
            customer.save()
            
            messages.success(request, f'Cliente {customer.code} actualizado exitosamente')
            return redirect('accounts_receivable:customer_detail', customer_id=customer.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar cliente: {str(e)}')
    
    context = {
        'customer': customer,
        'companies': companies,
        'customer_types': customer_types,
    }
    
    return render(request, 'accounts_receivable/edit_customer.html', context)


@login_required
@require_company_access
def invoice_list(request):
    current_company = request.current_company

    """Lista de facturas."""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    company_filter = request.GET.get('company', '')
    
    invoices = Invoice.objects.select_related('customer', 'company')
    
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(customer__business_name__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(reference__icontains=search)
        )
    
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    if company_filter:
        invoices = invoices.filter(company_id=company_filter)
    
    invoices = invoices.order_by('-invoice_date')
    
    # Paginate
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    invoices_page = paginator.get_page(page_number)
    
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'invoices': invoices_page,
        'companies': companies,
        'search': search,
        'status_filter': status_filter,
        'company_filter': company_filter,
        'status_choices': Invoice.STATUS_CHOICES,
    }
    
    return render(request, 'accounts_receivable/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """Detalle de factura."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'accounts_receivable/invoice_detail.html', context)


@login_required
def edit_invoice(request, invoice_id):
    """Editar factura."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Only allow editing of draft invoices
    if invoice.status != 'draft':
        messages.warning(request, 'Solo se pueden editar facturas en borrador')
        return redirect('accounts_receivable:invoice_detail', invoice_id=invoice.id)
    
    companies = Company.objects.filter(is_active=True)
    customers = Customer.objects.filter(is_active=True)
    
    context = {
        'invoice': invoice,
        'companies': companies,
        'customers': customers,
        'editing': True,
    }
    
    return render(request, 'accounts_receivable/edit_invoice.html', context)


@login_required
@require_company_access
def payment_list(request):
    current_company = request.current_company

    """Lista de pagos."""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    company_filter = request.GET.get('company', '')
    
    payments = Payment.objects.select_related('customer', 'company')
    
    if search:
        payments = payments.filter(
            Q(number__icontains=search) |
            Q(customer__business_name__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(reference__icontains=search)
        )
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if company_filter:
        payments = payments.filter(company_id=company_filter)
    
    payments = payments.order_by('-date')
    
    # Paginate
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    payments_page = paginator.get_page(page_number)
    
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'payments': payments_page,
        'companies': companies,
        'search': search,
        'status_filter': status_filter,
        'company_filter': company_filter,
        'status_choices': Payment.STATUS_CHOICES,
    }
    
    return render(request, 'accounts_receivable/payment_list.html', context)


@login_required
def payment_detail(request, payment_id):
    """Detalle del pago."""
    payment = get_object_or_404(Payment, id=payment_id)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'accounts_receivable/payment_detail.html', context)