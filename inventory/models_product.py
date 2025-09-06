"""
Modelos de productos para el módulo de inventarios.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

from core.models import Company, User, Currency
from accounting.models_accounts import Account, CostCenter


class ProductCategory(models.Model):
    """
    Categorías de productos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_categories')
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    is_active = models.BooleanField(default=True)
    
    # Cuentas contables por defecto
    inventory_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='categories_inventory')
    cost_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='categories_cost')
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='categories_revenue')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'inventory_product_categories'
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Producto'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class UnitOfMeasure(models.Model):
    """
    Unidades de medida.
    """
    MEASURE_TYPE_CHOICES = [
        ('length', 'Longitud'),
        ('weight', 'Peso'),
        ('volume', 'Volumen'),
        ('area', 'Área'),
        ('time', 'Tiempo'),
        ('unit', 'Unidad'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='units_of_measure')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    measure_type = models.CharField(max_length=20, choices=MEASURE_TYPE_CHOICES)
    
    # Conversión a unidad base
    base_unit = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='derived_units')
    conversion_factor = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'inventory_units_of_measure'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(models.Model):
    """
    Productos del inventario.
    """
    PRODUCT_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
        ('kit', 'Kit'),
        ('raw_material', 'Materia Prima'),
        ('finished_good', 'Producto Terminado'),
    ]
    
    COSTING_METHOD_CHOICES = [
        ('average', 'Promedio Ponderado'),
        ('fifo', 'PEPS (Primero en Entrar, Primero en Salir)'),
        ('lifo', 'UEPS (Último en Entrar, Primero en Salir)'),
        ('standard', 'Costo Estándar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    
    # Identificación
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Clasificación
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='product')
    
    # Códigos adicionales
    barcode = models.CharField(max_length=50, blank=True)
    internal_reference = models.CharField(max_length=50, blank=True)
    supplier_reference = models.CharField(max_length=50, blank=True)
    
    # Unidades
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='products')
    purchase_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, null=True, blank=True, related_name='products_purchase')
    sale_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, null=True, blank=True, related_name='products_sale')
    
    # Precios y costos
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    list_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    sale_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Método de costeo
    costing_method = models.CharField(max_length=20, choices=COSTING_METHOD_CHOICES, default='average')
    
    # Control de inventario
    track_inventory = models.BooleanField(default=True)
    track_lots = models.BooleanField(default=False)
    track_serial_numbers = models.BooleanField(default=False)
    track_expiration = models.BooleanField(default=False)
    
    # Niveles de inventario
    minimum_stock = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    maximum_stock = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    reorder_point = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Cuentas contables
    inventory_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='products_inventory')
    cost_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='products_cost')
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='products_revenue')
    
    # Configuración fiscal
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_for_sale = models.BooleanField(default=True)
    is_for_purchase = models.BooleanField(default=True)
    
    # Imagen
    image = models.ImageField(upload_to='products/', blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='products_created')
    
    class Meta:
        db_table = 'inventory_products'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        unique_together = ['company', 'code']
        ordering = ['code']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['barcode']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_current_stock(self, warehouse=None):
        """Obtiene el stock actual del producto."""
        # Implementar lógica de cálculo de stock
        return 0
    
    def get_available_stock(self, warehouse=None):
        """Obtiene el stock disponible (descontando reservas)."""
        # Implementar lógica de stock disponible
        return self.get_current_stock(warehouse)




