"""
Modelos para el módulo de Inventarios.
Incluye productos, bodegas, movimientos y control de stock.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Period, Currency
from accounting.models_accounts import Account, CostCenter, Project

# Importar todos los modelos de inventory
from .models_product import ProductCategory, UnitOfMeasure, Product


class Warehouse(models.Model):
    """
    Bodegas o almacenes para el control de inventario.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Ubicación
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Configuración
    is_active = models.BooleanField(default=True)
    is_main_warehouse = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'inventory_warehouses'
        verbose_name = 'Bodega'
        verbose_name_plural = 'Bodegas'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StockMovement(models.Model):
    """
    Movimientos de inventario (entradas, salidas, ajustes).
    """
    MOVEMENT_TYPE_CHOICES = [
        ('entry', 'Entrada'),
        ('exit', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia'),
        ('initial', 'Inventario Inicial'),
    ]
    
    MOVEMENT_REASON_CHOICES = [
        ('purchase', 'Compra'),
        ('sale', 'Venta'),
        ('return_customer', 'Devolución de Cliente'),
        ('return_supplier', 'Devolución a Proveedor'),
        ('damage', 'Daño/Pérdida'),
        ('obsolescence', 'Obsolescencia'),
        ('count_adjustment', 'Ajuste por Conteo'),
        ('cost_adjustment', 'Ajuste de Costo'),
        ('transfer_in', 'Transferencia Entrada'),
        ('transfer_out', 'Transferencia Salida'),
        ('production', 'Producción'),
        ('consumption', 'Consumo'),
        ('initial_inventory', 'Inventario Inicial'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_movements')
    
    # Información principal
    movement_date = models.DateTimeField(default=timezone.now)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    movement_reason = models.CharField(max_length=20, choices=MOVEMENT_REASON_CHOICES)
    
    # Producto y bodega
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_movements')
    warehouse_destination = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, null=True, blank=True, 
        related_name='stock_movements_destination'
    )
    
    # Cantidades
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Referencias
    document_type = models.CharField(max_length=50, blank=True)
    document_number = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Control de lotes y series
    lot_number = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Contabilidad
    journal_entry = models.ForeignKey(
        'accounting.JournalEntry', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='stock_movements'
    )
    
    class Meta:
        db_table = 'inventory_stock_movements'
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'movement_date']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['document_type', 'document_number']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.code} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calcular costo total
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)


class ProductStock(models.Model):
    """
    Stock actual de productos por bodega.
    Tabla de resumen para consultas rápidas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_stocks')
    
    # Producto y bodega
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='product_stocks')
    
    # Stock
    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    quantity_available = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Costos
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Control
    last_movement_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_product_stocks'
        verbose_name = 'Stock de Producto'
        verbose_name_plural = 'Stock de Productos'
        unique_together = ['company', 'product', 'warehouse']
        ordering = ['product__code', 'warehouse__code']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['quantity_on_hand']),
        ]
    
    def __str__(self):
        return f"{self.product.code} - {self.warehouse.code}: {self.quantity_on_hand}"
    
    def calculate_available_quantity(self):
        """Calcula la cantidad disponible (en mano - reservada)."""
        self.quantity_available = self.quantity_on_hand - self.quantity_reserved
        return self.quantity_available
