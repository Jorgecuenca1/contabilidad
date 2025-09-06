"""
Modelos de facturas para el módulo de Cuentas por Cobrar.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account, CostCenter, Project
from .models_customer import Customer


class Invoice(models.Model):
    """
    Facturas de venta a clientes.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('paid', 'Pagada'),
        ('partial', 'Pago Parcial'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Anulada'),
    ]
    
    TYPE_CHOICES = [
        ('invoice', 'Factura'),
        ('credit_note', 'Nota Crédito'),
        ('debit_note', 'Nota Débito'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    
    # Identificación
    number = models.CharField(max_length=20)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='invoice')
    series = models.CharField(max_length=10, default='A')
    
    # Cliente
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    
    # Fechas
    date = models.DateField()
    due_date = models.DateField()
    
    # Referencia
    reference = models.CharField(max_length=100, blank=True)
    purchase_order = models.CharField(max_length=50, blank=True)
    
    # Montos
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Pagos
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Facturación electrónica
    electronic_invoice = models.BooleanField(default=False)
    cufe = models.CharField(max_length=100, blank=True, help_text="Código Único de Facturación Electrónica")
    xml_file = models.FileField(upload_to='invoices/xml/', blank=True)
    pdf_file = models.FileField(upload_to='invoices/pdf/', blank=True)
    
    # Contabilización
    is_posted = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices_created')
    
    class Meta:
        db_table = 'ar_invoices'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        unique_together = ['company', 'number', 'series']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.series}{self.number} - {self.customer.business_name}"
    
    def clean(self):
        """Validaciones de la factura."""
        if self.due_date < self.date:
            raise ValidationError("La fecha de vencimiento no puede ser anterior a la fecha de la factura")
        
        if self.paid_amount > self.total_amount:
            raise ValidationError("El monto pagado no puede ser mayor al total de la factura")
    
    def save(self, *args, **kwargs):
        """Calcula el balance antes de guardar."""
        self.balance = self.total_amount - self.paid_amount
        
        # Actualizar estado basado en pagos
        if self.balance <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif self.due_date < timezone.now().date() and self.balance > 0:
            self.status = 'overdue'
        
        super().save(*args, **kwargs)
    
    def get_days_overdue(self):
        """Obtiene los días de vencimiento."""
        if self.due_date >= timezone.now().date():
            return 0
        return (timezone.now().date() - self.due_date).days


class InvoiceLine(models.Model):
    """
    Líneas de factura con productos/servicios.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    
    # Producto/Servicio
    product_code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200)
    
    # Cantidades y precios
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Totales
    line_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Impuestos
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Contabilización
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='invoice_lines_revenue')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Orden
    line_number = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ar_invoice_lines'
        verbose_name = 'Línea de Factura'
        verbose_name_plural = 'Líneas de Factura'
        ordering = ['invoice', 'line_number']
    
    def __str__(self):
        return f"{self.invoice.number} - {self.line_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        """Calcula totales antes de guardar."""
        # Calcular descuento
        if self.discount_percentage > 0:
            self.discount_amount = (self.quantity * self.unit_price) * (self.discount_percentage / 100)
        
        # Calcular subtotal
        subtotal = (self.quantity * self.unit_price) - self.discount_amount
        
        # Calcular impuestos
        self.tax_amount = subtotal * (self.tax_rate / 100)
        
        # Total de la línea
        self.line_total = subtotal + self.tax_amount
        
        super().save(*args, **kwargs)




