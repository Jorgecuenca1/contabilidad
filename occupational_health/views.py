"""
Vistas del módulo Salud Ocupacional
Gestión completa de exámenes ocupacionales, aptitud laboral y reportes empresariales
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
    OccupationalExam, LaboratoryTest, WorkAptitude,
    OccupationalRisk, HealthRecommendation, CompanyReport
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def occupational_health_dashboard(request):
    """Dashboard principal de salud ocupacional"""
    company = get_current_company(request)

    # Estadísticas
    total_exams_today = OccupationalExam.objects.filter(
        company=company,
        exam_date__date=timezone.now().date()
    ).count()

    # Exámenes por tipo
    exams_by_type = OccupationalExam.objects.filter(
        company=company
    ).values('exam_type').annotate(count=Count('id'))

    # Exámenes por estado
    exams_by_status = OccupationalExam.objects.filter(
        company=company
    ).values('status').annotate(count=Count('id'))

    # Aptitudes laborales activas
    total_aptitudes = WorkAptitude.objects.filter(company=company).count()

    # Reportes generados este mes
    reports_this_month = CompanyReport.objects.filter(
        company=company,
        created_at__year=timezone.now().year,
        created_at__month=timezone.now().month
    ).count()

    # Pacientes únicos evaluados
    total_workers = Patient.objects.filter(
        company=company,
        occupational_exams__isnull=False
    ).distinct().count()

    # Exámenes recientes
    recent_exams = OccupationalExam.objects.filter(
        company=company
    ).select_related('patient__third_party', 'examiner').order_by('-exam_date')[:10]

    # Aptitudes recientes
    recent_aptitudes = WorkAptitude.objects.filter(
        company=company
    ).select_related('exam__patient__third_party', 'issued_by').order_by('-issue_date')[:10]

    # Reportes recientes
    recent_reports = CompanyReport.objects.filter(
        company=company
    ).select_related('created_by').order_by('-created_at')[:10]

    context = {
        'total_exams_today': total_exams_today,
        'exams_by_type': exams_by_type,
        'exams_by_status': exams_by_status,
        'total_aptitudes': total_aptitudes,
        'reports_this_month': reports_this_month,
        'total_workers': total_workers,
        'recent_exams': recent_exams,
        'recent_aptitudes': recent_aptitudes,
        'recent_reports': recent_reports,
    }

    return render(request, 'occupational_health/dashboard.html', context)


# ==================== EXÁMENES OCUPACIONALES ====================

@login_required
@company_required
def exam_list(request):
    """Listado de exámenes ocupacionales"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    exam_type = request.GET.get('exam_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    company_name_filter = request.GET.get('company_name', '')

    exams = OccupationalExam.objects.filter(company=company).select_related(
        'patient__third_party', 'examiner'
    )

    if search:
        exams = exams.filter(
            Q(exam_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search) |
            Q(company_name__icontains=search)
        )

    if exam_type:
        exams = exams.filter(exam_type=exam_type)

    if status:
        exams = exams.filter(status=status)

    if date_from:
        exams = exams.filter(exam_date__gte=date_from)

    if date_to:
        exams = exams.filter(exam_date__lte=date_to)

    if company_name_filter:
        exams = exams.filter(company_name__icontains=company_name_filter)

    exams = exams.order_by('-exam_date')

    paginator = Paginator(exams, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'exam_type_filter': exam_type,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
        'company_name_filter': company_name_filter,
    }

    return render(request, 'occupational_health/exam_list.html', context)


@login_required
@company_required
def exam_create(request):
    """Crear nuevo examen ocupacional"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de examen
            last_exam = OccupationalExam.objects.filter(company=company).aggregate(
                last_number=Max('exam_number')
            )
            if last_exam['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_exam['last_number'])))
                    exam_number = f"EXOCU-{last_num + 1:07d}"
                except ValueError:
                    exam_number = "EXOCU-0000001"
            else:
                exam_number = "EXOCU-0000001"

            exam = OccupationalExam.objects.create(
                company=company,
                exam_number=exam_number,
                patient=patient,
                company_name=request.POST.get('company_name'),
                job_position=request.POST.get('job_position'),
                work_area=request.POST.get('work_area', ''),
                years_in_position=request.POST.get('years_in_position') or None,
                work_schedule=request.POST.get('work_schedule', ''),
                exam_type=request.POST.get('exam_type'),
                exam_date=request.POST.get('exam_date'),
                examiner=request.user,
                previous_jobs=request.POST.get('previous_jobs', ''),
                occupational_exposures=request.POST.get('occupational_exposures', ''),
                use_of_ppe=request.POST.get('use_of_ppe', ''),
                personal_medical_history=request.POST.get('personal_medical_history', ''),
                family_medical_history=request.POST.get('family_medical_history', ''),
                current_medications=request.POST.get('current_medications', ''),
                allergies=request.POST.get('allergies', ''),
                smoking=request.POST.get('smoking', ''),
                alcohol=request.POST.get('alcohol', ''),
                physical_activity=request.POST.get('physical_activity', ''),
                blood_pressure=request.POST.get('blood_pressure', ''),
                heart_rate=request.POST.get('heart_rate') or None,
                respiratory_rate=request.POST.get('respiratory_rate') or None,
                temperature=request.POST.get('temperature') or None,
                weight=request.POST.get('weight') or None,
                height=request.POST.get('height') or None,
                head_neck_exam=request.POST.get('head_neck_exam', ''),
                cardiovascular_exam=request.POST.get('cardiovascular_exam', ''),
                respiratory_exam=request.POST.get('respiratory_exam', ''),
                abdominal_exam=request.POST.get('abdominal_exam', ''),
                musculoskeletal_exam=request.POST.get('musculoskeletal_exam', ''),
                neurological_exam=request.POST.get('neurological_exam', ''),
                dermatological_exam=request.POST.get('dermatological_exam', ''),
                laboratory_tests_ordered=request.POST.get('laboratory_tests_ordered', ''),
                imaging_studies_ordered=request.POST.get('imaging_studies_ordered', ''),
                other_tests_ordered=request.POST.get('other_tests_ordered', ''),
                diagnosis=request.POST.get('diagnosis', ''),
                findings=request.POST.get('findings', ''),
                status=request.POST.get('status', 'programado'),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Examen ocupacional {exam_number} creado exitosamente')
            return redirect('occupational_health:exam_detail', exam_id=exam.id)

        except Exception as e:
            messages.error(request, f'Error al crear el examen: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'occupational_health/exam_form.html', context)


@login_required
@company_required
def exam_detail(request, exam_id):
    """Detalle del examen ocupacional"""
    company = get_current_company(request)
    exam = get_object_or_404(
        OccupationalExam.objects.select_related(
            'patient__third_party', 'examiner'
        ),
        id=exam_id,
        company=company
    )

    # Obtener exámenes de laboratorio
    laboratory_tests = exam.laboratory_tests.all().order_by('-test_date')

    # Obtener riesgos ocupacionales
    occupational_risks = exam.occupational_risks.all().order_by('-risk_level', 'risk_type')

    # Obtener recomendaciones
    health_recommendations = exam.health_recommendations.all().order_by('-priority', 'category')

    # Obtener aptitud laboral si existe
    try:
        work_aptitude = exam.work_aptitude
    except WorkAptitude.DoesNotExist:
        work_aptitude = None

    context = {
        'exam': exam,
        'laboratory_tests': laboratory_tests,
        'occupational_risks': occupational_risks,
        'health_recommendations': health_recommendations,
        'work_aptitude': work_aptitude,
    }

    return render(request, 'occupational_health/exam_detail.html', context)


@login_required
@company_required
def exam_update_status(request, exam_id):
    """Actualizar estado del examen"""
    company = get_current_company(request)
    exam = get_object_or_404(OccupationalExam, id=exam_id, company=company)

    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            if new_status in dict(OccupationalExam.STATUS_CHOICES):
                exam.status = new_status
                exam.save()
                messages.success(request, f'Estado del examen actualizado a {exam.get_status_display()}')
            else:
                messages.error(request, 'Estado no válido')
        except Exception as e:
            messages.error(request, f'Error al actualizar estado: {str(e)}')

    return redirect('occupational_health:exam_detail', exam_id=exam.id)


# ==================== EXÁMENES DE LABORATORIO ====================

@login_required
@company_required
def lab_test_create(request, exam_id):
    """Crear examen de laboratorio para un examen ocupacional"""
    company = get_current_company(request)
    exam = get_object_or_404(OccupationalExam, id=exam_id, company=company)

    if request.method == 'POST':
        try:
            LaboratoryTest.objects.create(
                company=company,
                exam=exam,
                test_type=request.POST.get('test_type'),
                test_name=request.POST.get('test_name'),
                test_date=request.POST.get('test_date'),
                result_value=request.POST.get('result_value', ''),
                result_status=request.POST.get('result_status', 'pendiente'),
                reference_values=request.POST.get('reference_values', ''),
                interpretation=request.POST.get('interpretation', ''),
                laboratory_name=request.POST.get('laboratory_name', ''),
                performed_by=request.POST.get('performed_by', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, 'Examen de laboratorio agregado exitosamente')
            return redirect('occupational_health:exam_detail', exam_id=exam.id)

        except Exception as e:
            messages.error(request, f'Error al agregar el examen de laboratorio: {str(e)}')

    context = {
        'exam': exam,
    }

    return render(request, 'occupational_health/lab_test_form.html', context)


@login_required
@company_required
def lab_test_detail(request, test_id):
    """Detalle del examen de laboratorio"""
    company = get_current_company(request)
    lab_test = get_object_or_404(
        LaboratoryTest.objects.select_related('exam__patient__third_party'),
        id=test_id,
        company=company
    )

    context = {
        'lab_test': lab_test,
    }

    return render(request, 'occupational_health/lab_test_detail.html', context)


# ==================== APTITUD LABORAL ====================

@login_required
@company_required
def aptitude_create(request, exam_id):
    """Crear concepto de aptitud laboral"""
    company = get_current_company(request)
    exam = get_object_or_404(OccupationalExam, id=exam_id, company=company)

    # Verificar si ya existe una aptitud para este examen
    try:
        existing = exam.work_aptitude
        messages.warning(request, 'Este examen ya tiene un concepto de aptitud laboral.')
        return redirect('occupational_health:exam_detail', exam_id=exam.id)
    except WorkAptitude.DoesNotExist:
        pass

    if request.method == 'POST':
        try:
            # Generar número de aptitud
            last_aptitude = WorkAptitude.objects.filter(company=company).aggregate(
                last_number=Max('aptitude_number')
            )
            if last_aptitude['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_aptitude['last_number'])))
                    aptitude_number = f"APT-{last_num + 1:07d}"
                except ValueError:
                    aptitude_number = "APT-0000001"
            else:
                aptitude_number = "APT-0000001"

            aptitude = WorkAptitude.objects.create(
                company=company,
                aptitude_number=aptitude_number,
                exam=exam,
                aptitude=request.POST.get('aptitude'),
                issue_date=request.POST.get('issue_date'),
                valid_until=request.POST.get('valid_until') or None,
                restrictions=request.POST.get('restrictions', ''),
                recommendations=request.POST.get('recommendations', ''),
                requires_follow_up=request.POST.get('requires_follow_up') == 'on',
                follow_up_date=request.POST.get('follow_up_date') or None,
                follow_up_notes=request.POST.get('follow_up_notes', ''),
                medical_justification=request.POST.get('medical_justification'),
                observations=request.POST.get('observations', ''),
                issued_by=request.user,
                created_by=request.user
            )

            # Actualizar estado del examen a completado
            exam.status = 'completado'
            exam.save()

            messages.success(request, f'Concepto de aptitud laboral {aptitude_number} creado exitosamente')
            return redirect('occupational_health:aptitude_detail', aptitude_id=aptitude.id)

        except Exception as e:
            messages.error(request, f'Error al crear el concepto de aptitud: {str(e)}')

    context = {
        'exam': exam,
    }

    return render(request, 'occupational_health/aptitude_form.html', context)


@login_required
@company_required
def aptitude_detail(request, aptitude_id):
    """Detalle del concepto de aptitud laboral"""
    company = get_current_company(request)
    aptitude = get_object_or_404(
        WorkAptitude.objects.select_related(
            'exam__patient__third_party', 'issued_by'
        ),
        id=aptitude_id,
        company=company
    )

    context = {
        'aptitude': aptitude,
    }

    return render(request, 'occupational_health/aptitude_detail.html', context)


@login_required
@company_required
def aptitude_list(request):
    """Listado de aptitudes laborales"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    aptitude_type = request.GET.get('aptitude', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    aptitudes = WorkAptitude.objects.filter(company=company).select_related(
        'exam__patient__third_party', 'issued_by'
    )

    if search:
        aptitudes = aptitudes.filter(
            Q(aptitude_number__icontains=search) |
            Q(exam__patient__third_party__name__icontains=search) |
            Q(exam__patient__third_party__identification_number__icontains=search) |
            Q(exam__company_name__icontains=search)
        )

    if aptitude_type:
        aptitudes = aptitudes.filter(aptitude=aptitude_type)

    if date_from:
        aptitudes = aptitudes.filter(issue_date__gte=date_from)

    if date_to:
        aptitudes = aptitudes.filter(issue_date__lte=date_to)

    aptitudes = aptitudes.order_by('-issue_date')

    paginator = Paginator(aptitudes, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'aptitude_filter': aptitude_type,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'occupational_health/aptitude_list.html', context)


# ==================== RIESGOS OCUPACIONALES ====================

@login_required
@company_required
def risk_create(request, exam_id):
    """Crear riesgo ocupacional para un examen"""
    company = get_current_company(request)
    exam = get_object_or_404(OccupationalExam, id=exam_id, company=company)

    if request.method == 'POST':
        try:
            OccupationalRisk.objects.create(
                company=company,
                exam=exam,
                risk_type=request.POST.get('risk_type'),
                risk_description=request.POST.get('risk_description'),
                risk_level=request.POST.get('risk_level'),
                exposure_time=request.POST.get('exposure_time', ''),
                control_measures=request.POST.get('control_measures', ''),
                recommended_controls=request.POST.get('recommended_controls', ''),
                created_by=request.user
            )

            messages.success(request, 'Riesgo ocupacional agregado exitosamente')
            return redirect('occupational_health:exam_detail', exam_id=exam.id)

        except Exception as e:
            messages.error(request, f'Error al agregar el riesgo: {str(e)}')

    context = {
        'exam': exam,
    }

    return render(request, 'occupational_health/risk_form.html', context)


@login_required
@company_required
def risk_list(request):
    """Listado de riesgos ocupacionales"""
    company = get_current_company(request)

    risk_type = request.GET.get('risk_type', '')
    risk_level = request.GET.get('risk_level', '')
    search = request.GET.get('search', '')

    risks = OccupationalRisk.objects.filter(company=company).select_related(
        'exam__patient__third_party'
    )

    if risk_type:
        risks = risks.filter(risk_type=risk_type)

    if risk_level:
        risks = risks.filter(risk_level=risk_level)

    if search:
        risks = risks.filter(
            Q(risk_description__icontains=search) |
            Q(exam__patient__third_party__name__icontains=search) |
            Q(exam__company_name__icontains=search)
        )

    risks = risks.order_by('-risk_level', '-created_at')

    paginator = Paginator(risks, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'risk_type_filter': risk_type,
        'risk_level_filter': risk_level,
        'search': search,
    }

    return render(request, 'occupational_health/risk_list.html', context)


# ==================== RECOMENDACIONES DE SALUD ====================

@login_required
@company_required
def recommendation_create(request, exam_id):
    """Crear recomendación de salud para un examen"""
    company = get_current_company(request)
    exam = get_object_or_404(OccupationalExam, id=exam_id, company=company)

    if request.method == 'POST':
        try:
            HealthRecommendation.objects.create(
                company=company,
                exam=exam,
                category=request.POST.get('category'),
                recommendation=request.POST.get('recommendation'),
                priority=request.POST.get('priority'),
                implementation_deadline=request.POST.get('implementation_deadline') or None,
                responsible_person=request.POST.get('responsible_person', ''),
                implemented=request.POST.get('implemented') == 'on',
                implementation_date=request.POST.get('implementation_date') or None,
                implementation_notes=request.POST.get('implementation_notes', ''),
                created_by=request.user
            )

            messages.success(request, 'Recomendación de salud agregada exitosamente')
            return redirect('occupational_health:exam_detail', exam_id=exam.id)

        except Exception as e:
            messages.error(request, f'Error al agregar la recomendación: {str(e)}')

    context = {
        'exam': exam,
    }

    return render(request, 'occupational_health/recommendation_form.html', context)


@login_required
@company_required
def recommendation_list(request):
    """Listado de recomendaciones de salud"""
    company = get_current_company(request)

    category = request.GET.get('category', '')
    priority = request.GET.get('priority', '')
    implemented = request.GET.get('implemented', '')
    search = request.GET.get('search', '')

    recommendations = HealthRecommendation.objects.filter(company=company).select_related(
        'exam__patient__third_party'
    )

    if category:
        recommendations = recommendations.filter(category=category)

    if priority:
        recommendations = recommendations.filter(priority=priority)

    if implemented:
        recommendations = recommendations.filter(implemented=(implemented == 'true'))

    if search:
        recommendations = recommendations.filter(
            Q(recommendation__icontains=search) |
            Q(exam__patient__third_party__name__icontains=search) |
            Q(exam__company_name__icontains=search)
        )

    recommendations = recommendations.order_by('-priority', '-created_at')

    paginator = Paginator(recommendations, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'category_filter': category,
        'priority_filter': priority,
        'implemented_filter': implemented,
        'search': search,
    }

    return render(request, 'occupational_health/recommendation_list.html', context)


# ==================== REPORTES EMPRESARIALES ====================

@login_required
@company_required
def report_list(request):
    """Listado de reportes empresariales"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    report_type = request.GET.get('report_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    reports = CompanyReport.objects.filter(company=company).select_related('created_by')

    if search:
        reports = reports.filter(
            Q(report_number__icontains=search) |
            Q(report_title__icontains=search) |
            Q(client_company__icontains=search)
        )

    if report_type:
        reports = reports.filter(report_type=report_type)

    if status:
        reports = reports.filter(status=status)

    if date_from:
        reports = reports.filter(period_start__gte=date_from)

    if date_to:
        reports = reports.filter(period_end__lte=date_to)

    reports = reports.order_by('-created_at')

    paginator = Paginator(reports, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'report_type_filter': report_type,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'occupational_health/report_list.html', context)


@login_required
@company_required
def report_create(request):
    """Crear nuevo reporte empresarial"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Generar número de reporte
            last_report = CompanyReport.objects.filter(company=company).aggregate(
                last_number=Max('report_number')
            )
            if last_report['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_report['last_number'])))
                    report_number = f"REP-{last_num + 1:07d}"
                except ValueError:
                    report_number = "REP-0000001"
            else:
                report_number = "REP-0000001"

            # Generar estadísticas básicas según el tipo de reporte
            statistics = {}
            report_type = request.POST.get('report_type')
            period_start = request.POST.get('period_start')
            period_end = request.POST.get('period_end')

            if report_type == 'consolidado_examenes':
                exams = OccupationalExam.objects.filter(
                    company=company,
                    exam_date__range=[period_start, period_end]
                )
                statistics = {
                    'total_exams': exams.count(),
                    'by_type': dict(exams.values('exam_type').annotate(count=Count('id')).values_list('exam_type', 'count')),
                    'by_status': dict(exams.values('status').annotate(count=Count('id')).values_list('status', 'count')),
                }
            elif report_type == 'aptitudes':
                aptitudes = WorkAptitude.objects.filter(
                    company=company,
                    issue_date__range=[period_start, period_end]
                )
                statistics = {
                    'total_aptitudes': aptitudes.count(),
                    'by_type': dict(aptitudes.values('aptitude').annotate(count=Count('id')).values_list('aptitude', 'count')),
                }
            elif report_type == 'riesgos_identificados':
                risks = OccupationalRisk.objects.filter(
                    company=company,
                    created_at__range=[period_start, period_end]
                )
                statistics = {
                    'total_risks': risks.count(),
                    'by_type': dict(risks.values('risk_type').annotate(count=Count('id')).values_list('risk_type', 'count')),
                    'by_level': dict(risks.values('risk_level').annotate(count=Count('id')).values_list('risk_level', 'count')),
                }

            report = CompanyReport.objects.create(
                company=company,
                report_number=report_number,
                report_type=report_type,
                report_title=request.POST.get('report_title'),
                period_start=period_start,
                period_end=period_end,
                client_company=request.POST.get('client_company', ''),
                work_area_filter=request.POST.get('work_area_filter', ''),
                job_position_filter=request.POST.get('job_position_filter', ''),
                summary=request.POST.get('summary', ''),
                findings=request.POST.get('findings', ''),
                statistics=statistics,
                recommendations=request.POST.get('recommendations', ''),
                conclusions=request.POST.get('conclusions', ''),
                attachments_description=request.POST.get('attachments_description', ''),
                status=request.POST.get('status', 'borrador'),
                generated_date=request.POST.get('generated_date') or None,
                sent_date=request.POST.get('sent_date') or None,
                recipient=request.POST.get('recipient', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Reporte empresarial {report_number} creado exitosamente')
            return redirect('occupational_health:report_detail', report_id=report.id)

        except Exception as e:
            messages.error(request, f'Error al crear el reporte: {str(e)}')

    context = {}

    return render(request, 'occupational_health/report_form.html', context)


@login_required
@company_required
def report_detail(request, report_id):
    """Detalle del reporte empresarial"""
    company = get_current_company(request)
    report = get_object_or_404(
        CompanyReport.objects.select_related('created_by'),
        id=report_id,
        company=company
    )

    context = {
        'report': report,
    }

    return render(request, 'occupational_health/report_detail.html', context)


@login_required
@company_required
def report_update_status(request, report_id):
    """Actualizar estado del reporte"""
    company = get_current_company(request)
    report = get_object_or_404(CompanyReport, id=report_id, company=company)

    if request.method == 'POST':
        try:
            new_status = request.POST.get('status')
            if new_status in dict(CompanyReport.STATUS_CHOICES):
                report.status = new_status

                # Actualizar fecha según estado
                if new_status == 'generado' and not report.generated_date:
                    report.generated_date = timezone.now().date()
                elif new_status == 'enviado' and not report.sent_date:
                    report.sent_date = timezone.now().date()

                report.save()
                messages.success(request, f'Estado del reporte actualizado a {report.get_status_display()}')
            else:
                messages.error(request, 'Estado no válido')
        except Exception as e:
            messages.error(request, f'Error al actualizar estado: {str(e)}')

    return redirect('occupational_health:report_detail', report_id=report.id)
