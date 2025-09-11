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
        current_company = get_current_company(request)
        
        if not current_company:
            messages.error(request, 'Debe seleccionar una empresa para acceder a este módulo.')
            return redirect('/')
        
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