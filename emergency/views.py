"""
Vistas del módulo Urgencias
Sistema de urgencias médicas con triage, admisión y atención
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from core.decorators import company_required, module_permission_required
from core.utils import get_current_company
from core.models import User
from patients.models import Patient
from .models import (
    TriageAssessment, EmergencyAdmission, VitalSignsRecord,
    EmergencyAttention, EmergencyProcedure, EmergencyDischarge
)


@login_required
@company_required
@module_permission_required('emergency')
def emergency_dashboard(request):
    """Dashboard principal del módulo de urgencias."""
    company_id = request.session.get('active_company')
    today = timezone.now().date()

    # Estadísticas básicas
    total_admissions = EmergencyAdmission.objects.filter(
        company_id=company_id
    ).count()

    active_admissions = EmergencyAdmission.objects.filter(
        company_id=company_id,
        status__in=['waiting', 'in_attention', 'observation']
    ).count()

    admissions_today = EmergencyAdmission.objects.filter(
        company_id=company_id,
        admission_datetime__date=today
    ).count()

    # Estadísticas por estado
    admissions_by_status = EmergencyAdmission.objects.filter(
        company_id=company_id,
        status__in=['waiting', 'in_attention', 'observation']
    ).values('status').annotate(count=Count('id'))

    status_stats = {item['status']: item['count'] for item in admissions_by_status}

    # Estadísticas por nivel de triage
    triage_today = TriageAssessment.objects.filter(
        company_id=company_id,
        triage_datetime__date=today
    ).values('triage_level').annotate(count=Count('id')).order_by('triage_level')

    triage_stats = {item['triage_level']: item['count'] for item in triage_today}

    # Pacientes activos por nivel de triage (color)
    active_patients = EmergencyAdmission.objects.filter(
        company_id=company_id,
        status__in=['waiting', 'in_attention', 'observation']
    ).select_related('patient__third_party', 'triage', 'attending_physician').order_by(
        'triage__triage_level', '-admission_datetime'
    )

    # Organizar por nivel de triage para el tablero
    triage_board = {
        'I': [],
        'II': [],
        'III': [],
        'IV': [],
        'V': [],
    }

    for admission in active_patients:
        level = admission.triage.triage_level
        if level in triage_board:
            triage_board[level].append(admission)

    # Triages recientes pendientes de admisión
    pending_triage = TriageAssessment.objects.filter(
        company_id=company_id,
        admission__isnull=True
    ).select_related('patient__third_party', 'triage_nurse').order_by(
        'triage_level', '-arrival_datetime'
    )[:10]

    # Altas del día
    discharges_today = EmergencyDischarge.objects.filter(
        company_id=company_id,
        discharge_datetime__date=today
    ).count()

    context = {
        'total_admissions': total_admissions,
        'active_admissions': active_admissions,
        'admissions_today': admissions_today,
        'discharges_today': discharges_today,
        'status_stats': status_stats,
        'triage_stats': triage_stats,
        'triage_board': triage_board,
        'pending_triage': pending_triage,
    }

    return render(request, 'emergency/dashboard.html', context)


# =============================================================================
# TRIAGE
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def triage_list(request):
    """Lista de evaluaciones de triage."""
    company_id = request.session.get('active_company')

    triages = TriageAssessment.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'triage_nurse')

    # Filtros
    triage_level = request.GET.get('triage_level')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    has_admission = request.GET.get('has_admission')
    search = request.GET.get('search')

    if triage_level:
        triages = triages.filter(triage_level=triage_level)

    if date_from:
        triages = triages.filter(arrival_datetime__date__gte=date_from)

    if date_to:
        triages = triages.filter(arrival_datetime__date__lte=date_to)

    if has_admission == 'true':
        triages = triages.filter(admission__isnull=False)
    elif has_admission == 'false':
        triages = triages.filter(admission__isnull=True)

    if search:
        triages = triages.filter(
            Q(triage_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(patient__medical_record_number__icontains=search) |
            Q(chief_complaint__icontains=search)
        )

    # Paginación
    paginator = Paginator(triages.order_by('-arrival_datetime'), 15)
    page = request.GET.get('page')
    triages = paginator.get_page(page)

    context = {
        'triages': triages,
        'level_choices': TriageAssessment.TRIAGE_LEVEL_CHOICES,
        'filters': {
            'triage_level': triage_level,
            'date_from': date_from,
            'date_to': date_to,
            'has_admission': has_admission,
            'search': search,
        }
    }

    return render(request, 'emergency/triage_list.html', context)


@login_required
@company_required
@module_permission_required('emergency')
def triage_detail(request, triage_id):
    """Detalle de evaluación de triage."""
    company_id = request.session.get('active_company')
    triage = get_object_or_404(
        TriageAssessment.objects.select_related(
            'patient__third_party', 'triage_nurse', 'created_by'
        ),
        id=triage_id,
        company_id=company_id
    )

    # Verificar si tiene admisión asociada
    has_admission = hasattr(triage, 'admission')

    context = {
        'triage': triage,
        'has_admission': has_admission,
    }

    return render(request, 'emergency/triage_detail.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def triage_create(request):
    """Crear nueva evaluación de triage."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            triage = TriageAssessment()
            triage.company_id = company_id
            triage.patient_id = request.POST.get('patient')
            triage.arrival_datetime = request.POST.get('arrival_datetime')
            triage.arrival_mode = request.POST.get('arrival_mode')
            triage.accompanied_by = request.POST.get('accompanied_by', '')

            # Motivo de consulta
            triage.chief_complaint = request.POST.get('chief_complaint')
            triage.symptom_duration = request.POST.get('symptom_duration', '')

            # Signos vitales
            triage.blood_pressure = request.POST.get('blood_pressure', '')
            heart_rate = request.POST.get('heart_rate')
            if heart_rate:
                triage.heart_rate = int(heart_rate)
            respiratory_rate = request.POST.get('respiratory_rate')
            if respiratory_rate:
                triage.respiratory_rate = int(respiratory_rate)
            temperature = request.POST.get('temperature')
            if temperature:
                triage.temperature = float(temperature)
            oxygen_saturation = request.POST.get('oxygen_saturation')
            if oxygen_saturation:
                triage.oxygen_saturation = int(oxygen_saturation)
            pain_scale = request.POST.get('pain_scale')
            if pain_scale:
                triage.pain_scale = int(pain_scale)

            # Evaluación
            triage.consciousness_level = request.POST.get('consciousness_level', 'alert')
            glasgow_score = request.POST.get('glasgow_score')
            if glasgow_score:
                triage.glasgow_score = int(glasgow_score)

            # Clasificación de triage
            triage.triage_level = request.POST.get('triage_level')

            # Observaciones
            triage.warning_signs = request.POST.get('warning_signs', '')
            triage.allergies = request.POST.get('allergies', '')
            triage.current_medications = request.POST.get('current_medications', '')

            # Personal
            triage.triage_nurse_id = request.POST.get('triage_nurse')
            triage.observations = request.POST.get('observations', '')

            triage.created_by = request.user
            triage.save()

            messages.success(request, f'Triage {triage.triage_number} creado exitosamente.')
            return redirect('emergency:triage_detail', triage_id=triage.id)
        except Exception as e:
            messages.error(request, f'Error al crear el triage: {str(e)}')

    # Obtener pacientes y enfermeras
    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party')

    nurses = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'patients': patients,
        'nurses': nurses,
        'arrival_mode_choices': TriageAssessment.ARRIVAL_MODE_CHOICES,
        'consciousness_level_choices': TriageAssessment.CONSCIOUSNESS_LEVEL_CHOICES,
        'triage_level_choices': TriageAssessment.TRIAGE_LEVEL_CHOICES,
    }

    return render(request, 'emergency/triage_form.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def triage_update(request, triage_id):
    """Actualizar evaluación de triage."""
    company_id = request.session.get('active_company')
    triage = get_object_or_404(
        TriageAssessment,
        id=triage_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            # Actualizar campos editables
            triage.arrival_mode = request.POST.get('arrival_mode')
            triage.accompanied_by = request.POST.get('accompanied_by', '')
            triage.chief_complaint = request.POST.get('chief_complaint')
            triage.symptom_duration = request.POST.get('symptom_duration', '')

            # Signos vitales
            triage.blood_pressure = request.POST.get('blood_pressure', '')
            heart_rate = request.POST.get('heart_rate')
            triage.heart_rate = int(heart_rate) if heart_rate else None
            respiratory_rate = request.POST.get('respiratory_rate')
            triage.respiratory_rate = int(respiratory_rate) if respiratory_rate else None
            temperature = request.POST.get('temperature')
            triage.temperature = float(temperature) if temperature else None
            oxygen_saturation = request.POST.get('oxygen_saturation')
            triage.oxygen_saturation = int(oxygen_saturation) if oxygen_saturation else None
            pain_scale = request.POST.get('pain_scale')
            triage.pain_scale = int(pain_scale) if pain_scale else None

            # Evaluación
            triage.consciousness_level = request.POST.get('consciousness_level', 'alert')
            glasgow_score = request.POST.get('glasgow_score')
            triage.glasgow_score = int(glasgow_score) if glasgow_score else None

            # Clasificación
            triage.triage_level = request.POST.get('triage_level')

            # Observaciones
            triage.warning_signs = request.POST.get('warning_signs', '')
            triage.allergies = request.POST.get('allergies', '')
            triage.current_medications = request.POST.get('current_medications', '')
            triage.observations = request.POST.get('observations', '')

            # Estado
            if request.POST.get('patient_called') == 'on':
                triage.patient_called = True
                if not triage.call_datetime:
                    triage.call_datetime = timezone.now()
            else:
                triage.patient_called = False

            triage.save()

            messages.success(request, 'Triage actualizado exitosamente.')
            return redirect('emergency:triage_detail', triage_id=triage.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar el triage: {str(e)}')

    nurses = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'triage': triage,
        'nurses': nurses,
        'arrival_mode_choices': TriageAssessment.ARRIVAL_MODE_CHOICES,
        'consciousness_level_choices': TriageAssessment.CONSCIOUSNESS_LEVEL_CHOICES,
        'triage_level_choices': TriageAssessment.TRIAGE_LEVEL_CHOICES,
        'is_update': True,
    }

    return render(request, 'emergency/triage_form.html', context)


# =============================================================================
# ADMISIONES DE URGENCIAS
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def admission_list(request):
    """Lista de admisiones de urgencias."""
    company_id = request.session.get('active_company')

    admissions = EmergencyAdmission.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'triage', 'attending_physician')

    # Filtros
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    physician_id = request.GET.get('physician')
    triage_level = request.GET.get('triage_level')
    search = request.GET.get('search')

    if status:
        admissions = admissions.filter(status=status)

    if date_from:
        admissions = admissions.filter(admission_datetime__date__gte=date_from)

    if date_to:
        admissions = admissions.filter(admission_datetime__date__lte=date_to)

    if physician_id:
        admissions = admissions.filter(attending_physician_id=physician_id)

    if triage_level:
        admissions = admissions.filter(triage__triage_level=triage_level)

    if search:
        admissions = admissions.filter(
            Q(admission_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(patient__medical_record_number__icontains=search) |
            Q(emergency_area__icontains=search) |
            Q(bed_number__icontains=search)
        )

    # Paginación
    paginator = Paginator(admissions.order_by('-admission_datetime'), 15)
    page = request.GET.get('page')
    admissions = paginator.get_page(page)

    # Para filtros
    physicians = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'admissions': admissions,
        'status_choices': EmergencyAdmission.STATUS_CHOICES,
        'triage_level_choices': TriageAssessment.TRIAGE_LEVEL_CHOICES,
        'physicians': physicians,
        'filters': {
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
            'physician': physician_id,
            'triage_level': triage_level,
            'search': search,
        }
    }

    return render(request, 'emergency/admission_list.html', context)


@login_required
@company_required
@module_permission_required('emergency')
def admission_detail(request, admission_id):
    """Detalle de admisión de urgencias."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission.objects.select_related(
            'patient__third_party', 'triage', 'attending_physician',
            'assigned_nurse', 'created_by'
        ),
        id=admission_id,
        company_id=company_id
    )

    # Obtener registros de signos vitales
    vital_signs = VitalSignsRecord.objects.filter(
        admission=admission
    ).select_related('recorded_by').order_by('-recorded_datetime')

    # Verificar si tiene atención asociada
    has_attention = hasattr(admission, 'attention')

    # Verificar si tiene alta
    has_discharge = hasattr(admission, 'discharge')

    # Obtener procedimientos
    procedures = EmergencyProcedure.objects.filter(
        admission=admission
    ).select_related('performed_by').order_by('-procedure_datetime')

    context = {
        'admission': admission,
        'vital_signs': vital_signs,
        'procedures': procedures,
        'has_attention': has_attention,
        'has_discharge': has_discharge,
    }

    return render(request, 'emergency/admission_detail.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def admission_create(request):
    """Crear nueva admisión de urgencias."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            admission = EmergencyAdmission()
            admission.company_id = company_id
            admission.triage_id = request.POST.get('triage')

            # El paciente se obtiene del triage
            triage = TriageAssessment.objects.get(id=admission.triage_id)
            admission.patient = triage.patient

            admission.admission_datetime = request.POST.get('admission_datetime')

            # Ubicación
            admission.emergency_area = request.POST.get('emergency_area', '')
            admission.bed_number = request.POST.get('bed_number', '')

            # Personal
            admission.attending_physician_id = request.POST.get('attending_physician')
            nurse_id = request.POST.get('assigned_nurse')
            if nurse_id:
                admission.assigned_nurse_id = nurse_id

            # Información de seguro
            admission.insurance_company = request.POST.get('insurance_company', '')
            admission.authorization_number = request.POST.get('authorization_number', '')
            admission.requires_authorization = request.POST.get('requires_authorization') == 'on'

            # Observaciones
            admission.admission_notes = request.POST.get('admission_notes', '')

            admission.created_by = request.user
            admission.save()

            messages.success(request, f'Admisión {admission.admission_number} creada exitosamente.')
            return redirect('emergency:admission_detail', admission_id=admission.id)
        except Exception as e:
            messages.error(request, f'Error al crear la admisión: {str(e)}')

    # Obtener triages sin admisión
    available_triages = TriageAssessment.objects.filter(
        company_id=company_id,
        admission__isnull=True
    ).select_related('patient__third_party').order_by('triage_level', '-arrival_datetime')

    physicians = User.objects.filter(company_id=company_id, is_active=True)
    nurses = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'available_triages': available_triages,
        'physicians': physicians,
        'nurses': nurses,
    }

    return render(request, 'emergency/admission_form.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def admission_update_status(request, admission_id):
    """Actualizar estado de admisión."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(EmergencyAdmission.STATUS_CHOICES):
            old_status = admission.status
            admission.status = new_status

            # Si pasa a atención, registrar inicio
            if new_status == 'in_attention' and not admission.attention_start_datetime:
                admission.attention_start_datetime = timezone.now()

            # Si se completa, registrar fin
            if new_status in ['discharged', 'hospitalized', 'transferred', 'deceased']:
                if not admission.attention_end_datetime:
                    admission.attention_end_datetime = timezone.now()

            admission.save()
            messages.success(request, f'Estado actualizado de {old_status} a {admission.get_status_display()}')
        else:
            messages.error(request, 'Estado inválido')

    return redirect('emergency:admission_detail', admission_id=admission_id)


# =============================================================================
# SIGNOS VITALES
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def vital_signs_list(request, admission_id):
    """Lista de signos vitales de una admisión."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    vital_signs = VitalSignsRecord.objects.filter(
        admission=admission
    ).select_related('recorded_by').order_by('-recorded_datetime')

    context = {
        'admission': admission,
        'vital_signs': vital_signs,
    }

    return render(request, 'emergency/vital_signs_list.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def vital_signs_create(request, admission_id):
    """Crear nuevo registro de signos vitales."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            vital_signs = VitalSignsRecord()
            vital_signs.company_id = company_id
            vital_signs.admission = admission
            vital_signs.recorded_datetime = request.POST.get('recorded_datetime')

            # Signos vitales
            systolic = request.POST.get('blood_pressure_systolic')
            if systolic:
                vital_signs.blood_pressure_systolic = int(systolic)
            diastolic = request.POST.get('blood_pressure_diastolic')
            if diastolic:
                vital_signs.blood_pressure_diastolic = int(diastolic)
            heart_rate = request.POST.get('heart_rate')
            if heart_rate:
                vital_signs.heart_rate = int(heart_rate)
            respiratory_rate = request.POST.get('respiratory_rate')
            if respiratory_rate:
                vital_signs.respiratory_rate = int(respiratory_rate)
            temperature = request.POST.get('temperature')
            if temperature:
                vital_signs.temperature = float(temperature)
            oxygen_saturation = request.POST.get('oxygen_saturation')
            if oxygen_saturation:
                vital_signs.oxygen_saturation = int(oxygen_saturation)
            pain_scale = request.POST.get('pain_scale')
            if pain_scale:
                vital_signs.pain_scale = int(pain_scale)

            # Datos adicionales
            weight = request.POST.get('weight')
            if weight:
                vital_signs.weight = float(weight)
            height = request.POST.get('height')
            if height:
                vital_signs.height = float(height)
            glasgow_score = request.POST.get('glasgow_score')
            if glasgow_score:
                vital_signs.glasgow_score = int(glasgow_score)

            vital_signs.observations = request.POST.get('observations', '')
            vital_signs.recorded_by = request.user
            vital_signs.save()

            messages.success(request, 'Signos vitales registrados exitosamente.')
            return redirect('emergency:admission_detail', admission_id=admission.id)
        except Exception as e:
            messages.error(request, f'Error al registrar signos vitales: {str(e)}')

    context = {
        'admission': admission,
    }

    return render(request, 'emergency/vital_signs_form.html', context)


@login_required
@company_required
@module_permission_required('emergency')
def vital_signs_chart(request, admission_id):
    """Gráfica de tendencias de signos vitales."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    vital_signs = VitalSignsRecord.objects.filter(
        admission=admission
    ).order_by('recorded_datetime').values(
        'recorded_datetime', 'blood_pressure_systolic', 'blood_pressure_diastolic',
        'heart_rate', 'respiratory_rate', 'temperature', 'oxygen_saturation', 'pain_scale'
    )

    context = {
        'admission': admission,
        'vital_signs_data': list(vital_signs),
    }

    return render(request, 'emergency/vital_signs_chart.html', context)


# =============================================================================
# ATENCIÓN DE URGENCIAS
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def attention_detail(request, attention_id):
    """Detalle de atención de urgencias."""
    company_id = request.session.get('active_company')
    attention = get_object_or_404(
        EmergencyAttention.objects.select_related(
            'patient__third_party', 'admission', 'physician', 'created_by'
        ),
        id=attention_id,
        company_id=company_id
    )

    context = {
        'attention': attention,
    }

    return render(request, 'emergency/attention_detail.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def attention_create(request, admission_id):
    """Crear nueva atención de urgencias."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    # Verificar que no tenga atención ya creada
    if hasattr(admission, 'attention'):
        messages.warning(request, 'Esta admisión ya tiene una atención registrada.')
        return redirect('emergency:attention_detail', attention_id=admission.attention.id)

    if request.method == 'POST':
        try:
            attention = EmergencyAttention()
            attention.company_id = company_id
            attention.admission = admission
            attention.patient = admission.patient
            attention.physician_id = request.POST.get('physician')
            attention.attention_date = request.POST.get('attention_date')

            # Anamnesis
            attention.current_illness = request.POST.get('current_illness')
            attention.review_of_systems = request.POST.get('review_of_systems', '')
            attention.personal_history = request.POST.get('personal_history', '')
            attention.family_history = request.POST.get('family_history', '')
            attention.allergies = request.POST.get('allergies', '')
            attention.current_medications = request.POST.get('current_medications', '')

            # Examen físico
            attention.general_appearance = request.POST.get('general_appearance', '')
            attention.physical_examination = request.POST.get('physical_examination')
            attention.cardiovascular_exam = request.POST.get('cardiovascular_exam', '')
            attention.respiratory_exam = request.POST.get('respiratory_exam', '')
            attention.abdominal_exam = request.POST.get('abdominal_exam', '')
            attention.neurological_exam = request.POST.get('neurological_exam', '')

            # Diagnóstico
            attention.diagnosis = request.POST.get('diagnosis')
            attention.differential_diagnosis = request.POST.get('differential_diagnosis', '')

            # Plan de tratamiento
            attention.treatment_plan = request.POST.get('treatment_plan')
            attention.medications_prescribed = request.POST.get('medications_prescribed', '')
            attention.procedures_indicated = request.POST.get('procedures_indicated', '')

            # Estudios
            attention.lab_tests_ordered = request.POST.get('lab_tests_ordered', '')
            attention.imaging_studies_ordered = request.POST.get('imaging_studies_ordered', '')

            # Evolución
            attention.clinical_evolution = request.POST.get('clinical_evolution', '')
            attention.prognosis = request.POST.get('prognosis', '')
            attention.observations = request.POST.get('observations', '')

            attention.created_by = request.user
            attention.save()

            # Actualizar estado de admisión
            if admission.status == 'waiting':
                admission.status = 'in_attention'
                admission.attention_start_datetime = timezone.now()
                admission.save()

            messages.success(request, f'Atención {attention.attention_number} creada exitosamente.')
            return redirect('emergency:attention_detail', attention_id=attention.id)
        except Exception as e:
            messages.error(request, f'Error al crear la atención: {str(e)}')

    physicians = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'admission': admission,
        'physicians': physicians,
    }

    return render(request, 'emergency/attention_form.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def attention_update(request, attention_id):
    """Actualizar atención de urgencias."""
    company_id = request.session.get('active_company')
    attention = get_object_or_404(
        EmergencyAttention,
        id=attention_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            # Anamnesis
            attention.current_illness = request.POST.get('current_illness')
            attention.review_of_systems = request.POST.get('review_of_systems', '')
            attention.personal_history = request.POST.get('personal_history', '')
            attention.family_history = request.POST.get('family_history', '')
            attention.allergies = request.POST.get('allergies', '')
            attention.current_medications = request.POST.get('current_medications', '')

            # Examen físico
            attention.general_appearance = request.POST.get('general_appearance', '')
            attention.physical_examination = request.POST.get('physical_examination')
            attention.cardiovascular_exam = request.POST.get('cardiovascular_exam', '')
            attention.respiratory_exam = request.POST.get('respiratory_exam', '')
            attention.abdominal_exam = request.POST.get('abdominal_exam', '')
            attention.neurological_exam = request.POST.get('neurological_exam', '')

            # Diagnóstico
            attention.diagnosis = request.POST.get('diagnosis')
            attention.differential_diagnosis = request.POST.get('differential_diagnosis', '')

            # Plan de tratamiento
            attention.treatment_plan = request.POST.get('treatment_plan')
            attention.medications_prescribed = request.POST.get('medications_prescribed', '')
            attention.procedures_indicated = request.POST.get('procedures_indicated', '')

            # Estudios
            attention.lab_tests_ordered = request.POST.get('lab_tests_ordered', '')
            attention.imaging_studies_ordered = request.POST.get('imaging_studies_ordered', '')

            # Evolución
            attention.clinical_evolution = request.POST.get('clinical_evolution', '')
            attention.prognosis = request.POST.get('prognosis', '')
            attention.observations = request.POST.get('observations', '')

            attention.save()

            messages.success(request, 'Atención actualizada exitosamente.')
            return redirect('emergency:attention_detail', attention_id=attention.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar la atención: {str(e)}')

    context = {
        'attention': attention,
        'is_update': True,
    }

    return render(request, 'emergency/attention_form.html', context)


# =============================================================================
# PROCEDIMIENTOS
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def procedure_list(request, attention_id):
    """Lista de procedimientos de una atención."""
    company_id = request.session.get('active_company')
    attention = get_object_or_404(
        EmergencyAttention,
        id=attention_id,
        company_id=company_id
    )

    procedures = EmergencyProcedure.objects.filter(
        admission=attention.admission
    ).select_related('performed_by').order_by('-procedure_datetime')

    context = {
        'attention': attention,
        'procedures': procedures,
    }

    return render(request, 'emergency/procedure_list.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def procedure_create(request, attention_id):
    """Crear nuevo procedimiento."""
    company_id = request.session.get('active_company')
    attention = get_object_or_404(
        EmergencyAttention,
        id=attention_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            procedure = EmergencyProcedure()
            procedure.company_id = company_id
            procedure.admission = attention.admission
            procedure.procedure_type = request.POST.get('procedure_type')
            procedure.procedure_name = request.POST.get('procedure_name')
            procedure.procedure_datetime = request.POST.get('procedure_datetime')

            # Descripción
            procedure.indication = request.POST.get('indication')
            procedure.procedure_description = request.POST.get('procedure_description')
            procedure.materials_used = request.POST.get('materials_used', '')

            # Personal
            procedure.performed_by_id = request.POST.get('performed_by')
            procedure.assisted_by = request.POST.get('assisted_by', '')

            # Resultado
            procedure.complications = request.POST.get('complications', '')
            procedure.outcome = request.POST.get('outcome', '')
            procedure.observations = request.POST.get('observations', '')

            procedure.created_by = request.user
            procedure.save()

            messages.success(request, 'Procedimiento registrado exitosamente.')
            return redirect('emergency:attention_detail', attention_id=attention.id)
        except Exception as e:
            messages.error(request, f'Error al registrar el procedimiento: {str(e)}')

    professionals = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'attention': attention,
        'professionals': professionals,
        'procedure_type_choices': EmergencyProcedure.PROCEDURE_TYPE_CHOICES,
    }

    return render(request, 'emergency/procedure_form.html', context)


# =============================================================================
# ALTA DE URGENCIAS
# =============================================================================

@login_required
@company_required
@module_permission_required('emergency')
def discharge_detail(request, discharge_id):
    """Detalle de alta de urgencias."""
    company_id = request.session.get('active_company')
    discharge = get_object_or_404(
        EmergencyDischarge.objects.select_related(
            'patient__third_party', 'admission', 'discharge_physician', 'created_by'
        ),
        id=discharge_id,
        company_id=company_id
    )

    context = {
        'discharge': discharge,
    }

    return render(request, 'emergency/discharge_detail.html', context)


@login_required
@company_required
@module_permission_required('emergency', 'edit')
def discharge_create(request, admission_id):
    """Crear alta de urgencias."""
    company_id = request.session.get('active_company')
    admission = get_object_or_404(
        EmergencyAdmission,
        id=admission_id,
        company_id=company_id
    )

    # Verificar que no tenga alta ya creada
    if hasattr(admission, 'discharge'):
        messages.warning(request, 'Esta admisión ya tiene un alta registrada.')
        return redirect('emergency:discharge_detail', discharge_id=admission.discharge.id)

    if request.method == 'POST':
        try:
            discharge = EmergencyDischarge()
            discharge.company_id = company_id
            discharge.admission = admission
            discharge.patient = admission.patient

            discharge.discharge_datetime = request.POST.get('discharge_datetime')
            discharge.discharge_type = request.POST.get('discharge_type')
            discharge.discharge_condition = request.POST.get('discharge_condition')

            # Diagnóstico final
            discharge.final_diagnosis = request.POST.get('final_diagnosis')

            # Tratamiento y recomendaciones
            discharge.treatment_received = request.POST.get('treatment_received')
            discharge.discharge_medications = request.POST.get('discharge_medications', '')
            discharge.recommendations = request.POST.get('recommendations')
            discharge.warning_signs = request.POST.get('warning_signs', '')

            # Seguimiento
            discharge.follow_up_required = request.POST.get('follow_up_required') == 'on'
            discharge.follow_up_specialty = request.POST.get('follow_up_specialty', '')
            follow_up_days = request.POST.get('follow_up_days')
            if follow_up_days:
                discharge.follow_up_days = int(follow_up_days)

            # Incapacidad
            sick_leave_days = request.POST.get('sick_leave_days')
            if sick_leave_days:
                discharge.sick_leave_days = int(sick_leave_days)

            # Hospitalización
            discharge.hospitalization_service = request.POST.get('hospitalization_service', '')
            discharge.bed_assigned = request.POST.get('bed_assigned', '')

            # Traslado
            discharge.transfer_institution = request.POST.get('transfer_institution', '')
            discharge.transfer_reason = request.POST.get('transfer_reason', '')

            # Personal
            discharge.discharge_physician_id = request.POST.get('discharge_physician')
            discharge.observations = request.POST.get('observations', '')

            discharge.created_by = request.user
            discharge.save()

            # Actualizar estado de admisión según tipo de alta
            if discharge.discharge_type == 'home':
                admission.status = 'discharged'
            elif discharge.discharge_type == 'hospitalization':
                admission.status = 'hospitalized'
            elif discharge.discharge_type == 'transfer':
                admission.status = 'transferred'
            elif discharge.discharge_type == 'deceased':
                admission.status = 'deceased'
            elif discharge.discharge_type in ['voluntary', 'left_without_attention']:
                admission.status = 'left_without_attention'

            if not admission.attention_end_datetime:
                admission.attention_end_datetime = timezone.now()
            admission.save()

            messages.success(request, f'Alta {discharge.discharge_number} creada exitosamente.')
            return redirect('emergency:discharge_detail', discharge_id=discharge.id)
        except Exception as e:
            messages.error(request, f'Error al crear el alta: {str(e)}')

    physicians = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'admission': admission,
        'physicians': physicians,
        'discharge_type_choices': EmergencyDischarge.DISCHARGE_TYPE_CHOICES,
        'discharge_condition_choices': EmergencyDischarge.DISCHARGE_CONDITION_CHOICES,
    }

    return render(request, 'emergency/discharge_form.html', context)


# =============================================================================
# API/AJAX ENDPOINTS
# =============================================================================

@login_required
@company_required
def get_triage_info(request, triage_id):
    """API para obtener información del triage (AJAX)."""
    company_id = request.session.get('active_company')

    try:
        triage = TriageAssessment.objects.select_related('patient__third_party').get(
            id=triage_id,
            company_id=company_id
        )

        data = {
            'id': str(triage.id),
            'triage_number': triage.triage_number,
            'patient_id': str(triage.patient.id),
            'patient_name': triage.patient.get_full_name(),
            'triage_level': triage.triage_level,
            'triage_color': triage.triage_color,
            'chief_complaint': triage.chief_complaint,
            'arrival_datetime': triage.arrival_datetime.isoformat(),
            'blood_pressure': triage.blood_pressure or '',
            'heart_rate': triage.heart_rate or '',
            'temperature': str(triage.temperature) if triage.temperature else '',
            'oxygen_saturation': triage.oxygen_saturation or '',
            'allergies': triage.allergies or '',
            'current_medications': triage.current_medications or '',
        }

        return JsonResponse(data)
    except TriageAssessment.DoesNotExist:
        return JsonResponse({'error': 'Triage no encontrado'}, status=404)
