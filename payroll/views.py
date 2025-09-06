"""
Vistas para el módulo de nómina.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models, transaction
from django.utils import timezone

from core.models import Company
from .models_employee import Employee, EmployeeType
from .models_payroll import PayrollPeriod, Payroll


@login_required
def payroll_dashboard(request):
    """
    Dashboard principal de nómina.
    """
    # Obtener empresas del usuario
    companies = Company.objects.filter(is_active=True)
    
    # Estadísticas generales
    total_employees = Employee.objects.filter(is_active=True).count()
    active_periods = PayrollPeriod.objects.filter(status__in=['open', 'calculated']).count()
    total_payroll = 0  # Aquí se calcularía el total de nómina
    pending_certificates = 0  # Certificados pendientes
    
    # Estadísticas por tipo de empleado
    employee_types_stats = []
    for emp_type in EmployeeType.objects.filter(is_active=True):
        count = Employee.objects.filter(employee_type=emp_type, is_active=True).count()
        if count > 0:
            avg_salary = Employee.objects.filter(
                employee_type=emp_type, 
                is_active=True
            ).aggregate(avg_salary=models.Avg('basic_salary'))['avg_salary'] or 0
            
            employee_types_stats.append({
                'name': emp_type.name,
                'count': count,
                'avg_salary': avg_salary
            })
    
    # Períodos recientes
    recent_payrolls = PayrollPeriod.objects.filter(
        status__in=['calculated', 'approved', 'paid']
    ).order_by('-created_at')[:5]
    
    context = {
        'companies': companies,
        'total_employees': total_employees,
        'active_periods': active_periods,
        'total_payroll': total_payroll,
        'pending_certificates': pending_certificates,
        'employee_types_stats': employee_types_stats,
        'recent_payrolls': recent_payrolls,
        'current_period': PayrollPeriod.objects.filter(status='open').first(),
    }
    
    return render(request, 'payroll/dashboard.html', context)


@login_required
def new_employee(request):
    """Vista para crear nuevo empleado."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos básicos
                company_id = request.POST.get('company')
                employee_number = request.POST.get('employee_number')
                document_type = request.POST.get('document_type')
                document_number = request.POST.get('document_number')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                birth_date = request.POST.get('birth_date')
                gender = request.POST.get('gender')
                marital_status = request.POST.get('marital_status')
                
                # Contacto
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                city = request.POST.get('city')
                
                # Información laboral
                employee_type_id = request.POST.get('employee_type')
                hire_date = request.POST.get('hire_date')
                contract_type = request.POST.get('contract_type')
                basic_salary = request.POST.get('basic_salary')
                
                # Seguridad social
                eps = request.POST.get('eps')
                pension_fund = request.POST.get('pension_fund')
                arl = request.POST.get('arl')
                ccf = request.POST.get('ccf')
                
                # Información bancaria
                bank_name = request.POST.get('bank_name')
                account_type = request.POST.get('account_type')
                account_number = request.POST.get('account_number')
                
                company = Company.objects.get(id=company_id)
                employee_type = EmployeeType.objects.get(id=employee_type_id) if employee_type_id else None
                
                # Crear el empleado
                employee = Employee.objects.create(
                    company=company,
                    employee_number=employee_number,
                    employee_type=employee_type,
                    document_type=document_type,
                    document_number=document_number,
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    gender=gender,
                    marital_status=marital_status,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    hire_date=hire_date,
                    contract_type=contract_type,
                    basic_salary=float(basic_salary) if basic_salary else 0,
                    eps=eps,
                    pension_fund=pension_fund,
                    arl=arl,
                    ccf=ccf,
                    bank_name=bank_name,
                    account_type=account_type,
                    account_number=account_number,
                    created_by=request.user
                )
                
                messages.success(request, f'Empleado {employee.first_name} {employee.last_name} creado exitosamente')
                return redirect('payroll:new_employee')
                
        except Exception as e:
            messages.error(request, f'Error al crear el empleado: {str(e)}')
    
    # Datos para el template
    context = {
        'companies': Company.objects.filter(is_active=True),
        'employee_types': EmployeeType.objects.filter(is_active=True),
    }
    
    return render(request, 'payroll/new_employee.html', context)