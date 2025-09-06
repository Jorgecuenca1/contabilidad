"""
Modelos de cuentas contables y plan de cuentas.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from core.models import Company, User, Currency


class AccountType(models.Model):
    """
    Tipos de cuenta contable (Activo, Pasivo, Patrimonio, Ingresos, Gastos).
    """
    TYPE_CHOICES = [
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Patrimonio'),
        ('income', 'Ingresos'),
        ('expense', 'Gastos'),
        ('cost', 'Costos'),
    ]
    
    NATURE_CHOICES = [
        ('debit', 'Débito'),
        ('credit', 'Crédito'),
    ]
    
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES)
    is_balance_sheet = models.BooleanField(default=True, help_text="Aparece en balance general")
    is_income_statement = models.BooleanField(default=False, help_text="Aparece en estado de resultados")
    
    class Meta:
        db_table = 'accounting_account_types'
        verbose_name = 'Tipo de Cuenta'
        verbose_name_plural = 'Tipos de Cuenta'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ChartOfAccounts(models.Model):
    """
    Plan de cuentas maestro por empresa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='chart_of_accounts')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    account_code_length = models.IntegerField(default=6, help_text="Longitud del código de cuenta")
    cost_center_required = models.BooleanField(default=False)
    project_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_chart_of_accounts'
        verbose_name = 'Plan de Cuentas'
        verbose_name_plural = 'Planes de Cuentas'
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Account(models.Model):
    """
    Cuenta contable individual dentro del plan de cuentas.
    """
    CONTROL_CHOICES = [
        ('none', 'Sin Control'),
        ('receivables', 'Cuentas por Cobrar'),
        ('payables', 'Cuentas por Pagar'),
        ('inventory', 'Inventarios'),
        ('fixed_assets', 'Activos Fijos'),
        ('bank', 'Bancos'),
        ('cash', 'Caja'),
        ('tax', 'Impuestos'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart_of_accounts = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, related_name='accounts')
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    control_type = models.CharField(max_length=20, choices=CONTROL_CHOICES, default='none')
    
    # Comportamiento
    is_active = models.BooleanField(default=True)
    is_detail = models.BooleanField(default=True, help_text="Permite movimientos directos")
    requires_third_party = models.BooleanField(default=False)
    requires_cost_center = models.BooleanField(default=False)
    requires_project = models.BooleanField(default=False)
    
    # Configuración de moneda
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True)
    allow_multi_currency = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_accounts'
        verbose_name = 'Cuenta Contable'
        verbose_name_plural = 'Cuentas Contables'
        unique_together = ['chart_of_accounts', 'code']
        ordering = ['code']
        indexes = [
            models.Index(fields=['chart_of_accounts', 'code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active', 'is_detail']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_full_code(self):
        """Obtiene el código completo incluyendo jerarquía."""
        if self.parent:
            return f"{self.parent.get_full_code()}.{self.code}"
        return self.code


class CostCenter(models.Model):
    """
    Centros de costo para segmentación de la información contable.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Presupuesto
    has_budget = models.BooleanField(default=False)
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cost_centers_created')
    
    class Meta:
        db_table = 'accounting_cost_centers'
        verbose_name = 'Centro de Costo'
        verbose_name_plural = 'Centros de Costo'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Project(models.Model):
    """
    Proyectos para segmentación adicional de la información contable.
    """
    STATUS_CHOICES = [
        ('planning', 'Planificación'),
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Responsables
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Presupuesto
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='projects_created')
    
    class Meta:
        db_table = 'accounting_projects'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
