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
from core.utils import get_current_company, require_company_access

from .models_employee import Employee, EmployeeType
from .models_payroll import PayrollPeriod, Payroll, PayrollConcept, PayrollDetail
from .models_healthcare import HealthcareRole, MedicalSpecialty, NursingSpecialty, EmployeeHealthcareProfile
from decimal import Decimal
from datetime import datetime, date


@login_required
@require_company_access
def payroll_dashboard(request):
    current_company = request.current_company

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
@require_company_access
def new_employee(request):
    current_company = request.current_company

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
                
                # Información de salud (solo para empresas del sector salud)
                healthcare_role_id = request.POST.get('healthcare_role')
                medical_specialty_id = request.POST.get('medical_specialty')
                nursing_specialty_id = request.POST.get('nursing_specialty')
                medical_license_number = request.POST.get('medical_license_number')
                medical_license_expiry = request.POST.get('medical_license_expiry')
                assigned_department = request.POST.get('assigned_department')
                years_experience = request.POST.get('years_experience')
                
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
                
                # Crear perfil de salud si la empresa es del sector salud y se proporcionaron datos
                if company.is_healthcare_company() and healthcare_role_id:
                    healthcare_role = HealthcareRole.objects.get(id=healthcare_role_id) if healthcare_role_id else None
                    medical_specialty = MedicalSpecialty.objects.get(id=medical_specialty_id) if medical_specialty_id else None
                    nursing_specialty = NursingSpecialty.objects.get(id=nursing_specialty_id) if nursing_specialty_id else None
                    
                    healthcare_profile = EmployeeHealthcareProfile.objects.create(
                        employee=employee,
                        healthcare_role=healthcare_role,
                        medical_specialty=medical_specialty,
                        nursing_specialty=nursing_specialty,
                        medical_license_number=medical_license_number or '',
                        medical_license_expiry=medical_license_expiry if medical_license_expiry else None,
                        assigned_department=assigned_department or '',
                        years_experience=int(years_experience) if years_experience else 0,
                        created_by=request.user
                    )
                    
                    messages.success(request, f'Empleado {employee.first_name} {employee.last_name} creado exitosamente con perfil de salud')
                else:
                    messages.success(request, f'Empleado {employee.first_name} {employee.last_name} creado exitosamente')
                
                return redirect('payroll:new_employee')
                
        except Exception as e:
            messages.error(request, f'Error al crear el empleado: {str(e)}')
    
    # Datos para el template
    context = {
        'current_company': current_company,
        'employee_types': EmployeeType.objects.filter(is_active=True),
        'is_healthcare_company': current_company.is_healthcare_company(),
        'healthcare_roles': HealthcareRole.objects.filter(is_active=True).order_by('category', 'name'),
        'medical_specialties': MedicalSpecialty.objects.filter(is_active=True, specialty_type='medica').order_by('category', 'name'),
        'nursing_specialties': NursingSpecialty.objects.filter(is_active=True).order_by('name'),
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
        if concept.code == 'SALARY':  # Salario básico proporcional
            daily_salary = employee.basic_salary / Decimal('30')
            return (daily_salary * Decimal(str(payroll.days_worked))).quantize(Decimal('0.01'))
        elif concept.code == 'TRANSPORT':  # Auxilio de transporte
            # Solo para salarios <= 2 SMMLV (2,600,000 en 2025)
            if employee.basic_salary <= Decimal('2600000'):
                daily_transport = Decimal('162000') / Decimal('30')  # Auxilio 2025
                return (daily_transport * Decimal(str(payroll.days_worked))).quantize(Decimal('0.01'))
            return Decimal('0')
        return concept.fixed_value
        
    elif concept.calculation_type == 'percentage':
        # Base para cálculo de seguridad social y prestaciones
        if concept.code in ['EPS_EMP', 'PENSION_EMP', 'EPS_EMP_PATRON', 'PENSION_PATRON', 'ARL']:
            # Salario base más otros devengos que afectan seguridad social
            daily_salary = employee.basic_salary / Decimal('30')
            base_salary_period = daily_salary * Decimal(str(payroll.days_worked))
            # El auxilio de transporte NO afecta la base de seguridad social
            base_amount = base_salary_period
        elif concept.code in ['SEVERANCE', 'SEVERANCE_INT', 'BONUS_PROV', 'VACATION_PROV']:
            # Prestaciones sociales se calculan sobre salario + auxilio
            daily_salary = employee.basic_salary / Decimal('30')
            base_salary_period = daily_salary * Decimal(str(payroll.days_worked))
            if employee.basic_salary <= Decimal('2600000'):
                daily_transport = Decimal('162000') / Decimal('30')
                transport_period = daily_transport * Decimal(str(payroll.days_worked))
                base_amount = base_salary_period + transport_period
            else:
                base_amount = base_salary_period
        elif concept.code == 'SOLIDARITY_FUND':
            # Solo para salarios > 4 SMMLV
            if employee.basic_salary > Decimal('5200000'):  # 4 * 1,300,000
                daily_salary = employee.basic_salary / Decimal('30')
                base_amount = daily_salary * Decimal(str(payroll.days_worked))
            else:
                return Decimal('0')
        elif concept.code in ['SENA', 'ICBF', 'CCF']:
            # Parafiscales: solo para empleados normales (no salario integral)
            if employee.employee_type.applies_parafiscals:
                daily_salary = employee.basic_salary / Decimal('30')
                base_amount = daily_salary * Decimal(str(payroll.days_worked))
            else:
                return Decimal('0')
        else:
            # Para otros conceptos porcentuales
            daily_salary = employee.basic_salary / Decimal('30')
            base_amount = daily_salary * Decimal(str(payroll.days_worked))
        
        return (base_amount * concept.percentage / Decimal('100')).quantize(Decimal('0.01'))
    
    elif concept.calculation_type == 'days':
        daily_salary = employee.basic_salary / Decimal('30')
        return (daily_salary * Decimal(str(payroll.days_worked))).quantize(Decimal('0.01'))
    
    elif concept.calculation_type == 'formula':
        # Para fórmulas complejas como retención en la fuente
        if concept.code == 'RETENTION':
            return calculate_income_tax_retention(employee, payroll)
        return concept.fixed_value
    
    return concept.fixed_value


def calculate_income_tax_retention(employee, payroll):
    """Calcular retención en la fuente según tabla DIAN 2025."""
    # Salario mensual equivalente
    monthly_salary = employee.basic_salary
    
    # Tabla simplificada retención fuente 2025 (empleados)
    # UVT 2025 = $47,065
    uvt_2025 = Decimal('47065')
    
    # Rangos en UVT
    if monthly_salary <= uvt_2025 * 95:  # Hasta 95 UVT
        return Decimal('0')
    elif monthly_salary <= uvt_2025 * 150:  # 95-150 UVT
        excess = monthly_salary - (uvt_2025 * 95)
        return (excess * Decimal('0.19')).quantize(Decimal('0.01'))
    elif monthly_salary <= uvt_2025 * 360:  # 150-360 UVT
        base = (uvt_2025 * 55) * Decimal('0.19')
        excess = monthly_salary - (uvt_2025 * 150)
        return (base + (excess * Decimal('0.28'))).quantize(Decimal('0.01'))
    else:  # Más de 360 UVT
        base1 = (uvt_2025 * 55) * Decimal('0.19')
        base2 = (uvt_2025 * 210) * Decimal('0.28')
        excess = monthly_salary - (uvt_2025 * 360)
        return (base1 + base2 + (excess * Decimal('0.33'))).quantize(Decimal('0.01'))


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
@require_company_access
def generate_pila(request):
    current_company = request.current_company

    """Vista para generar planilla PILA."""
    if request.method == 'POST':
        try:
            company_id = request.POST.get('company')
            period_id = request.POST.get('period')
            pila_type = request.POST.get('pila_type', 'N')
            
            company = Company.objects.get(id=company_id)
            period = PayrollPeriod.objects.get(id=period_id)
            
            # Generar archivo PILA
            pila_content = generate_pila_file(company, period, pila_type)
            
            # Crear respuesta con archivo
            from django.http import HttpResponse
            response = HttpResponse(pila_content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="PILA_{company.tax_id}_{period.start_date.strftime("%Y%m")}.txt"'
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar PILA: {str(e)}')
    
    companies = Company.objects.filter(is_active=True)
    periods = PayrollPeriod.objects.filter(status__in=['calculated', 'approved', 'paid']).order_by('-start_date')[:12]
    
    context = {
        'companies': companies,
        'periods': periods,
    }
    
    return render(request, 'payroll/pila.html', context)


def generate_pila_file(company, period, pila_type='N'):
    """Generar contenido del archivo PILA."""
    lines = []
    
    # Línea 1: Encabezado
    header = {
        'tipo_registro': '1',
        'formato': '03',  # Formato 03
        'nit_aportante': company.tax_id.replace('-', ''),
        'dv': company.tax_id[-1] if '-' in company.tax_id else '0',
        'razon_social': company.name[:200].ljust(200),
        'tipo_documento': '31',  # NIT
        'periodo_pago': period.start_date.strftime('%Y-%m-%d'),
        'fecha_pago': period.payment_date.strftime('%Y-%m-%d'),
        'numero_empleados': str(period.payrolls.count()).zfill(5),
        'tipo_planilla': pila_type,
        'fecha_matricula': company.created_at.strftime('%Y-%m-%d'),
        'clase_aportante': '01',  # Empleador
        'naturaleza_juridica': '16',  # Sociedad por acciones simplificada
        'tipo_persona': 'J',  # Jurídica
    }
    
    # Construir línea de encabezado (registro tipo 1)
    header_line = (
        header['tipo_registro'] +
        header['formato'] +
        header['nit_aportante'].zfill(16) +
        header['dv'] +
        header['razon_social'] +
        header['tipo_documento'] +
        header['periodo_pago'] +
        header['fecha_pago'] +
        header['numero_empleados'] +
        header['tipo_planilla'] +
        'A' +  # Forma de pago: A = Aportes
        header['fecha_matricula'] +
        header['clase_aportante'] +
        header['naturaleza_juridica'] +
        header['tipo_persona'] +
        '0' * 50  # Espacios en blanco
    )
    lines.append(header_line)
    
    # Líneas de detalle por empleado (registro tipo 2)
    payrolls = period.payrolls.filter(status__in=['calculated', 'approved']).select_related('employee')
    
    for payroll in payrolls:
        employee = payroll.employee
        
        # Calcular aportes
        salary_base = payroll.total_earnings - payroll.employee.transportation_allowance if hasattr(payroll, 'employee') else payroll.total_earnings
        
        # EPS
        eps_employee = salary_base * Decimal('0.04')  # 4%
        eps_employer = salary_base * Decimal('0.085')  # 8.5%
        
        # Pensión
        pension_employee = salary_base * Decimal('0.04')  # 4%
        pension_employer = salary_base * Decimal('0.12')  # 12%
        
        # ARL
        arl_employer = salary_base * Decimal('0.00522')  # 0.522% clase I
        
        # Parafiscales (solo si aplica)
        sena = salary_base * Decimal('0.02') if employee.employee_type.applies_parafiscals else Decimal('0')  # 2%
        icbf = salary_base * Decimal('0.03') if employee.employee_type.applies_parafiscals else Decimal('0')  # 3%
        ccf = salary_base * Decimal('0.04') if employee.employee_type.applies_parafiscals else Decimal('0')  # 4%
        
        detail = {
            'tipo_registro': '2',
            'secuencia': str(payrolls.filter(id__lte=payroll.id).count()).zfill(5),
            'tipo_documento': '13' if employee.document_type == 'CC' else '22',  # CC o CE
            'numero_documento': employee.document_number.zfill(16),
            'primer_apellido': employee.last_name.split()[0][:20].ljust(20) if employee.last_name else ''.ljust(20),
            'segundo_apellido': employee.last_name.split()[1][:30].ljust(30) if len(employee.last_name.split()) > 1 else ''.ljust(30),
            'primer_nombre': employee.first_name.split()[0][:20].ljust(20) if employee.first_name else ''.ljust(20),
            'segundo_nombre': employee.first_name.split()[1][:30].ljust(30) if len(employee.first_name.split()) > 1 else ''.ljust(30),
            'tipo_cotizante': '01',  # Empleado dependiente
            'subtipo_cotizante': '00',
            'extranjero': 'N',
            'colombiano_exterior': 'N',
            'departamento': '11',  # Bogotá por defecto
            'municipio': '001',  # Bogotá
            'tipo_salario': '01',  # Fijo
            'integral': 'N',
            'salario': str(int(employee.basic_salary)).zfill(9),
            'dias_cotizados': str(payroll.days_worked).zfill(2),
            
            # EPS
            'eps': employee.eps_code or 'EPS001',
            'aporte_eps_empleado': str(int(eps_employee)).zfill(9),
            'aporte_eps_empleador': str(int(eps_employer)).zfill(9),
            
            # Pensión
            'pension': employee.pension_fund_code or 'PEN001', 
            'aporte_pension_empleado': str(int(pension_employee)).zfill(9),
            'aporte_pension_empleador': str(int(pension_employer)).zfill(9),
            
            # ARL
            'arl': employee.arl_code or 'ARL001',
            'clase_riesgo': '1',
            'aporte_arl': str(int(arl_employer)).zfill(9),
            
            # CCF
            'ccf': employee.ccf_code or 'CCF001',
            'aporte_ccf': str(int(ccf)).zfill(9),
            'aporte_sena': str(int(sena)).zfill(9),
            'aporte_icbf': str(int(icbf)).zfill(9),
        }
        
        # Construir línea de detalle (registro tipo 2)
        detail_line = (
            detail['tipo_registro'] +
            detail['secuencia'] +
            detail['tipo_documento'] +
            detail['numero_documento'] +
            detail['primer_apellido'] +
            detail['segundo_apellido'] +
            detail['primer_nombre'] +
            detail['segundo_nombre'] +
            detail['tipo_cotizante'] +
            detail['subtipo_cotizante'] +
            detail['extranjero'] +
            detail['colombiano_exterior'] +
            detail['departamento'] +
            detail['municipio'] +
            detail['tipo_salario'] +
            detail['integral'] +
            detail['salario'] +
            detail['dias_cotizados'] +
            detail['eps'] +
            detail['aporte_eps_empleado'] +
            detail['aporte_eps_empleador'] +
            detail['pension'] +
            detail['aporte_pension_empleado'] +
            detail['aporte_pension_empleador'] +
            detail['arl'] +
            detail['clase_riesgo'] +
            detail['aporte_arl'] +
            detail['ccf'] +
            detail['aporte_ccf'] +
            detail['aporte_sena'] +
            detail['aporte_icbf'] +
            '0' * 50  # Campos adicionales en blanco
        )
        lines.append(detail_line)
    
    return '\n'.join(lines)


@login_required
@require_company_access
def payroll_reports(request):
    current_company = request.current_company

    """Vista para reportes de nómina."""
    companies = Company.objects.filter(is_active=True)
    periods = PayrollPeriod.objects.filter(status__in=['calculated', 'approved', 'paid']).order_by('-start_date')[:12]
    
    context = {
        'companies': companies,
        'periods': periods,
    }
    
    return render(request, 'payroll/reports.html', context)