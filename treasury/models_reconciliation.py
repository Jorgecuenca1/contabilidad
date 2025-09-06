"""
Modelos de conciliación bancaria y flujo de caja.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from core.models import Company, User, Period, Currency
from .models_bank import BankAccount


class BankReconciliation(models.Model):
    """
    Conciliaciones bancarias.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('approved', 'Aprobada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_reconciliations')
    
    # Identificación
    number = models.CharField(max_length=20)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='reconciliations')
    
    # Período
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Saldos
    book_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Saldo según libros")
    bank_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Saldo según banco")
    
    # Ajustes
    deposits_in_transit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_checks = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bank_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    interest_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_adjustments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Resultado
    reconciled_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Aprobación
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reconciliations')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    bank_statement = models.FileField(upload_to='reconciliations/', blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reconciliations_created')
    
    class Meta:
        db_table = 'treasury_bank_reconciliations'
        verbose_name = 'Conciliación Bancaria'
        verbose_name_plural = 'Conciliaciones Bancarias'
        unique_together = ['company', 'number']
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['company', 'period_end']),
            models.Index(fields=['bank_account']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.bank_account.name} - {self.period_end}"
    
    def calculate_difference(self):
        """Calcula la diferencia de conciliación."""
        adjusted_book_balance = (self.book_balance + self.interest_earned - 
                               self.bank_charges + self.other_adjustments)
        adjusted_bank_balance = (self.bank_balance + self.deposits_in_transit - 
                               self.outstanding_checks)
        self.difference = adjusted_book_balance - adjusted_bank_balance
        return self.difference


class CashFlow(models.Model):
    """
    Flujo de caja proyectado vs real.
    """
    FLOW_TYPE_CHOICES = [
        ('projected', 'Proyectado'),
        ('actual', 'Real'),
    ]
    
    CATEGORY_CHOICES = [
        ('operating', 'Operativo'),
        ('investing', 'Inversión'),
        ('financing', 'Financiamiento'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cash_flows')
    
    # Identificación
    period = models.ForeignKey(Period, on_delete=models.PROTECT)
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Descripción
    concept = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Montos
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    inflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_flow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Fechas
    date = models.DateField()
    
    # Referencia
    reference_document = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'treasury_cash_flows'
        verbose_name = 'Flujo de Caja'
        verbose_name_plural = 'Flujos de Caja'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', 'period']),
            models.Index(fields=['flow_type', 'category']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.concept} - {self.date} - ${self.net_flow}"
    
    def save(self, *args, **kwargs):
        """Calcula el flujo neto antes de guardar."""
        self.net_flow = self.inflow - self.outflow
        super().save(*args, **kwargs)




