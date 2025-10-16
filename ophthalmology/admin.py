"""
Admin del módulo Oftalmología
"""

from django.contrib import admin
from .models import (
    OphthalConsultation, VisualAcuity, Refraction, IntraocularPressure,
    Biomicroscopy, FundusExam, LensPrescription
)


@admin.register(OphthalConsultation)
class OphthalConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_number', 'patient', 'ophthalmologist', 'consultation_date', 'status')
    list_filter = ('status', 'uses_glasses', 'uses_contact_lenses', 'consultation_date')
    search_fields = ('consultation_number', 'patient__third_party__name', 'patient__third_party__identification_number')
    date_hierarchy = 'consultation_date'
    readonly_fields = ('consultation_number', 'created_at', 'updated_at')


@admin.register(VisualAcuity)
class VisualAcuityAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'od_distance_sc', 'os_distance_sc', 'created_at')
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Refraction)
class RefractionAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'refraction_type', 'od_sphere', 'os_sphere', 'created_at')
    list_filter = ('refraction_type',)
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(IntraocularPressure)
class IntraocularPressureAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'od_pressure', 'os_pressure', 'measurement_time')
    list_filter = ('measurement_method',)
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Biomicroscopy)
class BiomicroscopyAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'created_at')
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FundusExam)
class FundusExamAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'od_cup_disc_ratio', 'os_cup_disc_ratio', 'created_at')
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LensPrescription)
class LensPrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_number', 'patient', 'ophthalmologist', 'prescription_date', 'lens_type', 'is_active')
    list_filter = ('lens_type', 'recommended_usage', 'is_active', 'prescription_date')
    search_fields = ('prescription_number', 'patient__third_party__name', 'patient__third_party__identification_number')
    date_hierarchy = 'prescription_date'
    readonly_fields = ('prescription_number', 'created_at', 'updated_at')
