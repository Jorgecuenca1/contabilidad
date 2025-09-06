"""
Modelos de pagos para el módulo de Cuentas por Pagar.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account
from .models_supplier import Supplier
from .models_bill import PurchaseInvoice


class SupplierPayment(models.Model):
    """
    Pagos realizados a proveedores.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('ach', 'ACH'),
        ('electronic', 'Pago Electrónico'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('sent', 'Enviado'),
        ('confirmed', 'Confirmado'),
        ('reconciled', 'Conciliado'),
        ('cancelled', 'Anulado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_payments')
    
    # Identificación
    number = models.CharField(max_length=20)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='payments')
    
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
    
    # Información del cheque/transferencia
    check_number = models.CharField(max_length=20, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    
    # Cuentas contables
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, help_text="Cuenta de efectivo/banco")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Aprobación
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Contabilización
    is_posted = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='supplier_payments_created')
    
    class Meta:
        db_table = 'ap_supplier_payments'
        verbose_name = 'Pago a Proveedor'
        verbose_name_plural = 'Pagos a Proveedores'
        unique_together = ['company', 'number']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['supplier']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.supplier.business_name} - ${self.amount}"


class PaymentAllocation(models.Model):
    """
    Aplicación de pagos a facturas específicas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(SupplierPayment, on_delete=models.CASCADE, related_name='allocations')
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='payment_allocations')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ap_payment_allocations_created')
    
    class Meta:
        db_table = 'ap_payment_allocations'
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


class PaymentSchedule(models.Model):
    """
    Programación de pagos a proveedores.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('scheduled', 'Programado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_schedules')
    
    # Referencia
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='payment_schedules')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    
    # Programación
    scheduled_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pago realizado
    payment = models.ForeignKey(SupplierPayment, on_delete=models.SET_NULL, null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    # Notas
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'ap_payment_schedules'
        verbose_name = 'Programación de Pago'
        verbose_name_plural = 'Programaciones de Pago'
        ordering = ['scheduled_date', 'priority']
        indexes = [
            models.Index(fields=['company', 'scheduled_date']),
            models.Index(fields=['supplier']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.invoice.number} - {self.scheduled_date} - ${self.amount}"


class SupplierStatement(models.Model):
    """
    Estados de cuenta de proveedores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_statements')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='statements')
    
    # Período
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Saldos
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Archivo generado
    pdf_file = models.FileField(upload_to='statements/suppliers/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'ap_supplier_statements'
        verbose_name = 'Estado de Cuenta de Proveedor'
        verbose_name_plural = 'Estados de Cuenta de Proveedores'
        unique_together = ['supplier', 'period_start', 'period_end']
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.supplier.business_name} - {self.period_start} a {self.period_end}"
