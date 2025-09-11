"""
API utilities and decorators for consistent API behavior across modules.
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def api_view(require_login=True):
    """
    Decorator for API views with consistent error handling and authentication.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            try:
                # Apply login_required if needed
                if require_login:
                    if not request.user.is_authenticated:
                        return JsonResponse({'error': 'Authentication required'}, status=401)
                
                # Set JSON content type header for all responses
                result = view_func(request, *args, **kwargs)
                
                if hasattr(result, 'content_type'):
                    if not result.get('Content-Type'):
                        result['Content-Type'] = 'application/json'
                
                return result
                
            except Exception as e:
                return JsonResponse({
                    'error': f'Internal server error: {str(e)}'
                }, status=500)
        
        return wrapped_view
    return decorator


def validate_company_access(view_func):
    """
    Decorator to validate that user has access to specified company.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        company_id = request.GET.get('company') or kwargs.get('company_id')
        
        if company_id:
            from core.models import Company
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                # Check user access to company
                if not request.user.companies.filter(id=company_id).exists() and not request.user.is_superuser:
                    return JsonResponse({'error': 'No tiene permisos para acceder a esta empresa'}, status=403)
            except Company.DoesNotExist:
                return JsonResponse({'error': 'Empresa no encontrada'}, status=404)
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def json_response_format(data=None, error=None, status=200):
    """
    Standardized JSON response format.
    """
    response_data = {}
    
    if data is not None:
        response_data.update(data)
    
    if error:
        response_data['error'] = error
        status = status if status >= 400 else 400
    
    return JsonResponse(response_data, status=status)