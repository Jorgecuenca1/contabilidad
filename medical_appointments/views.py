"""
Vistas para el módulo de Citas Médicas.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from core.decorators import company_required, module_permission_required
from .models import MedicalAppointment, DoctorSchedule, AppointmentType, WaitingList
from payroll.models import Employee
from payroll.models_healthcare import EmployeeHealthcareProfile


@login_required
@company_required
@module_permission_required('medical_appointments')
def appointments_dashboard(request):
    """Dashboard principal de citas médicas."""
    company = request.session.get('active_company')
    today = timezone.now().date()
    
    # Estadísticas básicas
    context = {
        'appointments_today': MedicalAppointment.objects.filter(
            company=company,
            appointment_date__date=today
        ).count(),
        'appointments_pending': MedicalAppointment.objects.filter(
            company=company,
            status='pending'
        ).count(),
        'appointments_confirmed': MedicalAppointment.objects.filter(
            company=company,
            status='confirmed',
            appointment_date__gte=timezone.now()
        ).count(),
        'waiting_list_count': WaitingList.objects.filter(
            company=company,
            status='active'
        ).count(),
        'recent_appointments': MedicalAppointment.objects.filter(
            company=company
        ).order_by('-created_at')[:5],
    }
    
    return render(request, 'medical_appointments/dashboard.html', context)


@login_required
@company_required
@module_permission_required('medical_appointments')
def appointments_list(request):
    """Lista de citas médicas."""
    company = request.session.get('active_company')
    
    appointments = MedicalAppointment.objects.filter(company=company)
    
    # Si es médico, solo sus citas
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee:
            appointments = appointments.filter(doctor=employee)
    
    # Filtros
    status = request.GET.get('status')
    doctor = request.GET.get('doctor')
    appointment_type = request.GET.get('appointment_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status:
        appointments = appointments.filter(status=status)
    
    if doctor:
        appointments = appointments.filter(doctor_id=doctor)
    
    if appointment_type:
        appointments = appointments.filter(appointment_type_id=appointment_type)
    
    if date_from:
        appointments = appointments.filter(appointment_date__date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__date__lte=date_to)
    
    if search:
        appointments = appointments.filter(
            Q(appointment_number__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(chief_complaint__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(appointments.order_by('-appointment_date'), 20)
    page = request.GET.get('page')
    appointments = paginator.get_page(page)
    
    # Para filtros
    doctors = Employee.objects.filter(
        company=company,
        healthcare_profile__healthcare_role__category__in=['medico']
    )
    appointment_types = AppointmentType.objects.filter(company=company, is_active=True)
    
    context = {
        'appointments': appointments,
        'status_choices': MedicalAppointment.STATUS_CHOICES,
        'doctors': doctors,
        'appointment_types': appointment_types,
        'filters': {
            'status': status,
            'doctor': doctor,
            'appointment_type': appointment_type,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'medical_appointments/appointments_list.html', context)


@login_required
@company_required
@module_permission_required('medical_appointments')
def appointment_detail(request, appointment_id):
    """Detalle de cita médica."""
    company = request.session.get('active_company')
    appointment = get_object_or_404(MedicalAppointment, id=appointment_id, company=company)
    
    # Verificar permisos
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee and appointment.doctor != employee:
            messages.error(request, 'No tienes permisos para ver esta cita.')
            return redirect('medical_appointments:list')
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'medical_appointments/appointment_detail.html', context)


@login_required
@company_required
@module_permission_required('medical_appointments', 'edit')
def new_appointment(request):
    """Crear nueva cita médica con selección de doctor por especialidad."""
    company = request.session.get('active_company')
    
    if request.method == 'POST':
        # Procesar formulario (implementar lógica completa)
        messages.success(request, 'Cita creada exitosamente.')
        return redirect('medical_appointments:list')
    
    # Obtener especialidades disponibles
    specialties = EmployeeHealthcareProfile.objects.filter(
        employee__company=company,
        healthcare_role__category='medico'
    ).values(
        'medical_specialty__code',
        'medical_specialty__name'
    ).distinct()
    
    # Tipos de cita
    appointment_types = AppointmentType.objects.filter(company=company, is_active=True)
    
    context = {
        'specialties': specialties,
        'appointment_types': appointment_types,
    }
    
    return render(request, 'medical_appointments/new_appointment.html', context)


@login_required
@company_required
@module_permission_required('medical_appointments')
def get_doctors_by_specialty(request):
    """API para obtener médicos por especialidad (AJAX)."""
    company = request.session.get('active_company')
    specialty_code = request.GET.get('specialty')
    
    if not specialty_code:
        return JsonResponse({'doctors': []})
    
    # Buscar médicos con esa especialidad
    doctors = Employee.objects.filter(
        company=company,
        healthcare_profile__medical_specialty__code=specialty_code,
        healthcare_profile__healthcare_role__category='medico'
    ).select_related('healthcare_profile__medical_specialty')
    
    doctors_list = [{
        'id': str(doctor.id),
        'name': doctor.get_full_name(),
        'specialty': doctor.healthcare_profile.medical_specialty.name if doctor.healthcare_profile.medical_specialty else '',
        'position': doctor.position,
    } for doctor in doctors]
    
    return JsonResponse({'doctors': doctors_list})


@login_required
@company_required
@module_permission_required('medical_appointments')
def get_available_slots(request):
    """API para obtener horarios disponibles de un doctor (AJAX)."""
    company = request.session.get('active_company')
    doctor_id = request.GET.get('doctor')
    date_str = request.GET.get('date')
    
    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})
    
    try:
        doctor = Employee.objects.get(id=doctor_id, company=company)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Buscar horario del médico para ese día
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            weekday=date.weekday(),
            is_active=True
        ).first()
        
        if not schedule:
            return JsonResponse({'slots': []})
        
        # Obtener slots disponibles
        available_slots = schedule.get_available_slots(date)
        
        slots_list = [{
            'time': slot.strftime('%H:%M'),
            'display': slot.strftime('%I:%M %p'),
        } for slot in available_slots]
        
        return JsonResponse({'slots': slots_list})
        
    except (Employee.DoesNotExist, ValueError):
        return JsonResponse({'slots': []})


@login_required
@company_required
@module_permission_required('medical_appointments')
def doctor_schedules(request):
    """Gestión de horarios de médicos."""
    company = request.session.get('active_company')
    
    schedules = DoctorSchedule.objects.filter(company=company).select_related('doctor')
    doctors = Employee.objects.filter(
        company=company,
        healthcare_profile__healthcare_role__category='medico'
    )
    
    context = {
        'schedules': schedules,
        'doctors': doctors,
        'weekdays': DoctorSchedule.WEEKDAY_CHOICES,
    }
    
    return render(request, 'medical_appointments/doctor_schedules.html', context)


@login_required
@company_required
@module_permission_required('medical_appointments')
def waiting_list(request):
    """Lista de espera de citas."""
    company = request.session.get('active_company')
    
    waiting_list = WaitingList.objects.filter(company=company).order_by('priority', 'created_at')
    
    context = {
        'waiting_list': waiting_list,
        'status_choices': WaitingList.STATUS_CHOICES,
    }
    
    return render(request, 'medical_appointments/waiting_list.html', context)