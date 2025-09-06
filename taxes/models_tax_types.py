"""
Tipos de impuestos y configuraciones.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User
from accounting.models_accounts import Account


class TaxType(models.Model):
    """
    Tipos de impuestos (IVA, Retención Fuente, ICA, etc.)
    """
    TAX_CATEGORY_CHOICES = [
        ('vat', 'IVA'),
        ('withholding_source', 'Retención en la Fuente'),
        ('withholding_vat', 'Retención de IVA'),
        ('withholding_ica', 'Retención de ICA'),
        ('ica', 'Impuesto de Industria y Comercio'),
        ('income_tax', 'Impuesto de Renta'),
        ('wealth_tax', 'Impuesto al Patrimonio'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_types')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=TAX_CATEGORY_CHOICES)
    
    # Configuración del impuesto
    rate = models.DecimalField(max_digits=8, decimal_places=4, help_text="Tarifa del impuesto (%)")
    is_percentage = models.BooleanField(default=True)
    minimum_base = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    maximum_base = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Configuración contable
    account_payable = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='tax_payable', null=True, blank=True)
    account_receivable = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='tax_receivable', null=True, blank=True)
    
    # Configuración de reportes
    dian_code = models.CharField(max_length=10, blank=True, help_text="Código DIAN")
    form_line = models.CharField(max_length=20, blank=True, help_text="Línea en formulario")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'taxes_types'
        verbose_name = 'Tipo de Impuesto'
        verbose_name_plural = 'Tipos de Impuesto'
        unique_together = ['company', 'code']
        ordering = ['category', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.rate}%)"


class TaxCalendar(models.Model):
    """
    Calendario tributario con fechas de vencimiento.
    """
    OBLIGATION_TYPE_CHOICES = [
        ('vat_declaration', 'Declaración IVA'),
        ('vat_payment', 'Pago IVA'),
        ('income_declaration', 'Declaración Renta'),
        ('income_payment', 'Pago Renta'),
        ('withholding_declaration', 'Declaración Retenciones'),
        ('withholding_payment', 'Pago Retenciones'),
        ('ica_declaration', 'Declaración ICA'),
        ('ica_payment', 'Pago ICA'),
        ('other', 'Otra Obligación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_calendar')
    
    obligation_type = models.CharField(max_length=30, choices=OBLIGATION_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    
    # Período
    period_year = models.IntegerField()
    period_month = models.IntegerField(null=True, blank=True)
    period_number = models.IntegerField(null=True, blank=True)
    
    # Fechas
    due_date = models.DateField()
    extended_due_date = models.DateField(null=True, blank=True)
    
    # Control
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    
    # Información adicional
    last_digit_nit = models.CharField(max_length=1, blank=True, help_text="Último dígito del NIT")
    observations = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'taxes_calendar'
        verbose_name = 'Calendario Tributario'
        verbose_name_plural = 'Calendario Tributario'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['company', 'due_date']),
            models.Index(fields=['obligation_type', 'period_year']),
        ]
    
    def __str__(self):
        return f"{self.get_obligation_type_display()} - {self.due_date}"




