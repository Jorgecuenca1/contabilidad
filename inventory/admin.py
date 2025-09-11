"""
Configuración del admin para los modelos de inventario.
"""

from django.contrib import admin
from .models import Warehouse, StockMovement, ProductStock
from .models_product import ProductCategory, UnitOfMeasure, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Admin para categorías de producto."""
    list_display = ('code', 'name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    """Admin para unidades de medida."""
    list_display = ('code', 'name', 'symbol', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin para productos."""
    list_display = ('code', 'name', 'category', 'unit_of_measure', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """Admin para bodegas."""
    list_display = ('code', 'name', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


# Temporalmente deshabilitamos estos admin hasta revisar los campos exactos
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin para movimientos de inventario."""
    list_display = ('product', 'warehouse', 'movement_type', 'quantity', 'movement_date')
    list_filter = ('movement_type', 'warehouse', 'movement_date')
    search_fields = ('product__name', 'product__code')
    readonly_fields = ('created_at',)


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    """Admin para stock de productos."""
    list_display = ('product', 'warehouse', 'quantity_on_hand', 'quantity_available')
    list_filter = ('warehouse',)
    search_fields = ('product__name', 'product__code')
    readonly_fields = ('updated_at',)
