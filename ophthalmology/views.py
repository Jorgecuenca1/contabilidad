"""
Vistas del módulo Oftalmología
Gestión completa de consultas oftalmológicas, agudeza visual y refracción
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
    OphthalConsultation, VisualAcuity, Refraction, IntraocularPressure,
    Biomicroscopy, FundusExam, LensPrescription
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def ophthalmology_dashboard(request):
    """Dashboard principal de oftalmología"""
    company = get_current_company(request)

    # Estadísticas
    total_consultations_today = OphthalConsultation.objects.filter(
        company=company,
        consultation_date__date=timezone.now().date()
    ).count()

    total_consultations_month = OphthalConsultation.objects.filter(
        company=company,
        consultation_date__month=timezone.now().month,
        consultation_date__year=timezone.now().year
    ).count()

    active_prescriptions = LensPrescription.objects.filter(
        company=company,
        is_active=True,
        valid_until__gte=timezone.now().date()
    ).count()

    # Consultas recientes
    recent_consultations = OphthalConsultation.objects.filter(
        company=company
    ).select_related('patient__third_party', 'ophthalmologist').order_by('-consultation_date')[:10]

    # Prescripciones recientes
    recent_prescriptions = LensPrescription.objects.filter(
        company=company
    ).select_related('patient__third_party', 'ophthalmologist').order_by('-prescription_date')[:10]

    context = {
        'total_consultations_today': total_consultations_today,
        'total_consultations_month': total_consultations_month,
        'active_prescriptions': active_prescriptions,
        'recent_consultations': recent_consultations,
        'recent_prescriptions': recent_prescriptions,
    }

    return render(request, 'ophthalmology/dashboard.html', context)


# ==================== CONSULTAS ====================

@login_required
@company_required
def consultation_list(request):
    """Listado de consultas oftalmológicas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    consultations = OphthalConsultation.objects.filter(company=company).select_related(
        'patient__third_party', 'ophthalmologist'
    )

    if search:
        consultations = consultations.filter(
            Q(consultation_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if status:
        consultations = consultations.filter(status=status)

    if date_from:
        consultations = consultations.filter(consultation_date__gte=date_from)

    consultations = consultations.order_by('-consultation_date')

    paginator = Paginator(consultations, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
        'date_from': date_from,
    }

    return render(request, 'ophthalmology/consultation_list.html', context)


@login_required
@company_required
def consultation_create(request):
    """Crear nueva consulta oftalmológica"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de consulta
            last_consultation = OphthalConsultation.objects.filter(company=company).aggregate(
                last_number=Max('consultation_number')
            )
            if last_consultation['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_consultation['last_number'])))
                consultation_number = f"OFTAL-{last_num + 1:07d}"
            else:
                consultation_number = "OFTAL-0000001"

            consultation = OphthalConsultation.objects.create(
                company=company,
                consultation_number=consultation_number,
                patient=patient,
                ophthalmologist=request.user,
                chief_complaint=request.POST.get('chief_complaint'),
                ocular_history=request.POST.get('ocular_history', ''),
                family_ocular_history=request.POST.get('family_ocular_history', ''),
                systemic_history=request.POST.get('systemic_history', ''),
                current_medications=request.POST.get('current_medications', ''),
                allergies=request.POST.get('allergies', ''),
                symptoms=request.POST.get('symptoms', ''),
                uses_glasses=request.POST.get('uses_glasses') == 'on',
                uses_contact_lenses=request.POST.get('uses_contact_lenses') == 'on',
                diagnosis_right_eye=request.POST.get('diagnosis_right_eye', ''),
                diagnosis_left_eye=request.POST.get('diagnosis_left_eye', ''),
                diagnosis_both_eyes=request.POST.get('diagnosis_both_eyes', ''),
                treatment_plan=request.POST.get('treatment_plan', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Consulta {consultation_number} creada exitosamente')
            return redirect('ophthalmology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'ophthalmology/consultation_form.html', context)


@login_required
@company_required
def consultation_detail(request, consultation_id):
    """Detalle de la consulta oftalmológica"""
    company = get_current_company(request)
    consultation = get_object_or_404(
        OphthalConsultation.objects.select_related(
            'patient__third_party', 'ophthalmologist'
        ),
        id=consultation_id,
        company=company
    )

    # Obtener datos relacionados
    try:
        visual_acuity = consultation.visual_acuity
    except VisualAcuity.DoesNotExist:
        visual_acuity = None

    try:
        refraction = consultation.refraction
    except Refraction.DoesNotExist:
        refraction = None

    try:
        intraocular_pressure = consultation.intraocular_pressure
    except IntraocularPressure.DoesNotExist:
        intraocular_pressure = None

    try:
        biomicroscopy = consultation.biomicroscopy
    except Biomicroscopy.DoesNotExist:
        biomicroscopy = None

    try:
        fundus_exam = consultation.fundus_exam
    except FundusExam.DoesNotExist:
        fundus_exam = None

    prescriptions = consultation.lens_prescriptions.all().order_by('-prescription_date')

    context = {
        'consultation': consultation,
        'visual_acuity': visual_acuity,
        'refraction': refraction,
        'intraocular_pressure': intraocular_pressure,
        'biomicroscopy': biomicroscopy,
        'fundus_exam': fundus_exam,
        'prescriptions': prescriptions,
    }

    return render(request, 'ophthalmology/consultation_detail.html', context)


# ==================== AGUDEZA VISUAL ====================

@login_required
@company_required
def visual_acuity_create(request, consultation_id):
    """Crear/editar agudeza visual"""
    company = get_current_company(request)
    consultation = get_object_or_404(OphthalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            visual_acuity, created = VisualAcuity.objects.get_or_create(
                company=company,
                consultation=consultation,
                defaults={'created_by': request.user}
            )

            # Actualizar campos
            visual_acuity.od_distance_sc = request.POST.get('od_distance_sc', '')
            visual_acuity.od_near_sc = request.POST.get('od_near_sc', '')
            visual_acuity.od_distance_cc = request.POST.get('od_distance_cc', '')
            visual_acuity.od_near_cc = request.POST.get('od_near_cc', '')
            visual_acuity.os_distance_sc = request.POST.get('os_distance_sc', '')
            visual_acuity.os_near_sc = request.POST.get('os_near_sc', '')
            visual_acuity.os_distance_cc = request.POST.get('os_distance_cc', '')
            visual_acuity.os_near_cc = request.POST.get('os_near_cc', '')
            visual_acuity.ou_distance_sc = request.POST.get('ou_distance_sc', '')
            visual_acuity.ou_near_sc = request.POST.get('ou_near_sc', '')
            visual_acuity.ou_distance_cc = request.POST.get('ou_distance_cc', '')
            visual_acuity.ou_near_cc = request.POST.get('ou_near_cc', '')
            visual_acuity.od_pinhole = request.POST.get('od_pinhole', '')
            visual_acuity.os_pinhole = request.POST.get('os_pinhole', '')
            visual_acuity.observations = request.POST.get('observations', '')
            visual_acuity.save()

            messages.success(request, 'Agudeza visual guardada exitosamente')
            return redirect('ophthalmology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al guardar agudeza visual: {str(e)}')

    try:
        visual_acuity = consultation.visual_acuity
    except VisualAcuity.DoesNotExist:
        visual_acuity = None

    context = {
        'consultation': consultation,
        'visual_acuity': visual_acuity,
    }

    return render(request, 'ophthalmology/visual_acuity_form.html', context)


# ==================== REFRACCIÓN ====================

@login_required
@company_required
def refraction_create(request, consultation_id):
    """Crear/editar refracción"""
    company = get_current_company(request)
    consultation = get_object_or_404(OphthalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            refraction, created = Refraction.objects.get_or_create(
                company=company,
                consultation=consultation,
                defaults={'created_by': request.user}
            )

            # Actualizar campos
            refraction.od_sphere = request.POST.get('od_sphere') or None
            refraction.od_cylinder = request.POST.get('od_cylinder') or None
            refraction.od_axis = request.POST.get('od_axis') or None
            refraction.od_add = request.POST.get('od_add') or None
            refraction.od_prism = request.POST.get('od_prism', '')
            refraction.os_sphere = request.POST.get('os_sphere') or None
            refraction.os_cylinder = request.POST.get('os_cylinder') or None
            refraction.os_axis = request.POST.get('os_axis') or None
            refraction.os_add = request.POST.get('os_add') or None
            refraction.os_prism = request.POST.get('os_prism', '')
            refraction.pd_distance = request.POST.get('pd_distance') or None
            refraction.pd_near = request.POST.get('pd_near') or None
            refraction.refraction_type = request.POST.get('refraction_type', 'subjective')
            refraction.observations = request.POST.get('observations', '')
            refraction.save()

            messages.success(request, 'Refracción guardada exitosamente')
            return redirect('ophthalmology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al guardar refracción: {str(e)}')

    try:
        refraction = consultation.refraction
    except Refraction.DoesNotExist:
        refraction = None

    context = {
        'consultation': consultation,
        'refraction': refraction,
    }

    return render(request, 'ophthalmology/refraction_form.html', context)


# ==================== PRESCRIPCIONES DE LENTES ====================

@login_required
@company_required
def prescription_list(request):
    """Listado de prescripciones de lentes"""
    company = get_current_company(request)

    search = request.GET.get('search', '')

    prescriptions = LensPrescription.objects.filter(company=company).select_related(
        'patient__third_party', 'ophthalmologist'
    )

    if search:
        prescriptions = prescriptions.filter(
            Q(prescription_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    prescriptions = prescriptions.order_by('-prescription_date')

    paginator = Paginator(prescriptions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
    }

    return render(request, 'ophthalmology/prescription_list.html', context)


@login_required
@company_required
def prescription_create(request, consultation_id=None):
    """Crear nueva prescripción de lentes"""
    company = get_current_company(request)

    consultation = None
    if consultation_id:
        consultation = get_object_or_404(OphthalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de prescripción
            last_prescription = LensPrescription.objects.filter(company=company).aggregate(
                last_number=Max('prescription_number')
            )
            if last_prescription['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_prescription['last_number'])))
                prescription_number = f"RX-{last_num + 1:07d}"
            else:
                prescription_number = "RX-0000001"

            prescription = LensPrescription.objects.create(
                company=company,
                prescription_number=prescription_number,
                consultation=consultation,
                patient=patient,
                ophthalmologist=request.user,
                lens_type=request.POST.get('lens_type'),
                recommended_usage=request.POST.get('recommended_usage', 'full_time'),
                od_sphere=request.POST.get('od_sphere'),
                od_cylinder=request.POST.get('od_cylinder') or None,
                od_axis=request.POST.get('od_axis') or None,
                od_add=request.POST.get('od_add') or None,
                os_sphere=request.POST.get('os_sphere'),
                os_cylinder=request.POST.get('os_cylinder') or None,
                os_axis=request.POST.get('os_axis') or None,
                os_add=request.POST.get('os_add') or None,
                pd_distance=request.POST.get('pd_distance'),
                pd_near=request.POST.get('pd_near') or None,
                anti_reflective=request.POST.get('anti_reflective') == 'on',
                photochromic=request.POST.get('photochromic') == 'on',
                blue_filter=request.POST.get('blue_filter') == 'on',
                polarized=request.POST.get('polarized') == 'on',
                recommended_material=request.POST.get('recommended_material', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Prescripción {prescription_number} creada exitosamente')
            return redirect('ophthalmology:prescription_detail', prescription_id=prescription.id)

        except Exception as e:
            messages.error(request, f'Error al crear la prescripción: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
        'consultation': consultation,
    }

    return render(request, 'ophthalmology/prescription_form.html', context)


@login_required
@company_required
def prescription_detail(request, prescription_id):
    """Detalle de la prescripción de lentes"""
    company = get_current_company(request)
    prescription = get_object_or_404(
        LensPrescription.objects.select_related(
            'patient__third_party', 'ophthalmologist', 'consultation'
        ),
        id=prescription_id,
        company=company
    )

    context = {
        'prescription': prescription,
    }

    return render(request, 'ophthalmology/prescription_detail.html', context)
