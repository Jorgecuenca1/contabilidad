"""
Utilidades para el sistema de contabilidad multiempresa.
"""

from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from core.models import Company


def get_current_company(request):
    """
    Obtiene la empresa actual del usuario desde el contexto.
    Utiliza el context processor para obtener la empresa seleccionada.
    """
    # El context processor maneja toda la lógica de selección de empresa
    from core.context_processors import company_context
    context = company_context(request)
    return context.get('current_company')


def require_company_access(view_func):
    """
    Decorator que verifica que el usuario tenga acceso a una empresa.
    Redirige al dashboard si no hay empresa seleccionada.
    """
    def wrapper(request, *args, **kwargs):
        # DEBUG: Imprimir toda la sesión
        print("=" * 80)
        print("DEBUG require_company_access:")
        print(f"Usuario: {request.user}")
        print(f"Sesión completa: {dict(request.session)}")
        print(f"Path: {request.path}")

        # Obtener empresa directamente de la sesión (más confiable que context_processor)
        active_company_id = request.session.get('active_company') or request.session.get('selected_company_id')
        print(f"active_company_id encontrado: {active_company_id}")

        if not active_company_id:
            print("ERROR: No hay active_company_id en sesión!")
            print("=" * 80)
            messages.error(request, 'Debe seleccionar una empresa para acceder a este módulo.')
            return redirect('core:company_selector')

        # Obtener la empresa de la base de datos
        try:
            current_company = Company.objects.get(id=active_company_id, is_active=True)
            print(f"Empresa encontrada: {current_company.name}")

            # Verificar acceso del usuario
            if not request.user.can_access_company(current_company):
                print(f"ERROR: Usuario no tiene acceso a {current_company.name}")
                print("=" * 80)
                messages.error(request, 'No tiene acceso a esta empresa.')
                return redirect('core:company_selector')

            print("SUCCESS: Todo OK, acceso permitido!")
            print("=" * 80)
        except Company.DoesNotExist:
            print(f"ERROR: Empresa {active_company_id} no existe!")
            print("=" * 80)
            messages.error(request, 'Empresa no válida.')
            request.session.pop('active_company', None)
            request.session.pop('selected_company_id', None)
            return redirect('core:company_selector')

        # Añadir la empresa al request para fácil acceso
        request.current_company = current_company

        return view_func(request, *args, **kwargs)

    return wrapper


def filter_by_company(queryset, company):
    """
    Filtra un queryset por empresa.
    """
    if hasattr(queryset.model, 'company'):
        return queryset.filter(company=company)
    return queryset


def get_company_data(company):
    """
    Obtiene datos básicos de una empresa para mostrar en templates.
    """
    if not company:
        return {}
    
    return {
        'company_name': company.name,
        'company_id': company.id,
        'company_nit': company.tax_id,
    }