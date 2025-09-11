"""
Decoradores personalizados para autenticación y autorización.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden, Http404
from django.contrib import messages
from django.shortcuts import redirect

from .models import Company, UserCompanyPermission


def company_required(view_func):
    """
    Decorador que requiere que el usuario tenga al menos una empresa asignada.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        user_companies = request.user.companies.filter(is_active=True)
        if not user_companies.exists():
            messages.error(
                request, 
                'Su usuario no tiene empresas asignadas. Contacte al administrador.'
            )
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return login_required(_wrapped_view)


def company_permission_required(permission_field):
    """
    Decorador que verifica permisos específicos por empresa y módulo.
    
    Args:
        permission_field: Campo de permiso a verificar (ej: 'can_access_accounting')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si el usuario tiene el permiso en alguna empresa activa
            has_permission = UserCompanyPermission.objects.filter(
                user=request.user,
                company__is_active=True,
                **{permission_field: True}
            ).exists()
            
            if not has_permission:
                messages.error(
                    request,
                    f'No tiene permisos para acceder a este módulo.'
                )
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    
    return decorator


def role_required(allowed_roles):
    """
    Decorador que verifica el rol del usuario.
    
    Args:
        allowed_roles: Lista de roles permitidos o rol único como string
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f'Su rol ({request.user.get_role_display()}) no tiene permisos para esta acción.'
                )
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    
    return decorator


def company_access_required(company_field='company_id'):
    """
    Decorador que verifica que el usuario tenga acceso a la empresa específica.
    
    Args:
        company_field: Nombre del campo en kwargs que contiene el ID de la empresa
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            company_id = kwargs.get(company_field)
            if not company_id:
                raise Http404("Company not specified")
            
            # Verificar que la empresa existe y está activa
            try:
                company = Company.objects.get(id=company_id, is_active=True)
            except Company.DoesNotExist:
                raise Http404("Company not found")
            
            # Verificar que el usuario tiene acceso a esta empresa
            has_access = request.user.companies.filter(
                id=company_id,
                is_active=True
            ).exists()
            
            if not has_access:
                messages.error(
                    request,
                    'No tiene permisos para acceder a esta empresa.'
                )
                return redirect('core:dashboard')
            
            # Agregar la empresa al request para uso posterior
            request.current_company = company
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    
    return decorator


def permission_level_required(min_level='read'):
    """
    Decorador que verifica el nivel mínimo de permisos.
    
    Args:
        min_level: Nivel mínimo requerido ('read', 'write', 'approve', 'admin')
    """
    level_hierarchy = {
        'read': 0,
        'write': 1,
        'approve': 2,
        'admin': 3
    }
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            company = getattr(request, 'current_company', None)
            if not company:
                # Intentar obtener de la primera empresa del usuario
                user_companies = request.user.companies.filter(is_active=True)
                if user_companies.exists():
                    company = user_companies.first()
                else:
                    messages.error(request, 'No tiene empresas asignadas.')
                    return redirect('core:dashboard')
            
            # Verificar nivel de permisos
            try:
                permission = UserCompanyPermission.objects.get(
                    user=request.user,
                    company=company
                )
                
                user_level = level_hierarchy.get(permission.permission_level, 0)
                required_level = level_hierarchy.get(min_level, 0)
                
                if user_level < required_level:
                    messages.error(
                        request,
                        f'Requiere permisos de {min_level} o superior.'
                    )
                    return redirect('core:dashboard')
                
            except UserCompanyPermission.DoesNotExist:
                messages.error(request, 'No tiene permisos para esta empresa.')
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    
    return decorator


def max_amount_required(amount_field='amount'):
    """
    Decorador que verifica límites de aprobación por cantidad.
    
    Args:
        amount_field: Campo del request.POST que contiene la cantidad
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Solo aplicar en métodos POST/PUT/PATCH
            if request.method not in ['POST', 'PUT', 'PATCH']:
                return view_func(request, *args, **kwargs)
            
            amount = request.POST.get(amount_field)
            if amount:
                try:
                    amount = float(amount)
                    
                    company = getattr(request, 'current_company', None)
                    if company:
                        permission = UserCompanyPermission.objects.filter(
                            user=request.user,
                            company=company
                        ).first()
                        
                        if permission and amount > permission.max_amount_approval:
                            messages.error(
                                request,
                                f'El monto ${amount:,.2f} excede su límite de aprobación '
                                f'de ${permission.max_amount_approval:,.2f}'
                            )
                            return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))
                
                except (ValueError, TypeError):
                    pass  # Si no se puede convertir, continuar
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    
    return decorator


# Decoradores combinados para casos comunes

@company_required
@company_permission_required('can_access_accounting')
def accounting_required(view_func):
    """Decorador combinado para módulo de contabilidad."""
    return view_func


@company_required
@company_permission_required('can_access_receivables')
def receivables_required(view_func):
    """Decorador combinado para módulo de cuentas por cobrar."""
    return view_func


@company_required
@company_permission_required('can_access_payables')
def payables_required(view_func):
    """Decorador combinado para módulo de cuentas por pagar."""
    return view_func


@company_required
@company_permission_required('can_access_treasury')
def treasury_required(view_func):
    """Decorador combinado para módulo de tesorería."""
    return view_func


@company_required
@company_permission_required('can_access_payroll')
def payroll_required(view_func):
    """Decorador combinado para módulo de nómina."""
    return view_func


@company_required
@company_permission_required('can_access_taxes')
def taxes_required(view_func):
    """Decorador combinado para módulo de impuestos."""
    return view_func


@company_required
@company_permission_required('can_access_reports')
def reports_required(view_func):
    """Decorador combinado para módulo de reportes."""
    return view_func


def module_permission_required(module_code, permission_level='view'):
    """
    Decorador que verifica permisos de módulo específico.
    
    Args:
        module_code: Código del módulo (ej: 'medical_records')
        permission_level: Nivel de permiso requerido ('view', 'edit', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Si es superusuario o admin, permitir acceso
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            company_id = request.session.get('active_company_id')
            if not company_id:
                messages.warning(request, 'Debe seleccionar una empresa para acceder.')
                return redirect('core:dashboard')
            
            try:
                from .models_modules import SystemModule, CompanyModule, UserModulePermission
                
                # Verificar que el módulo exists
                module = SystemModule.objects.get(code=module_code, is_available=True)
                
                # Verificar que está activado para la empresa
                company_module = CompanyModule.objects.get(
                    company_id=company_id,
                    module=module,
                    is_enabled=True
                )
                
                # Verificar permisos del usuario para este módulo
                user_permission = UserModulePermission.objects.filter(
                    user=request.user,
                    company_module=company_module
                ).first()
                
                if not user_permission:
                    messages.error(request, f'No tiene permisos para acceder al módulo {module.name}.')
                    return redirect('core:dashboard')
                
                # Verificar nivel de permiso
                permission_hierarchy = {'view': 1, 'edit': 2, 'admin': 3}
                required_level = permission_hierarchy.get(permission_level, 1)
                user_level = permission_hierarchy.get(user_permission.permission_level, 1)
                
                if user_level < required_level:
                    messages.error(request, f'No tiene suficientes permisos para esta acción en {module.name}.')
                    return redirect('core:dashboard')
                
            except (SystemModule.DoesNotExist, CompanyModule.DoesNotExist):
                messages.error(request, 'El módulo solicitado no existe o no está disponible.')
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return login_required(_wrapped_view)
    return decorator