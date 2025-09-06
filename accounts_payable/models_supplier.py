"""
Modelos de proveedores para el módulo de Cuentas por Pagar.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account


class SupplierType(models.Model):
    """
    Tipos de proveedor para clasificación.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_types')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración
    payment_days_default = models.IntegerField(default=30)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'ap_supplier_types'
        verbose_name = 'Tipo de Proveedor'
        verbose_name_plural = 'Tipos de Proveedor'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(models.Model):
    """
    Proveedores del sistema.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('NIT', 'NIT'),
        ('CE', 'Cédula de Extranjería'),
        ('PP', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad'),
        ('RC', 'Registro Civil'),
    ]
    
    REGIME_CHOICES = [
        ('simplified', 'Régimen Simplificado'),
        ('common', 'Régimen Común'),
        ('special', 'Régimen Especial'),
        ('no_resident', 'No Residente'),
    ]
    
    SUPPLIER_CLASS_CHOICES = [
        ('goods', 'Bienes'),
        ('services', 'Servicios'),
        ('both', 'Bienes y Servicios'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    
    # Identificación
    code = models.CharField(max_length=20)
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=20)
    verification_digit = models.CharField(max_length=2, blank=True)
    
    # Información básica
    business_name = models.CharField(max_length=200, help_text="Razón social")
    trade_name = models.CharField(max_length=200, blank=True, help_text="Nombre comercial")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Clasificación
    supplier_type = models.ForeignKey(SupplierType, on_delete=models.PROTECT)
    supplier_class = models.CharField(max_length=20, choices=SUPPLIER_CLASS_CHOICES, default='both')
    regime = models.CharField(max_length=20, choices=REGIME_CHOICES, default='common')
    
    # Contacto
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Colombia')
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Contacto comercial
    contact_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Configuración comercial
    payment_days = models.IntegerField(default=30, help_text="Días de pago")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Cuentas contables
    payable_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='suppliers_payable')
    advance_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='suppliers_advance')
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='suppliers_expense')
    
    # Configuración fiscal
    is_tax_agent = models.BooleanField(default=False, help_text="Agente de retención")
    tax_responsibilities = models.JSONField(default=list, help_text="Responsabilidades fiscales")
    
    # Retenciones
    applies_income_tax_retention = models.BooleanField(default=True)
    income_tax_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    applies_vat_retention = models.BooleanField(default=False)
    vat_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    applies_ica_retention = models.BooleanField(default=False)
    ica_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Información bancaria
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_type = models.CharField(max_length=20, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='suppliers_created')
    
    class Meta:
        db_table = 'ap_suppliers'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        unique_together = ['company', 'code']
        indexes = [
            models.Index(fields=['company', 'document_number']),
            models.Index(fields=['business_name']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.business_name}"
    
    def get_full_name(self):
        """Obtiene el nombre completo del proveedor."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.business_name
    
    def get_current_balance(self):
        """Obtiene el saldo actual del proveedor."""
        # Implementar lógica de cálculo de saldo
        return 0




