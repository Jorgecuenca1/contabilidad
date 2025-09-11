"""
Vistas para el sistema de reportes.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
import json

from core.models import Company, Period
from accounting.models_accounts import Account
from .services import ReportService
from .models import ReportTemplate, GeneratedReport


@login_required
def reports_dashboard(request):
    """
    Dashboard principal de reportes.
    """
    # Manejar selección de empresa
    company_id = request.GET.get('company_id') or request.session.get('selected_company_id')
    
    # Obtener todas las empresas del usuario
    if request.user.is_superuser:
        companies = Company.objects.filter(is_active=True)
    else:
        companies = request.user.companies.filter(is_active=True)
    
    # Si no hay empresas disponibles, buscar cualquier empresa
    if not companies.exists():
        companies = Company.objects.filter(is_active=True)[:5]  # Limitar a 5 empresas para pruebas
    
    selected_company = None
    if company_id:
        try:
            selected_company = companies.get(id=company_id)
            request.session['selected_company_id'] = str(selected_company.id)
        except Company.DoesNotExist:
            pass
    
    # Si no hay empresa seleccionada, tomar la primera
    if not selected_company:
        selected_company = request.user.default_company or companies.first()
        if selected_company:
            request.session['selected_company_id'] = str(selected_company.id)
    
    # Reportes recientes
    recent_reports = []
    if selected_company:
        try:
            recent_reports = GeneratedReport.objects.filter(
                company=selected_company,
                created_by=request.user
            ).order_by('-created_at')[:10]
        except:
            # El modelo GeneratedReport podría no existir aún
            pass
    
    context = {
        'companies': companies,
        'selected_company': selected_company,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
def balance_sheet(request):
    """Vista para el Balance General."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'reports/balance_sheet.html', context)


@login_required
def income_statement(request):
    """Vista para el Estado de Resultados."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'reports/income_statement.html', context)


@login_required
def trial_balance(request):
    """Vista para el Balance de Prueba."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'reports/trial_balance.html', context)


@login_required
def general_ledger(request):
    """Vista para el Libro Mayor."""
    companies = Company.objects.filter(is_active=True)
    accounts = Account.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
        'accounts': accounts,
    }
    
    return render(request, 'reports/general_ledger.html', context)


@login_required
def aging_report(request, report_type=None):
    """Vista para reportes de antigüedad de saldos."""
    companies = Company.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
        'report_type': report_type,
    }
    
    return render(request, 'reports/aging_report.html', context)


@login_required
def financial_reports(request):
    """
    Reportes financieros principales.
    """
    companies = request.user.companies.filter(is_active=True)
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'reports/financial_reports.html', context)


@login_required
def generate_balance_sheet(request):
    """
    Generar Balance General.
    """
    if request.method == 'GET':
        # Mostrar formulario
        companies = Company.objects.filter(is_active=True)
        
        context = {
            'companies': companies,
            'report_title': 'Balance General',
            'report_description': 'Genere el balance general a una fecha específica',
            'form_action': request.path,
            'date_fields': ['period_end'],
        }
        return render(request, 'reports/report_form.html', context)
        
    elif request.method == 'POST':
        company_id = request.POST.get('company_id')
        period_end = request.POST.get('period_end')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            
            # Usar fecha actual si no se proporciona
            if not period_end:
                period_end_date = timezone.now().date()
            else:
                period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Verificar permisos (superusuarios tienen acceso completo)
            if not request.user.is_superuser and not request.user.companies.filter(id=company_id).exists():
                return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
            
            # Generar reporte
            report_service = ReportService(company)
            report_buffer = report_service.generate_balance_sheet(period_end_date, format_type)
            
            # Preparar respuesta
            if format_type == 'pdf':
                response = HttpResponse(report_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="balance_general_{company.name}_{period_end}.pdf"'
            else:
                response = HttpResponse(report_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="balance_general_{company.name}_{period_end}.xlsx"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no soportado'}, status=405)


@login_required
def generate_income_statement(request):
    """
    Generar Estado de Resultados.
    """
    if request.method == 'GET':
        # Mostrar formulario
        companies = Company.objects.filter(is_active=True)
        
        context = {
            'companies': companies,
            'report_title': 'Estado de Resultados',
            'report_description': 'Genere el estado de resultados para un período específico',
            'form_action': request.path,
            'date_fields': ['period_start', 'period_end'],
        }
        return render(request, 'reports/report_form.html', context)
        
    elif request.method == 'POST':
        company_id = request.POST.get('company_id')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            
            # Usar fechas por defecto si no se proporcionan
            current_date = timezone.now().date()
            if not period_start:
                period_start_date = current_date.replace(month=1, day=1)  # Inicio del año
            else:
                period_start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
                
            if not period_end:
                period_end_date = current_date
            else:
                period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Verificar permisos (superusuarios tienen acceso completo)
            if not request.user.is_superuser and not request.user.companies.filter(id=company_id).exists():
                return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
            
            # Generar reporte
            report_service = ReportService(company)
            report_buffer = report_service.generate_income_statement(period_start_date, period_end_date, format_type)
            
            # Preparar respuesta
            if format_type == 'pdf':
                response = HttpResponse(report_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="estado_resultados_{company.name}_{period_start}_{period_end}.pdf"'
            else:
                response = HttpResponse(report_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="estado_resultados_{company.name}_{period_start}_{period_end}.xlsx"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no soportado'}, status=405)


@login_required
def generate_trial_balance(request):
    """
    Generar Balance de Prueba.
    """
    if request.method == 'GET':
        # Mostrar formulario
        companies = Company.objects.filter(is_active=True)
        
        context = {
            'companies': companies,
            'report_title': 'Balance de Prueba',
            'report_description': 'Genere el balance de prueba a una fecha específica',
            'form_action': request.path,
            'date_fields': ['period_end'],
        }
        return render(request, 'reports/report_form.html', context)
        
    elif request.method == 'POST':
        company_id = request.POST.get('company_id')
        period_end = request.POST.get('period_end')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            
            # Usar fecha actual si no se proporciona
            if not period_end:
                period_end_date = timezone.now().date()
            else:
                period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Verificar permisos (superusuarios tienen acceso completo)
            if not request.user.is_superuser and not request.user.companies.filter(id=company_id).exists():
                return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
            
            # Generar reporte
            report_service = ReportService(company)
            report_buffer = report_service.generate_trial_balance(period_end_date, format_type)
            
            # Preparar respuesta
            if format_type == 'pdf':
                response = HttpResponse(report_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="balance_prueba_{company.name}_{period_end}.pdf"'
            else:
                response = HttpResponse(report_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="balance_prueba_{company.name}_{period_end}.xlsx"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no soportado'}, status=405)


@login_required
def generate_aging_report(request):
    """
    Generar Reporte de Cartera Vencida.
    """
    if request.method == 'GET':
        # Mostrar formulario
        companies = Company.objects.filter(is_active=True)
        
        context = {
            'companies': companies,
            'report_title': 'Reporte de Cartera Vencida',
            'report_description': 'Genere el análisis de vencimiento de CxC y CxP',
            'form_action': request.path,
            'date_fields': ['report_date'],
            'additional_fields': ['report_type'],
        }
        return render(request, 'reports/report_form.html', context)
        
    elif request.method == 'POST':
        company_id = request.POST.get('company_id')
        report_date = request.POST.get('report_date')
        report_type = request.POST.get('report_type', 'receivables')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            
            # Usar fecha actual si no se proporciona
            if not report_date:
                report_date_obj = timezone.now().date()
            else:
                report_date_obj = datetime.strptime(report_date, '%Y-%m-%d').date()
            
            # Verificar permisos (superusuarios tienen acceso completo)
            if not request.user.is_superuser and not request.user.companies.filter(id=company_id).exists():
                return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
            
            # Generar reporte
            report_service = ReportService(company)
            report_buffer = report_service.generate_aging_report(report_date_obj, report_type, format_type)
            
            # Preparar respuesta
            report_name = 'cartera_cxc' if report_type == 'receivables' else 'cartera_cxp'
            
            if format_type == 'pdf':
                response = HttpResponse(report_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report_name}_{company.name}_{report_date}.pdf"'
            else:
                response = HttpResponse(report_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{report_name}_{company.name}_{report_date}.xlsx"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no soportado'}, status=405)


@login_required
def generate_general_ledger(request):
    """
    Generar Libro Mayor.
    """
    if request.method == 'GET':
        # Mostrar formulario
        companies = Company.objects.filter(is_active=True)
        
        context = {
            'companies': companies,
            'report_title': 'Libro Mayor',
            'report_description': 'Genere el libro mayor de una cuenta específica',
            'form_action': request.path,
            'date_fields': ['period_start', 'period_end'],
            'additional_fields': ['account_id'],
        }
        return render(request, 'reports/report_form.html', context)
        
    elif request.method == 'POST':
        company_id = request.POST.get('company_id')
        account_id = request.POST.get('account_id')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            company = get_object_or_404(Company, id=company_id)
            account = get_object_or_404(Account, id=account_id, chart_of_accounts__company=company)
            
            # Usar fechas por defecto si no se proporcionan
            current_date = timezone.now().date()
            if not period_start:
                period_start_date = current_date.replace(month=1, day=1)  # Inicio del año
            else:
                period_start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
                
            if not period_end:
                period_end_date = current_date
            else:
                period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Verificar permisos (superusuarios tienen acceso completo)
            if not request.user.is_superuser and not request.user.companies.filter(id=company_id).exists():
                return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
            
            # Generar reporte
            report_service = ReportService(company)
            report_buffer = report_service.generate_general_ledger(account_id, period_start_date, period_end_date, format_type)
            
            # Preparar respuesta
            if format_type == 'pdf':
                response = HttpResponse(report_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="mayor_{account.code}_{company.name}_{period_start}_{period_end}.pdf"'
            else:
                response = HttpResponse(report_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="mayor_{account.code}_{company.name}_{period_start}_{period_end}.xlsx"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no soportado'}, status=405)


@login_required
def get_company_accounts(request, company_id):
    """
    Obtener cuentas de una empresa para selección.
    """
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # Verificar permisos
        if not request.user.companies.filter(id=company_id).exists():
            return JsonResponse({'error': 'No tiene permisos para esta empresa'}, status=403)
        
        accounts = Account.objects.filter(
            chart_of_accounts__company=company,
            is_detail=True,
            is_active=True
        ).order_by('code')
        
        accounts_data = [
            {
                'id': str(account.id),
                'code': account.code,
                'name': account.name,
                'full_name': f"{account.code} - {account.name}"
            }
            for account in accounts
        ]
        
        return JsonResponse({'accounts': accounts_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)