"""
Modelos de facturas de compra para el módulo de Cuentas por Pagar.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account, CostCenter, Project
from .models_supplier import Supplier


class PurchaseInvoice(models.Model):
    """
    Facturas de compra de proveedores.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('received', 'Recibida'),
        ('approved', 'Aprobada'),
        ('paid', 'Pagada'),
        ('partial', 'Pago Parcial'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Anulada'),
    ]
    
    TYPE_CHOICES = [
        ('invoice', 'Factura'),
        ('credit_note', 'Nota Crédito'),
        ('debit_note', 'Nota Débito'),
        ('support_document', 'Documento Soporte'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_invoices')
    
    # Identificación
    number = models.CharField(max_length=20)
    supplier_invoice_number = models.CharField(max_length=50, help_text="Número de factura del proveedor")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='invoice')
    
    # Proveedor
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='invoices')
    
    # Fechas
    date = models.DateField()
    due_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)
    
    # Referencia
    reference = models.CharField(max_length=100, blank=True)
    purchase_order = models.CharField(max_length=50, blank=True)
    
    # Montos
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Retenciones
    income_tax_retention = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_retention = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ica_retention = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_retentions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total menos retenciones")
    
    # Pagos
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Aprobación
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_invoices')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    pdf_file = models.FileField(upload_to='invoices/purchase/', blank=True)
    xml_file = models.FileField(upload_to='invoices/purchase/xml/', blank=True)
    
    # Contabilización
    is_posted = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='purchase_invoices_created')
    
    class Meta:
        db_table = 'ap_purchase_invoices'
        verbose_name = 'Factura de Compra'
        verbose_name_plural = 'Facturas de Compra'
        unique_together = ['company', 'number']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['supplier']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['supplier_invoice_number']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.supplier.business_name}"
    
    def clean(self):
        """Validaciones de la factura."""
        if self.due_date < self.date:
            raise ValidationError("La fecha de vencimiento no puede ser anterior a la fecha de la factura")
        
        if self.paid_amount > self.net_amount:
            raise ValidationError("El monto pagado no puede ser mayor al neto de la factura")
    
    def save(self, *args, **kwargs):
        """Calcula totales antes de guardar."""
        # Calcular neto (total menos retenciones)
        total_retentions = (self.income_tax_retention + self.vat_retention + 
                          self.ica_retention + self.other_retentions)
        self.net_amount = self.total_amount - total_retentions
        
        # Calcular balance
        self.balance = self.net_amount - self.paid_amount
        
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


class PurchaseInvoiceLine(models.Model):
    """
    Líneas de factura de compra con productos/servicios.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='lines')
    
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
    
    # Retenciones
    income_tax_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    income_tax_retention_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vat_retention_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Contabilización
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='purchase_lines_expense')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Orden
    line_number = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ap_purchase_invoice_lines'
        verbose_name = 'Línea de Factura de Compra'
        verbose_name_plural = 'Líneas de Factura de Compra'
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
        
        # Calcular retenciones
        if self.income_tax_retention_rate > 0:
            self.income_tax_retention_amount = subtotal * (self.income_tax_retention_rate / 100)
        
        if self.vat_retention_rate > 0:
            self.vat_retention_amount = self.tax_amount * (self.vat_retention_rate / 100)
        
        # Total de la línea
        self.line_total = subtotal + self.tax_amount
        
        super().save(*args, **kwargs)




