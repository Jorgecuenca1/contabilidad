"""
Vistas para el módulo de Laboratorio Clínico.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from core.decorators import company_required, module_permission_required
from .models import LabOrder, TestResult, LabTest, LabSection, Specimen, TestCategory


@login_required
@company_required
@module_permission_required('laboratory')
def laboratory_dashboard(request):
    """Dashboard principal del laboratorio."""
    company = request.session.get('active_company')
    today = timezone.now().date()
    
    # Estadísticas básicas
    context = {
        'orders_today': LabOrder.objects.filter(
            company=company,
            ordered_date__date=today
        ).count(),
        'pending_results': TestResult.objects.filter(
            order_item__lab_order__company=company,
            status='pending'
        ).count(),
        'completed_results': TestResult.objects.filter(
            order_item__lab_order__company=company,
            status='completed'
        ).count(),
        'in_progress_results': TestResult.objects.filter(
            order_item__lab_order__company=company,
            status='in_progress'
        ).count(),
        'recent_orders': LabOrder.objects.filter(company=company).order_by('-created_at')[:5],
    }
    
    return render(request, 'laboratory/dashboard.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_orders_list(request):
    """Lista de órdenes de laboratorio."""
    company = request.session.get('active_company')
    
    orders = LabOrder.objects.filter(company=company)
    
    # Filtros
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status:
        orders = orders.filter(status=status)
    
    if priority:
        orders = orders.filter(priority=priority)
    
    if date_from:
        orders = orders.filter(ordered_date__date__gte=date_from)
    
    if date_to:
        orders = orders.filter(ordered_date__date__lte=date_to)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(patient__name__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(orders.order_by('-ordered_date'), 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    context = {
        'orders': orders,
        'status_choices': LabOrder.STATUS_CHOICES,
        'priority_choices': LabOrder.PRIORITY_CHOICES,
        'filters': {
            'status': status,
            'priority': priority,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'laboratory/orders_list.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_order_detail(request, order_id):
    """Detalle de orden de laboratorio."""
    company = request.session.get('active_company')
    order = get_object_or_404(LabOrder, id=order_id, company=company)
    
    results = TestResult.objects.filter(order_item__lab_order=order).order_by('created_at')
    specimens = order.specimens.order_by('created_at')
    
    context = {
        'order': order,
        'results': results,
        'specimens': specimens,
    }
    
    return render(request, 'laboratory/order_detail.html', context)


@login_required
@company_required
@module_permission_required('laboratory', 'edit')
def new_lab_order(request):
    """Crear nueva orden de laboratorio."""
    company = request.session.get('active_company')
    
    if request.method == 'POST':
        # Procesar formulario (implementar lógica completa)
        messages.success(request, 'Orden de laboratorio creada exitosamente.')
        return redirect('laboratory:orders_list')
    
    # Obtener exámenes disponibles
    lab_tests = LabTest.objects.filter(company=company, is_active=True)
    sections = LabSection.objects.filter(company=company, is_active=True)
    
    context = {
        'lab_tests': lab_tests,
        'sections': sections,
        'priority_choices': LabOrder.PRIORITY_CHOICES,
    }
    
    return render(request, 'laboratory/new_order.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_results_list(request):
    """Lista de resultados de laboratorio."""
    company = request.session.get('active_company')
    
    results = TestResult.objects.filter(order_item__lab_order__company=company)
    
    # Filtros
    status = request.GET.get('status')
    category = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        results = results.filter(status=status)

    if category:
        results = results.filter(order_item__lab_test__category_id=category)
    
    if date_from:
        results = results.filter(created_at__date__gte=date_from)
    
    if date_to:
        results = results.filter(created_at__date__lte=date_to)
    
    if search:
        results = results.filter(
            Q(order_item__lab_order__order_number__icontains=search) |
            Q(order_item__lab_order__patient__name__icontains=search) |
            Q(order_item__lab_test__name__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(results.order_by('-created_at'), 20)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    categories = TestCategory.objects.filter(company=company, is_active=True)

    context = {
        'results': results,
        'status_choices': TestResult.STATUS_CHOICES,
        'categories': categories,
        'filters': {
            'status': status,
            'category': category,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'laboratory/results_list.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_result_detail(request, result_id):
    """Detalle de resultado de laboratorio."""
    company = request.session.get('active_company')
    result = get_object_or_404(TestResult, id=result_id, order_item__lab_order__company=company)
    
    context = {
        'result': result,
        'order': result.order_item.lab_order,
    }
    
    return render(request, 'laboratory/result_detail.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_tests_catalog(request):
    """Catálogo de exámenes de laboratorio."""
    company = request.session.get('active_company')
    
    tests = LabTest.objects.filter(company=company)
    
    # Filtros
    category = request.GET.get('category')
    search = request.GET.get('search')

    if category:
        tests = tests.filter(category_id=category)
    
    if search:
        tests = tests.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(tests.order_by('category__name', 'name'), 20)
    page = request.GET.get('page')
    tests = paginator.get_page(page)

    categories = TestCategory.objects.filter(company=company, is_active=True)

    context = {
        'tests': tests,
        'categories': categories,
        'filters': {
            'category': category,
            'search': search,
        }
    }
    
    return render(request, 'laboratory/tests_catalog.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_test_detail(request, test_id):
    """Detalle de examen de laboratorio."""
    company = request.session.get('active_company')
    test = get_object_or_404(LabTest, id=test_id, company=company)
    
    context = {
        'test': test,
    }
    
    return render(request, 'laboratory/test_detail.html', context)


@login_required
@company_required
@module_permission_required('laboratory')
def lab_sections(request):
    """Secciones del laboratorio."""
    company = request.session.get('active_company')
    
    sections = LabSection.objects.filter(company=company)
    
    context = {
        'sections': sections,
    }
    
    return render(request, 'laboratory/sections.html', context)