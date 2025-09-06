"""
Vistas para el módulo de sector público.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.models import Company
from .models import Budget, CDP, RP


@login_required
def public_sector_dashboard(request):
    """
    Dashboard principal de sector público.
    """
    # Obtener empresas del usuario
    companies = Company.objects.filter(is_active=True)
    
    # Estadísticas del sector público (simuladas por ahora)
    total_budget = 5000000000      # Presupuesto total
    executed_budget = 2500000000   # Presupuesto ejecutado
    pending_cdps = 15             # CDPs pendientes
    pending_rps = 8               # RPs pendientes
    
    context = {
        'companies': companies,
        'total_budget': total_budget,
        'executed_budget': executed_budget,
        'pending_cdps': pending_cdps,
        'pending_rps': pending_rps,
        'execution_percentage': (executed_budget / total_budget * 100) if total_budget > 0 else 0,
    }
    
    return render(request, 'public_sector/dashboard.html', context)