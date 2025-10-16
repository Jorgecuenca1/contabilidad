"""
Vistas del módulo de Cardiología
Gestión completa de servicios cardiológicos
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from core.models import Company
from core.utils import get_current_company, require_company_access
from third_parties.models import ThirdParty
from payroll.models import Employee

from .models import (
    CardiologyConsultation, Electrocardiogram, Echocardiogram,
    StressTest, HolterMonitoring, CardiovascularRiskAssessment
)


@login_required
@require_company_access
def cardiology_dashboard(request):
    """
    Dashboard del módulo de cardiología.
    Muestra estadísticas y estudios recientes.
    """
    current_company = request.current_company

    # Estadísticas generales
    total_consultations = CardiologyConsultation.objects.filter(
        company=current_company
    ).count()

    today_consultations = CardiologyConsultation.objects.filter(
        company=current_company,
        consultation_date__date=date.today(),
        status__in=['scheduled', 'in_progress']
    ).count()

    pending_ecgs = Electrocardiogram.objects.filter(
        company=current_company,
        result='abnormal'
    ).count()

    high_risk_patients = CardiovascularRiskAssessment.objects.filter(
        company=current_company,
        risk_level__in=['high', 'very_high']
    ).count()

    # Consultas recientes
    recent_consultations = CardiologyConsultation.objects.filter(
        company=current_company
    ).select_related('patient', 'cardiologist').order_by('-consultation_date')[:10]

    # ECGs recientes
    recent_ecgs = Electrocardiogram.objects.filter(
        company=current_company
    ).select_related('patient', 'interpreted_by').order_by('-ecg_date')[:5]

    # Ecocardiogramas recientes
    recent_echos = Echocardiogram.objects.filter(
        company=current_company
    ).select_related('patient', 'interpreted_by').order_by('-echo_date')[:5]

    # Cardiólogos disponibles
    cardiologists = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='cardiólogo') |
        Q(position__icontains='cardiologo')
    )[:5]

    context = {
        'current_company': current_company,
        'total_consultations': total_consultations,
        'today_consultations': today_consultations,
        'pending_ecgs': pending_ecgs,
        'high_risk_patients': high_risk_patients,
        'recent_consultations': recent_consultations,
        'recent_ecgs': recent_ecgs,
        'recent_echos': recent_echos,
        'cardiologists': cardiologists,
    }

    return render(request, 'cardiology/dashboard.html', context)


# ============================================================
# CONSULTAS CARDIOLÓGICAS
# ============================================================

@login_required
@require_company_access
def consultation_list(request):
    """Lista de consultas cardiológicas."""
    current_company = request.current_company

    # Filtros
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    consultation_type_filter = request.GET.get('consultation_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    consultations = CardiologyConsultation.objects.filter(
        company=current_company
    ).select_related('patient', 'cardiologist')

    if search_query:
        consultations = consultations.filter(
            Q(consultation_number__icontains=search_query) |
            Q(patient__name__icontains=search_query) |
            Q(patient__document_number__icontains=search_query)
        )

    if status_filter:
        consultations = consultations.filter(status=status_filter)

    if consultation_type_filter:
        consultations = consultations.filter(consultation_type=consultation_type_filter)

    if date_from:
        consultations = consultations.filter(consultation_date__gte=date_from)

    if date_to:
        consultations = consultations.filter(consultation_date__lte=date_to)

    # Paginación
    paginator = Paginator(consultations.order_by('-consultation_date'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'consultation_type_filter': consultation_type_filter,
        'status_choices': CardiologyConsultation.STATUS_CHOICES,
        'consultation_type_choices': CardiologyConsultation.CONSULTATION_TYPE_CHOICES,
    }

    return render(request, 'cardiology/consultation_list.html', context)


@login_required
@require_company_access
def consultation_create(request):
    """Crear nueva consulta cardiológica."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            # Generar número de consulta
            consultation_number = f"CARDIO-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            consultation = CardiologyConsultation.objects.create(
                company=current_company,
                consultation_number=consultation_number,
                patient_id=request.POST['patient_id'],
                consultation_date=request.POST.get('consultation_date', timezone.now()),
                consultation_type=request.POST['consultation_type'],
                status=request.POST.get('status', 'scheduled'),
                cardiologist_id=request.POST['cardiologist_id'],
                chief_complaint=request.POST['chief_complaint'],
                cardiovascular_history=request.POST.get('cardiovascular_history', ''),

                # Factores de riesgo
                has_hypertension=bool(request.POST.get('has_hypertension')),
                has_diabetes=bool(request.POST.get('has_diabetes')),
                has_dyslipidemia=bool(request.POST.get('has_dyslipidemia')),
                is_smoker=bool(request.POST.get('is_smoker')),
                has_family_history_cvd=bool(request.POST.get('has_family_history_cvd')),
                is_sedentary=bool(request.POST.get('is_sedentary')),
                has_obesity=bool(request.POST.get('has_obesity')),

                # Signos vitales
                blood_pressure_systolic=int(request.POST.get('blood_pressure_systolic', 0)) or None,
                blood_pressure_diastolic=int(request.POST.get('blood_pressure_diastolic', 0)) or None,
                heart_rate=int(request.POST.get('heart_rate', 0)) or None,
                oxygen_saturation=int(request.POST.get('oxygen_saturation', 0)) or None,

                created_by=request.user
            )

            messages.success(request, f'Consulta {consultation.consultation_number} creada exitosamente.')
            return redirect('cardiology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    # Datos para el formulario
    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    cardiologists = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='cardiólogo') |
        Q(position__icontains='cardiologo')
    )

    context = {
        'current_company': current_company,
        'patients': patients,
        'cardiologists': cardiologists,
        'consultation_type_choices': CardiologyConsultation.CONSULTATION_TYPE_CHOICES,
        'status_choices': CardiologyConsultation.STATUS_CHOICES,
    }

    return render(request, 'cardiology/consultation_form.html', context)


@login_required
@require_company_access
def consultation_detail(request, consultation_id):
    """Detalle de una consulta cardiológica."""
    current_company = request.current_company

    consultation = get_object_or_404(
        CardiologyConsultation,
        id=consultation_id,
        company=current_company
    )

    # Estudios relacionados
    ecgs = consultation.electrocardiograms.all()
    echos = consultation.echocardiograms.all()
    stress_tests = consultation.stress_tests.all()
    holters = consultation.holter_monitorings.all()
    risk_assessments = consultation.risk_assessments.all()

    context = {
        'current_company': current_company,
        'consultation': consultation,
        'ecgs': ecgs,
        'echos': echos,
        'stress_tests': stress_tests,
        'holters': holters,
        'risk_assessments': risk_assessments,
    }

    return render(request, 'cardiology/consultation_detail.html', context)


@login_required
@require_company_access
def consultation_update(request, consultation_id):
    """Actualizar consulta cardiológica."""
    current_company = request.current_company

    consultation = get_object_or_404(
        CardiologyConsultation,
        id=consultation_id,
        company=current_company
    )

    if request.method == 'POST':
        try:
            consultation.status = request.POST.get('status', consultation.status)
            consultation.cardiac_auscultation = request.POST.get('cardiac_auscultation', '')
            consultation.peripheral_pulses = request.POST.get('peripheral_pulses', '')
            consultation.edema_presence = bool(request.POST.get('edema_presence'))
            consultation.edema_description = request.POST.get('edema_description', '')

            # Diagnóstico
            consultation.primary_diagnosis_code = request.POST.get('primary_diagnosis_code', '')
            consultation.primary_diagnosis_description = request.POST.get('primary_diagnosis_description', '')
            consultation.secondary_diagnoses = request.POST.get('secondary_diagnoses', '')

            # Plan de manejo
            consultation.treatment_plan = request.POST.get('treatment_plan', '')
            consultation.medications_prescribed = request.POST.get('medications_prescribed', '')

            # Órdenes
            consultation.ecg_ordered = bool(request.POST.get('ecg_ordered'))
            consultation.echo_ordered = bool(request.POST.get('echo_ordered'))
            consultation.stress_test_ordered = bool(request.POST.get('stress_test_ordered'))
            consultation.holter_ordered = bool(request.POST.get('holter_ordered'))

            # Seguimiento
            consultation.follow_up_instructions = request.POST.get('follow_up_instructions', '')
            if request.POST.get('follow_up_date'):
                consultation.follow_up_date = request.POST['follow_up_date']

            consultation.save()

            messages.success(request, 'Consulta actualizada exitosamente.')
            return redirect('cardiology:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar la consulta: {str(e)}')

    context = {
        'current_company': current_company,
        'consultation': consultation,
        'status_choices': CardiologyConsultation.STATUS_CHOICES,
    }

    return render(request, 'cardiology/consultation_update.html', context)


# ============================================================
# ELECTROCARDIOGRAMAS (ECG)
# ============================================================

@login_required
@require_company_access
def ecg_list(request):
    """Lista de electrocardiogramas."""
    current_company = request.current_company

    ecgs = Electrocardiogram.objects.filter(
        company=current_company
    ).select_related('patient', 'interpreted_by').order_by('-ecg_date')

    # Filtros
    search_query = request.GET.get('search', '')
    result_filter = request.GET.get('result', '')

    if search_query:
        ecgs = ecgs.filter(
            Q(ecg_number__icontains=search_query) |
            Q(patient__name__icontains=search_query)
        )

    if result_filter:
        ecgs = ecgs.filter(result=result_filter)

    paginator = Paginator(ecgs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
        'result_choices': Electrocardiogram.RESULT_CHOICES,
    }

    return render(request, 'cardiology/ecg_list.html', context)


@login_required
@require_company_access
def ecg_create(request):
    """Crear nuevo electrocardiograma."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            ecg_number = f"ECG-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            ecg = Electrocardiogram.objects.create(
                company=current_company,
                ecg_number=ecg_number,
                patient_id=request.POST['patient_id'],
                cardiology_consultation_id=request.POST.get('consultation_id') or None,
                ecg_date=request.POST.get('ecg_date', timezone.now()),
                ecg_type=request.POST.get('ecg_type', 'resting'),
                performed_by_id=request.POST['performed_by_id'],
                interpreted_by_id=request.POST['interpreted_by_id'],

                # Parámetros
                heart_rate=int(request.POST['heart_rate']),
                pr_interval=Decimal(request.POST.get('pr_interval', 0)) or None,
                qrs_duration=Decimal(request.POST.get('qrs_duration', 0)) or None,
                qt_interval=Decimal(request.POST.get('qt_interval', 0)) or None,
                qtc_interval=Decimal(request.POST.get('qtc_interval', 0)) or None,

                # Ejes
                p_wave_axis=int(request.POST.get('p_wave_axis', 0)) or None,
                qrs_axis=int(request.POST.get('qrs_axis', 0)) or None,
                t_wave_axis=int(request.POST.get('t_wave_axis', 0)) or None,

                # Ritmo
                rhythm=request.POST.get('rhythm', 'sinus_rhythm'),
                rhythm_description=request.POST.get('rhythm_description', ''),

                # Hallazgos
                findings=request.POST['findings'],
                has_st_changes=bool(request.POST.get('has_st_changes')),
                has_t_wave_changes=bool(request.POST.get('has_t_wave_changes')),
                has_q_waves=bool(request.POST.get('has_q_waves')),
                has_hypertrophy=bool(request.POST.get('has_hypertrophy')),
                has_conduction_block=bool(request.POST.get('has_conduction_block')),

                # Interpretación
                interpretation=request.POST['interpretation'],
                result=request.POST['result'],
                conclusion=request.POST['conclusion'],
                recommendations=request.POST.get('recommendations', ''),

                created_by=request.user
            )

            messages.success(request, f'ECG {ecg.ecg_number} creado exitosamente.')
            return redirect('cardiology:ecg_detail', ecg_id=ecg.id)

        except Exception as e:
            messages.error(request, f'Error al crear el ECG: {str(e)}')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    technicians = Employee.objects.filter(
        company=current_company,
        is_active=True
    )

    consultations = CardiologyConsultation.objects.filter(
        company=current_company,
        ecg_ordered=True
    ).select_related('patient')

    context = {
        'current_company': current_company,
        'patients': patients,
        'technicians': technicians,
        'consultations': consultations,
        'ecg_type_choices': Electrocardiogram.ECG_TYPE_CHOICES,
        'rhythm_choices': Electrocardiogram.RHYTHM_CHOICES,
        'result_choices': Electrocardiogram.RESULT_CHOICES,
    }

    return render(request, 'cardiology/ecg_form.html', context)


@login_required
@require_company_access
def ecg_detail(request, ecg_id):
    """Detalle de un electrocardiograma."""
    current_company = request.current_company

    ecg = get_object_or_404(
        Electrocardiogram,
        id=ecg_id,
        company=current_company
    )

    context = {
        'current_company': current_company,
        'ecg': ecg,
    }

    return render(request, 'cardiology/ecg_detail.html', context)


# ============================================================
# ECOCARDIOGRAMAS
# ============================================================

@login_required
@require_company_access
def echo_list(request):
    """Lista de ecocardiogramas."""
    current_company = request.current_company

    echos = Echocardiogram.objects.filter(
        company=current_company
    ).select_related('patient', 'interpreted_by').order_by('-echo_date')

    paginator = Paginator(echos, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
    }

    return render(request, 'cardiology/echo_list.html', context)


@login_required
@require_company_access
def echo_create(request):
    """Crear nuevo ecocardiograma."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            echo_number = f"ECO-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            echo = Echocardiogram.objects.create(
                company=current_company,
                echo_number=echo_number,
                patient_id=request.POST['patient_id'],
                cardiology_consultation_id=request.POST.get('consultation_id') or None,
                echo_date=request.POST.get('echo_date', timezone.now()),
                echo_type=request.POST.get('echo_type', 'transthoracic'),
                performed_by_id=request.POST['performed_by_id'],
                interpreted_by_id=request.POST['interpreted_by_id'],

                # Signos vitales
                blood_pressure_systolic=int(request.POST.get('blood_pressure_systolic', 0)) or None,
                blood_pressure_diastolic=int(request.POST.get('blood_pressure_diastolic', 0)) or None,
                heart_rate=int(request.POST.get('heart_rate', 0)) or None,

                # Función VI
                lv_end_diastolic_diameter=Decimal(request.POST.get('lv_end_diastolic_diameter', 0)) or None,
                lv_end_systolic_diameter=Decimal(request.POST.get('lv_end_systolic_diameter', 0)) or None,
                ejection_fraction=Decimal(request.POST.get('ejection_fraction', 0)) or None,

                # Válvulas
                mitral_valve_normal=bool(request.POST.get('mitral_valve_normal', True)),
                aortic_valve_normal=bool(request.POST.get('aortic_valve_normal', True)),

                # Hallazgos
                findings=request.POST['findings'],
                conclusion=request.POST['conclusion'],
                result=request.POST['result'],
                recommendations=request.POST.get('recommendations', ''),

                created_by=request.user
            )

            messages.success(request, f'Ecocardiograma {echo.echo_number} creado exitosamente.')
            return redirect('cardiology:echo_detail', echo_id=echo.id)

        except Exception as e:
            messages.error(request, f'Error al crear el ecocardiograma: {str(e)}')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    technicians = Employee.objects.filter(
        company=current_company,
        is_active=True
    )

    context = {
        'current_company': current_company,
        'patients': patients,
        'technicians': technicians,
        'echo_type_choices': Echocardiogram.ECHO_TYPE_CHOICES,
        'result_choices': Echocardiogram.RESULT_CHOICES,
    }

    return render(request, 'cardiology/echo_form.html', context)


@login_required
@require_company_access
def echo_detail(request, echo_id):
    """Detalle de un ecocardiograma."""
    current_company = request.current_company

    echo = get_object_or_404(
        Echocardiogram,
        id=echo_id,
        company=current_company
    )

    context = {
        'current_company': current_company,
        'echo': echo,
    }

    return render(request, 'cardiology/echo_detail.html', context)


# ============================================================
# PRUEBAS DE ESFUERZO
# ============================================================

@login_required
@require_company_access
def stress_test_list(request):
    """Lista de pruebas de esfuerzo."""
    current_company = request.current_company

    tests = StressTest.objects.filter(
        company=current_company
    ).select_related('patient', 'supervised_by').order_by('-test_date')

    paginator = Paginator(tests, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
    }

    return render(request, 'cardiology/stress_test_list.html', context)


@login_required
@require_company_access
def stress_test_create(request):
    """Crear nueva prueba de esfuerzo."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            test_number = f"STRESS-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            test = StressTest.objects.create(
                company=current_company,
                test_number=test_number,
                patient_id=request.POST['patient_id'],
                test_date=request.POST.get('test_date', timezone.now()),
                protocol_used=request.POST.get('protocol_used', 'bruce'),
                performed_by_id=request.POST['performed_by_id'],
                supervised_by_id=request.POST['supervised_by_id'],

                # Datos basales
                baseline_bp_systolic=int(request.POST['baseline_bp_systolic']),
                baseline_bp_diastolic=int(request.POST['baseline_bp_diastolic']),
                baseline_heart_rate=int(request.POST['baseline_heart_rate']),

                # Ejercicio
                exercise_duration_minutes=Decimal(request.POST['exercise_duration_minutes']),
                max_heart_rate_achieved=int(request.POST['max_heart_rate_achieved']),
                max_heart_rate_predicted=int(request.POST['max_heart_rate_predicted']),
                percentage_max_hr=Decimal(request.POST['percentage_max_hr']),
                max_bp_systolic=int(request.POST['max_bp_systolic']),
                max_bp_diastolic=int(request.POST['max_bp_diastolic']),

                # Detención
                stop_reason=request.POST['stop_reason'],
                stop_reason_details=request.POST.get('stop_reason_details', ''),

                # Hallazgos
                st_segment_changes=bool(request.POST.get('st_segment_changes')),
                st_segment_description=request.POST.get('st_segment_description', ''),

                # Resultado
                result=request.POST['result'],
                interpretation=request.POST['interpretation'],
                conclusion=request.POST['conclusion'],
                recommendations=request.POST.get('recommendations', ''),

                created_by=request.user
            )

            messages.success(request, f'Prueba de esfuerzo {test.test_number} creada exitosamente.')
            return redirect('cardiology:stress_test_detail', test_id=test.id)

        except Exception as e:
            messages.error(request, f'Error al crear la prueba: {str(e)}')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    physicians = Employee.objects.filter(
        company=current_company,
        is_active=True
    )

    context = {
        'current_company': current_company,
        'patients': patients,
        'physicians': physicians,
        'protocol_choices': StressTest.PROTOCOL_CHOICES,
        'stop_reason_choices': StressTest.STOP_REASON_CHOICES,
        'result_choices': StressTest.RESULT_CHOICES,
    }

    return render(request, 'cardiology/stress_test_form.html', context)


@login_required
@require_company_access
def stress_test_detail(request, test_id):
    """Detalle de una prueba de esfuerzo."""
    current_company = request.current_company

    test = get_object_or_404(
        StressTest,
        id=test_id,
        company=current_company
    )

    context = {
        'current_company': current_company,
        'test': test,
    }

    return render(request, 'cardiology/stress_test_detail.html', context)


# ============================================================
# HOLTER
# ============================================================

@login_required
@require_company_access
def holter_list(request):
    """Lista de monitoreos Holter."""
    current_company = request.current_company

    holters = HolterMonitoring.objects.filter(
        company=current_company
    ).select_related('patient', 'interpreted_by').order_by('-start_datetime')

    paginator = Paginator(holters, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
    }

    return render(request, 'cardiology/holter_list.html', context)


@login_required
@require_company_access
def holter_create(request):
    """Crear nuevo monitoreo Holter."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            holter_number = f"HOLTER-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            holter = HolterMonitoring.objects.create(
                company=current_company,
                holter_number=holter_number,
                patient_id=request.POST['patient_id'],
                start_datetime=request.POST['start_datetime'],
                end_datetime=request.POST['end_datetime'],
                duration=request.POST.get('duration', '24h'),
                placed_by_id=request.POST['placed_by_id'],
                interpreted_by_id=request.POST['interpreted_by_id'],

                # Análisis del ritmo
                predominant_rhythm=request.POST['predominant_rhythm'],
                total_beats=int(request.POST['total_beats']),
                min_heart_rate=int(request.POST['min_heart_rate']),
                max_heart_rate=int(request.POST['max_heart_rate']),
                average_heart_rate=int(request.POST['average_heart_rate']),

                # Arritmias
                total_supraventricular_ectopics=int(request.POST.get('total_supraventricular_ectopics', 0)),
                total_ventricular_ectopics=int(request.POST.get('total_ventricular_ectopics', 0)),

                # Hallazgos
                findings=request.POST['findings'],
                interpretation=request.POST['interpretation'],
                conclusion=request.POST['conclusion'],
                recommendations=request.POST.get('recommendations', ''),

                created_by=request.user
            )

            messages.success(request, f'Holter {holter.holter_number} creado exitosamente.')
            return redirect('cardiology:holter_detail', holter_id=holter.id)

        except Exception as e:
            messages.error(request, f'Error al crear el Holter: {str(e)}')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    technicians = Employee.objects.filter(
        company=current_company,
        is_active=True
    )

    context = {
        'current_company': current_company,
        'patients': patients,
        'technicians': technicians,
        'duration_choices': HolterMonitoring.DURATION_CHOICES,
    }

    return render(request, 'cardiology/holter_form.html', context)


@login_required
@require_company_access
def holter_detail(request, holter_id):
    """Detalle de un monitoreo Holter."""
    current_company = request.current_company

    holter = get_object_or_404(
        HolterMonitoring,
        id=holter_id,
        company=current_company
    )

    context = {
        'current_company': current_company,
        'holter': holter,
    }

    return render(request, 'cardiology/holter_detail.html', context)


# ============================================================
# EVALUACIÓN DE RIESGO CARDIOVASCULAR
# ============================================================

@login_required
@require_company_access
def risk_assessment_list(request):
    """Lista de evaluaciones de riesgo cardiovascular."""
    current_company = request.current_company

    assessments = CardiovascularRiskAssessment.objects.filter(
        company=current_company
    ).select_related('patient', 'evaluated_by').order_by('-assessment_date')

    paginator = Paginator(assessments, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'current_company': current_company,
        'page_obj': page_obj,
    }

    return render(request, 'cardiology/risk_assessment_list.html', context)


@login_required
@require_company_access
def risk_assessment_create(request):
    """Crear nueva evaluación de riesgo cardiovascular."""
    current_company = request.current_company

    if request.method == 'POST':
        try:
            assessment_number = f"RISK-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            assessment = CardiovascularRiskAssessment.objects.create(
                company=current_company,
                assessment_number=assessment_number,
                patient_id=request.POST['patient_id'],
                cardiology_consultation_id=request.POST['consultation_id'],
                assessment_date=request.POST.get('assessment_date', date.today()),
                evaluated_by_id=request.POST['evaluated_by_id'],

                # Datos demográficos
                age=int(request.POST['age']),
                gender=request.POST['gender'],

                # Factores de riesgo
                systolic_blood_pressure=int(request.POST['systolic_blood_pressure']),
                is_on_antihypertensive_treatment=bool(request.POST.get('is_on_antihypertensive_treatment')),
                total_cholesterol=Decimal(request.POST['total_cholesterol']),
                hdl_cholesterol=Decimal(request.POST['hdl_cholesterol']),
                ldl_cholesterol=Decimal(request.POST['ldl_cholesterol']),
                triglycerides=Decimal(request.POST['triglycerides']),
                is_diabetic=bool(request.POST.get('is_diabetic')),
                is_smoker=bool(request.POST.get('is_smoker')),

                # Cálculo de riesgo
                score_type=request.POST.get('score_type', 'framingham'),
                risk_score=Decimal(request.POST['risk_score']),
                risk_percentage=Decimal(request.POST['risk_percentage']),
                risk_level=request.POST['risk_level'],

                # Objetivos
                target_ldl=Decimal(request.POST['target_ldl']),
                target_blood_pressure=request.POST['target_blood_pressure'],

                # Recomendaciones
                lifestyle_recommendations=request.POST['lifestyle_recommendations'],
                pharmacological_recommendations=request.POST.get('pharmacological_recommendations', ''),
                follow_up_plan=request.POST['follow_up_plan'],

                created_by=request.user
            )

            messages.success(request, f'Evaluación de riesgo {assessment.assessment_number} creada exitosamente.')
            return redirect('cardiology:risk_assessment_detail', assessment_id=assessment.id)

        except Exception as e:
            messages.error(request, f'Error al crear la evaluación: {str(e)}')

    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=current_company.id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    consultations = CardiologyConsultation.objects.filter(
        company=current_company
    ).select_related('patient')

    physicians = Employee.objects.filter(
        company=current_company,
        is_active=True
    )

    context = {
        'current_company': current_company,
        'patients': patients,
        'consultations': consultations,
        'physicians': physicians,
        'score_type_choices': CardiovascularRiskAssessment.SCORE_TYPE_CHOICES,
        'risk_level_choices': CardiovascularRiskAssessment.RISK_LEVEL_CHOICES,
    }

    return render(request, 'cardiology/risk_assessment_form.html', context)


@login_required
@require_company_access
def risk_assessment_detail(request, assessment_id):
    """Detalle de una evaluación de riesgo cardiovascular."""
    current_company = request.current_company

    assessment = get_object_or_404(
        CardiovascularRiskAssessment,
        id=assessment_id,
        company=current_company
    )

    context = {
        'current_company': current_company,
        'assessment': assessment,
    }

    return render(request, 'cardiology/risk_assessment_detail.html', context)


# ============================================================
# PACIENTES CARDIOLÓGICOS
# ============================================================

@login_required
@require_company_access
def patient_cardiology_profile(request, patient_id):
    """Perfil cardiológico completo de un paciente."""
    current_company = request.current_company

    patient = get_object_or_404(
        ThirdParty,
        id=patient_id,
        company=current_company
    )

    # Historial completo del paciente
    consultations = patient.cardiology_consultations.all().order_by('-consultation_date')
    ecgs = patient.electrocardiograms.all().order_by('-ecg_date')
    echos = patient.echocardiograms.all().order_by('-echo_date')
    stress_tests = patient.stress_tests.all().order_by('-test_date')
    holters = patient.holter_monitorings.all().order_by('-start_datetime')
    risk_assessments = patient.cardiovascular_risk_assessments.all().order_by('-assessment_date')

    context = {
        'current_company': current_company,
        'patient': patient,
        'consultations': consultations,
        'ecgs': ecgs,
        'echos': echos,
        'stress_tests': stress_tests,
        'holters': holters,
        'risk_assessments': risk_assessments,
    }

    return render(request, 'cardiology/patient_profile.html', context)
