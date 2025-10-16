"""
Vistas del módulo Psicología
Gestión completa de consultas, sesiones terapéuticas y seguimiento
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
    PsychologicalConsultation, TherapySession, PsychologicalAssessment,
    PsychologicalTest, TreatmentPlan, ProgressNote
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def psychology_dashboard(request):
    """Dashboard principal de psicología"""
    company = get_current_company(request)

    # Estadísticas
    total_consultations_today = PsychologicalConsultation.objects.filter(
        company=company,
        consultation_date__date=timezone.now().date()
    ).count()

    total_sessions_today = TherapySession.objects.filter(
        company=company,
        session_date__date=timezone.now().date()
    ).count()

    active_treatment_plans = TreatmentPlan.objects.filter(
        company=company,
        status='active'
    ).count()

    total_patients = Patient.objects.filter(
        company=company,
        psychological_consultations__isnull=False
    ).distinct().count()

    # Consultas recientes
    recent_consultations = PsychologicalConsultation.objects.filter(
        company=company
    ).select_related('patient__third_party', 'psychologist').order_by('-consultation_date')[:10]

    # Sesiones recientes
    recent_sessions = TherapySession.objects.filter(
        company=company
    ).select_related('patient__third_party', 'psychologist').order_by('-session_date')[:10]

    # Planes de tratamiento activos
    active_plans = TreatmentPlan.objects.filter(
        company=company,
        status='active'
    ).select_related('patient__third_party', 'psychologist').order_by('-plan_date')[:10]

    context = {
        'total_consultations_today': total_consultations_today,
        'total_sessions_today': total_sessions_today,
        'active_treatment_plans': active_treatment_plans,
        'total_patients': total_patients,
        'recent_consultations': recent_consultations,
        'recent_sessions': recent_sessions,
        'active_plans': active_plans,
    }

    return render(request, 'psychology/dashboard.html', context)


# ==================== CONSULTAS ====================

@login_required
@company_required
def consultation_list(request):
    """Listado de consultas psicológicas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    consultations = PsychologicalConsultation.objects.filter(company=company).select_related(
        'patient__third_party', 'psychologist'
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

    return render(request, 'psychology/consultation_list.html', context)


@login_required
@company_required
def consultation_create(request):
    """Crear nueva consulta psicológica"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de consulta
            last_consultation = PsychologicalConsultation.objects.filter(company=company).aggregate(
                last_number=Max('consultation_number')
            )
            if last_consultation['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_consultation['last_number'])))
                consultation_number = f"PSY-{last_num + 1:07d}"
            else:
                consultation_number = "PSY-0000001"

            consultation = PsychologicalConsultation.objects.create(
                company=company,
                consultation_number=consultation_number,
                patient=patient,
                psychologist=request.user,
                chief_complaint=request.POST.get('chief_complaint'),
                referred_by=request.POST.get('referred_by', ''),
                personal_history=request.POST.get('personal_history', ''),
                family_history=request.POST.get('family_history', ''),
                medical_history=request.POST.get('medical_history', ''),
                psychiatric_history=request.POST.get('psychiatric_history', ''),
                current_medications=request.POST.get('current_medications', ''),
                substance_use=request.POST.get('substance_use', ''),
                appearance=request.POST.get('appearance', ''),
                behavior=request.POST.get('behavior', ''),
                speech=request.POST.get('speech', ''),
                mood=request.POST.get('mood', ''),
                affect=request.POST.get('affect', ''),
                thought_process=request.POST.get('thought_process', ''),
                thought_content=request.POST.get('thought_content', ''),
                perception=request.POST.get('perception', ''),
                cognition=request.POST.get('cognition', ''),
                insight=request.POST.get('insight', ''),
                judgment=request.POST.get('judgment', ''),
                suicide_risk=request.POST.get('suicide_risk', 'none'),
                homicide_risk=request.POST.get('homicide_risk', 'none'),
                diagnosis=request.POST.get('diagnosis'),
                dsm_code=request.POST.get('dsm_code', ''),
                treatment_recommendations=request.POST.get('treatment_recommendations'),
                therapy_type=request.POST.get('therapy_type', ''),
                frequency=request.POST.get('frequency', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Consulta {consultation_number} creada exitosamente')
            return redirect('psychology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'psychology/consultation_form.html', context)


@login_required
@company_required
def consultation_detail(request, consultation_id):
    """Detalle de la consulta psicológica"""
    company = get_current_company(request)
    consultation = get_object_or_404(
        PsychologicalConsultation.objects.select_related(
            'patient__third_party', 'psychologist'
        ),
        id=consultation_id,
        company=company
    )

    # Obtener datos relacionados
    therapy_sessions = consultation.therapy_sessions.all().order_by('-session_date')
    assessments = consultation.assessments.all().order_by('-assessment_date')
    treatment_plans = consultation.treatment_plans.all().order_by('-plan_date')

    context = {
        'consultation': consultation,
        'therapy_sessions': therapy_sessions,
        'assessments': assessments,
        'treatment_plans': treatment_plans,
    }

    return render(request, 'psychology/consultation_detail.html', context)


# ==================== SESIONES TERAPÉUTICAS ====================

@login_required
@company_required
def session_list(request):
    """Listado de sesiones terapéuticas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    sessions = TherapySession.objects.filter(company=company).select_related(
        'patient__third_party', 'psychologist', 'consultation'
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

    return render(request, 'psychology/session_list.html', context)


@login_required
@company_required
def session_create(request, consultation_id=None):
    """Crear nueva sesión terapéutica"""
    company = get_current_company(request)

    consultation = None
    if consultation_id:
        consultation = get_object_or_404(PsychologicalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de sesión
            last_session = TherapySession.objects.filter(company=company).aggregate(
                last_number=Max('session_number')
            )
            if last_session['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_session['last_number'])))
                session_number = f"SES-{last_num + 1:07d}"
            else:
                session_number = "SES-0000001"

            session = TherapySession.objects.create(
                company=company,
                session_number=session_number,
                consultation=consultation,
                patient=patient,
                psychologist=request.user,
                session_duration=request.POST.get('session_duration', 60),
                session_type=request.POST.get('session_type', 'individual'),
                modality=request.POST.get('modality', 'in_person'),
                presenting_issues=request.POST.get('presenting_issues'),
                interventions=request.POST.get('interventions'),
                patient_response=request.POST.get('patient_response', ''),
                progress_summary=request.POST.get('progress_summary', ''),
                goals_addressed=request.POST.get('goals_addressed', ''),
                homework_assigned=request.POST.get('homework_assigned', ''),
                homework_completed=request.POST.get('homework_completed') == 'on',
                next_session_goals=request.POST.get('next_session_goals', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            # Fecha de próxima sesión
            if request.POST.get('next_session_date'):
                session.next_session_date = request.POST.get('next_session_date')
                session.save()

            messages.success(request, f'Sesión {session_number} creada exitosamente')
            return redirect('psychology:session_detail', session_id=session.id)

        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
        'consultation': consultation,
    }

    return render(request, 'psychology/session_form.html', context)


@login_required
@company_required
def session_detail(request, session_id):
    """Detalle de la sesión terapéutica"""
    company = get_current_company(request)
    session = get_object_or_404(
        TherapySession.objects.select_related(
            'patient__third_party', 'psychologist', 'consultation'
        ),
        id=session_id,
        company=company
    )

    # Obtener nota de progreso si existe
    try:
        progress_note = session.progress_note
    except ProgressNote.DoesNotExist:
        progress_note = None

    context = {
        'session': session,
        'progress_note': progress_note,
    }

    return render(request, 'psychology/session_detail.html', context)


# ==================== PLANES DE TRATAMIENTO ====================

@login_required
@company_required
def treatment_plan_list(request):
    """Listado de planes de tratamiento"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    plans = TreatmentPlan.objects.filter(company=company).select_related(
        'patient__third_party', 'psychologist', 'consultation'
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

    return render(request, 'psychology/treatment_plan_list.html', context)


@login_required
@company_required
def treatment_plan_create(request, consultation_id):
    """Crear nuevo plan de tratamiento"""
    company = get_current_company(request)
    consultation = get_object_or_404(PsychologicalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            # Generar número de plan
            last_plan = TreatmentPlan.objects.filter(company=company).aggregate(
                last_number=Max('plan_number')
            )
            if last_plan['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_plan['last_number'])))
                plan_number = f"PLAN-{last_num + 1:07d}"
            else:
                plan_number = "PLAN-0000001"

            plan = TreatmentPlan.objects.create(
                company=company,
                plan_number=plan_number,
                consultation=consultation,
                patient=consultation.patient,
                psychologist=request.user,
                start_date=request.POST.get('start_date'),
                diagnosis=request.POST.get('diagnosis'),
                long_term_goals=request.POST.get('long_term_goals'),
                short_term_goals=request.POST.get('short_term_goals'),
                therapeutic_approach=request.POST.get('therapeutic_approach'),
                interventions=request.POST.get('interventions'),
                session_frequency=request.POST.get('session_frequency'),
                estimated_sessions=request.POST.get('estimated_sessions') or None,
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            # Fecha de finalización estimada
            if request.POST.get('end_date'):
                plan.end_date = request.POST.get('end_date')
                plan.save()

            messages.success(request, f'Plan de tratamiento {plan_number} creado exitosamente')
            return redirect('psychology:treatment_plan_detail', plan_id=plan.id)

        except Exception as e:
            messages.error(request, f'Error al crear el plan de tratamiento: {str(e)}')

    context = {
        'consultation': consultation,
    }

    return render(request, 'psychology/treatment_plan_form.html', context)


@login_required
@company_required
def treatment_plan_detail(request, plan_id):
    """Detalle del plan de tratamiento"""
    company = get_current_company(request)
    plan = get_object_or_404(
        TreatmentPlan.objects.select_related(
            'patient__third_party', 'psychologist', 'consultation'
        ),
        id=plan_id,
        company=company
    )

    # Obtener notas de progreso
    progress_notes = plan.progress_notes.all().order_by('-note_date')

    context = {
        'plan': plan,
        'progress_notes': progress_notes,
    }

    return render(request, 'psychology/treatment_plan_detail.html', context)


# ==================== EVALUACIONES ====================

@login_required
@company_required
def assessment_list(request):
    """Listado de evaluaciones psicológicas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    assessment_type = request.GET.get('assessment_type', '')

    assessments = PsychologicalAssessment.objects.filter(company=company).select_related(
        'patient__third_party', 'psychologist', 'consultation'
    )

    if search:
        assessments = assessments.filter(
            Q(assessment_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if assessment_type:
        assessments = assessments.filter(assessment_type=assessment_type)

    assessments = assessments.order_by('-assessment_date')

    paginator = Paginator(assessments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'assessment_type_filter': assessment_type,
    }

    return render(request, 'psychology/assessment_list.html', context)


@login_required
@company_required
def assessment_create(request, consultation_id=None):
    """Crear nueva evaluación psicológica"""
    company = get_current_company(request)

    consultation = None
    if consultation_id:
        consultation = get_object_or_404(PsychologicalConsultation, id=consultation_id, company=company)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de evaluación
            last_assessment = PsychologicalAssessment.objects.filter(company=company).aggregate(
                last_number=Max('assessment_number')
            )
            if last_assessment['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_assessment['last_number'])))
                assessment_number = f"EVAL-{last_num + 1:07d}"
            else:
                assessment_number = "EVAL-0000001"

            assessment = PsychologicalAssessment.objects.create(
                company=company,
                assessment_number=assessment_number,
                consultation=consultation,
                patient=patient,
                psychologist=request.user,
                assessment_type=request.POST.get('assessment_type'),
                purpose=request.POST.get('purpose'),
                results_summary=request.POST.get('results_summary'),
                interpretations=request.POST.get('interpretations'),
                conclusions=request.POST.get('conclusions'),
                recommendations=request.POST.get('recommendations'),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Evaluación {assessment_number} creada exitosamente')
            return redirect('psychology:assessment_detail', assessment_id=assessment.id)

        except Exception as e:
            messages.error(request, f'Error al crear la evaluación: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
        'consultation': consultation,
    }

    return render(request, 'psychology/assessment_form.html', context)


@login_required
@company_required
def assessment_detail(request, assessment_id):
    """Detalle de la evaluación psicológica"""
    company = get_current_company(request)
    assessment = get_object_or_404(
        PsychologicalAssessment.objects.select_related(
            'patient__third_party', 'psychologist', 'consultation'
        ),
        id=assessment_id,
        company=company
    )

    # Obtener pruebas psicológicas
    tests = assessment.tests.all().order_by('test_name')

    context = {
        'assessment': assessment,
        'tests': tests,
    }

    return render(request, 'psychology/assessment_detail.html', context)
