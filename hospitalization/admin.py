"""
Admin del módulo Hospitalización
"""

from django.contrib import admin
from .models import (
    Ward, Bed, Admission, AdmissionTransfer,
    MedicalEvolution, MedicalOrder, AdmissionServiceItem
)


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'ward_type', 'floor', 'bed_capacity', 'is_active')
    list_filter = ('ward_type', 'floor', 'is_active')
    search_fields = ('code', 'name', 'building')


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('code', 'ward', 'room_number', 'bed_type', 'status', 'daily_rate', 'is_active')
    list_filter = ('ward', 'bed_type', 'status', 'is_active')
    search_fields = ('code', 'room_number')


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'patient', 'bed', 'admission_date', 'status', 'attending_physician')
    list_filter = ('status', 'admission_type', 'admission_date')
    search_fields = ('admission_number', 'patient__third_party__name', 'patient__medical_record_number')
    date_hierarchy = 'admission_date'


@admin.register(MedicalEvolution)
class MedicalEvolutionAdmin(admin.ModelAdmin):
    list_display = ('admission', 'evolution_date', 'evolution_type', 'created_by')
    list_filter = ('evolution_type', 'evolution_date')
    date_hierarchy = 'evolution_date'


@admin.register(MedicalOrder)
class MedicalOrderAdmin(admin.ModelAdmin):
    list_display = ('admission', 'order_date', 'order_type', 'priority', 'status', 'ordered_by')
    list_filter = ('order_type', 'priority', 'status', 'order_date')
    date_hierarchy = 'order_date'


@admin.register(AdmissionServiceItem)
class AdmissionServiceItemAdmin(admin.ModelAdmin):
    list_display = ('admission', 'service_code', 'service_description', 'quantity', 'unit_price', 'service_date')
    list_filter = ('service_date',)
    date_hierarchy = 'service_date'
