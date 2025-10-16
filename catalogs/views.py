"""
Vistas del módulo Catálogos CUPS/CUMS
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.utils import require_company_access


@login_required
@require_company_access
def index(request):
    """Vista principal del módulo"""
    current_company = request.current_company

    context = {
        'current_company': current_company,
        'module_name': 'Catálogos CUPS/CUMS',
    }
    return render(request, 'catalogs/index.html', context)
