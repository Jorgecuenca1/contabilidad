"""
Context processors para el sistema de contabilidad multiempresa.
"""

def company_context(request):
    """
    Context processor que maneja la selección de empresa por usuario.
    """
    context = {
        'current_company': None,
        'user_companies': [],
        'can_select_company': False,
        'user_role': None,
    }
    
    if request.user.is_authenticated:
        context['user_role'] = request.user.role
        
        # Obtener empresas accesibles para el usuario
        accessible_companies = request.user.get_accessible_companies()
        context['user_companies'] = accessible_companies
        
        if request.user.role == 'dueno_empresa':
            # Dueños de empresa automáticamente usan su empresa
            context['current_company'] = request.user.owned_company
            context['can_select_company'] = False
        elif request.user.role in ['admin', 'contador']:
            # Administradores y contadores pueden seleccionar empresa
            context['can_select_company'] = True

            # Obtener empresa seleccionada de la sesión (soportar ambas claves para compatibilidad)
            selected_company_id = request.session.get('selected_company_id') or request.session.get('active_company')
            if selected_company_id:
                try:
                    selected_company = accessible_companies.filter(id=selected_company_id).first()
                    if selected_company:
                        context['current_company'] = selected_company
                    else:
                        # La empresa en sesión ya no está disponible, limpiar y usar la primera
                        request.session.pop('selected_company_id', None)
                        request.session.pop('active_company', None)
                        context['current_company'] = accessible_companies.first()
                except:
                    context['current_company'] = accessible_companies.first()
            else:
                # No hay empresa seleccionada, usar la primera disponible
                context['current_company'] = accessible_companies.first()
        else:
            # Otros roles usan su empresa por defecto o la primera asignada
            context['current_company'] = request.user.default_company or accessible_companies.first()
            context['can_select_company'] = accessible_companies.count() > 1
    
    return context