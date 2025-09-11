"""
Middleware personalizado para el sistema de contabilidad multiempresa.
"""

from django.shortcuts import redirect
from django.http import Http404, HttpResponseForbidden
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
import logging

from .models import AuditLog, UserCompanyPermission

logger = logging.getLogger(__name__)


class MultiCompanyAccessMiddleware:
    """
    Middleware que verifica el acceso multi-empresa y registra actividad.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar request antes de la vista
        if request.user.is_authenticated:
            self.process_user_access(request)
        
        response = self.get_response(request)
        
        # Procesar response después de la vista
        if request.user.is_authenticated:
            self.log_user_activity(request, response)
        
        return response

    def process_user_access(self, request):
        """Procesa el acceso del usuario y verifica permisos."""
        user = request.user
        
        # Verificar si el usuario tiene empresas asignadas
        if not user.is_superuser:
            user_companies = user.companies.filter(is_active=True)
            
            # Si el usuario no tiene empresas asignadas, redirigir a página de error
            if not user_companies.exists() and not self.is_public_path(request.path):
                messages.error(request, 'Su usuario no tiene empresas asignadas. Contacte al administrador.')
                logout(request)
                return redirect('admin:login')
        
        # Actualizar última actividad
        user.last_login = timezone.now()
        user.last_login_ip = self.get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])

    def log_user_activity(self, request, response):
        """Registra la actividad del usuario para auditoría."""
        if not request.user.is_authenticated:
            return
            
        # Solo registrar ciertas acciones para evitar spam de logs
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                # Obtener la empresa del contexto si está disponible
                company = getattr(request, 'current_company', None)
                if not company and request.user.companies.exists():
                    company = request.user.companies.first()
                
                if company:
                    AuditLog.objects.create(
                        company=company,
                        user=request.user,
                        action=self.get_action_from_method(request.method),
                        model_name=self.extract_model_from_path(request.path),
                        object_id=self.extract_object_id_from_path(request.path),
                        object_repr=f"{request.method} {request.path}",
                        changes={
                            'method': request.method,
                            'path': request.path,
                            'status_code': response.status_code
                        },
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
            except Exception as e:
                logger.error(f"Error logging user activity: {e}")

    def is_public_path(self, path):
        """Verifica si la ruta es pública (no requiere empresa)."""
        public_paths = [
            '/admin/login/',
            '/admin/logout/',
            '/accounts/login/',
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        return any(path.startswith(pub_path) for pub_path in public_paths)

    def get_client_ip(self, request):
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_action_from_method(self, method):
        """Mapea métodos HTTP a acciones de auditoría."""
        mapping = {
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return mapping.get(method, 'unknown')

    def extract_model_from_path(self, path):
        """Extrae el modelo de la ruta."""
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return path

    def extract_object_id_from_path(self, path):
        """Extrae el ID del objeto de la ruta."""
        parts = path.strip('/').split('/')
        for part in parts:
            if part.isdigit() or self.is_uuid(part):
                return part
        return ''

    def is_uuid(self, value):
        """Verifica si un valor es un UUID válido."""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except ValueError:
            return False


class CompanyPermissionMiddleware:
    """
    Middleware que verifica permisos específicos por empresa y módulo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Los superusuarios tienen acceso completo
        if request.user.is_authenticated and not request.user.is_superuser:
            # Verificar permisos de módulo basado en la URL
            if not self.has_module_permission(request):
                return HttpResponseForbidden(
                    "No tiene permisos para acceder a este módulo."
                )
        
        response = self.get_response(request)
        return response

    def has_module_permission(self, request):
        """Verifica si el usuario tiene permisos para el módulo actual."""
        path = request.path
        user = request.user
        
        # Mapear rutas a permisos de módulo
        module_permissions = {
            '/accounting/': 'can_access_accounting',
            '/accounts_receivable/': 'can_access_receivables',
            '/accounts_payable/': 'can_access_payables',
            '/treasury/': 'can_access_treasury',
            '/inventory/': 'can_access_inventory',
            '/fixed-assets/': 'can_access_fixed_assets',
            '/payroll/': 'can_access_payroll',
            '/taxes/': 'can_access_taxes',
            '/reports/': 'can_access_reports',
            '/public-sector/': 'can_access_public_sector',
        }
        
        # Verificar si la ruta coincide con algún módulo
        for path_prefix, permission_field in module_permissions.items():
            if path.startswith(path_prefix):
                # Verificar si el usuario tiene permisos en alguna empresa
                user_permissions = UserCompanyPermission.objects.filter(
                    user=user,
                    company__is_active=True
                )
                
                # Verificar si tiene el permiso específico del módulo
                has_permission = user_permissions.filter(
                    **{permission_field: True}
                ).exists()
                
                if not has_permission:
                    logger.warning(
                        f"User {user.username} tried to access {path} "
                        f"without {permission_field} permission"
                    )
                    return False
        
        return True


class SessionSecurityMiddleware:
    """
    Middleware para mejorar la seguridad de sesiones.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            self.check_session_security(request)
        
        response = self.get_response(request)
        return response

    def check_session_security(self, request):
        """Verifica la seguridad de la sesión."""
        # Verificar IP consistency (opcional, puede ser problemático con proxies)
        stored_ip = request.session.get('user_ip')
        current_ip = self.get_client_ip(request)
        
        if stored_ip is None:
            request.session['user_ip'] = current_ip
        # Nota: Deshabilitado por ahora para evitar problemas con proxies/NAT
        # elif stored_ip != current_ip:
        #     logout(request)
        #     messages.error(request, 'Sesión invalidada por cambio de IP.')
        #     return redirect('admin:login')
        
        # Verificar tiempo de inactividad
        last_activity = request.session.get('last_activity')
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if (timezone.now() - last_activity).total_seconds() > 3600:  # 1 hora
                logout(request)
                messages.info(request, 'Sesión expirada por inactividad.')
                return redirect('admin:login')
        
        request.session['last_activity'] = timezone.now().isoformat()

    def get_client_ip(self, request):
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip