"""
Vistas para el selector de empresa después del login.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Company
from .models_modules import SystemModule, CompanyModule, UserModulePermission


@login_required
def company_selector(request):
    """Selector de empresa para administradores después del login."""
    user = request.user
    
    # Solo superadmin, admin y contadores ven el selector
    if user.role not in ['superadmin', 'admin', 'contador']:
        # Para otros usuarios, redirigir directamente a su empresa
        companies = user.get_accessible_companies()
        if companies.exists():
            request.session['active_company'] = str(companies.first().id)
            return redirect('core:dashboard')
        else:
            messages.error(request, 'No tienes acceso a ninguna empresa.')
            return redirect('core:login')
    
    # Obtener empresas accesibles para el usuario
    companies = user.get_accessible_companies()
    
    # Si solo tiene acceso a una empresa, ir directamente al dashboard
    if companies.count() == 1:
        request.session['active_company'] = str(companies.first().id)
        return redirect('core:dashboard')
    
    context = {
        'companies': companies,
        'user': user,
    }
    
    return render(request, 'core/company_selector.html', context)


@login_required
@require_POST
def select_company(request):
    """Seleccionar empresa activa."""
    company_id = request.POST.get('company_id')
    
    if not company_id:
        messages.error(request, 'Debe seleccionar una empresa.')
        return redirect('core:company_selector')
    
    # Verificar que el usuario tiene acceso a esta empresa
    try:
        company = get_object_or_404(Company, id=company_id)
        if not request.user.can_access_company(company):
            messages.error(request, 'No tienes acceso a esta empresa.')
            return redirect('core:company_selector')
    except (Company.DoesNotExist, ValueError):
        messages.error(request, 'Empresa no válida.')
        return redirect('core:company_selector')
    
    # Limpiar sesión anterior
    if 'active_company' in request.session:
        del request.session['active_company']
    if 'active_company_name' in request.session:
        del request.session['active_company_name']
    
    # Guardar empresa activa en sesión
    request.session['active_company'] = str(company.id)
    request.session['active_company_name'] = company.name
    request.session.save()  # Forzar guardado
    
    messages.success(request, f'Empresa seleccionada: {company.name}')
    return redirect('core:dashboard')


@login_required
def company_modules_config(request, company_id):
    """Configuración de módulos de una empresa."""
    company = get_object_or_404(Company, id=company_id)
    
    # Verificar acceso
    if not request.user.can_access_company(company):
        messages.error(request, 'No tienes acceso a esta empresa.')
        return redirect('core:company_selector')
    
    # Solo superadmin y admin pueden configurar módulos
    if request.user.role not in ['superadmin', 'admin']:
        messages.error(request, 'No tienes permisos para configurar módulos.')
        return redirect('core:dashboard')
    
    # Obtener todos los módulos del sistema
    all_modules = SystemModule.objects.filter(is_available=True).order_by('category', 'name')
    
    # Obtener módulos activos de la empresa
    active_modules = CompanyModule.objects.filter(
        company=company, 
        is_enabled=True
    ).select_related('module')
    
    active_module_ids = set(active_modules.values_list('module_id', flat=True))
    
    # Organizar módulos por categoría
    modules_by_category = {}
    for module in all_modules:
        category = module.get_category_display()
        if category not in modules_by_category:
            modules_by_category[category] = []
        
        # Verificar si está disponible para la empresa
        can_activate = module.can_be_activated_for_company(company)
        is_active = module.id in active_module_ids
        
        modules_by_category[category].append({
            'module': module,
            'is_active': is_active,
            'can_activate': can_activate,
            'is_core': module.is_core_module,
        })
    
    context = {
        'company': company,
        'modules_by_category': modules_by_category,
        'total_active': len(active_module_ids),
    }
    
    return render(request, 'core/company_modules_config.html', context)


@login_required
@require_POST
def toggle_company_module(request):
    """Activar/desactivar módulo de empresa via AJAX."""
    company_id = request.POST.get('company_id')
    module_id = request.POST.get('module_id')
    action = request.POST.get('action')  # 'activate' o 'deactivate'
    
    try:
        company = get_object_or_404(Company, id=company_id)
        module = get_object_or_404(SystemModule, id=module_id)
        
        # Verificar permisos
        if not request.user.can_access_company(company) or request.user.role not in ['superadmin', 'admin']:
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Verificar si el módulo puede ser activado para esta empresa
        if action == 'activate' and not module.can_be_activated_for_company(company):
            return JsonResponse({
                'success': False, 
                'error': f'Módulo no disponible para empresas del sector {company.get_category_display()}'
            })
        
        # No permitir desactivar módulos core
        if action == 'deactivate' and module.is_core_module:
            return JsonResponse({
                'success': False,
                'error': 'No se pueden desactivar módulos principales'
            })
        
        if action == 'activate':
            company_module, created = CompanyModule.objects.get_or_create(
                company=company,
                module=module,
                defaults={
                    'is_enabled': True,
                    'enabled_by': request.user,
                }
            )
            if not created:
                company_module.is_enabled = True
                company_module.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Módulo {module.name} activado',
                'action': 'activated'
            })
        
        elif action == 'deactivate':
            try:
                company_module = CompanyModule.objects.get(
                    company=company, 
                    module=module
                )
                company_module.is_enabled = False
                company_module.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Módulo {module.name} desactivado',
                    'action': 'deactivated'
                })
            except CompanyModule.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Módulo no encontrado'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Acción no válida'})


@login_required
def switch_company(request):
    """Cambiar de empresa activa sin logout."""
    # Limpiar empresa activa de la sesión
    if 'active_company' in request.session:
        del request.session['active_company']
    if 'active_company_name' in request.session:
        del request.session['active_company_name']
    
    # Forzar guardado y limpiar caché
    request.session.save()
    request.session.flush()
    
    messages.info(request, 'Selecciona la empresa a la que deseas acceder.')
    return redirect('core:company_selector')