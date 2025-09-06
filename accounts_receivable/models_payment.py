"""
Modelos de pagos para el módulo de Cuentas por Cobrar.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account
from .models_customer import Customer
from .models_invoice import Invoice


class Payment(models.Model):
    """
    Pagos recibidos de clientes.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('card', 'Tarjeta'),
        ('electronic', 'Pago Electrónico'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('reconciled', 'Conciliado'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customer_payments')
    
    # Identificación
    number = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payments')
    
    # Fechas
    date = models.DateField()
    value_date = models.DateField(help_text="Fecha valor del pago")
    
    # Monto
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Método de pago
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True, help_text="Referencia del pago")
    
    # Cuentas contables
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, help_text="Cuenta de efectivo/banco")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Contabilización
    is_posted = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='customer_payments_created')
    
    class Meta:
        db_table = 'ar_payments'
        verbose_name = 'Pago de Cliente'
        verbose_name_plural = 'Pagos de Clientes'
        unique_together = ['company', 'number']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.customer.business_name} - ${self.amount}"


class PaymentAllocation(models.Model):
    """
    Aplicación de pagos a facturas específicas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payment_allocations')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ar_payment_allocations_created')
    
    class Meta:
        db_table = 'ar_payment_allocations'
        verbose_name = 'Aplicación de Pago'
        verbose_name_plural = 'Aplicaciones de Pago'
        unique_together = ['payment', 'invoice']
    
    def __str__(self):
        return f"{self.payment.number} -> {self.invoice.number} (${self.amount})"
    
    def clean(self):
        """Validaciones de la aplicación."""
        if self.amount > self.payment.amount:
            raise ValidationError("El monto aplicado no puede ser mayor al monto del pago")
        
        if self.amount > self.invoice.balance:
            raise ValidationError("El monto aplicado no puede ser mayor al saldo de la factura")


class CustomerStatement(models.Model):
    """
    Estados de cuenta de clientes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customer_statements')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='statements')
    
    # Período
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Saldos
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Archivo generado
    pdf_file = models.FileField(upload_to='statements/', blank=True)
    
    # Estado
    is_sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'ar_customer_statements'
        verbose_name = 'Estado de Cuenta'
        verbose_name_plural = 'Estados de Cuenta'
        unique_together = ['customer', 'period_start', 'period_end']
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.customer.business_name} - {self.period_start} a {self.period_end}"
