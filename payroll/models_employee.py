"""
Modelos de empleados para el sistema de nómina.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date

from core.models import Company, User
from accounting.models_accounts import CostCenter


class EmployeeType(models.Model):
    """
    Tipos de empleado (Empleado, Contratista, Aprendiz, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employee_types')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración de nómina
    applies_social_security = models.BooleanField(default=True, help_text="Aplica seguridad social")
    applies_parafiscals = models.BooleanField(default=True, help_text="Aplica parafiscales")
    applies_labor_benefits = models.BooleanField(default=True, help_text="Aplica prestaciones sociales")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_employee_types'
        verbose_name = 'Tipo de Empleado'
        verbose_name_plural = 'Tipos de Empleado'
        unique_together = ['company', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """
    Empleado con toda la información requerida por la legislación colombiana.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('PP', 'Pasaporte'),
        ('NIT', 'NIT'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('divorced', 'Divorciado(a)'),
        ('widowed', 'Viudo(a)'),
        ('union', 'Unión Libre'),
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('indefinite', 'Término Indefinido'),
        ('fixed', 'Término Fijo'),
        ('labor', 'Obra o Labor'),
        ('apprentice', 'Aprendizaje'),
        ('internship', 'Práctica'),
        ('services', 'Prestación de Servicios'),
    ]
    
    SALARY_TYPE_CHOICES = [
        ('fixed', 'Salario Fijo'),
        ('variable', 'Salario Variable'),
        ('integral', 'Salario Integral'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('vacation', 'Vacaciones'),
        ('medical_leave', 'Incapacidad'),
        ('maternity_leave', 'Licencia de Maternidad'),
        ('suspended', 'Suspendido'),
        ('terminated', 'Retirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.PROTECT)
    
    # Información personal
    employee_code = models.CharField(max_length=20)
    document_type = models.CharField(max_length=3, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    
    # Contacto
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    
    # Información laboral
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    position = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True)
    
    # Información salarial
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES)
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    transportation_allowance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_fixed_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Seguridad social
    eps_code = models.CharField(max_length=10, blank=True, help_text="Código EPS")
    eps_name = models.CharField(max_length=200, blank=True, help_text="Nombre EPS")
    pension_fund_code = models.CharField(max_length=10, blank=True, help_text="Código Fondo de Pensiones")
    pension_fund_name = models.CharField(max_length=200, blank=True, help_text="Nombre Fondo de Pensiones")
    arl_code = models.CharField(max_length=10, blank=True, help_text="Código ARL")
    arl_name = models.CharField(max_length=200, blank=True, help_text="Nombre ARL")
    ccf_code = models.CharField(max_length=10, blank=True, help_text="Código CCF")
    ccf_name = models.CharField(max_length=200, blank=True, help_text="Nombre CCF")
    
    # Configuración de nómina
    bank_account = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    account_type = models.CharField(max_length=20, blank=True, choices=[
        ('savings', 'Ahorros'),
        ('checking', 'Corriente'),
    ])
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_employees'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        unique_together = ['company', 'employee_code']
        ordering = ['employee_code']
    
    def __str__(self):
        return f"{self.employee_code} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_current_age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))




