"""
Vistas para el módulo de Procedimientos Médicos.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from core.decorators import company_required, module_permission_required
from .models import MedicalProcedure, CUPSCode, ProcedureTemplate, ProcedureResult


@login_required
@company_required
@module_permission_required('medical_procedures')
def procedures_dashboard(request):
    """Dashboard principal de procedimientos médicos."""
    company = request.session.get('active_company')
    today = timezone.now().date()
    
    # Estadísticas básicas
    context = {
        'procedures_today': MedicalProcedure.objects.filter(
            company=company,
            scheduled_date__date=today
        ).count(),
        'procedures_scheduled': MedicalProcedure.objects.filter(
            company=company,
            status='scheduled'
        ).count(),
        'procedures_completed': MedicalProcedure.objects.filter(
            company=company,
            status='completed'
        ).count(),
        'procedures_in_progress': MedicalProcedure.objects.filter(
            company=company,
            status='in_progress'
        ).count(),
        'recent_procedures': MedicalProcedure.objects.filter(
            company=company
        ).order_by('-created_at')[:5],
    }
    
    return render(request, 'medical_procedures/dashboard.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def procedures_list(request):
    """Lista de procedimientos médicos."""
    company = request.session.get('active_company')
    
    procedures = MedicalProcedure.objects.filter(company=company)
    
    # Si es médico, solo sus procedimientos
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee:
            procedures = procedures.filter(primary_physician=employee)
    
    # Filtros
    status = request.GET.get('status')
    cups_category = request.GET.get('cups_category')
    physician = request.GET.get('physician')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status:
        procedures = procedures.filter(status=status)
    
    if cups_category:
        procedures = procedures.filter(cups_code__category=cups_category)
    
    if physician:
        procedures = procedures.filter(primary_physician_id=physician)
    
    if date_from:
        procedures = procedures.filter(scheduled_date__date__gte=date_from)
    
    if date_to:
        procedures = procedures.filter(scheduled_date__date__lte=date_to)
    
    if search:
        procedures = procedures.filter(
            Q(procedure_number__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(cups_code__cups_code__icontains=search) |
            Q(cups_code__short_description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(procedures.order_by('-scheduled_date'), 20)
    page = request.GET.get('page')
    procedures = paginator.get_page(page)
    
    context = {
        'procedures': procedures,
        'status_choices': MedicalProcedure.STATUS_CHOICES,
        'category_choices': CUPSCode.CATEGORY_CHOICES,
        'filters': {
            'status': status,
            'cups_category': cups_category,
            'physician': physician,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'medical_procedures/procedures_list.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def procedure_detail(request, procedure_id):
    """Detalle de procedimiento médico."""
    company = request.session.get('active_company')
    procedure = get_object_or_404(MedicalProcedure, id=procedure_id, company=company)
    
    # Verificar permisos
    if not request.user.is_staff and hasattr(request.user, 'employee'):
        employee = request.user.employee.filter(company=company).first()
        if employee and procedure.primary_physician != employee:
            messages.error(request, 'No tienes permisos para ver este procedimiento.')
            return redirect('medical_procedures:list')
    
    context = {
        'procedure': procedure,
        'images': procedure.images.order_by('capture_timestamp'),
        'result': getattr(procedure, 'result', None),
    }
    
    return render(request, 'medical_procedures/procedure_detail.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures', 'edit')
def new_procedure(request):
    """Crear nuevo procedimiento médico."""
    company = request.session.get('active_company')
    
    if request.method == 'POST':
        # Procesar formulario (implementar lógica completa)
        messages.success(request, 'Procedimiento programado exitosamente.')
        return redirect('medical_procedures:list')
    
    # Códigos CUPS por categoría
    cups_codes = CUPSCode.objects.filter(is_active=True)
    templates = ProcedureTemplate.objects.filter(company=company, is_active=True)
    
    context = {
        'cups_codes': cups_codes,
        'templates': templates,
        'category_choices': CUPSCode.CATEGORY_CHOICES,
        'anesthesia_choices': MedicalProcedure.ANESTHESIA_TYPE_CHOICES,
    }
    
    return render(request, 'medical_procedures/new_procedure.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def cups_catalog(request):
    """Catálogo de códigos CUPS."""
    
    cups_codes = CUPSCode.objects.filter(is_active=True)
    
    # Filtros
    category = request.GET.get('category')
    complexity = request.GET.get('complexity')
    search = request.GET.get('search')
    
    if category:
        cups_codes = cups_codes.filter(category=category)
    
    if complexity:
        cups_codes = cups_codes.filter(complexity=complexity)
    
    if search:
        cups_codes = cups_codes.filter(
            Q(cups_code__icontains=search) |
            Q(short_description__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(cups_codes.order_by('cups_code'), 20)
    page = request.GET.get('page')
    cups_codes = paginator.get_page(page)
    
    context = {
        'cups_codes': cups_codes,
        'category_choices': CUPSCode.CATEGORY_CHOICES,
        'complexity_choices': CUPSCode.COMPLEXITY_CHOICES,
        'filters': {
            'category': category,
            'complexity': complexity,
            'search': search,
        }
    }
    
    return render(request, 'medical_procedures/cups_catalog.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def cups_detail(request, cups_id):
    """Detalle de código CUPS."""
    cups_code = get_object_or_404(CUPSCode, id=cups_id)
    
    # Estadísticas de uso
    company = request.session.get('active_company')
    procedures_count = MedicalProcedure.objects.filter(
        company=company, 
        cups_code=cups_code
    ).count()
    
    context = {
        'cups_code': cups_code,
        'procedures_count': procedures_count,
    }
    
    return render(request, 'medical_procedures/cups_detail.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def procedure_templates(request):
    """Plantillas de procedimientos."""
    company = request.session.get('active_company')
    
    templates = ProcedureTemplate.objects.filter(company=company)
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'medical_procedures/procedure_templates.html', context)


@login_required
@company_required
@module_permission_required('medical_procedures')
def get_cups_by_category(request):
    """API para obtener códigos CUPS por categoría (AJAX)."""
    category = request.GET.get('category')
    
    if not category:
        return JsonResponse({'cups_codes': []})
    
    cups_codes = CUPSCode.objects.filter(
        category=category, 
        is_active=True
    ).order_by('cups_code')
    
    cups_list = [{
        'id': str(cups_code.id),
        'code': cups_code.cups_code,
        'description': cups_code.short_description,
        'estimated_duration': cups_code.estimated_duration,
        'requires_anesthesia': cups_code.requires_anesthesia,
        'total_price': float(cups_code.get_total_price()),
    } for cups_code in cups_codes]
    
    return JsonResponse({'cups_codes': cups_list})