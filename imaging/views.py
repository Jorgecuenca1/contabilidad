"""
Vistas del módulo Imágenes Diagnósticas
Gestión completa de radiología, estudios y reportes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta

from core.decorators import company_required
from core.utils import get_current_company
from patients.models import Patient
from .models import (
    ImagingModality, ImagingEquipment, ImagingOrder, ImagingStudy,
    ImagingReport, QualityControlCheck
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def imaging_dashboard(request):
    """Dashboard principal de imágenes diagnósticas"""
    company = get_current_company(request)

    # Estadísticas
    total_orders_today = ImagingOrder.objects.filter(
        company=company,
        ordering_date__date=timezone.now().date()
    ).count()

    pending_orders = ImagingOrder.objects.filter(company=company, status='pending').count()
    scheduled_today = ImagingOrder.objects.filter(
        company=company,
        scheduled_date__date=timezone.now().date()
    ).count()

    studies_pending_report = ImagingStudy.objects.filter(
        company=company,
        status='completed'
    ).exclude(report__isnull=False).count()

    # Equipos operacionales
    operational_equipment = ImagingEquipment.objects.filter(
        company=company,
        status='operational',
        is_active=True
    ).count()

    # Órdenes recientes
    recent_orders = ImagingOrder.objects.filter(company=company).select_related(
        'patient__third_party', 'modality', 'ordering_physician'
    ).order_by('-ordering_date')[:15]

    # Estudios completados hoy
    studies_today = ImagingStudy.objects.filter(
        company=company,
        study_date__date=timezone.now().date()
    ).count()

    # Órdenes por modalidad (últimos 30 días)
    orders_by_modality = ImagingOrder.objects.filter(
        company=company,
        ordering_date__gte=timezone.now() - timedelta(days=30)
    ).values('modality__name').annotate(total=Count('id')).order_by('-total')[:10]

    context = {
        'total_orders_today': total_orders_today,
        'pending_orders': pending_orders,
        'scheduled_today': scheduled_today,
        'studies_pending_report': studies_pending_report,
        'operational_equipment': operational_equipment,
        'studies_today': studies_today,
        'recent_orders': recent_orders,
        'orders_by_modality': orders_by_modality,
    }

    return render(request, 'imaging/dashboard.html', context)


# ==================== ÓRDENES ====================

@login_required
@company_required
def order_list(request):
    """Listado de órdenes"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    modality_id = request.GET.get('modality', '')
    date_from = request.GET.get('date_from', '')

    orders = ImagingOrder.objects.filter(company=company).select_related(
        'patient__third_party', 'modality', 'ordering_physician'
    )

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if status:
        orders = orders.filter(status=status)

    if modality_id:
        orders = orders.filter(modality_id=modality_id)

    if date_from:
        orders = orders.filter(ordering_date__gte=date_from)

    orders = orders.order_by('-ordering_date')

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    modalities = ImagingModality.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'modalities': modalities,
        'search': search,
        'status_filter': status,
        'modality_filter': modality_id,
        'date_from': date_from,
    }

    return render(request, 'imaging/order_list.html', context)


@login_required
@company_required
def order_create(request):
    """Crear nueva orden"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            modality_id = request.POST.get('modality')

            patient = get_object_or_404(Patient, id=patient_id, company=company)
            modality = get_object_or_404(ImagingModality, id=modality_id, company=company)

            # Generar número de orden
            last_order = ImagingOrder.objects.filter(company=company).aggregate(
                last_number=Max('order_number')
            )
            if last_order['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_order['last_number'])))
                order_number = f"IMG-{last_num + 1:07d}"
            else:
                order_number = "IMG-0000001"

            order = ImagingOrder.objects.create(
                company=company,
                order_number=order_number,
                patient=patient,
                modality=modality,
                procedure_description=request.POST.get('procedure_description'),
                anatomical_region=request.POST.get('anatomical_region'),
                clinical_indication=request.POST.get('clinical_indication'),
                clinical_history=request.POST.get('clinical_history', ''),
                ordering_physician=request.user,
                priority=request.POST.get('priority', 'routine'),
                has_allergies=request.POST.get('has_allergies') == 'on',
                allergies_description=request.POST.get('allergies_description', ''),
                total_cost=modality.base_price,
                created_by=request.user
            )

            messages.success(request, f'Orden {order_number} creada exitosamente')
            return redirect('imaging:order_detail', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Error al crear la orden: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')
    modalities = ImagingModality.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'patients': patients,
        'modalities': modalities,
    }

    return render(request, 'imaging/order_form.html', context)


@login_required
@company_required
def order_detail(request, order_id):
    """Detalle de la orden"""
    company = get_current_company(request)
    order = get_object_or_404(
        ImagingOrder.objects.select_related(
            'patient__third_party', 'modality', 'ordering_physician', 'scheduled_equipment'
        ),
        id=order_id,
        company=company
    )

    # Estudios relacionados
    studies = order.studies.all().select_related('equipment_used', 'performing_technologist')

    context = {
        'order': order,
        'studies': studies,
    }

    return render(request, 'imaging/order_detail.html', context)


# ==================== ESTUDIOS ====================

@login_required
@company_required
def study_list(request):
    """Listado de estudios"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    pending_report = request.GET.get('pending_report', '')

    studies = ImagingStudy.objects.filter(company=company).select_related(
        'order__patient__third_party', 'equipment_used', 'performing_technologist'
    )

    if search:
        studies = studies.filter(
            Q(study_number__icontains=search) |
            Q(order__order_number__icontains=search) |
            Q(order__patient__third_party__name__icontains=search)
        )

    if status:
        studies = studies.filter(status=status)

    if pending_report == 'yes':
        studies = studies.filter(report__isnull=True, status='completed')

    studies = studies.order_by('-study_date')

    paginator = Paginator(studies, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
        'pending_report': pending_report,
    }

    return render(request, 'imaging/study_list.html', context)


@login_required
@company_required
def study_create(request, order_id):
    """Crear estudio"""
    company = get_current_company(request)
    order = get_object_or_404(ImagingOrder, id=order_id, company=company)

    if not order.can_perform():
        messages.error(request, 'No se puede realizar el estudio. Verifique el consentimiento.')
        return redirect('imaging:order_detail', order_id=order.id)

    if request.method == 'POST':
        try:
            equipment_id = request.POST.get('equipment')
            equipment = get_object_or_404(ImagingEquipment, id=equipment_id, company=company)

            # Generar número de estudio
            last_study = ImagingStudy.objects.filter(company=company).aggregate(
                last_number=Max('study_number')
            )
            if last_study['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_study['last_number'])))
                study_number = f"ST-{last_num + 1:07d}"
            else:
                study_number = "ST-0000001"

            study = ImagingStudy.objects.create(
                company=company,
                order=order,
                study_number=study_number,
                equipment_used=equipment,
                performing_technologist=request.user,
                contrast_used=request.POST.get('contrast_used') == 'on',
                contrast_type=request.POST.get('contrast_type', ''),
                number_of_images=int(request.POST.get('number_of_images', 0)),
                technical_notes=request.POST.get('technical_notes', ''),
                status='completed',
                completion_date=timezone.now(),
                created_by=request.user
            )

            # Actualizar estado de la orden
            order.status = 'completed'
            order.save()

            messages.success(request, f'Estudio {study_number} creado exitosamente')
            return redirect('imaging:study_detail', study_id=study.id)

        except Exception as e:
            messages.error(request, f'Error al crear el estudio: {str(e)}')

    equipment = ImagingEquipment.objects.filter(
        company=company,
        modality=order.modality,
        status='operational',
        is_active=True
    ).order_by('name')

    context = {
        'order': order,
        'equipment': equipment,
    }

    return render(request, 'imaging/study_form.html', context)


@login_required
@company_required
def study_detail(request, study_id):
    """Detalle del estudio"""
    company = get_current_company(request)
    study = get_object_or_404(
        ImagingStudy.objects.select_related(
            'order__patient__third_party', 'equipment_used', 'performing_technologist', 'radiologist_assigned'
        ),
        id=study_id,
        company=company
    )

    # Informe si existe
    report = None
    try:
        report = study.report
    except ImagingReport.DoesNotExist:
        pass

    context = {
        'study': study,
        'report': report,
    }

    return render(request, 'imaging/study_detail.html', context)


# ==================== INFORMES ====================

@login_required
@company_required
def report_create(request, study_id):
    """Crear informe radiológico"""
    company = get_current_company(request)
    study = get_object_or_404(ImagingStudy, id=study_id, company=company)

    if hasattr(study, 'report'):
        messages.warning(request, 'Este estudio ya tiene un informe')
        return redirect('imaging:study_detail', study_id=study.id)

    if request.method == 'POST':
        try:
            # Generar número de informe
            last_report = ImagingReport.objects.filter(company=company).aggregate(
                last_number=Max('report_number')
            )
            if last_report['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_report['last_number'])))
                report_number = f"REP-{last_num + 1:07d}"
            else:
                report_number = "REP-0000001"

            report = ImagingReport.objects.create(
                company=company,
                study=study,
                report_number=report_number,
                radiologist=request.user,
                technique=request.POST.get('technique'),
                findings=request.POST.get('findings'),
                impression=request.POST.get('impression'),
                recommendations=request.POST.get('recommendations', ''),
                is_normal=request.POST.get('is_normal') == 'on',
                is_critical=request.POST.get('is_critical') == 'on',
                status='draft',
                created_by=request.user
            )

            messages.success(request, f'Informe {report_number} creado exitosamente')
            return redirect('imaging:study_detail', study_id=study.id)

        except Exception as e:
            messages.error(request, f'Error al crear el informe: {str(e)}')

    context = {
        'study': study,
    }

    return render(request, 'imaging/report_form.html', context)


# ==================== EQUIPOS ====================

@login_required
@company_required
def equipment_list(request):
    """Listado de equipos"""
    company = get_current_company(request)

    equipment = ImagingEquipment.objects.filter(company=company).select_related('modality').order_by('name')

    context = {
        'equipment_list': equipment,
    }

    return render(request, 'imaging/equipment_list.html', context)


# ==================== APIs ====================

@login_required
@company_required
def api_equipment_by_modality(request):
    """API: Obtener equipos por modalidad"""
    company = get_current_company(request)
    modality_id = request.GET.get('modality_id')

    if modality_id:
        equipment = ImagingEquipment.objects.filter(
            company=company,
            modality_id=modality_id,
            status='operational',
            is_active=True
        ).values('id', 'code', 'name', 'room_location')
    else:
        equipment = []

    return JsonResponse(list(equipment), safe=False)
