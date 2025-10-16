"""
Views para el módulo de Facturación de Salud
Sistema de facturación de servicios de salud con integración RIPS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime, timedelta

from core.decorators import company_required
from core.models import Company
from core.utils import get_current_company
from .models import (
    HealthTariff, HealthInvoice, HealthInvoiceItem,
    HealthPayment, InvoiceGlosa
)


@login_required
@company_required
def billing_dashboard(request):
    """
    Dashboard principal del módulo de facturación de salud
    Muestra estadísticas, facturas pendientes, glosas, etc.
    """
    company = get_current_company(request)

    # Obtener parámetros de filtro (mes actual por defecto)
    today = timezone.now().date()
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = today.month
        year = today.year

    # Filtro base
    invoices = HealthInvoice.objects.filter(
        company=company,
        invoice_date__month=month,
        invoice_date__year=year
    )

    # Estadísticas principales
    total_invoiced = invoices.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    total_paid = invoices.filter(
        status='paid'
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    pending_amount = invoices.filter(
        status__in=['issued', 'approved']
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    glosa_amount = invoices.filter(
        has_glosa=True
    ).aggregate(
        total=Sum('glosa_amount')
    )['total'] or Decimal('0.00')

    # Facturas por estado
    invoices_by_status = invoices.values('status').annotate(
        count=Count('id'),
        amount=Sum('total')
    ).order_by('status')

    # Facturas recientes (últimas 10)
    recent_invoices = invoices.select_related(
        'payer', 'patient', 'created_by'
    ).order_by('-created_at')[:10]

    # Facturas con glosa
    glosa_invoices = invoices.filter(
        has_glosa=True
    ).select_related('payer', 'patient').order_by('-invoice_date')[:5]

    # Top 5 pagadores por monto
    top_payers = invoices.values(
        'payer__name'
    ).annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('-total')[:5]

    # Facturas por tipo
    invoices_by_type = invoices.values('invoice_type').annotate(
        count=Count('id'),
        amount=Sum('total')
    ).order_by('-amount')

    # Tarifario activo
    active_tariff = HealthTariff.objects.filter(
        company=company,
        is_active=True
    ).first()

    context = {
        'company': company,
        'month': month,
        'year': year,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'glosa_amount': glosa_amount,
        'invoices_by_status': invoices_by_status,
        'recent_invoices': recent_invoices,
        'glosa_invoices': glosa_invoices,
        'top_payers': top_payers,
        'invoices_by_type': invoices_by_type,
        'active_tariff': active_tariff,
        'total_invoices': invoices.count(),
    }

    return render(request, 'billing_health/dashboard.html', context)


@login_required
@company_required
def invoice_list(request):
    """
    Lista de facturas con filtros avanzados
    """
    company = get_current_company(request)

    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    payer_id = request.GET.get('payer', '')
    invoice_type = request.GET.get('invoice_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    has_glosa = request.GET.get('has_glosa', '')
    rips_generated = request.GET.get('rips_generated', '')

    # Query base
    invoices = HealthInvoice.objects.filter(company=company)

    # Aplicar filtros
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(patient__document_number__icontains=search) |
            Q(payer__name__icontains=search)
        )

    if status:
        invoices = invoices.filter(status=status)

    if payer_id:
        invoices = invoices.filter(payer_id=payer_id)

    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(invoice_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(invoice_date__lte=date_to_obj)
        except ValueError:
            pass

    if has_glosa:
        invoices = invoices.filter(has_glosa=(has_glosa == 'true'))

    if rips_generated:
        invoices = invoices.filter(rips_generated=(rips_generated == 'true'))

    # Ordenar
    sort_by = request.GET.get('sort', '-invoice_date')
    invoices = invoices.select_related(
        'payer', 'patient', 'created_by', 'tariff'
    ).order_by(sort_by)

    # Paginación
    paginator = Paginator(invoices, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Para los filtros
    from third_parties.models import ThirdParty
    payers = ThirdParty.objects.filter(
        company=company,
        is_payer=True,
        is_active=True
    ).order_by('name')

    context = {
        'page_obj': page_obj,
        'payers': payers,
        'search': search,
        'status': status,
        'payer_id': payer_id,
        'invoice_type': invoice_type,
        'date_from': date_from,
        'date_to': date_to,
        'has_glosa': has_glosa,
        'rips_generated': rips_generated,
        'sort_by': sort_by,
        'total_results': paginator.count,
    }

    return render(request, 'billing_health/invoice_list.html', context)


@login_required
@company_required
def invoice_create(request):
    """
    Crear nueva factura de salud
    """
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Obtener datos básicos
            invoice_number = request.POST.get('invoice_number')
            invoice_date = request.POST.get('invoice_date')
            invoice_type = request.POST.get('invoice_type')
            payer_id = request.POST.get('payer_id')
            patient_id = request.POST.get('patient_id')
            tariff_id = request.POST.get('tariff_id')
            contract_number = request.POST.get('contract_number', '')

            # DIAN fields
            dian_resolution = request.POST.get('dian_resolution', '')
            authorized_range_from = request.POST.get('authorized_range_from', 0)
            authorized_range_to = request.POST.get('authorized_range_to', 0)
            resolution_date = request.POST.get('resolution_date', None)

            # Validaciones
            if not invoice_number:
                messages.error(request, 'El número de factura es obligatorio')
                return redirect('billing_health:invoice_create')

            if HealthInvoice.objects.filter(
                company=company,
                invoice_number=invoice_number
            ).exists():
                messages.error(request, 'Ya existe una factura con ese número')
                return redirect('billing_health:invoice_create')

            # Crear factura
            invoice = HealthInvoice.objects.create(
                company=company,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                invoice_type=invoice_type,
                payer_id=payer_id,
                patient_id=patient_id,
                tariff_id=tariff_id,
                contract_number=contract_number,
                dian_resolution=dian_resolution,
                authorized_range_from=authorized_range_from or 0,
                authorized_range_to=authorized_range_to or 0,
                resolution_date=resolution_date if resolution_date else None,
                status='draft',
                created_by=request.user
            )

            messages.success(request, f'Factura {invoice_number} creada exitosamente')
            return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            messages.error(request, f'Error al crear factura: {str(e)}')
            return redirect('billing_health:invoice_create')

    # GET request - mostrar formulario
    from third_parties.models import ThirdParty

    payers = ThirdParty.objects.filter(
        company=company,
        is_payer=True,
        is_active=True
    ).order_by('name')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company=company,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name')[:100]  # Limitar para performance

    tariffs = HealthTariff.objects.filter(
        company=company,
        is_active=True
    ).order_by('-created_at')

    # Siguiente número de factura sugerido
    last_invoice = HealthInvoice.objects.filter(
        company=company
    ).order_by('-invoice_number').first()

    suggested_number = ''
    if last_invoice:
        try:
            last_num = int(''.join(filter(str.isdigit, last_invoice.invoice_number)))
            suggested_number = f"FAC-{last_num + 1:06d}"
        except ValueError:
            suggested_number = f"FAC-{timezone.now().year}-001"
    else:
        suggested_number = f"FAC-{timezone.now().year}-001"

    context = {
        'payers': payers,
        'patients': patients,
        'tariffs': tariffs,
        'suggested_number': suggested_number,
        'today': timezone.now().date(),
    }

    return render(request, 'billing_health/invoice_form.html', context)


@login_required
@company_required
def invoice_detail(request, invoice_id):
    """
    Detalle de factura con items, pagos y glosas
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    # Items de la factura
    items = invoice.items.all().order_by('line_number')

    # Pagos realizados
    payments = invoice.payments.all().order_by('-payment_date')

    # Glosas
    glosas = invoice.glosas.all().order_by('-created_at')

    # Calcular totales
    total_items = items.count()
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    pending_amount = invoice.total - total_paid

    context = {
        'invoice': invoice,
        'items': items,
        'payments': payments,
        'glosas': glosas,
        'total_items': total_items,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
    }

    return render(request, 'billing_health/invoice_detail.html', context)


@login_required
@company_required
def invoice_add_item(request, invoice_id):
    """
    Agregar item a una factura
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if invoice.status not in ['draft', 'pending']:
        messages.error(request, 'No se pueden agregar items a una factura aprobada o pagada')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    if request.method == 'POST':
        try:
            # Obtener datos del item
            service_type = request.POST.get('service_type')
            service_code = request.POST.get('service_code')
            service_name = request.POST.get('service_name')
            diagnosis_code = request.POST.get('diagnosis_code', '')
            quantity = Decimal(request.POST.get('quantity', '1'))
            unit_price = Decimal(request.POST.get('unit_price', '0'))
            copayment = Decimal(request.POST.get('copayment', '0'))
            moderator_fee = Decimal(request.POST.get('moderator_fee', '0'))
            authorization_number = request.POST.get('authorization_number', '')

            # Calcular subtotal
            subtotal = quantity * unit_price

            # Obtener el último número de línea
            last_item = invoice.items.order_by('-line_number').first()
            line_number = (last_item.line_number + 1) if last_item else 1

            # Crear item
            item = HealthInvoiceItem.objects.create(
                invoice=invoice,
                line_number=line_number,
                service_type=service_type,
                service_code=service_code,
                service_name=service_name,
                diagnosis_code=diagnosis_code,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                copayment=copayment,
                moderator_fee=moderator_fee,
                total=subtotal - copayment - moderator_fee,
                authorization_number=authorization_number,
                created_by=request.user
            )

            # Recalcular totales de la factura
            invoice.calculate_totals()

            messages.success(request, 'Item agregado exitosamente')
            return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            messages.error(request, f'Error al agregar item: {str(e)}')
            return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    # GET - Retornar JSON con servicios disponibles (AJAX)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@company_required
def invoice_delete_item(request, invoice_id, item_id):
    """
    Eliminar item de una factura
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if invoice.status not in ['draft', 'pending']:
        messages.error(request, 'No se pueden eliminar items de una factura aprobada o pagada')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    item = get_object_or_404(
        HealthInvoiceItem,
        id=item_id,
        invoice=invoice
    )

    item.delete()
    invoice.calculate_totals()

    messages.success(request, 'Item eliminado exitosamente')
    return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


@login_required
@company_required
def invoice_approve(request, invoice_id):
    """
    Aprobar una factura (cambiar estado a 'approved')
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if invoice.status != 'draft':
        messages.warning(request, 'Solo se pueden aprobar facturas en estado borrador')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    if invoice.items.count() == 0:
        messages.error(request, 'No se puede aprobar una factura sin items')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    try:
        invoice.approve_invoice(request.user)
        messages.success(request, f'Factura {invoice.invoice_number} aprobada exitosamente')
    except Exception as e:
        messages.error(request, f'Error al aprobar factura: {str(e)}')

    return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


@login_required
@company_required
def invoice_add_payment(request, invoice_id):
    """
    Registrar pago a una factura
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if request.method == 'POST':
        try:
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method')
            amount = Decimal(request.POST.get('amount', '0'))
            reference = request.POST.get('reference', '')
            notes = request.POST.get('notes', '')

            if amount <= 0:
                messages.error(request, 'El monto del pago debe ser mayor a 0')
                return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

            # Verificar que no se exceda el monto pendiente
            total_paid = invoice.payments.aggregate(
                Sum('amount')
            )['amount__sum'] or Decimal('0.00')
            pending = invoice.total - total_paid

            if amount > pending:
                messages.error(request, f'El monto excede el saldo pendiente (${pending})')
                return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

            # Crear pago
            payment = HealthPayment.objects.create(
                company=company,
                invoice=invoice,
                payment_date=payment_date,
                payment_method=payment_method,
                amount=amount,
                reference=reference,
                notes=notes,
                created_by=request.user
            )

            # Actualizar estado de factura si está totalmente pagada
            total_paid += amount
            if total_paid >= invoice.total:
                invoice.mark_as_paid(total_paid)

            messages.success(request, 'Pago registrado exitosamente')

        except Exception as e:
            messages.error(request, f'Error al registrar pago: {str(e)}')

    return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


@login_required
@company_required
def invoice_add_glosa(request, invoice_id):
    """
    Registrar glosa en una factura
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if request.method == 'POST':
        try:
            glosa_type = request.POST.get('glosa_type')
            glosa_code = request.POST.get('glosa_code', '')
            glosa_amount = Decimal(request.POST.get('glosa_amount', '0'))
            reason = request.POST.get('reason', '')
            affected_item_id = request.POST.get('affected_item_id', None)

            if glosa_amount <= 0:
                messages.error(request, 'El monto de la glosa debe ser mayor a 0')
                return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

            if glosa_amount > invoice.total:
                messages.error(request, 'El monto de la glosa excede el total de la factura')
                return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

            # Crear glosa
            glosa = InvoiceGlosa.objects.create(
                company=company,
                invoice=invoice,
                glosa_type=glosa_type,
                glosa_code=glosa_code,
                glosa_amount=glosa_amount,
                reason=reason,
                affected_item_id=affected_item_id if affected_item_id else None,
                status='pending',
                created_by=request.user
            )

            # Marcar factura como glosada
            invoice.has_glosa = True
            invoice.glosa_amount = invoice.glosas.aggregate(
                Sum('glosa_amount')
            )['glosa_amount__sum'] or Decimal('0.00')
            invoice.status = 'glosa'
            invoice.save()

            messages.success(request, 'Glosa registrada exitosamente')

        except Exception as e:
            messages.error(request, f'Error al registrar glosa: {str(e)}')

    return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


@login_required
@company_required
def glosa_respond(request, glosa_id):
    """
    Responder a una glosa
    """
    company = get_current_company(request)
    glosa = get_object_or_404(
        InvoiceGlosa,
        id=glosa_id,
        company=company
    )

    if request.method == 'POST':
        try:
            response = request.POST.get('response', '')
            status = request.POST.get('status', 'in_review')
            accepted_amount = request.POST.get('accepted_amount', '0')

            if accepted_amount:
                accepted_amount = Decimal(accepted_amount)
                if accepted_amount > glosa.glosa_amount:
                    messages.error(request, 'El monto aceptado no puede ser mayor al monto de la glosa')
                    return redirect('billing_health:invoice_detail', invoice_id=glosa.invoice.id)

            glosa.response = response
            glosa.status = status
            glosa.response_date = timezone.now()
            glosa.responded_by = request.user

            if accepted_amount:
                glosa.accepted_amount = accepted_amount

            glosa.save()

            # Actualizar estado de factura si todas las glosas están resueltas
            invoice = glosa.invoice
            pending_glosas = invoice.glosas.filter(
                status__in=['pending', 'in_review']
            ).count()

            if pending_glosas == 0:
                invoice.status = 'approved'
                invoice.save()

            messages.success(request, 'Respuesta a glosa registrada exitosamente')

        except Exception as e:
            messages.error(request, f'Error al responder glosa: {str(e)}')

    return redirect('billing_health:invoice_detail', invoice_id=glosa.invoice.id)


@login_required
@company_required
def generate_rips(request, invoice_id):
    """
    Generar archivos RIPS para una factura
    """
    company = get_current_company(request)
    invoice = get_object_or_404(
        HealthInvoice,
        id=invoice_id,
        company=company
    )

    if invoice.status not in ['approved', 'paid']:
        messages.error(request, 'Solo se pueden generar RIPS de facturas aprobadas o pagadas')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    try:
        # TODO: Implementar generación real de archivos RIPS
        # Por ahora, solo marcamos como generado

        invoice.rips_generated = True
        invoice.rips_generation_date = timezone.now()
        invoice.rips_file_path = f"rips/{company.id}/{invoice.invoice_number}/"
        invoice.save()

        messages.success(request, 'RIPS generados exitosamente')
        messages.info(request, 'Funcionalidad de generación RIPS en desarrollo')

    except Exception as e:
        messages.error(request, f'Error al generar RIPS: {str(e)}')

    return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


@login_required
@company_required
def tariff_list(request):
    """
    Lista de tarifarios
    """
    company = get_current_company(request)

    tariffs = HealthTariff.objects.filter(
        company=company
    ).order_by('-is_active', '-effective_date')

    context = {
        'tariffs': tariffs,
    }

    return render(request, 'billing_health/tariff_list.html', context)


@login_required
@company_required
def tariff_create(request):
    """
    Crear nuevo tarifario
    """
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            tariff_type = request.POST.get('tariff_type')
            name = request.POST.get('name')
            effective_date = request.POST.get('effective_date')
            uvr_value = Decimal(request.POST.get('uvr_value', '0'))
            smmlv_value = Decimal(request.POST.get('smmlv_value', '0'))
            global_increment = Decimal(request.POST.get('global_increment', '0'))

            tariff = HealthTariff.objects.create(
                company=company,
                tariff_type=tariff_type,
                name=name,
                effective_date=effective_date,
                uvr_value=uvr_value,
                smmlv_value=smmlv_value,
                global_increment_percentage=global_increment,
                is_active=True,
                created_by=request.user
            )

            messages.success(request, 'Tarifario creado exitosamente')
            return redirect('billing_health:tariff_list')

        except Exception as e:
            messages.error(request, f'Error al crear tarifario: {str(e)}')

    context = {
        'today': timezone.now().date(),
    }

    return render(request, 'billing_health/tariff_form.html', context)


# API endpoints para AJAX

@login_required
def api_search_patients(request):
    """
    API para buscar pacientes (autocomplete)
    """
    company = get_current_company(request)
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    from patients.models import Patient

    patients = Patient.objects.filter(
        company=company,
        is_active=True
    ).select_related('third_party').filter(
        Q(third_party__first_name__icontains=query) |
        Q(third_party__last_name__icontains=query) |
        Q(third_party__document_number__icontains=query) |
        Q(medical_record_number__icontains=query)
    )[:20]

    results = [
        {
            'id': p.id,
            'name': p.get_full_name(),
            'document': p.third_party.document_number,
            'medical_record': p.medical_record_number,
            'text': f"{p.get_full_name()} - {p.third_party.document_number} - HC: {p.medical_record_number}"
        }
        for p in patients
    ]

    return JsonResponse({'results': results})


@login_required
def api_search_services(request):
    """
    API para buscar servicios CUPS (autocomplete)
    """
    company = get_current_company(request)
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    # TODO: Integrar con módulo de catálogos CUPS
    # Por ahora retornamos respuesta vacía

    return JsonResponse({'results': []})


@login_required
def api_get_patient_unbilled_services(request):
    """
    API para obtener todos los servicios NO FACTURADOS de un paciente
    Retorna servicios de: farmacia, imágenes, hospitalizaciones, consultas, cirugías, etc.
    """
    company = get_current_company(request)
    patient_id = request.GET.get('patient_id', '')

    if not patient_id:
        return JsonResponse({'error': 'patient_id es requerido'}, status=400)

    from patients.models import Patient
    from django.contrib.contenttypes.models import ContentType

    try:
        patient = Patient.objects.get(id=patient_id, company=company)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

    services = []

    # 1. FARMACIA - Dispensaciones
    try:
        from pharmacy.models import Dispensing
        dispensings = Dispensing.objects.filter(
            patient=patient,
            company=company,
            is_billed=False
        ).select_related('medication')

        for disp in dispensings:
            services.append({
                'id': str(disp.id),
                'type': 'medication',
                'type_display': 'Medicamento',
                'service_code': disp.medication.cum_code if hasattr(disp.medication, 'cum_code') else '',
                'service_name': str(disp.medication),
                'date': disp.dispensing_date.strftime('%Y-%m-%d %H:%M'),
                'quantity': float(disp.quantity),
                'unit_price': float(disp.unit_price),
                'total': float(disp.total_cost),
                'content_type_id': ContentType.objects.get_for_model(Dispensing).id,
                'object_id': str(disp.id)
            })
    except:
        pass

    # 2. IMÁGENES DIAGNÓSTICAS
    try:
        from imaging.models import ImagingOrder
        imaging_orders = ImagingOrder.objects.filter(
            patient=patient,
            company=company,
            is_billed=False
        ).select_related('imaging_type')

        for order in imaging_orders:
            services.append({
                'id': str(order.id),
                'type': 'imaging',
                'type_display': 'Imagen Diagnóstica',
                'service_code': order.imaging_type.cups_code if hasattr(order.imaging_type, 'cups_code') else '',
                'service_name': str(order.imaging_type),
                'date': order.order_date.strftime('%Y-%m-%d %H:%M'),
                'quantity': 1,
                'unit_price': float(order.estimated_cost) if order.estimated_cost else 0,
                'total': float(order.estimated_cost) if order.estimated_cost else 0,
                'content_type_id': ContentType.objects.get_for_model(ImagingOrder).id,
                'object_id': str(order.id)
            })
    except:
        pass

    # 3. HOSPITALIZACIÓN
    try:
        from hospitalization.models import Admission
        admissions = Admission.objects.filter(
            patient=patient,
            company=company,
            is_billed=False
        )

        for adm in admissions:
            services.append({
                'id': str(adm.id),
                'type': 'hospitalization',
                'type_display': 'Hospitalización',
                'service_code': '',
                'service_name': f"Hospitalización {adm.room.room_number if adm.room else 'Sin habitación'}",
                'date': adm.admission_date.strftime('%Y-%m-%d %H:%M'),
                'quantity': adm.total_days if hasattr(adm, 'total_days') else 1,
                'unit_price': float(adm.daily_rate) if hasattr(adm, 'daily_rate') and adm.daily_rate else 0,
                'total': float(adm.total_cost) if hasattr(adm, 'total_cost') and adm.total_cost else 0,
                'content_type_id': ContentType.objects.get_for_model(Admission).id,
                'object_id': str(adm.id)
            })
    except:
        pass

    # 4. CIRUGÍAS
    try:
        from surgery.models import Surgery
        surgeries = Surgery.objects.filter(
            patient=patient,
            company=company,
            is_billed=False
        )

        for surg in surgeries:
            services.append({
                'id': str(surg.id),
                'type': 'surgery',
                'type_display': 'Cirugía',
                'service_code': surg.procedure_code if hasattr(surg, 'procedure_code') else '',
                'service_name': surg.procedure_name if hasattr(surg, 'procedure_name') else 'Cirugía',
                'date': surg.surgery_date.strftime('%Y-%m-%d %H:%M') if hasattr(surg, 'surgery_date') else '',
                'quantity': 1,
                'unit_price': float(surg.estimated_cost) if hasattr(surg, 'estimated_cost') and surg.estimated_cost else 0,
                'total': float(surg.total_cost) if hasattr(surg, 'total_cost') and surg.total_cost else 0,
                'content_type_id': ContentType.objects.get_for_model(Surgery).id,
                'object_id': str(surg.id)
            })
    except:
        pass

    # 5. CARDIOLOGÍA - Consultas y procedimientos
    try:
        from cardiology.models import CardiologyConsultation
        consultations = CardiologyConsultation.objects.filter(
            patient=patient,
            company=company,
            is_billed=False
        )

        for cons in consultations:
            services.append({
                'id': str(cons.id),
                'type': 'consultation',
                'type_display': 'Consulta Cardiología',
                'service_code': '890201',  # Código CUPS consulta médica
                'service_name': 'Consulta de Cardiología',
                'date': cons.consultation_date.strftime('%Y-%m-%d %H:%M'),
                'quantity': 1,
                'unit_price': float(cons.consultation_fee) if hasattr(cons, 'consultation_fee') and cons.consultation_fee else 35000,
                'total': float(cons.consultation_fee) if hasattr(cons, 'consultation_fee') and cons.consultation_fee else 35000,
                'content_type_id': ContentType.objects.get_for_model(CardiologyConsultation).id,
                'object_id': str(cons.id)
            })
    except:
        pass

    # Ordenar por fecha (más recientes primero)
    services.sort(key=lambda x: x['date'], reverse=True)

    return JsonResponse({
        'services': services,
        'total_services': len(services),
        'patient_name': patient.get_full_name(),
        'patient_document': patient.third_party.document_number
    })
