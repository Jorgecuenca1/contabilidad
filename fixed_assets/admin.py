"""
Configuración del admin para los modelos de activos fijos.
"""

from django.contrib import admin
from .models_asset import AssetCategory, FixedAsset, DepreciationEntry, AssetTransfer


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    """Admin para categorías de activos."""
    list_display = ('code', 'name', 'depreciation_method', 'useful_life_years', 'is_active')
    list_filter = ('depreciation_method', 'is_active')
    search_fields = ('code', 'name')


@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    """Admin para activos fijos."""
    list_display = ('code', 'name', 'category', 'company', 'acquisition_cost', 'status')
    list_filter = ('category', 'status', 'company')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DepreciationEntry)
class DepreciationEntryAdmin(admin.ModelAdmin):
    """Admin para entradas de depreciación."""
    list_display = ('asset', 'depreciation_amount')
    list_filter = ('asset__category',)
    search_fields = ('asset__name', 'asset__code')
    readonly_fields = ('created_at',)


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    """Admin para transferencias de activos."""
    list_display = ('asset', 'from_location', 'to_location', 'transfer_date', 'status')
    list_filter = ('status', 'transfer_date')
    search_fields = ('asset__name', 'asset__code')
    readonly_fields = ('created_at', 'updated_at')
