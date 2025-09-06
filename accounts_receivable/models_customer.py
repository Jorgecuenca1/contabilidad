"""
Modelos de clientes para el módulo de Cuentas por Cobrar.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account


class CustomerType(models.Model):
    """
    Tipos de cliente para clasificación.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customer_types')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración
    credit_limit_default = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_days_default = models.IntegerField(default=30)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'ar_customer_types'
        verbose_name = 'Tipo de Cliente'
        verbose_name_plural = 'Tipos de Cliente'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Customer(models.Model):
    """
    Clientes del sistema.
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    
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
    customer_type = models.ForeignKey(CustomerType, on_delete=models.PROTECT)
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
    
    # Configuración comercial
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_days = models.IntegerField(default=30, help_text="Días de crédito")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Cuentas contables
    receivable_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='customers_receivable')
    advance_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='customers_advance')
    
    # Configuración fiscal
    is_tax_responsible = models.BooleanField(default=True)
    tax_responsibilities = models.JSONField(default=list, help_text="Responsabilidades fiscales")
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='customers_created')
    
    class Meta:
        db_table = 'ar_customers'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
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
        """Obtiene el nombre completo del cliente."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.business_name
    
    def get_current_balance(self):
        """Obtiene el saldo actual del cliente."""
        # Implementar lógica de cálculo de saldo
        return 0
    
    def is_over_credit_limit(self):
        """Verifica si el cliente está sobre su límite de crédito."""
        if self.credit_limit <= 0:
            return False
        return self.get_current_balance() > self.credit_limit




