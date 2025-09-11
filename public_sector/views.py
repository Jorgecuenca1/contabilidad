"""
Vistas para el módulo de sector público.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from core.models import Company
from .models import Budget, CDP, RP, PublicReport, BudgetItem


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


@login_required
def generate_chip_report(request):
    """
    Generar reporte CHIP (Clasificador de Ingresos y Gastos Públicos).
    """
    # Obtener empresas del usuario
    companies = Company.objects.filter(is_active=True)
    
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        year = int(request.POST.get('year', 2024))
        quarter = request.POST.get('quarter')
        
        try:
            company = Company.objects.get(id=company_id)
            
            # Crear registro del reporte
            report = PublicReport.objects.create(
                company=company,
                report_type='chip',
                name=f'Reporte CHIP {year}',
                description=f'Reporte CHIP generado para {company.name} - Año {year}',
                period_year=year,
                period_quarter=int(quarter) if quarter else None,
                created_by=request.user
            )
            
            # Generar datos del reporte (simulado)
            chip_data = generate_chip_data(company, year, quarter)
            
            # Marcar como generado
            report.status = 'generated'
            report.save()
            
            context = {
                'report': report,
                'chip_data': chip_data,
                'company': company,
                'year': year,
                'quarter': quarter,
            }
            
            return render(request, 'public_sector/chip_report.html', context)
            
        except Exception as e:
            messages.error(request, f'Error al generar reporte CHIP: {str(e)}')
    
    context = {
        'companies': companies,
        'current_year': timezone.now().year,
    }
    
    return render(request, 'public_sector/chip_generate.html', context)


def generate_chip_data(company, year, quarter):
    """
    Generar datos CHIP para el reporte.
    """
    return {
        'ingresos': {
            'corrientes': 1500000000,
            'capital': 500000000,
            'total': 2000000000,
        },
        'gastos': {
            'funcionamiento': 800000000,
            'inversion': 700000000,
            'total': 1500000000,
        },
        'resultado_fiscal': 500000000,
        'detalle_ingresos': [
            {'codigo': '1.1.1.01', 'concepto': 'Predial Unificado', 'presupuestado': 500000000, 'recaudado': 450000000},
            {'codigo': '1.1.1.02', 'concepto': 'Industria y Comercio', 'presupuestado': 300000000, 'recaudado': 280000000},
            {'codigo': '1.2.1.01', 'concepto': 'Sistema General de Participaciones', 'presupuestado': 800000000, 'recaudado': 800000000},
            {'codigo': '1.3.1.01', 'concepto': 'Recursos de Capital', 'presupuestado': 400000000, 'recaudado': 350000000},
        ],
        'detalle_gastos': [
            {'codigo': '2.1.1.01', 'concepto': 'Gastos de Personal', 'presupuestado': 600000000, 'ejecutado': 580000000},
            {'codigo': '2.1.2.01', 'concepto': 'Gastos Generales', 'presupuestado': 200000000, 'ejecutado': 180000000},
            {'codigo': '2.1.3.01', 'concepto': 'Transferencias Corrientes', 'presupuestado': 100000000, 'ejecutado': 90000000},
            {'codigo': '2.2.1.01', 'concepto': 'Inversión Social', 'presupuestado': 500000000, 'ejecutado': 450000000},
        ]
    }