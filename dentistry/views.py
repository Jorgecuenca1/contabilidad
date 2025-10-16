"""
Vistas del módulo Odontología
Gestión completa de consultas, odontograma y tratamientos dentales
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta

from core.decorators import company_required
from core.utils import get_current_company
from patients.models import Patient
from .models import (
    DentalProcedureType, DentalCondition, DentalConsultation, Odontogram,
    OdontogramTooth, TreatmentPlan, TreatmentPlanItem, DentalProcedureRecord
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def dentistry_dashboard(request):
    """Dashboard principal de odontología"""
    company = get_current_company(request)

    # Estadísticas
    total_consultations_today = DentalConsultation.objects.filter(
        company=company,
        consultation_date__date=timezone.now().date()
    ).count()

    active_treatment_plans = TreatmentPlan.objects.filter(
        company=company,
        status='in_progress'
    ).count()

    pending_procedures = TreatmentPlanItem.objects.filter(
        company=company,
        status='pending'
    ).count()

    procedures_today = DentalProcedureRecord.objects.filter(
        company=company,
        procedure_date=timezone.now().date()
    ).count()

    # Consultas recientes
    recent_consultations = DentalConsultation.objects.filter(
        company=company
    ).select_related('patient__third_party', 'dentist').order_by('-consultation_date')[:10]

    # Planes de tratamiento activos
    active_plans = TreatmentPlan.objects.filter(
        company=company,
        status__in=['approved', 'in_progress']
    ).select_related('patient__third_party', 'dentist').order_by('-plan_date')[:10]

    # Procedimientos por categoría (últimos 30 días)
    procedures_by_category = DentalProcedureRecord.objects.filter(
        company=company,
        procedure_date__gte=timezone.now().date() - timedelta(days=30)
    ).values('procedure__category').annotate(total=Count('id')).order_by('-total')

    context = {
        'total_consultations_today': total_consultations_today,
        'active_treatment_plans': active_treatment_plans,
        'pending_procedures': pending_procedures,
        'procedures_today': procedures_today,
        'recent_consultations': recent_consultations,
        'active_plans': active_plans,
        'procedures_by_category': procedures_by_category,
    }

    return render(request, 'dentistry/dashboard.html', context)


# ==================== CONSULTAS ODONTOLÓGICAS ====================

@login_required
@company_required
def consultation_list(request):
    """Listado de consultas odontológicas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    consultations = DentalConsultation.objects.filter(company=company).select_related(
        'patient__third_party', 'dentist'
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

    return render(request, 'dentistry/consultation_list.html', context)


@login_required
@company_required
def consultation_create(request):
    """Crear nueva consulta odontológica"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            # Generar número de consulta
            last_consultation = DentalConsultation.objects.filter(company=company).aggregate(
                last_number=Max('consultation_number')
            )
            if last_consultation['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_consultation['last_number'])))
                consultation_number = f"ODON-{last_num + 1:07d}"
            else:
                consultation_number = "ODON-0000001"

            consultation = DentalConsultation.objects.create(
                company=company,
                consultation_number=consultation_number,
                patient=patient,
                dentist=request.user,
                chief_complaint=request.POST.get('chief_complaint'),
                current_illness=request.POST.get('current_illness', ''),
                dental_history=request.POST.get('dental_history', ''),
                medical_history=request.POST.get('medical_history', ''),
                extraoral_examination=request.POST.get('extraoral_examination', ''),
                intraoral_examination=request.POST.get('intraoral_examination', ''),
                oral_hygiene=request.POST.get('oral_hygiene', ''),
                diagnosis=request.POST.get('diagnosis'),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Consulta {consultation_number} creada exitosamente')
            return redirect('dentistry:consultation_detail', consultation_id=consultation.id)

        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'dentistry/consultation_form.html', context)


@login_required
@company_required
def consultation_detail(request, consultation_id):
    """Detalle de la consulta odontológica"""
    company = get_current_company(request)
    consultation = get_object_or_404(
        DentalConsultation.objects.select_related(
            'patient__third_party', 'dentist'
        ),
        id=consultation_id,
        company=company
    )

    # Odontogramas relacionados
    odontograms = consultation.odontograms.all().order_by('-odontogram_date')

    # Planes de tratamiento relacionados
    treatment_plans = consultation.treatment_plans.all().select_related('dentist').order_by('-plan_date')

    context = {
        'consultation': consultation,
        'odontograms': odontograms,
        'treatment_plans': treatment_plans,
    }

    return render(request, 'dentistry/consultation_detail.html', context)


# ==================== ODONTOGRAMA ====================

@login_required
@company_required
def odontogram_list(request):
    """Listado de odontogramas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')

    odontograms = Odontogram.objects.filter(company=company).select_related(
        'patient__third_party', 'consultation', 'created_by'
    )

    if search:
        odontograms = odontograms.filter(
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    odontograms = odontograms.order_by('-odontogram_date')

    paginator = Paginator(odontograms, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
    }

    return render(request, 'dentistry/odontogram_list.html', context)


@login_required
@company_required
def odontogram_create(request, patient_id):
    """Crear nuevo odontograma"""
    company = get_current_company(request)
    patient = get_object_or_404(Patient, id=patient_id, company=company)

    if request.method == 'POST':
        try:
            consultation_id = request.POST.get('consultation')
            consultation = None
            if consultation_id:
                consultation = get_object_or_404(DentalConsultation, id=consultation_id, company=company)

            odontogram = Odontogram.objects.create(
                company=company,
                patient=patient,
                consultation=consultation,
                dentition_type=request.POST.get('dentition_type', 'permanent'),
                general_observations=request.POST.get('general_observations', ''),
                created_by=request.user
            )

            messages.success(request, 'Odontograma creado exitosamente')
            return redirect('dentistry:odontogram_detail', odontogram_id=odontogram.id)

        except Exception as e:
            messages.error(request, f'Error al crear el odontograma: {str(e)}')

    # Consultas del paciente
    consultations = DentalConsultation.objects.filter(
        company=company,
        patient=patient
    ).order_by('-consultation_date')

    context = {
        'patient': patient,
        'consultations': consultations,
    }

    return render(request, 'dentistry/odontogram_form.html', context)


@login_required
@company_required
def odontogram_detail(request, odontogram_id):
    """Detalle del odontograma"""
    company = get_current_company(request)
    odontogram = get_object_or_404(
        Odontogram.objects.select_related(
            'patient__third_party', 'consultation', 'created_by'
        ),
        id=odontogram_id,
        company=company
    )

    # Dientes del odontograma
    teeth = odontogram.teeth.all().prefetch_related('conditions').order_by('fdi_number')

    # Condiciones dentales disponibles
    conditions = DentalCondition.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'odontogram': odontogram,
        'teeth': teeth,
        'conditions': conditions,
    }

    return render(request, 'dentistry/odontogram_detail.html', context)


@login_required
@company_required
def odontogram_tooth_update(request, odontogram_id):
    """Actualizar estado de un diente en el odontograma (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    company = get_current_company(request)
    odontogram = get_object_or_404(Odontogram, id=odontogram_id, company=company)

    try:
        fdi_number = request.POST.get('fdi_number')
        quadrant = fdi_number[0] if fdi_number else ''

        # Crear o actualizar diente
        tooth, created = OdontogramTooth.objects.get_or_create(
            company=company,
            odontogram=odontogram,
            fdi_number=fdi_number,
            defaults={
                'quadrant': quadrant,
                'created_by': request.user
            }
        )

        # Actualizar estado
        tooth.state = request.POST.get('state', 'present')
        tooth.surface_mesial = request.POST.get('surface_mesial') == 'on'
        tooth.surface_distal = request.POST.get('surface_distal') == 'on'
        tooth.surface_occlusal = request.POST.get('surface_occlusal') == 'on'
        tooth.surface_vestibular = request.POST.get('surface_vestibular') == 'on'
        tooth.surface_lingual = request.POST.get('surface_lingual') == 'on'
        tooth.observations = request.POST.get('observations', '')
        tooth.save()

        # Actualizar condiciones
        condition_ids = request.POST.getlist('conditions')
        tooth.conditions.set(condition_ids)

        return JsonResponse({'success': True, 'message': 'Diente actualizado'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== PLANES DE TRATAMIENTO ====================

@login_required
@company_required
def treatment_plan_list(request):
    """Listado de planes de tratamiento"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    plans = TreatmentPlan.objects.filter(company=company).select_related(
        'patient__third_party', 'dentist', 'consultation'
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

    return render(request, 'dentistry/treatment_plan_list.html', context)


@login_required
@company_required
def treatment_plan_create(request):
    """Crear nuevo plan de tratamiento"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            consultation_id = request.POST.get('consultation')
            consultation = None
            if consultation_id:
                consultation = get_object_or_404(DentalConsultation, id=consultation_id, company=company)

            odontogram_id = request.POST.get('odontogram')
            odontogram = None
            if odontogram_id:
                odontogram = get_object_or_404(Odontogram, id=odontogram_id, company=company)

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
                patient=patient,
                consultation=consultation,
                odontogram=odontogram,
                dentist=request.user,
                diagnosis=request.POST.get('diagnosis'),
                treatment_objectives=request.POST.get('treatment_objectives', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, f'Plan de tratamiento {plan_number} creado exitosamente')
            return redirect('dentistry:treatment_plan_detail', plan_id=plan.id)

        except Exception as e:
            messages.error(request, f'Error al crear el plan: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    context = {
        'patients': patients,
    }

    return render(request, 'dentistry/treatment_plan_form.html', context)


@login_required
@company_required
def treatment_plan_detail(request, plan_id):
    """Detalle del plan de tratamiento"""
    company = get_current_company(request)
    plan = get_object_or_404(
        TreatmentPlan.objects.select_related(
            'patient__third_party', 'dentist', 'consultation', 'odontogram'
        ),
        id=plan_id,
        company=company
    )

    # Ítems del plan
    items = plan.items.all().select_related('procedure', 'completed_by').order_by('sequence')

    # Procedimientos disponibles
    procedures = DentalProcedureType.objects.filter(company=company, is_active=True).order_by('category', 'name')

    context = {
        'plan': plan,
        'items': items,
        'procedures': procedures,
    }

    return render(request, 'dentistry/treatment_plan_detail.html', context)


@login_required
@company_required
def treatment_plan_item_add(request, plan_id):
    """Agregar ítem al plan de tratamiento"""
    if request.method != 'POST':
        return redirect('dentistry:treatment_plan_detail', plan_id=plan_id)

    company = get_current_company(request)
    plan = get_object_or_404(TreatmentPlan, id=plan_id, company=company)

    try:
        procedure_id = request.POST.get('procedure')
        procedure = get_object_or_404(DentalProcedureType, id=procedure_id, company=company)

        # Obtener el siguiente número de secuencia
        last_item = plan.items.aggregate(max_seq=Max('sequence'))
        next_sequence = (last_item['max_seq'] or 0) + 1

        unit_cost = float(request.POST.get('unit_cost', procedure.base_price))
        quantity = int(request.POST.get('quantity', 1))

        item = TreatmentPlanItem.objects.create(
            company=company,
            treatment_plan=plan,
            procedure=procedure,
            tooth_fdi=request.POST.get('tooth_fdi', ''),
            surfaces=request.POST.get('surfaces', ''),
            description=request.POST.get('description', ''),
            priority=request.POST.get('priority', 'medium'),
            sequence=next_sequence,
            unit_cost=unit_cost,
            quantity=quantity,
            created_by=request.user
        )

        # Recalcular total del plan
        plan.calculate_total_cost()
        plan.save()

        messages.success(request, 'Ítem agregado al plan de tratamiento')

    except Exception as e:
        messages.error(request, f'Error al agregar ítem: {str(e)}')

    return redirect('dentistry:treatment_plan_detail', plan_id=plan.id)


# ==================== PROCEDIMIENTOS REALIZADOS ====================

@login_required
@company_required
def procedure_record_list(request):
    """Listado de procedimientos realizados"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')

    procedures = DentalProcedureRecord.objects.filter(company=company).select_related(
        'patient__third_party', 'dentist', 'procedure'
    )

    if search:
        procedures = procedures.filter(
            Q(record_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search)
        )

    if date_from:
        procedures = procedures.filter(procedure_date__gte=date_from)

    procedures = procedures.order_by('-procedure_date')

    paginator = Paginator(procedures, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'date_from': date_from,
    }

    return render(request, 'dentistry/procedure_record_list.html', context)


@login_required
@company_required
def procedure_record_create(request):
    """Crear registro de procedimiento realizado"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            patient = get_object_or_404(Patient, id=patient_id, company=company)

            procedure_id = request.POST.get('procedure')
            procedure = get_object_or_404(DentalProcedureType, id=procedure_id, company=company)

            # Generar número de registro
            last_record = DentalProcedureRecord.objects.filter(company=company).aggregate(
                last_number=Max('record_number')
            )
            if last_record['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_record['last_number'])))
                record_number = f"PROC-{last_num + 1:07d}"
            else:
                record_number = "PROC-0000001"

            record = DentalProcedureRecord.objects.create(
                company=company,
                record_number=record_number,
                patient=patient,
                dentist=request.user,
                procedure=procedure,
                tooth_fdi=request.POST.get('tooth_fdi', ''),
                surfaces=request.POST.get('surfaces', ''),
                anesthesia_used=request.POST.get('anesthesia_used') == 'on',
                anesthesia_type=request.POST.get('anesthesia_type', ''),
                materials_used=request.POST.get('materials_used', ''),
                procedure_notes=request.POST.get('procedure_notes', ''),
                complications=request.POST.get('complications', ''),
                post_procedure_instructions=request.POST.get('post_procedure_instructions', ''),
                cost=float(request.POST.get('cost', procedure.base_price)),
                created_by=request.user
            )

            messages.success(request, f'Procedimiento {record_number} registrado exitosamente')
            return redirect('dentistry:procedure_record_detail', record_id=record.id)

        except Exception as e:
            messages.error(request, f'Error al registrar el procedimiento: {str(e)}')

    patients = Patient.objects.filter(company=company, is_active=True).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')
    procedures = DentalProcedureType.objects.filter(company=company, is_active=True).order_by('category', 'name')

    context = {
        'patients': patients,
        'procedures': procedures,
    }

    return render(request, 'dentistry/procedure_record_form.html', context)


@login_required
@company_required
def procedure_record_detail(request, record_id):
    """Detalle del procedimiento realizado"""
    company = get_current_company(request)
    record = get_object_or_404(
        DentalProcedureRecord.objects.select_related(
            'patient__third_party', 'dentist', 'procedure', 'consultation', 'treatment_plan_item'
        ),
        id=record_id,
        company=company
    )

    context = {
        'record': record,
    }

    return render(request, 'dentistry/procedure_record_detail.html', context)


# ==================== APIs ====================

@login_required
@company_required
def api_patient_consultations(request):
    """API: Obtener consultas de un paciente"""
    company = get_current_company(request)
    patient_id = request.GET.get('patient_id')

    if patient_id:
        consultations = DentalConsultation.objects.filter(
            company=company,
            patient_id=patient_id
        ).values('id', 'consultation_number', 'consultation_date', 'diagnosis').order_by('-consultation_date')
    else:
        consultations = []

    return JsonResponse(list(consultations), safe=False)


@login_required
@company_required
def api_patient_odontograms(request):
    """API: Obtener odontogramas de un paciente"""
    company = get_current_company(request)
    patient_id = request.GET.get('patient_id')

    if patient_id:
        odontograms = Odontogram.objects.filter(
            company=company,
            patient_id=patient_id
        ).values('id', 'odontogram_date', 'dentition_type').order_by('-odontogram_date')
    else:
        odontograms = []

    return JsonResponse(list(odontograms), safe=False)
