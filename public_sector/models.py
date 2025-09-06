"""
Sistema de contabilidad pública colombiana.
Incluye presupuesto, CDP, RP, PAC y reportes CHIP.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date

from core.models import Company, User, Period
from accounting.models_accounts import Account


class BudgetItem(models.Model):
    """
    Rubro presupuestal.
    """
    ITEM_TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
        ('investment', 'Inversión'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_items')
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    
    # Configuración
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True)
    is_detail = models.BooleanField(default=True, help_text="Permite movimientos directos")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'public_budget_items'
        verbose_name = 'Rubro Presupuestal'
        verbose_name_plural = 'Rubros Presupuestales'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Budget(models.Model):
    """
    Presupuesto anual.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('executed', 'En Ejecución'),
        ('closed', 'Cerrado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budgets')
    
    name = models.CharField(max_length=200)
    year = models.IntegerField()
    description = models.TextField(blank=True)
    
    # Totales
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='budgets_approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'public_budgets'
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        unique_together = ['company', 'year']
        ordering = ['-year']
    
    def __str__(self):
        return f"Presupuesto {self.year} - {self.name}"


class BudgetDetail(models.Model):
    """
    Detalle del presupuesto por rubro.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='details')
    budget_item = models.ForeignKey(BudgetItem, on_delete=models.PROTECT)
    
    # Valores
    initial_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    additions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transfers_in = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transfers_out = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Ejecución
    committed = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    accrued = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'public_budget_details'
        verbose_name = 'Detalle Presupuestal'
        verbose_name_plural = 'Detalles Presupuestales'
        unique_together = ['budget', 'budget_item']
    
    def __str__(self):
        return f"{self.budget.name} - {self.budget_item.name}"


class CDP(models.Model):
    """
    Certificado de Disponibilidad Presupuestal.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('committed', 'Comprometido'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cdps')
    budget = models.ForeignKey(Budget, on_delete=models.PROTECT)
    
    # Identificación
    number = models.CharField(max_length=50)
    date = models.DateField()
    description = models.TextField()
    
    # Beneficiario
    beneficiary_name = models.CharField(max_length=200)
    beneficiary_tax_id = models.CharField(max_length=20)
    
    # Valores
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    validity_date = models.DateField(help_text="Fecha de vigencia del CDP")
    
    # Auditoría
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='cdps_approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'public_cdps'
        verbose_name = 'CDP'
        verbose_name_plural = 'CDPs'
        unique_together = ['company', 'number']
        ordering = ['-date']
    
    def __str__(self):
        return f"CDP {self.number} - {self.beneficiary_name}"


class CDPDetail(models.Model):
    """
    Detalle del CDP por rubro presupuestal.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cdp = models.ForeignKey(CDP, on_delete=models.CASCADE, related_name='details')
    budget_item = models.ForeignKey(BudgetItem, on_delete=models.PROTECT)
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'public_cdp_details'
        verbose_name = 'Detalle CDP'
        verbose_name_plural = 'Detalles CDP'
        unique_together = ['cdp', 'budget_item']
    
    def __str__(self):
        return f"{self.cdp.number} - {self.budget_item.name}: {self.amount}"


class RP(models.Model):
    """
    Registro Presupuestal.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('executed', 'Ejecutado'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='rps')
    cdp = models.ForeignKey(CDP, on_delete=models.PROTECT)
    
    # Identificación
    number = models.CharField(max_length=50)
    date = models.DateField()
    description = models.TextField()
    
    # Contrato/Compromiso
    contract_number = models.CharField(max_length=50, blank=True)
    contract_date = models.DateField(null=True, blank=True)
    contract_object = models.TextField(blank=True)
    
    # Valores
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    executed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Auditoría
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='rps_approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'public_rps'
        verbose_name = 'RP'
        verbose_name_plural = 'RPs'
        unique_together = ['company', 'number']
        ordering = ['-date']
    
    def __str__(self):
        return f"RP {self.number} - {self.contract_number}"


class PublicReport(models.Model):
    """
    Reportes específicos del sector público (CHIP, CGN, etc.)
    """
    REPORT_TYPE_CHOICES = [
        ('chip', 'CHIP'),
        ('cgn_balance', 'Balance CGN'),
        ('cgn_execution', 'Ejecución Presupuestal CGN'),
        ('budget_execution', 'Ejecución Presupuestal'),
        ('cdp_report', 'Reporte CDPs'),
        ('rp_report', 'Reporte RPs'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('generated', 'Generado'),
        ('sent', 'Enviado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='public_reports')
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Período
    period_year = models.IntegerField()
    period_month = models.IntegerField(null=True, blank=True)
    period_quarter = models.IntegerField(null=True, blank=True)
    
    # Archivos
    file_path = models.FileField(upload_to='public_reports/', blank=True)
    
    # Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField(null=True, blank=True)
    sent_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'public_reports'
        verbose_name = 'Reporte Público'
        verbose_name_plural = 'Reportes Públicos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_year}"