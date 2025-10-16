"""
Vistas del módulo Rehabilitación
Gestión completa de consultas, planes y sesiones de rehabilitación física
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
    RehabilitationConsultation, PhysicalAssessment, RehabilitationPlan,
    RehabilitationSession, ExercisePrescription, ProgressMeasurement
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def rehabilitation_dashboard(request):
    """Dashboard principal de rehabilitación"""
    company = get_current_company(request)

    # Estadísticas
    total_consultations_today = RehabilitationConsultation.objects.filter(
        company=company,
        consultation_date__date=timezone.now().date()
    ).count()

    total_sessions_today = RehabilitationSession.objects.filter(
        company=company,
        session_date__date=timezone.now().date()
    ).count()

    active_plans = RehabilitationPlan.objects.filter(
        company=company,
        status='active'
    ).count()

    total_patients = Patient.objects.filter(
        company=company,
        rehabilitation_consultations__isnull=False
    ).distinct().count()

    # Consultas recientes
    recent_consultations = RehabilitationConsultation.objects.filter(
        company=company
    ).select_related('patient__third_party', 'physiotherapist').order_by('-consultation_date')[:10]

    # Sesiones recientes
    recent_sessions = RehabilitationSession.objects.filter(
        company=company
    ).select_related('patient__third_party', 'physiotherapist', 'plan').order_by('-session_date')[:10]

    # Planes activos
    active_plans_list = RehabilitationPlan.objects.filter(
        company=company,
        status='active'
    ).select_related('patient__third_party', 'physiotherapist').order_by('-plan_date')[:10]

    context = {
        'total_consultations_today': total_consultations_today,
        'total_sessions_today': total_sessions_today,
        'active_plans': active_plans,
        'total_patients': total_patients,
        'recent_consultations': recent_consultations,
        'recent_sessions': recent_sessions,
        'active_plans_list': active_plans_list,
    }

    return render(request, 'rehabilitation/dashboard.html', context)


# ==================== CONSULTAS ====================

@login_required
@company_required
def consultation_list(request):
    """Listado de consultas de rehabilitación"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    consultations = RehabilitationConsultation.objects.filter(company=company).select_related(
        'patient__third_party', 'physiotherapist'
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

    return render(request, 'rehabilitation/consultation_list.html', context)


@login_required
@company_required
def consultation_create(request):
    """Crear nueva consulta de rehabilitación"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de consulta
            last_consultation = RehabilitationConsultation.objects.filter(company=company).aggregate(
                last_number=Max('consultation_number')
            )
            if last_consultation['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_consultation['last_number'])))
                consultation_number = f"REHAB-{last_num + 1:07d}"
            else:
                consultation_number = "REHAB-0000001"

            consultation = RehabilitationConsultation.objects.create(
                company=company,
                consultation_number=consultation_number,
                patient=patient,
                physiotherapist=request.user,
                chief_complaint=request.POST.get('chief_complaint'),
                injury_mechanism=request.POST.get('injury_mechanism', ''),
                onset_date=request.POST.get('onset_date') or None,
                pain_level=request.POST.get('pain_level', 0),
                pain_location=request.POST.get('pain_location', ''),
                pain_description=request.POST.get('pain_description', ''),
                medical_history=request.POST.get('medical_history', ''),
                surgical_history=request.POST.get('surgical_history', ''),
                medications=request.POST.get('medications', ''),
                previous_treatments=request.POST.get('previous_treatments', ''),
                functional_limitations=request.POST.get('functional_limitations', ''),
                physical_exam_findings=request.POST.get('physical_exam_findings', ''),
                diagnosis=request.POST.get('diagnosis'),
                treatment_goals=request.POST.get('treatment_goals', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Consulta {consultation_number} creada exitosamente')
            return redirect('rehabilitation:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'rehabilitation/consultation_form.html', context)


@login_required
@company_required
def consultation_detail(request, consultation_id):
    """Detalle de la consulta de rehabilitación"""
    company = get_current_company(request)
    consultation = get_object_or_404(
        RehabilitationConsultation.objects.select_related(
            'patient__third_party', 'physiotherapist'
        ),
        id=consultation_id,
        company=company
    )

    # Obtener evaluación física si existe
    try:
        physical_assessment = consultation.physical_assessment
    except PhysicalAssessment.DoesNotExist:
        physical_assessment = None

    # Obtener planes de rehabilitación
    rehabilitation_plans = consultation.rehabilitation_plans.all().order_by('-plan_date')

    context = {
        'consultation': consultation,
        'physical_assessment': physical_assessment,
        'rehabilitation_plans': rehabilitation_plans,
    }

    return render(request, 'rehabilitation/consultation_detail.html', context)


# ==================== EVALUACIÓN FÍSICA ====================

@login_required
@company_required
def physical_assessment_create(request, consultation_id):
    """Crear evaluación física para una consulta"""
    company = get_current_company(request)
    consultation = get_object_or_404(RehabilitationConsultation, id=consultation_id, company=company)

    # Verificar si ya existe una evaluación
    try:
        existing = consultation.physical_assessment
        messages.warning(request, 'Esta consulta ya tiene una evaluación física.')
        return redirect('rehabilitation:consultation_detail', consultation_id=consultation.id)
    except PhysicalAssessment.DoesNotExist:
        pass

    if request.method == 'POST':
        try:
            PhysicalAssessment.objects.create(
                company=company,
                consultation=consultation,
                posture_analysis=request.POST.get('posture_analysis', ''),
                gait_analysis=request.POST.get('gait_analysis', ''),
                range_of_motion_findings=request.POST.get('range_of_motion_findings', ''),
                muscle_strength_findings=request.POST.get('muscle_strength_findings', ''),
                flexibility_assessment=request.POST.get('flexibility_assessment', ''),
                balance_assessment=request.POST.get('balance_assessment', ''),
                coordination_assessment=request.POST.get('coordination_assessment', ''),
                palpation_findings=request.POST.get('palpation_findings', ''),
                special_tests_performed=request.POST.get('special_tests_performed', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, 'Evaluación física creada exitosamente')
            return redirect('rehabilitation:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la evaluación física: {str(e)}')

    context = {
        'consultation': consultation,
    }

    return render(request, 'rehabilitation/physical_assessment_form.html', context)


# ==================== PLANES DE REHABILITACIÓN ====================

@login_required
@company_required
def plan_list(request):
    """Listado de planes de rehabilitación"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    plans = RehabilitationPlan.objects.filter(company=company).select_related(
        'patient__third_party', 'physiotherapist', 'consultation'
    )

    if search:
        plans = plans.filter(
            Q(plan_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if status:
        plans = plans.filter(status=status)

    plans = plans.order_by('-plan_date')

    paginator = Paginator(plans, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
    }

    return render(request, 'rehabilitation/plan_list.html', context)


@login_required
@company_required
def plan_create(request, consultation_id):
    """Crear nuevo plan de rehabilitación"""
    company = get_current_company(request)
    consultation = get_object_or_404(RehabilitationConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            # Generar número de plan
            last_plan = RehabilitationPlan.objects.filter(company=company).aggregate(
                last_number=Max('plan_number')
            )
            if last_plan['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_plan['last_number'])))
                plan_number = f"PLAN-{last_num + 1:07d}"
            else:
                plan_number = "PLAN-0000001"

            plan = RehabilitationPlan.objects.create(
                company=company,
                plan_number=plan_number,
                consultation=consultation,
                patient=consultation.patient,
                physiotherapist=request.user,
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                diagnosis=request.POST.get('diagnosis'),
                short_term_goals=request.POST.get('short_term_goals'),
                long_term_goals=request.POST.get('long_term_goals'),
                treatment_modalities=request.POST.get('treatment_modalities'),
                manual_therapy_techniques=request.POST.get('manual_therapy_techniques', ''),
                therapeutic_exercises_description=request.POST.get('therapeutic_exercises_description', ''),
                frequency_per_week=request.POST.get('frequency_per_week', 3),
                estimated_sessions=request.POST.get('estimated_sessions') or None,
                precautions=request.POST.get('precautions', ''),
                contraindications=request.POST.get('contraindications', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Plan de rehabilitación {plan_number} creado exitosamente')
            return redirect('rehabilitation:plan_detail', plan_id=plan.id)

        except Exception as e:
            messages.error(request, f'Error al crear el plan: {str(e)}')

    context = {
        'consultation': consultation,
    }

    return render(request, 'rehabilitation/plan_form.html', context)


@login_required
@company_required
def plan_detail(request, plan_id):
    """Detalle del plan de rehabilitación"""
    company = get_current_company(request)
    plan = get_object_or_404(
        RehabilitationPlan.objects.select_related(
            'patient__third_party', 'physiotherapist', 'consultation'
        ),
        id=plan_id,
        company=company
    )

    # Obtener ejercicios
    exercises = plan.exercises.filter(is_active=True).order_by('exercise_type', 'exercise_name')

    # Obtener sesiones
    sessions = plan.sessions.all().order_by('-session_date')

    # Obtener mediciones de progreso
    progress_measurements = plan.progress_measurements.all().order_by('-measurement_date')

    context = {
        'plan': plan,
        'exercises': exercises,
        'sessions': sessions,
        'progress_measurements': progress_measurements,
    }

    return render(request, 'rehabilitation/plan_detail.html', context)


# ==================== SESIONES ====================

@login_required
@company_required
def session_list(request):
    """Listado de sesiones de rehabilitación"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    sessions = RehabilitationSession.objects.filter(company=company).select_related(
        'patient__third_party', 'physiotherapist', 'plan'
    )

    if search:
        sessions = sessions.filter(
            Q(session_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if status:
        sessions = sessions.filter(status=status)

    if date_from:
        sessions = sessions.filter(session_date__gte=date_from)

    sessions = sessions.order_by('-session_date')

    paginator = Paginator(sessions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
        'date_from': date_from,
    }

    return render(request, 'rehabilitation/session_list.html', context)


@login_required
@company_required
def session_create(request, plan_id):
    """Crear nueva sesión de rehabilitación"""
    company = get_current_company(request)
    plan = get_object_or_404(RehabilitationPlan, id=plan_id, company=company)

    if request.method == 'POST':
        try:
            # Generar número de sesión
            last_session = RehabilitationSession.objects.filter(company=company).aggregate(
                last_number=Max('session_number')
            )
            if last_session['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_session['last_number'])))
                session_number = f"SES-{last_num + 1:07d}"
            else:
                session_number = "SES-0000001"

            # Calcular número de sesión en el plan
            session_count = plan.sessions.count() + 1

            session = RehabilitationSession.objects.create(
                company=company,
                session_number=session_number,
                plan=plan,
                patient=plan.patient,
                physiotherapist=request.user,
                session_duration=request.POST.get('session_duration', 60),
                session_number_in_plan=session_count,
                pain_level_pre=request.POST.get('pain_level_pre') or None,
                pain_level_post=request.POST.get('pain_level_post') or None,
                modalities_applied=request.POST.get('modalities_applied', ''),
                manual_therapy_performed=request.POST.get('manual_therapy_performed', ''),
                exercises_performed=request.POST.get('exercises_performed', ''),
                patient_tolerance=request.POST.get('patient_tolerance', ''),
                patient_response=request.POST.get('patient_response', ''),
                homework_assigned=request.POST.get('homework_assigned', ''),
                next_session_goals=request.POST.get('next_session_goals', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Sesión {session_number} creada exitosamente')
            return redirect('rehabilitation:session_detail', session_id=session.id)

        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')

    context = {
        'plan': plan,
    }

    return render(request, 'rehabilitation/session_form.html', context)


@login_required
@company_required
def session_detail(request, session_id):
    """Detalle de la sesión de rehabilitación"""
    company = get_current_company(request)
    session = get_object_or_404(
        RehabilitationSession.objects.select_related(
            'patient__third_party', 'physiotherapist', 'plan'
        ),
        id=session_id,
        company=company
    )

    context = {
        'session': session,
    }

    return render(request, 'rehabilitation/session_detail.html', context)


# ==================== EJERCICIOS ====================

@login_required
@company_required
def exercise_list(request, plan_id):
    """Listado de ejercicios de un plan"""
    company = get_current_company(request)
    plan = get_object_or_404(RehabilitationPlan, id=plan_id, company=company)

    exercises = plan.exercises.all().order_by('exercise_type', 'exercise_name')

    context = {
        'plan': plan,
        'exercises': exercises,
    }

    return render(request, 'rehabilitation/exercise_list.html', context)


@login_required
@company_required
def exercise_create(request, plan_id):
    """Crear nuevo ejercicio para un plan"""
    company = get_current_company(request)
    plan = get_object_or_404(RehabilitationPlan, id=plan_id, company=company)

    if request.method == 'POST':
        try:
            ExercisePrescription.objects.create(
                company=company,
                plan=plan,
                exercise_name=request.POST.get('exercise_name'),
                exercise_type=request.POST.get('exercise_type'),
                description=request.POST.get('description'),
                sets=request.POST.get('sets') or None,
                repetitions=request.POST.get('repetitions') or None,
                duration_seconds=request.POST.get('duration_seconds') or None,
                frequency_per_day=request.POST.get('frequency_per_day', 1),
                days_per_week=request.POST.get('days_per_week', 3),
                resistance_level=request.POST.get('resistance_level', ''),
                progression_criteria=request.POST.get('progression_criteria', ''),
                precautions=request.POST.get('precautions', ''),
                created_by=request.user
            )

            messages.success(request, 'Ejercicio agregado exitosamente')
            return redirect('rehabilitation:plan_detail', plan_id=plan.id)

        except Exception as e:
            messages.error(request, f'Error al crear el ejercicio: {str(e)}')

    context = {
        'plan': plan,
    }

    return render(request, 'rehabilitation/exercise_form.html', context)


# ==================== MEDICIONES DE PROGRESO ====================

@login_required
@company_required
def progress_measurement_create(request, plan_id):
    """Crear medición de progreso"""
    company = get_current_company(request)
    plan = get_object_or_404(RehabilitationPlan, id=plan_id, company=company)

    if request.method == 'POST':
        try:
            ProgressMeasurement.objects.create(
                company=company,
                plan=plan,
                measured_by=request.user,
                pain_level=request.POST.get('pain_level') or None,
                rom_measurements=request.POST.get('rom_measurements', ''),
                strength_measurements=request.POST.get('strength_measurements', ''),
                functional_tests_results=request.POST.get('functional_tests_results', ''),
                patient_reported_improvement=request.POST.get('patient_reported_improvement') or None,
                therapist_assessment=request.POST.get('therapist_assessment', ''),
                objective_progress_notes=request.POST.get('objective_progress_notes', ''),
                created_by=request.user
            )

            messages.success(request, 'Medición de progreso registrada exitosamente')
            return redirect('rehabilitation:plan_detail', plan_id=plan.id)

        except Exception as e:
            messages.error(request, f'Error al registrar el progreso: {str(e)}')

    context = {
        'plan': plan,
    }

    return render(request, 'rehabilitation/progress_measurement_form.html', context)
