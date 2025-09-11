"""
Vistas para el módulo de Historia Clínica.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from core.decorators import company_required, module_permission_required
from .models import MedicalRecord, Consultation, MedicalAttachment, SpecialtyTemplate


@login_required
@company_required
@module_permission_required('medical_records')
def medical_records_dashboard(request):
    """Dashboard principal de historia clínica."""
    company = request.session.get('active_company')
    
    # Estadísticas básicas
    context = {
        'total_records': MedicalRecord.objects.filter(company=company).count(),
        'active_records': MedicalRecord.objects.filter(company=company, status='active').count(),
        'consultations_today': Consultation.objects.filter(
            medical_record__company=company,
            consultation_date__date=timezone.now().date()
        ).count(),
        'recent_records': MedicalRecord.objects.filter(company=company).order_by('-last_update')[:5],
    }
    
    return render(request, 'medical_records/dashboard.html', context)


@login_required
@company_required
@module_permission_required('medical_records')
def medical_records_list(request):
    """Lista de historias clínicas."""
    company = request.session.get('active_company')
    
    records = MedicalRecord.objects.filter(company=company)
    
    # Filtros
    record_type = request.GET.get('record_type')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if record_type:
        records = records.filter(record_type=record_type)
    
    if status:
        records = records.filter(status=status)
    
    if search:
        records = records.filter(
            Q(record_number__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(attending_physician__first_name__icontains=search) |
            Q(attending_physician__last_name__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(records.order_by('-last_update'), 20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    
    context = {
        'records': records,
        'record_type_choices': MedicalRecord.RECORD_TYPE_CHOICES,
        'status_choices': MedicalRecord.STATUS_CHOICES,
        'filters': {
            'record_type': record_type,
            'status': status,
            'search': search,
        }
    }
    
    return render(request, 'medical_records/medical_records_list.html', context)


@login_required
@company_required
@module_permission_required('medical_records')
def medical_record_detail(request, record_id):
    """Detalle de historia clínica."""
    company = request.session.get('active_company')
    record = get_object_or_404(MedicalRecord, id=record_id, company=company)
    
    # Verificar permisos: médicos solo ven sus pacientes, admin ve todo
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee and record.attending_physician != employee:
            messages.error(request, 'No tienes permisos para ver esta historia clínica.')
            return redirect('medical_records:list')
    
    consultations = record.consultations.order_by('-consultation_date')
    attachments = record.attachments.order_by('-created_at')
    
    context = {
        'record': record,
        'consultations': consultations,
        'attachments': attachments,
    }
    
    return render(request, 'medical_records/medical_record_detail.html', context)


@login_required
@company_required
@module_permission_required('medical_records')
def consultations_list(request):
    """Lista de consultas."""
    company = request.session.get('active_company')
    
    consultations = Consultation.objects.filter(medical_record__company=company)
    
    # Si no es admin, filtrar por médico
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee:
            consultations = consultations.filter(attending_physician=employee)
    
    # Filtros
    status = request.GET.get('status')
    consultation_type = request.GET.get('consultation_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        consultations = consultations.filter(status=status)
    
    if consultation_type:
        consultations = consultations.filter(consultation_type=consultation_type)
    
    if date_from:
        consultations = consultations.filter(consultation_date__date__gte=date_from)
    
    if date_to:
        consultations = consultations.filter(consultation_date__date__lte=date_to)
    
    # Paginación
    paginator = Paginator(consultations.order_by('-consultation_date'), 20)
    page = request.GET.get('page')
    consultations = paginator.get_page(page)
    
    context = {
        'consultations': consultations,
        'status_choices': Consultation.STATUS_CHOICES,
        'type_choices': Consultation.CONSULTATION_TYPE_CHOICES,
        'filters': {
            'status': status,
            'consultation_type': consultation_type,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'medical_records/consultations_list.html', context)


@login_required
@company_required
@module_permission_required('medical_records')
def consultation_detail(request, consultation_id):
    """Detalle de consulta."""
    company = request.session.get('active_company')
    consultation = get_object_or_404(
        Consultation, 
        id=consultation_id, 
        medical_record__company=company
    )
    
    # Verificar permisos
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee and consultation.attending_physician != employee:
            messages.error(request, 'No tienes permisos para ver esta consulta.')
            return redirect('medical_records:consultations_list')
    
    context = {
        'consultation': consultation,
        'record': consultation.medical_record,
    }
    
    return render(request, 'medical_records/consultation_detail.html', context)


@login_required
@company_required
@module_permission_required('medical_records', 'edit')
def new_medical_record(request):
    """Crear nueva historia clínica."""
    # Vista placeholder - implementar formulario completo
    return render(request, 'medical_records/new_medical_record.html')


@login_required
@company_required
@module_permission_required('medical_records', 'edit')
def new_consultation(request, record_id=None):
    """Crear nueva consulta."""
    company = request.session.get('active_company')
    
    if record_id:
        record = get_object_or_404(MedicalRecord, id=record_id, company=company)
        context = {'record': record}
    else:
        context = {}
    
    # Vista placeholder - implementar formulario completo
    return render(request, 'medical_records/new_consultation.html', context)