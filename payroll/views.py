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
from .models_payroll import PayrollPeriod, Payroll, PayrollConcept, PayrollDetail
from decimal import Decimal
from datetime import datetime, date


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
                    employee_code=employee_number,
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
                    mobile=phone,
                    address=address,
                    city=city,
                    state='Colombia',
                    hire_date=hire_date,
                    contract_type=contract_type,
                    salary_type='fixed',
                    position='Empleado',
                    basic_salary=float(basic_salary) if basic_salary else 0,
                    eps_name=eps,
                    pension_fund_name=pension_fund,
                    arl_name=arl,
                    ccf_name=ccf,
                    bank_name=bank_name,
                    account_type=account_type,
                    bank_account=account_number,
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


@login_required
def liquidate_payroll(request, period_id=None):
    """Vista para liquidar nómina."""
    companies = Company.objects.filter(is_active=True)
    
    if period_id:
        try:
            period = PayrollPeriod.objects.get(id=period_id)
        except PayrollPeriod.DoesNotExist:
            messages.error(request, 'Período de nómina no encontrado')
            return redirect('payroll:dashboard')
    else:
        period = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_period':
            try:
                with transaction.atomic():
                    company_id = request.POST.get('company')
                    name = request.POST.get('name')
                    period_type = request.POST.get('period_type')
                    start_date = request.POST.get('start_date')
                    end_date = request.POST.get('end_date')
                    payment_date = request.POST.get('payment_date')
                    
                    company = Company.objects.get(id=company_id)
                    
                    period = PayrollPeriod.objects.create(
                        company=company,
                        name=name,
                        period_type=period_type,
                        start_date=start_date,
                        end_date=end_date,
                        payment_date=payment_date,
                        created_by=request.user
                    )
                    
                    messages.success(request, f'Período {period.name} creado exitosamente')
                    return redirect('payroll:liquidate_payroll', period_id=period.id)
                    
            except Exception as e:
                messages.error(request, f'Error al crear período: {str(e)}')
        
        elif action == 'calculate_payroll' and period:
            try:
                with transaction.atomic():
                    calculate_payroll_for_period(period, request.user)
                    messages.success(request, f'Nómina calculada para el período {period.name}')
                    
            except Exception as e:
                messages.error(request, f'Error al calcular nómina: {str(e)}')
        
        elif action == 'approve_payroll' and period:
            try:
                with transaction.atomic():
                    period.status = 'approved'
                    period.approved_at = timezone.now()
                    period.approved_by = request.user
                    period.save()
                    
                    # Aprobar todas las nóminas del período
                    period.payrolls.update(status='approved')
                    
                    messages.success(request, f'Nómina del período {period.name} aprobada')
                    
            except Exception as e:
                messages.error(request, f'Error al aprobar nómina: {str(e)}')
    
    # Obtener períodos disponibles
    periods = PayrollPeriod.objects.filter(company__is_active=True).order_by('-start_date')[:10]
    
    # Si hay un período seleccionado, obtener las nóminas
    payrolls = []
    if period:
        payrolls = Payroll.objects.filter(payroll_period=period).select_related('employee')
    
    context = {
        'companies': companies,
        'periods': periods,
        'current_period': period,
        'payrolls': payrolls,
    }
    
    return render(request, 'payroll/liquidate.html', context)


def calculate_payroll_for_period(period, user):
    """Calcular nómina para todos los empleados activos del período."""
    employees = Employee.objects.filter(
        company=period.company,
        is_active=True,
        status='active'
    )
    
    # Obtener conceptos de nómina activos
    concepts = PayrollConcept.objects.filter(
        company=period.company,
        is_active=True
    )
    
    total_earnings = Decimal('0')
    total_deductions = Decimal('0')
    total_contributions = Decimal('0')
    total_net = Decimal('0')
    
    for employee in employees:
        # Crear o actualizar nómina del empleado
        payroll, created = Payroll.objects.get_or_create(
            payroll_period=period,
            employee=employee,
            defaults={
                'company': period.company,
                'days_worked': 30,  # Valor por defecto
                'created_by': user
            }
        )
        
        # Limpiar detalles existentes si se está recalculando
        if not created:
            payroll.details.all().delete()
        
        payroll_earnings = Decimal('0')
        payroll_deductions = Decimal('0')
        payroll_contributions = Decimal('0')
        
        # Calcular conceptos
        for concept in concepts:
            amount = calculate_concept_amount(concept, employee, payroll)
            
            if amount > 0:
                PayrollDetail.objects.create(
                    payroll=payroll,
                    concept=concept,
                    quantity=1,
                    rate=amount,
                    amount=amount
                )
                
                if concept.concept_type == 'earning':
                    payroll_earnings += amount
                elif concept.concept_type == 'deduction':
                    payroll_deductions += amount
                elif concept.concept_type == 'employer_contribution':
                    payroll_contributions += amount
        
        # Actualizar totales de la nómina
        payroll.total_earnings = payroll_earnings
        payroll.total_deductions = payroll_deductions
        payroll.total_employer_contributions = payroll_contributions
        payroll.net_pay = payroll_earnings - payroll_deductions
        payroll.status = 'calculated'
        payroll.calculated_at = timezone.now()
        payroll.calculated_by = user
        payroll.save()
        
        # Sumar a los totales del período
        total_earnings += payroll_earnings
        total_deductions += payroll_deductions
        total_contributions += payroll_contributions
        total_net += payroll.net_pay
    
    # Actualizar totales del período
    period.total_earnings = total_earnings
    period.total_deductions = total_deductions
    period.total_employer_contributions = total_contributions
    period.total_net_pay = total_net
    period.status = 'calculated'
    period.calculated_at = timezone.now()
    period.calculated_by = user
    period.save()


def calculate_concept_amount(concept, employee, payroll):
    """Calcular el monto de un concepto para un empleado específico."""
    base_amount = Decimal('0')
    
    if concept.calculation_type == 'fixed':
        return concept.fixed_value
        
    elif concept.calculation_type == 'percentage':
        if concept.code == 'SALARY':  # Salario básico
            base_amount = employee.basic_salary
        elif concept.code == 'TRANSPORT':  # Auxilio de transporte
            base_amount = employee.transportation_allowance
        else:
            # Para otros conceptos, usar el salario básico como base
            base_amount = employee.basic_salary
        
        return (base_amount * concept.percentage / Decimal('100')).quantize(Decimal('0.01'))
    
    elif concept.calculation_type == 'days':
        daily_salary = employee.basic_salary / Decimal('30')
        return (daily_salary * Decimal(str(payroll.days_worked))).quantize(Decimal('0.01'))
    
    # Para conceptos más complejos, se podría implementar una fórmula
    return concept.fixed_value


@login_required
def generate_certificate(request, employee_id=None):
    """Vista para generar certificado de ingresos."""
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
        except Employee.DoesNotExist:
            messages.error(request, 'Empleado no encontrado')
            return redirect('payroll:dashboard')
    else:
        employee = None
    
    employees = Employee.objects.filter(is_active=True).order_by('employee_code')
    
    context = {
        'employee': employee,
        'employees': employees,
    }
    
    return render(request, 'payroll/certificate.html', context)


@login_required
def final_liquidation(request, employee_id=None):
    """Vista para liquidación final de empleados."""
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
        except Employee.DoesNotExist:
            messages.error(request, 'Empleado no encontrado')
            return redirect('payroll:dashboard')
    else:
        employee = None
    
    employees = Employee.objects.filter(is_active=True, status='active').order_by('employee_code')
    
    context = {
        'employee': employee,
        'employees': employees,
    }
    
    return render(request, 'payroll/final_liquidation.html', context)


@login_required
def generate_pila(request):
    """Vista para generar planilla PILA."""
    companies = Company.objects.filter(is_active=True)
    periods = PayrollPeriod.objects.filter(status__in=['calculated', 'approved', 'paid']).order_by('-start_date')[:12]
    
    context = {
        'companies': companies,
        'periods': periods,
    }
    
    return render(request, 'payroll/pila.html', context)


@login_required
def payroll_reports(request):
    """Vista para reportes de nómina."""
    companies = Company.objects.filter(is_active=True)
    periods = PayrollPeriod.objects.filter(status__in=['calculated', 'approved', 'paid']).order_by('-start_date')[:12]
    
    context = {
        'companies': companies,
        'periods': periods,
    }
    
    return render(request, 'payroll/reports.html', context)