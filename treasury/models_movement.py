"""
Modelos de movimientos bancarios y de caja.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from core.models import Company, User, Currency
from .models_bank import BankAccount, CashAccount


class BankMovement(models.Model):
    """
    Movimientos bancarios (extractos).
    """
    MOVEMENT_TYPE_CHOICES = [
        ('debit', 'Débito'),
        ('credit', 'Crédito'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('reconciled', 'Conciliado'),
        ('disputed', 'En Disputa'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='movements')
    
    # Identificación
    transaction_id = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    
    # Fechas
    date = models.DateField()
    value_date = models.DateField()
    
    # Movimiento
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance = models.DecimalField(max_digits=15, decimal_places=2, help_text="Saldo después del movimiento")
    
    # Descripción
    description = models.CharField(max_length=200)
    concept = models.CharField(max_length=100, blank=True)
    
    # Conciliación
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reconciled_date = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_movements')
    
    # Importación
    imported_from = models.CharField(max_length=100, blank=True, help_text="Fuente de importación")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'treasury_bank_movements'
        verbose_name = 'Movimiento Bancario'
        verbose_name_plural = 'Movimientos Bancarios'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['bank_account', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.bank_account.code} - {self.date} - {self.description}"
    
    def get_signed_amount(self):
        """Obtiene el monto con signo según el tipo de movimiento."""
        return self.amount if self.movement_type == 'credit' else -self.amount


class CashMovement(models.Model):
    """
    Movimientos de caja (recibos y egresos).
    """
    MOVEMENT_TYPE_CHOICES = [
        ('receipt', 'Recibo de Caja'),
        ('disbursement', 'Egreso de Caja'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cash_movements')
    
    # Identificación
    number = models.CharField(max_length=20)
    cash_account = models.ForeignKey(CashAccount, on_delete=models.PROTECT, related_name='movements')
    
    # Tipo y fecha
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    date = models.DateField()
    
    # Tercero
    third_party_name = models.CharField(max_length=200)
    third_party_document = models.CharField(max_length=20, blank=True)
    
    # Monto
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Descripción
    concept = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Contabilización
    is_posted = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_movements_created')
    
    class Meta:
        db_table = 'treasury_cash_movements'
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        unique_together = ['company', 'number']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['cash_account']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.concept} - ${self.amount}"
    
    def get_signed_amount(self):
        """Obtiene el monto con signo según el tipo de movimiento."""
        return self.amount if self.movement_type == 'receipt' else -self.amount




