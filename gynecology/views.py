"""
Vistas del módulo de Ginecología.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta

from core.models import Company
from core.utils import get_current_company, require_company_access
from third_parties.models import ThirdParty
from payroll.models import Employee, EmployeeHealthcareProfile

from .models import (
    Patient, GynecologyConsultationType, GynecologyProcedure,
    GynecologyAppointment, GynecologyMedicalRecord, GynecologyLabResult
)


@login_required
@require_company_access
def gynecology_dashboard(request):
    """
    Dashboard del módulo de ginecología.
    Solo disponible para empresas del sector salud.
    """
    current_company = request.current_company
    
    # Verificar que la empresa sea del sector salud
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    # Estadísticas generales
    total_patients = Patient.objects.filter(company=current_company, is_active=True).count()
    today_appointments = GynecologyAppointment.objects.filter(
        company=current_company,
        appointment_date=date.today(),
        status__in=['scheduled', 'confirmed', 'in_progress']
    ).count()
    
    pending_results = GynecologyLabResult.objects.filter(
        company=current_company,
        requires_follow_up=True
    ).count()
    
    # Citas de hoy
    today_appointments_list = GynecologyAppointment.objects.filter(
        company=current_company,
        appointment_date=date.today()
    ).select_related('patient', 'attending_physician').order_by('appointment_time')[:10]
    
    # Pacientes recientes
    recent_patients = Patient.objects.filter(
        company=current_company,
        is_active=True
    ).select_related('third_party').order_by('-created_at')[:10]
    
    # Médicos ginecólogos disponibles
    gynecologists = Employee.objects.filter(
        company=current_company,
        is_active=True,
        healthcare_profile__medical_specialty__name__icontains='ginecolog'
    ).select_related('healthcare_profile')[:5]
    
    context = {
        'current_company': current_company,
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_results': pending_results,
        'today_appointments_list': today_appointments_list,
        'recent_patients': recent_patients,
        'gynecologists': gynecologists,
    }
    
    return render(request, 'gynecology/dashboard.html', context)


@login_required
@require_company_access
def patient_list(request):
    """
    Lista de pacientes ginecológicas.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    # Filtros
    search_query = request.GET.get('search', '')
    insurance_filter = request.GET.get('insurance', '')
    
    patients = Patient.objects.filter(
        company=current_company,
        is_active=True
    ).select_related('third_party')
    
    if search_query:
        patients = patients.filter(
            Q(third_party__name__icontains=search_query) |
            Q(third_party__document_number__icontains=search_query) |
            Q(medical_record_number__icontains=search_query)
        )
    
    if insurance_filter:
        patients = patients.filter(insurance_type=insurance_filter)
    
    # Paginación
    paginator = Paginator(patients.order_by('third_party__name'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opciones para filtros
    insurance_options = Patient.INSURANCE_CHOICES
    
    context = {
        'current_company': current_company,
        'page_obj': page_obj,
        'search_query': search_query,
        'insurance_filter': insurance_filter,
        'insurance_options': insurance_options,
    }
    
    return render(request, 'gynecology/patient_list.html', context)


@login_required
@require_company_access
def new_patient(request):
    """
    Crear nueva paciente ginecológica.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Crear tercero primero
            third_party = ThirdParty.objects.create(
                company=current_company,
                type='customer',  # Los pacientes son clientes
                document_type=request.POST['document_type'],
                document_number=request.POST['document_number'],
                name=request.POST['name'],
                phone=request.POST.get('phone', ''),
                mobile=request.POST.get('mobile', ''),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                birth_date=request.POST.get('birth_date') if request.POST.get('birth_date') else None,
                gender=request.POST.get('gender', ''),
                is_active=True,
                created_by=request.user
            )
            
            # Crear paciente
            patient = Patient.objects.create(
                company=current_company,
                third_party=third_party,
                medical_record_number=request.POST['medical_record_number'],
                blood_type=request.POST.get('blood_type', ''),
                insurance_type=request.POST.get('insurance_type', 'eps'),
                eps_name=request.POST.get('eps_name', ''),
                insurance_number=request.POST.get('insurance_number', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                emergency_contact_relationship=request.POST.get('emergency_contact_relationship', ''),
                pregnancies=int(request.POST.get('pregnancies', 0)),
                births=int(request.POST.get('births', 0)),
                abortions=int(request.POST.get('abortions', 0)),
                cesarean_sections=int(request.POST.get('cesarean_sections', 0)),
                created_by=request.user
            )
            
            messages.success(request, f'Paciente {patient.get_full_name()} creada exitosamente.')
            return redirect('gynecology:patient_detail', patient_id=patient.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la paciente: {str(e)}')
    
    # Opciones para el formulario
    document_types = ThirdParty.DOCUMENT_TYPE_CHOICES
    gender_choices = ThirdParty.GENDER_CHOICES
    blood_types = Patient.BLOOD_TYPE_CHOICES
    insurance_types = Patient.INSURANCE_CHOICES
    
    context = {
        'current_company': current_company,
        'document_types': document_types,
        'gender_choices': gender_choices,
        'blood_types': blood_types,
        'insurance_types': insurance_types,
    }
    
    return render(request, 'gynecology/new_patient.html', context)


@login_required
@require_company_access
def patient_detail(request, patient_id):
    """
    Detalle de una paciente específica.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    patient = get_object_or_404(Patient, id=patient_id, company=current_company)
    
    # Citas de la paciente
    appointments = patient.appointments.all().select_related(
        'consultation_type', 'procedure', 'attending_physician'
    ).order_by('-appointment_date', '-appointment_time')[:10]
    
    # Historia clínica
    medical_records = patient.medical_records.all().select_related(
        'appointment'
    ).order_by('-created_at')[:5]
    
    # Resultados de laboratorio
    lab_results = patient.lab_results.all().order_by('-study_date')[:10]
    
    context = {
        'current_company': current_company,
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
        'lab_results': lab_results,
    }
    
    return render(request, 'gynecology/patient_detail.html', context)


@login_required
@require_company_access
def appointment_list(request):
    """
    Lista de citas ginecológicas.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    # Filtros
    date_filter = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    status_filter = request.GET.get('status', '')
    physician_filter = request.GET.get('physician', '')
    
    appointments = GynecologyAppointment.objects.filter(
        company=current_company
    ).select_related('patient', 'attending_physician', 'consultation_type')
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if physician_filter:
        appointments = appointments.filter(attending_physician_id=physician_filter)
    
    # Ordenar por hora de cita
    appointments = appointments.order_by('appointment_time')
    
    # Opciones para filtros
    status_options = GynecologyAppointment.STATUS_CHOICES
    physicians = Employee.objects.filter(
        company=current_company,
        is_active=True,
        healthcare_profile__medical_specialty__name__icontains='ginecolog'
    ).select_related('healthcare_profile')
    
    context = {
        'current_company': current_company,
        'appointments': appointments,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'physician_filter': physician_filter,
        'status_options': status_options,
        'physicians': physicians,
    }
    
    return render(request, 'gynecology/appointment_list.html', context)


@login_required
@require_company_access
def new_appointment(request):
    """
    Crear nueva cita ginecológica.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Generar número de cita
            appointment_number = f"GIN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            appointment = GynecologyAppointment.objects.create(
                company=current_company,
                appointment_number=appointment_number,
                patient_id=request.POST['patient_id'],
                appointment_date=request.POST['appointment_date'],
                appointment_time=request.POST['appointment_time'],
                appointment_type=request.POST['appointment_type'],
                consultation_type_id=request.POST.get('consultation_type_id') or None,
                procedure_id=request.POST.get('procedure_id') or None,
                attending_physician_id=request.POST['attending_physician_id'],
                chief_complaint=request.POST['chief_complaint'],
                notes=request.POST.get('notes', ''),
                estimated_duration=int(request.POST.get('estimated_duration', 30)),
                created_by=request.user
            )
            
            messages.success(request, f'Cita {appointment.appointment_number} creada exitosamente.')
            return redirect('gynecology:appointment_detail', appointment_id=appointment.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {str(e)}')
    
    # Datos para el formulario
    patients = Patient.objects.filter(company=current_company, is_active=True).select_related('third_party')
    consultation_types = GynecologyConsultationType.objects.filter(company=current_company, is_active=True)
    procedures = GynecologyProcedure.objects.filter(company=current_company, is_active=True)
    physicians = Employee.objects.filter(
        company=current_company,
        is_active=True,
        healthcare_profile__medical_specialty__name__icontains='ginecolog'
    ).select_related('healthcare_profile')
    
    appointment_types = GynecologyAppointment.APPOINTMENT_TYPE_CHOICES
    
    context = {
        'current_company': current_company,
        'patients': patients,
        'consultation_types': consultation_types,
        'procedures': procedures,
        'physicians': physicians,
        'appointment_types': appointment_types,
    }
    
    return render(request, 'gynecology/new_appointment.html', context)


@login_required
@require_company_access
def appointment_detail(request, appointment_id):
    """
    Detalle de una cita específica.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    appointment = get_object_or_404(
        GynecologyAppointment, 
        id=appointment_id, 
        company=current_company
    )
    
    context = {
        'current_company': current_company,
        'appointment': appointment,
    }
    
    return render(request, 'gynecology/appointment_detail.html', context)


@login_required
@require_company_access
def procedures_list(request):
    """
    Lista de procedimientos ginecológicos.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    procedures = GynecologyProcedure.objects.filter(company=current_company, is_active=True)
    
    # Filtros
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    if category:
        procedures = procedures.filter(category=category)
    
    if search:
        procedures = procedures.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(procedures.order_by('category', 'name'), 20)
    page = request.GET.get('page')
    procedures = paginator.get_page(page)
    
    context = {
        'current_company': current_company,
        'procedures': procedures,
        'category_choices': GynecologyProcedure.PROCEDURE_CATEGORY_CHOICES,
        'filters': {
            'category': category,
            'search': search,
        }
    }
    
    return render(request, 'gynecology/procedures_list.html', context)


@login_required
@require_company_access
def new_procedure(request):
    """
    Crear nuevo procedimiento ginecológico.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Crear nuevo procedimiento
            procedure = GynecologyProcedure(
                company=current_company,
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                category=request.POST.get('category'),
                description=request.POST.get('description', ''),
                requires_anesthesia=bool(request.POST.get('requires_anesthesia')),
                requires_hospitalization=bool(request.POST.get('requires_hospitalization')),
                estimated_duration=int(request.POST.get('estimated_duration', 30)),
                pre_procedure_instructions=request.POST.get('pre_procedure_instructions', ''),
                post_procedure_instructions=request.POST.get('post_procedure_instructions', ''),
                base_price=float(request.POST.get('base_price', 0)),
                created_by=request.user
            )
            procedure.save()
            
            messages.success(request, f'Procedimiento "{procedure.name}" creado exitosamente.')
            return redirect('gynecology:procedures_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear el procedimiento: {str(e)}')
    
    context = {
        'current_company': current_company,
        'category_choices': GynecologyProcedure.PROCEDURE_CATEGORY_CHOICES,
    }
    
    return render(request, 'gynecology/new_procedure.html', context)


@login_required
@require_company_access
def procedure_detail(request, procedure_id):
    """
    Detalle de un procedimiento ginecológico.
    """
    current_company = request.current_company
    
    if not current_company.is_healthcare_company():
        messages.error(request, 'Este módulo solo está disponible para empresas del sector salud.')
        return redirect('core:dashboard')
    
    procedure = get_object_or_404(
        GynecologyProcedure, 
        id=procedure_id, 
        company=current_company
    )
    
    context = {
        'current_company': current_company,
        'procedure': procedure,
    }
    
    return render(request, 'gynecology/procedure_detail.html', context)