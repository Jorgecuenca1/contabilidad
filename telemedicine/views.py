"""
Vistas del módulo Telemedicina
Consultas virtuales, atención domiciliaria y firma digital
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import hashlib

from core.decorators import company_required, module_permission_required
from core.utils import get_current_company
from core.models import User
from patients.models import Patient
from .models import (
    TelemedicineAppointment, VirtualConsultation, HomeCareVisit,
    MedicalDocument, DigitalSignature, TelemedicineStatistics
)


@login_required
@company_required
@module_permission_required('telemedicine')
def telemedicine_dashboard(request):
    """Dashboard principal del módulo de telemedicina."""
    company_id = request.session.get('active_company')
    today = timezone.now().date()

    # Estadísticas básicas
    appointments_today = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        scheduled_date__date=today
    ).count()

    appointments_pending = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        status='scheduled'
    ).count()

    appointments_confirmed = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        status='confirmed',
        scheduled_date__gte=timezone.now()
    ).count()

    virtual_consultations_count = VirtualConsultation.objects.filter(
        company_id=company_id,
        consultation_date__date=today
    ).count()

    home_care_visits_count = HomeCareVisit.objects.filter(
        company_id=company_id,
        scheduled_date__date=today
    ).count()

    documents_pending_signature = MedicalDocument.objects.filter(
        company_id=company_id,
        is_digitally_signed=False
    ).count()

    # Últimas actividades
    recent_appointments = TelemedicineAppointment.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'doctor').order_by('-created_at')[:5]

    recent_consultations = VirtualConsultation.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'doctor').order_by('-consultation_date')[:5]

    context = {
        'appointments_today': appointments_today,
        'appointments_pending': appointments_pending,
        'appointments_confirmed': appointments_confirmed,
        'virtual_consultations_count': virtual_consultations_count,
        'home_care_visits_count': home_care_visits_count,
        'documents_pending_signature': documents_pending_signature,
        'recent_appointments': recent_appointments,
        'recent_consultations': recent_consultations,
    }

    return render(request, 'telemedicine/dashboard.html', context)


# =============================================================================
# CITAS DE TELEMEDICINA
# =============================================================================

@login_required
@company_required
@module_permission_required('telemedicine')
def appointments_list(request):
    """Lista de citas de telemedicina."""
    company_id = request.session.get('active_company')

    appointments = TelemedicineAppointment.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'doctor')

    # Filtros
    status = request.GET.get('status')
    appointment_type = request.GET.get('appointment_type')
    priority = request.GET.get('priority')
    doctor_id = request.GET.get('doctor')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        appointments = appointments.filter(status=status)

    if appointment_type:
        appointments = appointments.filter(appointment_type=appointment_type)

    if priority:
        appointments = appointments.filter(priority=priority)

    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)

    if date_from:
        appointments = appointments.filter(scheduled_date__date__gte=date_from)

    if date_to:
        appointments = appointments.filter(scheduled_date__date__lte=date_to)

    if search:
        appointments = appointments.filter(
            Q(appointment_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(patient__medical_record_number__icontains=search) |
            Q(reason__icontains=search)
        )

    # Paginación
    paginator = Paginator(appointments.order_by('-scheduled_date'), 15)
    page = request.GET.get('page')
    appointments = paginator.get_page(page)

    # Para filtros
    doctors = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'appointments': appointments,
        'status_choices': TelemedicineAppointment.STATUS_CHOICES,
        'type_choices': TelemedicineAppointment.APPOINTMENT_TYPE_CHOICES,
        'priority_choices': [
            ('routine', 'Rutina'),
            ('urgent', 'Urgente'),
            ('emergency', 'Emergencia'),
        ],
        'doctors': doctors,
        'filters': {
            'status': status,
            'appointment_type': appointment_type,
            'priority': priority,
            'doctor': doctor_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'telemedicine/appointments_list.html', context)


@login_required
@company_required
@module_permission_required('telemedicine')
def appointment_detail(request, appointment_id):
    """Detalle de cita de telemedicina."""
    company_id = request.session.get('active_company')
    appointment = get_object_or_404(
        TelemedicineAppointment.objects.select_related(
            'patient__third_party', 'doctor', 'created_by'
        ),
        id=appointment_id,
        company_id=company_id
    )

    # Verificar si tiene consulta o visita asociada
    has_consultation = hasattr(appointment, 'virtual_consultation')
    has_visit = hasattr(appointment, 'home_care_visit')

    context = {
        'appointment': appointment,
        'has_consultation': has_consultation,
        'has_visit': has_visit,
    }

    return render(request, 'telemedicine/appointment_detail.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def appointment_create(request):
    """Crear nueva cita de telemedicina."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        # Crear cita (implementar lógica completa)
        try:
            appointment = TelemedicineAppointment()
            appointment.company_id = company_id
            appointment.patient_id = request.POST.get('patient')
            appointment.doctor_id = request.POST.get('doctor')
            appointment.appointment_type = request.POST.get('appointment_type')
            appointment.scheduled_date = request.POST.get('scheduled_date')
            appointment.duration_minutes = request.POST.get('duration_minutes', 30)
            appointment.reason = request.POST.get('reason')
            appointment.specialty = request.POST.get('specialty', '')
            appointment.priority = request.POST.get('priority', 'routine')

            # Campos específicos según tipo
            if appointment.appointment_type in ['virtual', 'chat']:
                appointment.meeting_link = request.POST.get('meeting_link', '')
                appointment.meeting_platform = request.POST.get('meeting_platform', '')
                appointment.meeting_id = request.POST.get('meeting_id', '')
                appointment.meeting_password = request.POST.get('meeting_password', '')
            elif appointment.appointment_type == 'home_care':
                appointment.home_address = request.POST.get('home_address', '')
                appointment.home_city = request.POST.get('home_city', '')
                appointment.home_phone = request.POST.get('home_phone', '')
                appointment.special_instructions = request.POST.get('special_instructions', '')

            appointment.pre_consultation_notes = request.POST.get('pre_consultation_notes', '')
            appointment.created_by = request.user
            appointment.save()

            messages.success(request, f'Cita {appointment.appointment_number} creada exitosamente.')
            return redirect('telemedicine:appointment_detail', appointment_id=appointment.id)
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {str(e)}')

    # Obtener pacientes y doctores
    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party')

    doctors = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'patients': patients,
        'doctors': doctors,
        'type_choices': TelemedicineAppointment.APPOINTMENT_TYPE_CHOICES,
        'priority_choices': [
            ('routine', 'Rutina'),
            ('urgent', 'Urgente'),
            ('emergency', 'Emergencia'),
        ],
    }

    return render(request, 'telemedicine/appointment_form.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def appointment_update_status(request, appointment_id):
    """Actualizar estado de cita."""
    company_id = request.session.get('active_company')
    appointment = get_object_or_404(
        TelemedicineAppointment,
        id=appointment_id,
        company_id=company_id
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TelemedicineAppointment.STATUS_CHOICES):
            appointment.status = new_status

            # Si se cancela, guardar razón
            if new_status == 'cancelled':
                appointment.cancellation_reason = request.POST.get('cancellation_reason', '')

            # Si se completa, guardar tiempos reales
            if new_status == 'completed':
                if not appointment.actual_start_time:
                    appointment.actual_start_time = timezone.now()
                appointment.actual_end_time = timezone.now()

            # Si se inicia, guardar hora de inicio
            if new_status == 'in_progress' and not appointment.actual_start_time:
                appointment.actual_start_time = timezone.now()

            appointment.save()
            messages.success(request, f'Estado actualizado a {appointment.get_status_display()}')
        else:
            messages.error(request, 'Estado inválido')

    return redirect('telemedicine:appointment_detail', appointment_id=appointment_id)


# =============================================================================
# CONSULTAS VIRTUALES
# =============================================================================

@login_required
@company_required
@module_permission_required('telemedicine')
def virtual_consultations_list(request):
    """Lista de consultas virtuales."""
    company_id = request.session.get('active_company')

    consultations = VirtualConsultation.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'doctor', 'appointment')

    # Filtros
    consultation_type = request.GET.get('consultation_type')
    doctor_id = request.GET.get('doctor')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if consultation_type:
        consultations = consultations.filter(consultation_type=consultation_type)

    if doctor_id:
        consultations = consultations.filter(doctor_id=doctor_id)

    if date_from:
        consultations = consultations.filter(consultation_date__date__gte=date_from)

    if date_to:
        consultations = consultations.filter(consultation_date__date__lte=date_to)

    if search:
        consultations = consultations.filter(
            Q(consultation_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(chief_complaint__icontains=search) |
            Q(diagnosis__icontains=search)
        )

    # Paginación
    paginator = Paginator(consultations.order_by('-consultation_date'), 15)
    page = request.GET.get('page')
    consultations = paginator.get_page(page)

    # Para filtros
    doctors = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'consultations': consultations,
        'type_choices': VirtualConsultation.CONSULTATION_TYPE_CHOICES,
        'doctors': doctors,
        'filters': {
            'consultation_type': consultation_type,
            'doctor': doctor_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'telemedicine/virtual_consultations_list.html', context)


@login_required
@company_required
@module_permission_required('telemedicine')
def virtual_consultation_detail(request, consultation_id):
    """Detalle de consulta virtual."""
    company_id = request.session.get('active_company')
    consultation = get_object_or_404(
        VirtualConsultation.objects.select_related(
            'patient__third_party', 'doctor', 'appointment', 'created_by'
        ),
        id=consultation_id,
        company_id=company_id
    )

    # Obtener documentos asociados
    documents = MedicalDocument.objects.filter(
        virtual_consultation=consultation
    ).order_by('-issue_date')

    context = {
        'consultation': consultation,
        'documents': documents,
    }

    return render(request, 'telemedicine/virtual_consultation_detail.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def virtual_consultation_create(request):
    """Crear nueva consulta virtual."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            consultation = VirtualConsultation()
            consultation.company_id = company_id

            # Campos básicos
            appointment_id = request.POST.get('appointment')
            if appointment_id:
                consultation.appointment_id = appointment_id

            consultation.patient_id = request.POST.get('patient')
            consultation.doctor_id = request.POST.get('doctor')
            consultation.consultation_type = request.POST.get('consultation_type')
            consultation.consultation_date = request.POST.get('consultation_date')
            consultation.duration_minutes = request.POST.get('duration_minutes')

            # Motivo y síntomas
            consultation.chief_complaint = request.POST.get('chief_complaint')
            consultation.symptoms = request.POST.get('symptoms')
            consultation.symptoms_duration = request.POST.get('symptoms_duration', '')

            # Examen y evaluación
            consultation.remote_examination = request.POST.get('remote_examination', '')
            consultation.vital_signs_reported = request.POST.get('vital_signs_reported', '')

            # Diagnóstico y tratamiento
            consultation.diagnosis = request.POST.get('diagnosis')
            consultation.treatment_plan = request.POST.get('treatment_plan')
            consultation.medications_prescribed = request.POST.get('medications_prescribed', '')

            # Recomendaciones
            consultation.recommendations = request.POST.get('recommendations', '')
            consultation.requires_in_person_visit = request.POST.get('requires_in_person_visit') == 'on'
            consultation.follow_up_required = request.POST.get('follow_up_required') == 'on'

            if consultation.follow_up_required:
                follow_up_date = request.POST.get('follow_up_date')
                if follow_up_date:
                    consultation.follow_up_date = follow_up_date

            # Exámenes solicitados
            consultation.lab_tests_ordered = request.POST.get('lab_tests_ordered', '')
            consultation.imaging_studies_ordered = request.POST.get('imaging_studies_ordered', '')

            # Incapacidades
            sick_leave_days = request.POST.get('sick_leave_days')
            if sick_leave_days:
                consultation.sick_leave_days = int(sick_leave_days)
            consultation.medical_certificate_issued = request.POST.get('medical_certificate_issued') == 'on'

            # Calidad técnica
            consultation.connection_quality = request.POST.get('connection_quality', 'good')
            consultation.technical_issues = request.POST.get('technical_issues', '')
            consultation.observations = request.POST.get('observations', '')

            consultation.created_by = request.user
            consultation.save()

            # Si hay cita asociada, marcarla como completada
            if consultation.appointment:
                consultation.appointment.status = 'completed'
                consultation.appointment.actual_end_time = timezone.now()
                consultation.appointment.save()

            messages.success(request, f'Consulta virtual {consultation.consultation_number} creada exitosamente.')
            return redirect('telemedicine:virtual_consultation_detail', consultation_id=consultation.id)
        except Exception as e:
            messages.error(request, f'Error al crear la consulta: {str(e)}')

    # Obtener citas disponibles (confirmadas o en progreso, tipo virtual)
    available_appointments = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        appointment_type__in=['virtual', 'phone', 'chat'],
        status__in=['confirmed', 'in_progress']
    ).select_related('patient__third_party', 'doctor')

    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party')

    doctors = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'available_appointments': available_appointments,
        'patients': patients,
        'doctors': doctors,
        'type_choices': VirtualConsultation.CONSULTATION_TYPE_CHOICES,
        'quality_choices': [
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('fair', 'Regular'),
            ('poor', 'Mala'),
        ],
    }

    return render(request, 'telemedicine/virtual_consultation_form.html', context)


# =============================================================================
# ATENCIÓN DOMICILIARIA
# =============================================================================

@login_required
@company_required
@module_permission_required('telemedicine')
def home_care_visits_list(request):
    """Lista de visitas domiciliarias."""
    company_id = request.session.get('active_company')

    visits = HomeCareVisit.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'healthcare_professional', 'appointment')

    # Filtros
    status = request.GET.get('status')
    visit_type = request.GET.get('visit_type')
    professional_id = request.GET.get('professional')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        visits = visits.filter(status=status)

    if visit_type:
        visits = visits.filter(visit_type=visit_type)

    if professional_id:
        visits = visits.filter(healthcare_professional_id=professional_id)

    if date_from:
        visits = visits.filter(scheduled_date__date__gte=date_from)

    if date_to:
        visits = visits.filter(scheduled_date__date__lte=date_to)

    if search:
        visits = visits.filter(
            Q(visit_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(address__icontains=search) |
            Q(city__icontains=search)
        )

    # Paginación
    paginator = Paginator(visits.order_by('-scheduled_date'), 15)
    page = request.GET.get('page')
    visits = paginator.get_page(page)

    # Para filtros
    professionals = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'visits': visits,
        'status_choices': HomeCareVisit.STATUS_CHOICES,
        'type_choices': HomeCareVisit.VISIT_TYPE_CHOICES,
        'professionals': professionals,
        'filters': {
            'status': status,
            'visit_type': visit_type,
            'professional': professional_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'telemedicine/home_care_visits_list.html', context)


@login_required
@company_required
@module_permission_required('telemedicine')
def home_care_visit_detail(request, visit_id):
    """Detalle de visita domiciliaria."""
    company_id = request.session.get('active_company')
    visit = get_object_or_404(
        HomeCareVisit.objects.select_related(
            'patient__third_party', 'healthcare_professional', 'appointment', 'created_by'
        ),
        id=visit_id,
        company_id=company_id
    )

    # Obtener documentos asociados
    documents = MedicalDocument.objects.filter(
        home_care_visit=visit
    ).order_by('-issue_date')

    context = {
        'visit': visit,
        'documents': documents,
    }

    return render(request, 'telemedicine/home_care_visit_detail.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def home_care_visit_create(request):
    """Crear nueva visita domiciliaria."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            visit = HomeCareVisit()
            visit.company_id = company_id

            # Campos básicos
            appointment_id = request.POST.get('appointment')
            if appointment_id:
                visit.appointment_id = appointment_id

            visit.patient_id = request.POST.get('patient')
            visit.healthcare_professional_id = request.POST.get('healthcare_professional')
            visit.accompanying_staff = request.POST.get('accompanying_staff', '')

            visit.visit_type = request.POST.get('visit_type')
            visit.scheduled_date = request.POST.get('scheduled_date')

            # Dirección
            visit.address = request.POST.get('address')
            visit.city = request.POST.get('city')
            visit.neighborhood = request.POST.get('neighborhood', '')
            visit.landmark_reference = request.POST.get('landmark_reference', '')
            visit.contact_phone = request.POST.get('contact_phone')

            # Motivo
            visit.visit_reason = request.POST.get('visit_reason')
            visit.patient_condition_on_arrival = request.POST.get('patient_condition_on_arrival', '')

            # Signos vitales
            visit.blood_pressure = request.POST.get('blood_pressure', '')
            heart_rate = request.POST.get('heart_rate')
            if heart_rate:
                visit.heart_rate = int(heart_rate)
            respiratory_rate = request.POST.get('respiratory_rate')
            if respiratory_rate:
                visit.respiratory_rate = int(respiratory_rate)
            temperature = request.POST.get('temperature')
            if temperature:
                visit.temperature = float(temperature)
            oxygen_saturation = request.POST.get('oxygen_saturation')
            if oxygen_saturation:
                visit.oxygen_saturation = int(oxygen_saturation)

            # Procedimientos
            visit.procedures_performed = request.POST.get('procedures_performed', '')
            visit.medications_administered = request.POST.get('medications_administered', '')
            visit.medical_supplies_used = request.POST.get('medical_supplies_used', '')

            # Evaluación
            visit.clinical_assessment = request.POST.get('clinical_assessment')
            visit.diagnosis = request.POST.get('diagnosis', '')
            visit.treatment_provided = request.POST.get('treatment_provided', '')

            # Instrucciones
            visit.instructions_to_patient = request.POST.get('instructions_to_patient', '')
            visit.instructions_to_caregiver = request.POST.get('instructions_to_caregiver', '')
            visit.next_visit_required = request.POST.get('next_visit_required') == 'on'

            if visit.next_visit_required:
                next_visit_date = request.POST.get('next_visit_date')
                if next_visit_date:
                    visit.next_visit_date = next_visit_date

            # Estado
            visit.status = request.POST.get('status', 'scheduled')
            visit.patient_satisfaction = request.POST.get('patient_satisfaction', '')
            visit.observations = request.POST.get('observations', '')
            visit.complications = request.POST.get('complications', '')

            visit.created_by = request.user
            visit.save()

            messages.success(request, f'Visita domiciliaria {visit.visit_number} creada exitosamente.')
            return redirect('telemedicine:home_care_visit_detail', visit_id=visit.id)
        except Exception as e:
            messages.error(request, f'Error al crear la visita: {str(e)}')

    # Obtener citas disponibles (tipo home_care)
    available_appointments = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        appointment_type='home_care',
        status__in=['confirmed', 'in_progress']
    ).select_related('patient__third_party', 'doctor')

    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party')

    professionals = User.objects.filter(company_id=company_id, is_active=True)

    context = {
        'available_appointments': available_appointments,
        'patients': patients,
        'professionals': professionals,
        'type_choices': HomeCareVisit.VISIT_TYPE_CHOICES,
        'status_choices': HomeCareVisit.STATUS_CHOICES,
        'satisfaction_choices': [
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('fair', 'Regular'),
            ('poor', 'Mala'),
        ],
    }

    return render(request, 'telemedicine/home_care_visit_form.html', context)


# =============================================================================
# DOCUMENTOS MÉDICOS
# =============================================================================

@login_required
@company_required
@module_permission_required('telemedicine')
def medical_documents_list(request):
    """Lista de documentos médicos."""
    company_id = request.session.get('active_company')

    documents = MedicalDocument.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party', 'virtual_consultation', 'home_care_visit', 'signed_by')

    # Filtros
    document_type = request.GET.get('document_type')
    is_signed = request.GET.get('is_signed')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if document_type:
        documents = documents.filter(document_type=document_type)

    if is_signed:
        documents = documents.filter(is_digitally_signed=(is_signed == 'true'))

    if date_from:
        documents = documents.filter(issue_date__gte=date_from)

    if date_to:
        documents = documents.filter(issue_date__lte=date_to)

    if search:
        documents = documents.filter(
            Q(document_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(document_title__icontains=search) |
            Q(diagnosis__icontains=search)
        )

    # Paginación
    paginator = Paginator(documents.order_by('-issue_date'), 15)
    page = request.GET.get('page')
    documents = paginator.get_page(page)

    context = {
        'documents': documents,
        'type_choices': MedicalDocument.DOCUMENT_TYPE_CHOICES,
        'filters': {
            'document_type': document_type,
            'is_signed': is_signed,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'telemedicine/medical_documents_list.html', context)


@login_required
@company_required
@module_permission_required('telemedicine')
def medical_document_detail(request, document_id):
    """Detalle de documento médico."""
    company_id = request.session.get('active_company')
    document = get_object_or_404(
        MedicalDocument.objects.select_related(
            'patient__third_party', 'virtual_consultation', 'home_care_visit',
            'signed_by', 'created_by'
        ),
        id=document_id,
        company_id=company_id
    )

    # Obtener historial de firmas
    signatures = DigitalSignature.objects.filter(
        document=document
    ).select_related('signer').order_by('-signature_date')

    context = {
        'document': document,
        'signatures': signatures,
    }

    return render(request, 'telemedicine/medical_document_detail.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def medical_document_create(request):
    """Crear nuevo documento médico."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            document = MedicalDocument()
            document.company_id = company_id

            document.patient_id = request.POST.get('patient')

            # Relaciones opcionales
            consultation_id = request.POST.get('virtual_consultation')
            if consultation_id:
                document.virtual_consultation_id = consultation_id

            visit_id = request.POST.get('home_care_visit')
            if visit_id:
                document.home_care_visit_id = visit_id

            document.document_type = request.POST.get('document_type')
            document.document_title = request.POST.get('document_title')
            document.document_content = request.POST.get('document_content')
            document.diagnosis = request.POST.get('diagnosis', '')
            document.observations = request.POST.get('observations', '')
            document.issue_date = request.POST.get('issue_date')

            valid_until = request.POST.get('valid_until')
            if valid_until:
                document.valid_until = valid_until

            document.created_by = request.user
            document.save()

            messages.success(request, f'Documento {document.document_number} creado exitosamente.')
            return redirect('telemedicine:medical_document_detail', document_id=document.id)
        except Exception as e:
            messages.error(request, f'Error al crear el documento: {str(e)}')

    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party')

    # Consultas recientes
    recent_consultations = VirtualConsultation.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party').order_by('-consultation_date')[:20]

    # Visitas recientes
    recent_visits = HomeCareVisit.objects.filter(
        company_id=company_id
    ).select_related('patient__third_party').order_by('-scheduled_date')[:20]

    context = {
        'patients': patients,
        'recent_consultations': recent_consultations,
        'recent_visits': recent_visits,
        'type_choices': MedicalDocument.DOCUMENT_TYPE_CHOICES,
    }

    return render(request, 'telemedicine/medical_document_form.html', context)


@login_required
@company_required
@module_permission_required('telemedicine', 'edit')
def medical_document_sign(request, document_id):
    """Firmar digitalmente un documento."""
    company_id = request.session.get('active_company')
    document = get_object_or_404(
        MedicalDocument,
        id=document_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            # Crear hash de firma
            signature_data = f"{document.id}{request.user.id}{timezone.now().isoformat()}"
            signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

            # Actualizar documento
            document.is_digitally_signed = True
            document.signed_by = request.user
            document.signature_date = timezone.now()
            document.digital_signature_hash = signature_hash
            document.save()

            # Crear registro de firma
            signature = DigitalSignature()
            signature.company_id = company_id
            signature.document = document
            signature.signer = request.user
            signature.signature_hash = signature_hash
            signature.signature_method = 'SHA256'
            signature.ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
            signature.device_info = request.META.get('HTTP_USER_AGENT', '')
            signature.is_valid = True
            signature.save()

            messages.success(request, 'Documento firmado digitalmente exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al firmar el documento: {str(e)}')

    return redirect('telemedicine:medical_document_detail', document_id=document_id)


# =============================================================================
# ESTADÍSTICAS Y REPORTES
# =============================================================================

@login_required
@company_required
@module_permission_required('telemedicine')
def telemedicine_statistics(request):
    """Estadísticas del módulo de telemedicina."""
    company_id = request.session.get('active_company')

    # Rango de fechas
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Estadísticas de citas
    appointments_stats = TelemedicineAppointment.objects.filter(
        company_id=company_id,
        scheduled_date__date__gte=date_from,
        scheduled_date__date__lte=date_to
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        virtual=Count('id', filter=Q(appointment_type='virtual')),
        home_care=Count('id', filter=Q(appointment_type='home_care')),
    )

    # Estadísticas de consultas
    consultations_stats = VirtualConsultation.objects.filter(
        company_id=company_id,
        consultation_date__date__gte=date_from,
        consultation_date__date__lte=date_to
    ).aggregate(
        total=Count('id'),
        avg_duration=Avg('duration_minutes'),
        with_follow_up=Count('id', filter=Q(follow_up_required=True)),
        requires_in_person=Count('id', filter=Q(requires_in_person_visit=True)),
    )

    # Estadísticas de visitas
    visits_stats = HomeCareVisit.objects.filter(
        company_id=company_id,
        scheduled_date__date__gte=date_from,
        scheduled_date__date__lte=date_to
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )

    # Estadísticas de documentos
    documents_stats = MedicalDocument.objects.filter(
        company_id=company_id,
        issue_date__gte=date_from,
        issue_date__lte=date_to
    ).aggregate(
        total=Count('id'),
        signed=Count('id', filter=Q(is_digitally_signed=True)),
        prescriptions=Count('id', filter=Q(document_type='prescription')),
        certificates=Count('id', filter=Q(document_type='medical_certificate')),
    )

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'appointments_stats': appointments_stats,
        'consultations_stats': consultations_stats,
        'visits_stats': visits_stats,
        'documents_stats': documents_stats,
    }

    return render(request, 'telemedicine/statistics.html', context)


# =============================================================================
# API/AJAX ENDPOINTS
# =============================================================================

@login_required
@company_required
def get_patient_info(request, patient_id):
    """API para obtener información del paciente (AJAX)."""
    company_id = request.session.get('active_company')

    try:
        patient = Patient.objects.select_related('third_party', 'eps').get(
            id=patient_id,
            company_id=company_id
        )

        data = {
            'id': str(patient.id),
            'full_name': patient.get_full_name(),
            'document_number': patient.third_party.document_number,
            'medical_record_number': patient.medical_record_number,
            'phone': patient.third_party.phone1 or '',
            'email': patient.third_party.email or '',
            'address': patient.third_party.address or '',
            'city': patient.third_party.city or '',
            'eps': patient.eps.name if patient.eps else '',
        }

        return JsonResponse(data)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)
