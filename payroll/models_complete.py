"""
Modelos completos para el Sistema de Nómina Colombiano
Incluye: Nómina Electrónica, Liquidaciones, Prestaciones Sociales, Seguridad Social
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from core.models import Company, User
from accounting.models import JournalEntry, ChartOfAccounts


class PayrollConfiguration(models.Model):
    """Configuración general de nómina por empresa"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_configs')
    
    # Salarios mínimos y auxilio de transporte
    minimum_wage = models.DecimalField(max_digits=12, decimal_places=2, default=1300000)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=162000)
    transport_allowance_limit = models.DecimalField(max_digits=12, decimal_places=2, default=2600000)
    
    # Porcentajes de seguridad social - Empleador
    health_employer = models.DecimalField(max_digits=5, decimal_places=2, default=8.5)
    pension_employer = models.DecimalField(max_digits=5, decimal_places=2, default=12)
    arl_employer = models.DecimalField(max_digits=5, decimal_places=2, default=0.522)
    
    # Porcentajes de seguridad social - Empleado
    health_employee = models.DecimalField(max_digits=5, decimal_places=2, default=4)
    pension_employee = models.DecimalField(max_digits=5, decimal_places=2, default=4)
    
    # Porcentajes parafiscales
    sena = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    icbf = models.DecimalField(max_digits=5, decimal_places=2, default=3)
    ccf = models.DecimalField(max_digits=5, decimal_places=2, default=4)
    
    # Prestaciones sociales
    cesantias = models.DecimalField(max_digits=5, decimal_places=2, default=8.33)
    intereses_cesantias = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    prima = models.DecimalField(max_digits=5, decimal_places=2, default=8.33)
    vacaciones = models.DecimalField(max_digits=5, decimal_places=2, default=4.17)
    
    # Cuentas contables
    wages_account = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, related_name='payroll_wages')
    health_payable_account = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, related_name='payroll_health')
    pension_payable_account = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, related_name='payroll_pension')
    
    year = models.IntegerField(default=2025)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['company', 'year']]
    
    def __str__(self):
        return f"Config Nómina {self.company.name} - {self.year}"


class ARLRiskClass(models.Model):
    """Clases de Riesgo ARL según Decreto 1772 de 1994"""
    RISK_CLASSES = [
        (1, 'Clase I - Riesgo Mínimo'),
        (2, 'Clase II - Riesgo Bajo'),
        (3, 'Clase III - Riesgo Medio'),
        (4, 'Clase IV - Riesgo Alto'),
        (5, 'Clase V - Riesgo Máximo')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    risk_class = models.IntegerField(choices=RISK_CLASSES)
    percentage = models.DecimalField(max_digits=5, decimal_places=3)
    description = models.CharField(max_length=200)
    
    class Meta:
        unique_together = [['company', 'risk_class']]
    
    def __str__(self):
        return f"Clase {self.risk_class} - {self.percentage}%"


class ContractType(models.Model):
    """Tipos de contrato laboral"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    has_benefits = models.BooleanField(default=True)  # Prestaciones sociales
    has_social_security = models.BooleanField(default=True)  # Seguridad social
    is_integral_salary = models.BooleanField(default=False)  # Salario integral
    
    class Meta:
        unique_together = [['company', 'code']]
    
    def __str__(self):
        return self.name


class EmployeeComplete(models.Model):
    """Modelo completo de empleado con toda la información colombiana"""
    DOCUMENT_TYPES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad')
    ]
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro')
    ]
    
    MARITAL_STATUS = [
        ('S', 'Soltero'),
        ('C', 'Casado'),
        ('D', 'Divorciado'),
        ('V', 'Viudo'),
        ('U', 'Unión Libre')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees_complete')
    
    # Información personal
    document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPES, default='CC')
    document_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS)
    
    # Información de contacto
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20)
    email = models.EmailField()
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)
    
    # Información laboral
    employee_code = models.CharField(max_length=20, unique=True)
    contract_type = models.ForeignKey(ContractType, on_delete=models.PROTECT)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Información salarial
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    has_transport_allowance = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('BANK', 'Transferencia Bancaria'),
        ('CHECK', 'Cheque'),
        ('CASH', 'Efectivo')
    ], default='BANK')
    
    # Información bancaria
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_type = models.CharField(max_length=20, choices=[
        ('SAVINGS', 'Ahorros'),
        ('CHECKING', 'Corriente')
    ], blank=True)
    bank_account_number = models.CharField(max_length=30, blank=True)
    
    # Seguridad Social
    eps_name = models.CharField(max_length=100)
    eps_code = models.CharField(max_length=20)
    pension_fund = models.CharField(max_length=100)
    pension_fund_code = models.CharField(max_length=20)
    arl_name = models.CharField(max_length=100)
    arl_risk_class = models.ForeignKey(ARLRiskClass, on_delete=models.PROTECT)
    ccf_name = models.CharField(max_length=100)  # Caja de Compensación Familiar
    
    # Cesantías
    cesantias_fund = models.CharField(max_length=100)
    
    # Estados
    is_active = models.BooleanField(default=True)
    retirement_date = models.DateField(null=True, blank=True)
    retirement_reason = models.CharField(max_length=200, blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_employees_complete')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.employee_code} - {self.get_full_name()}"
    
    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.second_last_name]
        return ' '.join(filter(None, parts))
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def years_of_service(self):
        end_date = self.retirement_date or date.today()
        years = (end_date - self.hire_date).days / 365.25
        return round(years, 2)


class PayrollPeriodComplete(models.Model):
    """Período de nómina mejorado"""
    PERIOD_TYPES = [
        ('WEEKLY', 'Semanal'),
        ('BIWEEKLY', 'Quincenal'),
        ('MONTHLY', 'Mensual')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_periods_complete')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default='BIWEEKLY')
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    period_number = models.IntegerField()  # 1 o 2 para quincenal, 1 para mensual
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    
    is_processed = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['company', 'year', 'month', 'period_number']]
        ordering = ['-year', '-month', '-period_number']
    
    def __str__(self):
        return f"Período {self.year}-{self.month:02d}-{self.period_number}"


class PayrollComplete(models.Model):
    """Nómina completa con todos los cálculos colombianos"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payrolls_complete')
    period = models.ForeignKey(PayrollPeriodComplete, on_delete=models.CASCADE, related_name='payrolls')
    employee = models.ForeignKey(EmployeeComplete, on_delete=models.CASCADE, related_name='payrolls')
    
    # Días trabajados
    days_worked = models.IntegerField(default=15)
    sundays_worked = models.IntegerField(default=0)
    holidays_worked = models.IntegerField(default=0)
    
    # Horas extras
    ordinary_overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 25%
    night_overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 75%
    sunday_ordinary_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 75%
    sunday_overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 110%
    holiday_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 175%
    
    # Devengados
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ordinary_overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    night_overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sunday_ordinary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sunday_overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    holiday_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Otros devengados
    commissions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total devengado
    total_earned = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Deducciones - Seguridad Social Empleado
    health_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solidarity_fund = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Fondo de solidaridad pensional
    
    # Otras deducciones
    loans = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    food_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    judicial_withholding = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retention_source = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total deducciones y neto
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Aportes patronales (no se descuentan al empleado)
    employer_health = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_pension = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_arl = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Parafiscales
    sena_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    icbf_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ccf_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Provisiones prestaciones sociales
    cesantias_provision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    intereses_cesantias_provision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prima_provision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vacaciones_provision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Contabilización
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Estados
    is_approved = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_payrolls_complete')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls_complete')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['period', 'employee']]
        ordering = ['-period__year', '-period__month', 'employee__last_name']
    
    def __str__(self):
        return f"Nómina {self.employee.get_full_name()} - {self.period}"
    
    def calculate_payroll(self):
        """Calcula todos los valores de la nómina"""
        config = PayrollConfiguration.objects.get(company=self.company, year=self.period.year)
        
        # Calcular salario base proporcional
        daily_salary = self.employee.base_salary / 30
        self.base_salary = daily_salary * self.days_worked
        
        # Auxilio de transporte (si aplica)
        if self.employee.has_transport_allowance and self.employee.base_salary <= config.transport_allowance_limit:
            daily_transport = config.transport_allowance / 30
            self.transport_allowance = daily_transport * self.days_worked
        
        # Calcular horas extras
        hourly_rate = self.employee.base_salary / 240  # 240 horas al mes
        self.ordinary_overtime = hourly_rate * Decimal('1.25') * self.ordinary_overtime_hours
        self.night_overtime = hourly_rate * Decimal('1.75') * self.night_overtime_hours
        self.sunday_ordinary = hourly_rate * Decimal('1.75') * self.sunday_ordinary_hours
        self.sunday_overtime = hourly_rate * Decimal('2.10') * self.sunday_overtime_hours
        self.holiday_payment = hourly_rate * Decimal('2.75') * self.holiday_hours
        
        # Total devengado
        self.total_earned = (
            self.base_salary + self.transport_allowance +
            self.ordinary_overtime + self.night_overtime +
            self.sunday_ordinary + self.sunday_overtime +
            self.holiday_payment + self.commissions +
            self.bonuses + self.other_income
        )
        
        # Base para seguridad social (sin auxilio de transporte)
        ss_base = self.total_earned - self.transport_allowance
        
        # Deducciones seguridad social empleado
        self.health_deduction = ss_base * (config.health_employee / 100)
        self.pension_deduction = ss_base * (config.pension_employee / 100)
        
        # Fondo de solidaridad (si aplica - salarios > 4 SMMLV)
        if self.employee.base_salary > (config.minimum_wage * 4):
            self.solidarity_fund = ss_base * Decimal('0.01')  # 1%
        
        # Total deducciones
        self.total_deductions = (
            self.health_deduction + self.pension_deduction +
            self.solidarity_fund + self.loans + self.food_deduction +
            self.judicial_withholding + self.retention_source +
            self.other_deductions
        )
        
        # Neto a pagar
        self.net_pay = self.total_earned - self.total_deductions
        
        # Aportes patronales
        self.employer_health = ss_base * (config.health_employer / 100)
        self.employer_pension = ss_base * (config.pension_employer / 100)
        self.employer_arl = ss_base * (self.employee.arl_risk_class.percentage / 100)
        
        # Parafiscales (si aplica - no para salario integral)
        if not self.employee.contract_type.is_integral_salary:
            self.sena_contribution = ss_base * (config.sena / 100)
            self.icbf_contribution = ss_base * (config.icbf / 100)
            self.ccf_contribution = ss_base * (config.ccf / 100)
        
        # Provisiones prestaciones sociales
        provision_base = self.total_earned
        self.cesantias_provision = provision_base * (config.cesantias / 100)
        self.intereses_cesantias_provision = provision_base * (config.intereses_cesantias / 100)
        self.prima_provision = provision_base * (config.prima / 100)
        self.vacaciones_provision = self.base_salary * (config.vacaciones / 100)
        
        self.save()


class Liquidation(models.Model):
    """Liquidación de contrato laboral"""
    LIQUIDATION_TYPES = [
        ('RESIGNATION', 'Renuncia Voluntaria'),
        ('DISMISSAL_JUST', 'Despido con Justa Causa'),
        ('DISMISSAL_UNJUST', 'Despido sin Justa Causa'),
        ('CONTRACT_END', 'Terminación de Contrato'),
        ('MUTUAL', 'Mutuo Acuerdo'),
        ('RETIREMENT', 'Jubilación'),
        ('DEATH', 'Muerte del Trabajador')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='liquidations')
    employee = models.ForeignKey(EmployeeComplete, on_delete=models.CASCADE, related_name='liquidations')
    liquidation_type = models.CharField(max_length=20, choices=LIQUIDATION_TYPES)
    termination_date = models.DateField()
    
    # Días a liquidar
    days_worked_current_year = models.IntegerField()
    vacation_days_pending = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Salario base de liquidación
    average_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Conceptos de liquidación
    salary_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cesantías
    cesantias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    intereses_cesantias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Prima
    prima = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Vacaciones
    vacaciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Indemnización (si aplica)
    indemnizacion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Bonificaciones
    bonificacion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deducciones
    loans_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Totales
    total_to_receive = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_payment = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Pago
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, blank=True)
    
    # Contabilización
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Documentos
    settlement_letter_generated = models.BooleanField(default=False)
    paz_y_salvo_generated = models.BooleanField(default=False)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_liquidations')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_liquidations')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    observations = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-termination_date']
    
    def __str__(self):
        return f"Liquidación {self.employee.get_full_name()} - {self.termination_date}"
    
    def calculate_liquidation(self):
        """Calcula todos los valores de la liquidación"""
        config = PayrollConfiguration.objects.get(
            company=self.company,
            year=self.termination_date.year
        )
        
        # Calcular días trabajados en el año
        year_start = date(self.termination_date.year, 1, 1)
        start_date = max(self.employee.hire_date, year_start)
        self.days_worked_current_year = (self.termination_date - start_date).days + 1
        
        # Calcular salario promedio (último año o fracción)
        # Aquí deberías calcular el promedio real de los últimos 12 meses
        self.average_salary = self.employee.base_salary
        
        # Cesantías: (Salario * Días trabajados) / 360
        self.cesantias = (self.average_salary * self.days_worked_current_year) / 360
        
        # Intereses de cesantías: (Cesantías * Días trabajados * 0.12) / 360
        self.intereses_cesantias = (self.cesantias * self.days_worked_current_year * Decimal('0.12')) / 360
        
        # Prima: (Salario * Días trabajados del semestre) / 360
        if self.termination_date.month <= 6:
            prima_days = self.days_worked_current_year
        else:
            july_first = date(self.termination_date.year, 7, 1)
            prima_days = (self.termination_date - july_first).days + 1
        self.prima = (self.average_salary * prima_days) / 360
        
        # Vacaciones: (Salario * Días pendientes) / 720
        years_worked = self.employee.years_of_service
        vacation_days_earned = years_worked * 15
        vacation_days_taken = 0  # Aquí deberías obtener los días ya tomados
        self.vacation_days_pending = vacation_days_earned - vacation_days_taken
        self.vacaciones = (self.average_salary * self.vacation_days_pending) / 30
        
        # Indemnización (si aplica - despido sin justa causa)
        if self.liquidation_type == 'DISMISSAL_UNJUST':
            self.calculate_indemnization()
        
        # Calcular totales
        self.total_to_receive = (
            self.salary_pending + self.cesantias + 
            self.intereses_cesantias + self.prima + 
            self.vacaciones + self.indemnizacion + 
            self.bonificacion
        )
        
        self.total_deductions = self.loans_pending + self.other_deductions
        self.net_payment = self.total_to_receive - self.total_deductions
        
        self.save()
    
    def calculate_indemnizacion(self):
        """Calcula la indemnización por despido sin justa causa"""
        years = self.employee.years_of_service
        salary = self.average_salary
        
        # Según el Código Sustantivo del Trabajo
        if salary < (10 * PayrollConfiguration.objects.get(
            company=self.company,
            year=self.termination_date.year
        ).minimum_wage):
            # Salarios menores a 10 SMMLV
            if years <= 1:
                self.indemnizacion = salary
            else:
                self.indemnizacion = salary + (salary * Decimal('0.65') * (years - 1))
        else:
            # Salarios mayores a 10 SMMLV
            if years <= 1:
                self.indemnizacion = salary * Decimal('0.67')
            else:
                self.indemnizacion = (salary * Decimal('0.67')) + (salary * Decimal('0.33') * (years - 1))


class ElectronicPayroll(models.Model):
    """Nómina Electrónica según Resolución DIAN 000013 de 2021"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='electronic_payrolls')
    payroll = models.OneToOneField(PayrollComplete, on_delete=models.CASCADE, related_name='electronic_payroll')
    
    # Numeración
    prefix = models.CharField(max_length=10)
    consecutive = models.IntegerField()
    cune = models.CharField(max_length=96, unique=True)  # Código Único de Nómina Electrónica
    
    # Fechas
    generation_date = models.DateTimeField()
    issue_date = models.DateField()
    
    # Información XML
    xml_content = models.TextField()
    xml_signed = models.TextField(blank=True)
    qr_code = models.TextField(blank=True)
    
    # Estado DIAN
    dian_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('ACCEPTED', 'Aceptado'),
        ('REJECTED', 'Rechazado'),
        ('ERROR', 'Error')
    ], default='PENDING')
    
    dian_response = models.TextField(blank=True)
    dian_tracking_id = models.CharField(max_length=100, blank=True)
    
    # Envío al trabajador
    sent_to_employee = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    employee_email = models.EmailField(blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['company', 'prefix', 'consecutive']]
        ordering = ['-issue_date', '-consecutive']
    
    def __str__(self):
        return f"NE{self.prefix}-{self.consecutive}"
    
    def generate_cune(self):
        """Genera el CUNE según especificaciones DIAN"""
        import hashlib
        
        # Formato: NumNE + FecNE + HorNE + ValNE + NitEmp + DocEmp + TipoXML + SoftwarePin
        data = f"{self.prefix}{self.consecutive}{self.issue_date}{self.payroll.net_pay}"
        data += f"{self.company.nit}{self.payroll.employee.document_number}"
        
        # Generar SHA-384
        hash_object = hashlib.sha384(data.encode())
        self.cune = hash_object.hexdigest()
        
        return self.cune