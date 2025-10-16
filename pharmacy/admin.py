"""
Admin del módulo Farmacia
"""

from django.contrib import admin
from .models import (
    MedicineCategory, Medicine, MedicineBatch,
    Dispensing, DispensingItem, InventoryMovement, StockAlert
)


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category_type', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('code', 'generic_name', 'category', 'pharmaceutical_form', 'is_active')
    list_filter = ('pharmaceutical_form', 'control_type', 'is_active')
    search_fields = ('code', 'generic_name', 'commercial_name', 'barcode')


@admin.register(MedicineBatch)
class MedicineBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'medicine', 'expiry_date', 'current_quantity', 'is_active')
    list_filter = ('is_active', 'is_quarantine', 'expiry_date')
    search_fields = ('batch_number', 'medicine__generic_name')


@admin.register(Dispensing)
class DispensingAdmin(admin.ModelAdmin):
    list_display = ('dispensing_number', 'patient', 'dispensing_date', 'status', 'total_amount')
    list_filter = ('status', 'dispensing_date')
    search_fields = ('dispensing_number', 'patient__name')


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'alert_type', 'priority', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'priority', 'is_resolved')
    search_fields = ('medicine__generic_name',)
