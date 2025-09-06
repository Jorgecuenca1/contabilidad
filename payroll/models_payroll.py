"""
Modelos de nómina y conceptos.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date

from core.models import Company, User
from accounting.models_accounts import Account
from .models_employee import Employee


class PayrollConcept(models.Model):
    """
    Conceptos de nómina (devengos, deducciones, aportes patronales).
    """
    CONCEPT_TYPE_CHOICES = [
        ('earning', 'Devengo'),
        ('deduction', 'Deducción'),
        ('employer_contribution', 'Aporte Patronal'),
        ('provision', 'Provisión'),
    ]
    
    CALCULATION_TYPE_CHOICES = [
        ('fixed', 'Valor Fijo'),
        ('percentage', 'Porcentaje'),
        ('formula', 'Fórmula'),
        ('days', 'Por Días'),
        ('hours', 'Por Horas'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_concepts')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    concept_type = models.CharField(max_length=30, choices=CONCEPT_TYPE_CHOICES)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPE_CHOICES)
    
    # Configuración de cálculo
    percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0, help_text="Porcentaje para cálculo")
    fixed_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Valor fijo")
    formula = models.TextField(blank=True, help_text="Fórmula de cálculo")
    
    # Configuración contable
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True)
    
    # Configuración de seguridad social
    affects_social_security = models.BooleanField(default=False)
    affects_parafiscals = models.BooleanField(default=False)
    affects_labor_benefits = models.BooleanField(default=False)
    affects_income_tax = models.BooleanField(default=False)
    
    # Configuración de reportes
    show_in_payslip = models.BooleanField(default=True)
    show_in_certificate = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_concepts'
        verbose_name = 'Concepto de Nómina'
        verbose_name_plural = 'Conceptos de Nómina'
        unique_together = ['company', 'code']
        ordering = ['concept_type', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class PayrollPeriod(models.Model):
    """
    Período de nómina (quincenal, mensual).
    """
    PERIOD_TYPE_CHOICES = [
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('weekly', 'Semanal'),
        ('daily', 'Diario'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('calculated', 'Calculado'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
        ('closed', 'Cerrado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_periods')
    
    name = models.CharField(max_length=100)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    
    # Control de estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    calculated_at = models.DateTimeField(null=True, blank=True)
    calculated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='payroll_periods_calculated')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='payroll_periods_approved')
    
    # Totales
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_employer_contributions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_periods'
        verbose_name = 'Período de Nómina'
        verbose_name_plural = 'Períodos de Nómina'
        unique_together = ['company', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class Payroll(models.Model):
    """
    Nómina individual de un empleado en un período.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('calculated', 'Calculado'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payrolls')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    
    # Información del período
    days_worked = models.IntegerField(default=30)
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Totales
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_employer_contributions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Auditoría
    calculated_at = models.DateTimeField(null=True, blank=True)
    calculated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='payrolls_calculated')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='payrolls_approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_payrolls'
        verbose_name = 'Nómina'
        verbose_name_plural = 'Nóminas'
        unique_together = ['payroll_period', 'employee']
        ordering = ['employee__employee_code']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.payroll_period.name}"


class PayrollDetail(models.Model):
    """
    Detalle de conceptos aplicados en una nómina.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='details')
    concept = models.ForeignKey(PayrollConcept, on_delete=models.PROTECT)
    
    # Valores de cálculo
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Información adicional
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_details'
        verbose_name = 'Detalle de Nómina'
        verbose_name_plural = 'Detalles de Nómina'
        unique_together = ['payroll', 'concept']
    
    def __str__(self):
        return f"{self.payroll} - {self.concept.name}: {self.amount}"


class LaborBenefit(models.Model):
    """
    Prestaciones sociales (cesantías, intereses, prima, vacaciones).
    """
    BENEFIT_TYPE_CHOICES = [
        ('severance', 'Cesantías'),
        ('severance_interest', 'Intereses sobre Cesantías'),
        ('bonus', 'Prima de Servicios'),
        ('vacation', 'Vacaciones'),
    ]
    
    STATUS_CHOICES = [
        ('accrued', 'Causado'),
        ('paid', 'Pagado'),
        ('compensated', 'Compensado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='labor_benefits')
    
    benefit_type = models.CharField(max_length=30, choices=BENEFIT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Cálculo
    base_salary = models.DecimalField(max_digits=15, decimal_places=2)
    days = models.IntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accrued')
    payment_date = models.DateField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_labor_benefits'
        verbose_name = 'Prestación Social'
        verbose_name_plural = 'Prestaciones Sociales'
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_benefit_type_display()}: {self.amount}"




