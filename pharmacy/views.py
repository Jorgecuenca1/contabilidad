"""
Vistas del módulo Farmacia
Sistema completo de gestión farmacéutica
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from core.decorators import company_required
from core.utils import get_current_company
from .models import (
    Medicine, MedicineCategory, MedicineBatch, Dispensing,
    DispensingItem, InventoryMovement, StockAlert
)


@login_required
@company_required
def pharmacy_dashboard(request):
    """Dashboard principal de farmacia con indicadores clave"""
    company = get_current_company(request)

    # Estadísticas generales
    total_medicines = Medicine.objects.filter(company=company, is_active=True).count()

    # Stock total
    total_stock_value = MedicineBatch.objects.filter(
        company=company,
        is_active=True,
        expiry_date__gt=timezone.now().date()
    ).annotate(
        batch_value=ExpressionWrapper(
            F('current_quantity') * F('unit_cost'),
            output_field=DecimalField()
        )
    ).aggregate(
        total=Sum('batch_value')
    )['total'] or Decimal('0')

    # Medicamentos con stock bajo
    low_stock_medicines = Medicine.objects.filter(
        company=company,
        is_active=True
    ).annotate(
        current_stock=Sum('batches__current_quantity', filter=Q(
            batches__is_active=True,
            batches__expiry_date__gt=timezone.now().date()
        ))
    ).filter(
        current_stock__lt=F('minimum_stock')
    ).count()

    # Medicamentos próximos a vencer (90 días)
    threshold_date = timezone.now().date() + timedelta(days=90)
    near_expiry_batches = MedicineBatch.objects.filter(
        company=company,
        is_active=True,
        expiry_date__lte=threshold_date,
        expiry_date__gt=timezone.now().date(),
        current_quantity__gt=0
    ).count()

    # Medicamentos vencidos
    expired_batches = MedicineBatch.objects.filter(
        company=company,
        is_active=True,
        expiry_date__lte=timezone.now().date(),
        current_quantity__gt=0
    ).count()

    # Dispensaciones del mes actual
    today = timezone.now().date()
    dispensings_month = Dispensing.objects.filter(
        company=company,
        dispensing_date__year=today.year,
        dispensing_date__month=today.month
    ).count()

    # Alertas pendientes
    active_alerts = StockAlert.objects.filter(
        company=company,
        is_resolved=False
    ).order_by('-priority', '-created_at')[:10]

    # Top 10 medicamentos más dispensados (último mes)
    last_month = timezone.now() - timedelta(days=30)
    top_medicines = DispensingItem.objects.filter(
        dispensing__company=company,
        dispensing__dispensing_date__gte=last_month,
        dispensing__status='delivered'
    ).values(
        'medicine__generic_name', 'medicine__code'
    ).annotate(
        total_quantity=Sum('quantity'),
        dispensings_count=Count('id')
    ).order_by('-total_quantity')[:10]

    # Dispensaciones recientes
    recent_dispensings = Dispensing.objects.filter(
        company=company
    ).select_related('patient', 'created_by').order_by('-dispensing_date')[:10]

    # Lotes próximos a vencer
    near_expiry_list = MedicineBatch.objects.filter(
        company=company,
        is_active=True,
        expiry_date__lte=threshold_date,
        expiry_date__gt=timezone.now().date(),
        current_quantity__gt=0
    ).select_related('medicine').order_by('expiry_date')[:10]

    context = {
        'total_medicines': total_medicines,
        'total_stock_value': total_stock_value,
        'low_stock_medicines': low_stock_medicines,
        'near_expiry_batches': near_expiry_batches,
        'expired_batches': expired_batches,
        'dispensings_month': dispensings_month,
        'active_alerts': active_alerts,
        'top_medicines': top_medicines,
        'recent_dispensings': recent_dispensings,
        'near_expiry_list': near_expiry_list,
    }

    return render(request, 'pharmacy/dashboard.html', context)


# ====================
# MEDICAMENTOS
# ====================

@login_required
@company_required
def medicine_list(request):
    """Lista de medicamentos con filtros"""
    company = get_current_company(request)

    # Filtros
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    pharmaceutical_form = request.GET.get('form', '')
    control_type = request.GET.get('control', '')
    status = request.GET.get('status', 'active')

    medicines = Medicine.objects.filter(company=company).select_related('category')

    if search:
        medicines = medicines.filter(
            Q(code__icontains=search) |
            Q(generic_name__icontains=search) |
            Q(commercial_name__icontains=search) |
            Q(active_ingredient__icontains=search) |
            Q(barcode__icontains=search)
        )

    if category_id:
        medicines = medicines.filter(category_id=category_id)

    if pharmaceutical_form:
        medicines = medicines.filter(pharmaceutical_form=pharmaceutical_form)

    if control_type:
        medicines = medicines.filter(control_type=control_type)

    if status == 'active':
        medicines = medicines.filter(is_active=True)
    elif status == 'inactive':
        medicines = medicines.filter(is_active=False)

    # Anotar stock actual
    medicines = medicines.annotate(
        current_stock=Sum('batches__current_quantity', filter=Q(
            batches__is_active=True,
            batches__expiry_date__gt=timezone.now().date()
        ))
    )

    # Ordenar
    sort = request.GET.get('sort', 'generic_name')
    medicines = medicines.order_by(sort)

    # Paginación
    paginator = Paginator(medicines, 50)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # Para filtros
    categories = MedicineCategory.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'pharmaceutical_form': pharmaceutical_form,
        'control_type': control_type,
        'status': status,
        'sort': sort,
    }

    return render(request, 'pharmacy/medicine_list.html', context)


@login_required
@company_required
def medicine_detail(request, medicine_id):
    """Detalle completo del medicamento"""
    company = get_current_company(request)
    medicine = get_object_or_404(Medicine, id=medicine_id, company=company)

    # Lotes activos
    active_batches = medicine.batches.filter(
        is_active=True,
        expiry_date__gt=timezone.now().date()
    ).order_by('expiry_date')

    # Stock total
    current_stock = medicine.get_current_stock()
    expired_stock = medicine.get_expired_stock()
    near_expiry_stock = medicine.get_near_expiry_stock()

    # Movimientos recientes
    recent_movements = medicine.movements.select_related(
        'batch', 'created_by'
    ).order_by('-movement_date')[:20]

    # Dispensaciones recientes
    recent_dispensings = DispensingItem.objects.filter(
        medicine=medicine,
        dispensing__status='delivered'
    ).select_related(
        'dispensing__patient', 'batch'
    ).order_by('-dispensing__dispensing_date')[:10]

    context = {
        'medicine': medicine,
        'active_batches': active_batches,
        'current_stock': current_stock,
        'expired_stock': expired_stock,
        'near_expiry_stock': near_expiry_stock,
        'recent_movements': recent_movements,
        'recent_dispensings': recent_dispensings,
        'needs_reorder': medicine.needs_reorder(),
        'is_below_minimum': medicine.is_below_minimum(),
    }

    return render(request, 'pharmacy/medicine_detail.html', context)


@login_required
@company_required
def medicine_create(request):
    """Crear nuevo medicamento"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            medicine = Medicine.objects.create(
                company=company,
                code=request.POST['code'],
                generic_name=request.POST['generic_name'],
                commercial_name=request.POST.get('commercial_name', ''),
                active_ingredient=request.POST['active_ingredient'],
                category_id=request.POST['category'],
                pharmaceutical_form=request.POST['pharmaceutical_form'],
                administration_route=request.POST['administration_route'],
                control_type=request.POST['control_type'],
                concentration=request.POST['concentration'],
                presentation=request.POST['presentation'],
                manufacturer=request.POST.get('manufacturer', ''),
                unit_cost=Decimal(request.POST.get('unit_cost', '0')),
                sale_price=Decimal(request.POST.get('sale_price', '0')),
                minimum_stock=Decimal(request.POST.get('minimum_stock', '0')),
                maximum_stock=Decimal(request.POST.get('maximum_stock', '0')),
                reorder_point=Decimal(request.POST.get('reorder_point', '0')),
                created_by=request.user,
            )

            messages.success(request, f'Medicamento {medicine.generic_name} creado exitosamente')
            return redirect('pharmacy:medicine_detail', medicine_id=medicine.id)

        except Exception as e:
            messages.error(request, f'Error al crear medicamento: {str(e)}')

    categories = MedicineCategory.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'categories': categories,
        'pharmaceutical_forms': Medicine.PHARMACEUTICAL_FORM_CHOICES,
        'administration_routes': Medicine.ADMINISTRATION_ROUTE_CHOICES,
        'control_types': Medicine.CONTROL_TYPE_CHOICES,
    }

    return render(request, 'pharmacy/medicine_form.html', context)


# ====================
# LOTES
# ====================

@login_required
@company_required
def batch_list(request):
    """Lista de lotes con control de vencimientos"""
    company = get_current_company(request)

    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'active')
    expiry_filter = request.GET.get('expiry', '')

    batches = MedicineBatch.objects.filter(company=company).select_related('medicine')

    if search:
        batches = batches.filter(
            Q(batch_number__icontains=search) |
            Q(medicine__generic_name__icontains=search) |
            Q(medicine__code__icontains=search)
        )

    if status == 'active':
        batches = batches.filter(is_active=True, expiry_date__gt=timezone.now().date())
    elif status == 'expired':
        batches = batches.filter(expiry_date__lte=timezone.now().date())
    elif status == 'quarantine':
        batches = batches.filter(is_quarantine=True)

    if expiry_filter == 'near':
        threshold = timezone.now().date() + timedelta(days=90)
        batches = batches.filter(
            expiry_date__lte=threshold,
            expiry_date__gt=timezone.now().date()
        )

    batches = batches.order_by('expiry_date', 'medicine__generic_name')

    # Paginación
    paginator = Paginator(batches, 50)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'expiry_filter': expiry_filter,
    }

    return render(request, 'pharmacy/batch_list.html', context)


@login_required
@company_required
def batch_create(request):
    """Registrar nuevo lote (entrada de inventario)"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            medicine_id = request.POST['medicine_id']
            medicine = Medicine.objects.get(id=medicine_id, company=company)

            quantity = Decimal(request.POST['quantity'])
            unit_cost = Decimal(request.POST['unit_cost'])

            batch = MedicineBatch.objects.create(
                company=company,
                medicine=medicine,
                batch_number=request.POST['batch_number'],
                manufacturing_date=request.POST['manufacturing_date'],
                expiry_date=request.POST['expiry_date'],
                initial_quantity=quantity,
                current_quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost,
                supplier=request.POST.get('supplier', ''),
                purchase_order=request.POST.get('purchase_order', ''),
                invoice_number=request.POST.get('invoice_number', ''),
                storage_location=request.POST.get('storage_location', ''),
                created_by=request.user,
            )

            # Registrar movimiento de entrada
            movement_number = f"ENT-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            InventoryMovement.objects.create(
                company=company,
                movement_number=movement_number,
                movement_type='entry',
                medicine=medicine,
                batch=batch,
                quantity=quantity,
                previous_quantity=0,
                new_quantity=quantity,
                reference_document=request.POST.get('invoice_number', ''),
                reason='Entrada de nuevo lote',
                created_by=request.user,
            )

            messages.success(request, f'Lote {batch.batch_number} registrado exitosamente')
            return redirect('pharmacy:medicine_detail', medicine_id=medicine.id)

        except Exception as e:
            messages.error(request, f'Error al registrar lote: {str(e)}')

    medicine_id = request.GET.get('medicine_id')
    medicine = None
    if medicine_id:
        medicine = get_object_or_404(Medicine, id=medicine_id, company=company)

    context = {
        'medicine': medicine,
    }

    return render(request, 'pharmacy/batch_form.html', context)


# ====================
# DISPENSACIÓN
# ====================

@login_required
@company_required
def dispensing_list(request):
    """Lista de dispensaciones"""
    company = get_current_company(request)

    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    dispensings = Dispensing.objects.filter(company=company).select_related(
        'patient', 'created_by', 'delivered_by'
    )

    if search:
        dispensings = dispensings.filter(
            Q(dispensing_number__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(prescription_number__icontains=search)
        )

    if status:
        dispensings = dispensings.filter(status=status)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            dispensings = dispensings.filter(dispensing_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            dispensings = dispensings.filter(dispensing_date__lte=date_to_obj)
        except ValueError:
            pass

    dispensings = dispensings.order_by('-dispensing_date')

    # Paginación
    paginator = Paginator(dispensings, 50)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'pharmacy/dispensing_list.html', context)


@login_required
@company_required
def dispensing_create(request):
    """Crear nueva dispensación"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Generar número de dispensación
            today = timezone.now()
            dispensing_number = f"DISP-{today.strftime('%Y%m%d%H%M%S')}"

            dispensing = Dispensing.objects.create(
                company=company,
                dispensing_number=dispensing_number,
                patient_id=request.POST['patient_id'],
                prescription_required=request.POST.get('prescription_required') == 'on',
                prescription_number=request.POST.get('prescription_number', ''),
                prescribing_physician=request.POST.get('prescribing_physician', ''),
                diagnosis=request.POST.get('diagnosis', ''),
                service_type=request.POST.get('service_type', ''),
                notes=request.POST.get('notes', ''),
                created_by=request.user,
            )

            messages.success(request, f'Dispensación {dispensing_number} creada. Agregue medicamentos.')
            return redirect('pharmacy:dispensing_detail', dispensing_id=dispensing.id)

        except Exception as e:
            messages.error(request, f'Error al crear dispensación: {str(e)}')

    context = {}
    return render(request, 'pharmacy/dispensing_form.html', context)


@login_required
@company_required
def dispensing_detail(request, dispensing_id):
    """Detalle de dispensación"""
    company = get_current_company(request)
    dispensing = get_object_or_404(Dispensing, id=dispensing_id, company=company)

    items = dispensing.items.select_related('medicine', 'batch').all()

    context = {
        'dispensing': dispensing,
        'items': items,
        'can_edit': dispensing.can_be_edited(),
    }

    return render(request, 'pharmacy/dispensing_detail.html', context)


@login_required
@company_required
def dispensing_add_item(request, dispensing_id):
    """Agregar medicamento a dispensación"""
    company = get_current_company(request)
    dispensing = get_object_or_404(Dispensing, id=dispensing_id, company=company)

    if not dispensing.can_be_edited():
        messages.error(request, 'No se pueden agregar items a esta dispensación')
        return redirect('pharmacy:dispensing_detail', dispensing_id=dispensing.id)

    if request.method == 'POST':
        try:
            medicine_id = request.POST['medicine_id']
            quantity = Decimal(request.POST['quantity'])

            medicine = Medicine.objects.get(id=medicine_id, company=company)

            # Buscar lote con FEFO (First Expired, First Out)
            batch = MedicineBatch.objects.filter(
                medicine=medicine,
                company=company,
                is_active=True,
                expiry_date__gt=timezone.now().date(),
                is_quarantine=False
            ).annotate(
                available=F('current_quantity') - F('reserved_quantity')
            ).filter(
                available__gte=quantity
            ).order_by('expiry_date').first()

            if not batch:
                messages.error(request, f'No hay stock suficiente de {medicine.generic_name}')
                return redirect('pharmacy:dispensing_detail', dispensing_id=dispensing.id)

            # Crear item
            item = DispensingItem.objects.create(
                dispensing=dispensing,
                medicine=medicine,
                batch=batch,
                quantity=quantity,
                unit_price=medicine.sale_price,
                dosage_instructions=request.POST.get('dosage_instructions', ''),
            )

            # Actualizar totales
            dispensing.calculate_totals()

            # Registrar movimiento de salida
            movement_number = f"SAL-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            previous_qty = batch.current_quantity
            batch.current_quantity -= quantity
            batch.save()

            InventoryMovement.objects.create(
                company=company,
                movement_number=movement_number,
                movement_type='exit',
                medicine=medicine,
                batch=batch,
                quantity=quantity,
                previous_quantity=previous_qty,
                new_quantity=batch.current_quantity,
                dispensing=dispensing,
                reason=f'Dispensación {dispensing.dispensing_number}',
                created_by=request.user,
            )

            messages.success(request, 'Medicamento agregado exitosamente')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('pharmacy:dispensing_detail', dispensing_id=dispensing.id)


@login_required
@company_required
def dispensing_deliver(request, dispensing_id):
    """Marcar dispensación como entregada"""
    company = get_current_company(request)
    dispensing = get_object_or_404(Dispensing, id=dispensing_id, company=company)

    if request.method == 'POST':
        try:
            received_by_name = request.POST['received_by_name']
            received_by_id = request.POST['received_by_id']

            dispensing.mark_as_delivered(request.user, received_by_name, received_by_id)

            messages.success(request, 'Dispensación marcada como entregada')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('pharmacy:dispensing_detail', dispensing_id=dispensing.id)


# ====================
# INVENTARIO
# ====================

@login_required
@company_required
def inventory_report(request):
    """Reporte de inventario valorizado"""
    company = get_current_company(request)

    # Medicamentos con stock
    medicines = Medicine.objects.filter(
        company=company,
        is_active=True
    ).annotate(
        current_stock=Sum('batches__current_quantity', filter=Q(
            batches__is_active=True,
            batches__expiry_date__gt=timezone.now().date()
        ))
    ).filter(
        current_stock__gt=0
    ).select_related('category').order_by('generic_name')

    # Calcular valores
    inventory_data = []
    total_value = Decimal('0')

    for medicine in medicines:
        batches = medicine.batches.filter(
            is_active=True,
            expiry_date__gt=timezone.now().date(),
            current_quantity__gt=0
        )

        stock = batches.aggregate(total=Sum('current_quantity'))['total'] or Decimal('0')
        avg_cost = batches.aggregate(
            avg=Sum(F('current_quantity') * F('unit_cost')) / Sum('current_quantity')
        )['avg'] or Decimal('0')

        value = stock * avg_cost
        total_value += value

        inventory_data.append({
            'medicine': medicine,
            'stock': stock,
            'avg_cost': avg_cost,
            'value': value,
        })

    context = {
        'inventory_data': inventory_data,
        'total_value': total_value,
    }

    return render(request, 'pharmacy/inventory_report.html', context)


# ====================
# ALERTAS
# ====================

@login_required
@company_required
def alerts_list(request):
    """Lista de alertas de stock"""
    company = get_current_company(request)

    status = request.GET.get('status', 'pending')

    alerts = StockAlert.objects.filter(company=company).select_related('medicine', 'batch')

    if status == 'pending':
        alerts = alerts.filter(is_resolved=False)
    elif status == 'resolved':
        alerts = alerts.filter(is_resolved=True)

    alerts = alerts.order_by('-priority', '-created_at')

    paginator = Paginator(alerts, 50)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'status': status,
    }

    return render(request, 'pharmacy/alerts_list.html', context)


# ====================
# API / AJAX
# ====================

@login_required
def api_search_medicines(request):
    """API para buscar medicamentos (autocomplete)"""
    company = get_current_company(request)
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    medicines = Medicine.objects.filter(
        company=company,
        is_active=True
    ).filter(
        Q(code__icontains=query) |
        Q(generic_name__icontains=query) |
        Q(commercial_name__icontains=query) |
        Q(barcode__icontains=query)
    ).annotate(
        current_stock=Sum('batches__current_quantity', filter=Q(
            batches__is_active=True,
            batches__expiry_date__gt=timezone.now().date()
        ))
    )[:20]

    results = [
        {
            'id': str(m.id),
            'code': m.code,
            'name': m.generic_name,
            'presentation': m.presentation,
            'stock': float(m.current_stock or 0),
            'price': float(m.sale_price),
            'text': f"{m.code} - {m.generic_name} ({m.presentation})"
        }
        for m in medicines
    ]

    return JsonResponse({'results': results})
