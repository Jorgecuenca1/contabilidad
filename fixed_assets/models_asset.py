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
        """Calcula la depreciación mensual según Colombian DIAN standards."""
        if self.useful_life_years == 0:
            return Decimal('0')
        
        total_months = (self.useful_life_years * 12) + self.useful_life_months
        if total_months == 0:
            return Decimal('0')
        
        if self.depreciation_method == 'straight_line':
            return self.depreciable_amount / total_months
        elif self.depreciation_method == 'declining_balance':
            # Saldos decrecientes: 200% del método lineal
            straight_line_rate = Decimal('1') / Decimal(self.useful_life_years)
            declining_rate = straight_line_rate * Decimal('2')
            current_book_value = self.acquisition_cost - self.accumulated_depreciation
            annual_depreciation = current_book_value * declining_rate
            return annual_depreciation / Decimal('12')
        elif self.depreciation_method == 'sum_of_years':
            # Suma de años dígitos
            remaining_years = max(0, self.useful_life_years - (self.accumulated_depreciation * self.useful_life_years / self.depreciable_amount))
            sum_years = (self.useful_life_years * (self.useful_life_years + 1)) / 2
            if sum_years > 0:
                annual_depreciation = (remaining_years / sum_years) * self.depreciable_amount
                return annual_depreciation / Decimal('12')
        
        return Decimal('0')
    
    def get_colombian_max_depreciation_rate(self):
        """Returns maximum depreciation rate according to Colombian DIAN standards."""
        category_rates = {
            'buildings': Decimal('2.22'),  # 45 years
            'machinery': Decimal('10.0'),  # 10 years  
            'vehicles': Decimal('10.0'),   # 10 years
            'computers': Decimal('20.0'),  # 5 years
            'furniture': Decimal('10.0'),  # 10 years
            'office_equipment': Decimal('20.0'),  # 5 years
        }
        
        # Get category code or use default
        category_code = getattr(self.category, 'code', '').lower()
        for key in category_rates:
            if key in category_code:
                return category_rates[key]
        
        # Default rate for general assets
        return Decimal('10.0')
    
    def validate_colombian_compliance(self):
        """Validates compliance with Colombian depreciation standards."""
        max_rate = self.get_colombian_max_depreciation_rate()
        annual_depreciation = self.calculate_monthly_depreciation() * 12
        current_rate = (annual_depreciation / self.acquisition_cost * 100) if self.acquisition_cost > 0 else 0
        
        return current_rate <= max_rate


class DepreciationEntry(models.Model):
    """
    Registro de depreciación de activos fijos con integración contable.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='depreciation_entries')
    
    # Activo fijo
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='depreciation_entries')
    
    # Fechas
    period_year = models.IntegerField()
    period_month = models.IntegerField()
    depreciation_date = models.DateField()
    
    # Valores
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    accumulated_before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    accumulated_after = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Método de depreciación utilizado
    method_used = models.CharField(max_length=20)
    
    # Información contable
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='depreciation_entries'
    )
    voucher_number = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('posted', 'Contabilizado'),
        ('reversed', 'Reversado'),
    ], default='draft')
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='depreciation_entries_created')
    
    class Meta:
        db_table = 'fixed_assets_depreciation_entries'
        verbose_name = 'Registro de Depreciación'
        verbose_name_plural = 'Registros de Depreciación'
        unique_together = ['company', 'asset', 'period_year', 'period_month']
        ordering = ['-period_year', '-period_month', 'asset__code']
        indexes = [
            models.Index(fields=['company', 'period_year', 'period_month']),
            models.Index(fields=['asset', 'depreciation_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Depreciación {self.asset.code} - {self.period_month:02d}/{self.period_year}"
    
    def save(self, *args, **kwargs):
        """Calculate accumulated values on save."""
        if not self.accumulated_after:
            self.accumulated_after = self.accumulated_before + self.depreciation_amount
        super().save(*args, **kwargs)


class AssetTransfer(models.Model):
    """
    Transferencias de activos fijos entre centros de costos o ubicaciones.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='asset_transfers')
    
    # Activo
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='transfers')
    
    # Transferencia
    transfer_date = models.DateField()
    from_cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='asset_transfers_from', null=True, blank=True)
    to_cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='asset_transfers_to', null=True, blank=True)
    from_location = models.CharField(max_length=200, blank=True)
    to_location = models.CharField(max_length=200, blank=True)
    from_responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_transfers_from_user')
    to_responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_transfers_to_user')
    
    # Detalles
    reason = models.TextField()
    notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], default='draft')
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='asset_transfers_created')
    
    class Meta:
        db_table = 'fixed_assets_transfers'
        verbose_name = 'Transferencia de Activo'
        verbose_name_plural = 'Transferencias de Activos'
        ordering = ['-transfer_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'transfer_date']),
            models.Index(fields=['asset', 'status']),
        ]
    
    def __str__(self):
        return f"Transferencia {self.asset.code} - {self.transfer_date.strftime('%d/%m/%Y')}"
