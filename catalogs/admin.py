"""
Admin del módulo Catálogos CUPS/CUMS
"""

from django.contrib import admin
from .models import (
    CUPSProcedure, CUMSMedication, ProcedureTariff,
    MedicationPrice, CatalogImportLog, FavoriteCatalogItem
)


@admin.register(CUPSProcedure)
class CUPSProcedureAdmin(admin.ModelAdmin):
    list_display = ['cups_code', 'description', 'category', 'status', 'requires_authorization']
    list_filter = ['category', 'status', 'requires_authorization']
    search_fields = ['cups_code', 'description', 'short_description']


@admin.register(CUMSMedication)
class CUMSMedicationAdmin(admin.ModelAdmin):
    list_display = ['cums_code', 'generic_name', 'commercial_name', 'pharmaceutical_form', 'status']
    list_filter = ['pharmaceutical_form', 'administration_route', 'status', 'pos_medication']
    search_fields = ['cums_code', 'generic_name', 'commercial_name']


@admin.register(ProcedureTariff)
class ProcedureTariffAdmin(admin.ModelAdmin):
    list_display = ['cups_procedure', 'eps', 'tariff_type', 'final_value', 'effective_date', 'is_active']
    list_filter = ['tariff_type', 'is_active']
    search_fields = ['cups_procedure__cups_code', 'eps__name']
    date_hierarchy = 'effective_date'


@admin.register(MedicationPrice)
class MedicationPriceAdmin(admin.ModelAdmin):
    list_display = ['cums_medication', 'eps', 'price_type', 'unit_price', 'effective_date', 'is_active']
    list_filter = ['price_type', 'is_active']
    search_fields = ['cums_medication__cums_code', 'eps__name']
    date_hierarchy = 'effective_date'


@admin.register(CatalogImportLog)
class CatalogImportLogAdmin(admin.ModelAdmin):
    list_display = ['import_type', 'file_name', 'status', 'total_records', 'imported_records', 'import_date']
    list_filter = ['import_type', 'status']
    search_fields = ['file_name']
    date_hierarchy = 'import_date'


@admin.register(FavoriteCatalogItem)
class FavoriteCatalogItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_type', 'specialty', 'sort_order']
    list_filter = ['item_type', 'specialty']
    search_fields = ['user__username']
