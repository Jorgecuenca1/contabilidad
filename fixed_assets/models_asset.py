"""
Modelos de activos fijos.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account, CostCenter


class AssetCategory(models.Model):
    """
    Categorías de activos fijos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='asset_categories')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración de depreciación
    useful_life_years = models.IntegerField(default=5, help_text="Vida útil en años")
    depreciation_method = models.CharField(max_length=20, default='straight_line', choices=[
        ('straight_line', 'Línea Recta'),
        ('declining_balance', 'Saldos Decrecientes'),
        ('sum_of_years', 'Suma de Años Dígitos'),
    ])
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Cuentas contables
    asset_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='asset_categories_asset')
    depreciation_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='asset_categories_depreciation')
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='asset_categories_expense')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'fixed_assets_categories'
        verbose_name = 'Categoría de Activo'
        verbose_name_plural = 'Categorías de Activos'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class FixedAsset(models.Model):
    """
    Activos fijos de la empresa.
    """
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('disposed', 'Dado de Baja'),
        ('sold', 'Vendido'),
        ('transferred', 'Transferido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fixed_assets')
    
    # Identificación
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Clasificación
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    
    # Información del activo
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    
    # Ubicación
    location = models.CharField(max_length=200, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    responsible_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsible_assets')
    
    # Fechas
    acquisition_date = models.DateField()
    start_depreciation_date = models.DateField()
    
    # Valores
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2)
    residual_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Depreciación
    useful_life_years = models.IntegerField()
    useful_life_months = models.IntegerField(default=0)
    depreciation_method = models.CharField(max_length=20, default='straight_line')
    
    # Valores calculados
    depreciable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_book_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Información adicional
    supplier = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    warranty_expiration = models.DateField(null=True, blank=True)
    
    # Imagen
    image = models.ImageField(upload_to='assets/', blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assets_created')
    
    class Meta:
        db_table = 'fixed_assets'
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
        unique_together = ['company', 'code']
        ordering = ['code']
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['status']),
            models.Index(fields=['cost_center']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Calcula valores antes de guardar."""
        self.depreciable_amount = self.acquisition_cost - self.residual_value
        self.net_book_value = self.acquisition_cost - self.accumulated_depreciation
        super().save(*args, **kwargs)
    
    def calculate_monthly_depreciation(self):
        """Calcula la depreciación mensual."""
        if self.useful_life_years == 0:
            return 0
        
        total_months = (self.useful_life_years * 12) + self.useful_life_months
        if total_months == 0:
            return 0
        
        if self.depreciation_method == 'straight_line':
            return self.depreciable_amount / total_months
        
        # Implementar otros métodos de depreciación
        return 0




