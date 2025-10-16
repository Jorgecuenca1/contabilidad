"""
Vistas del módulo Reportes Clínicos
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def index(request):
    """Vista principal del módulo"""
    company = request.session.get('company')
    if not company:
        messages.error(request, 'Debe seleccionar una empresa')
        return redirect('core:select_company')

    context = {
        'module_name': 'Reportes Clínicos',
    }
    return render(request, 'health_reports/index.html', context)
