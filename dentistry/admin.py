"""
Admin del módulo Odontología
"""

from django.contrib import admin
from .models import (
    DentalProcedureType, DentalCondition, DentalConsultation, Odontogram,
    OdontogramTooth, TreatmentPlan, TreatmentPlanItem, DentalProcedureRecord
)


@admin.register(DentalProcedureType)
class DentalProcedureTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'base_price', 'estimated_duration', 'is_active')
    list_filter = ('category', 'requires_anesthesia', 'is_active')
    search_fields = ('code', 'name', 'description')


@admin.register(DentalCondition)
class DentalConditionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'color', 'symbol', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(DentalConsultation)
class DentalConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_number', 'patient', 'dentist', 'consultation_date', 'status')
    list_filter = ('status', 'oral_hygiene', 'consultation_date')
    search_fields = ('consultation_number', 'patient__third_party__name', 'diagnosis')
    date_hierarchy = 'consultation_date'


@admin.register(Odontogram)
class OdontogramAdmin(admin.ModelAdmin):
    list_display = ('patient', 'dentition_type', 'odontogram_date', 'is_active', 'created_by')
    list_filter = ('dentition_type', 'is_active', 'odontogram_date')
    search_fields = ('patient__third_party__name',)
    date_hierarchy = 'odontogram_date'


@admin.register(OdontogramTooth)
class OdontogramToothAdmin(admin.ModelAdmin):
    list_display = ('odontogram', 'fdi_number', 'quadrant', 'state', 'tooth_type')
    list_filter = ('quadrant', 'state', 'tooth_type')
    search_fields = ('fdi_number', 'odontogram__patient__third_party__name')


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'patient', 'dentist', 'plan_date', 'status', 'total_estimated_cost', 'patient_consent')
    list_filter = ('status', 'patient_consent', 'plan_date')
    search_fields = ('plan_number', 'patient__third_party__name', 'diagnosis')
    date_hierarchy = 'plan_date'


@admin.register(TreatmentPlanItem)
class TreatmentPlanItemAdmin(admin.ModelAdmin):
    list_display = ('treatment_plan', 'procedure', 'tooth_fdi', 'surfaces', 'priority', 'status', 'total_cost')
    list_filter = ('priority', 'status')
    search_fields = ('treatment_plan__plan_number', 'procedure__name', 'tooth_fdi')


@admin.register(DentalProcedureRecord)
class DentalProcedureRecordAdmin(admin.ModelAdmin):
    list_display = ('record_number', 'patient', 'dentist', 'procedure', 'tooth_fdi', 'procedure_date', 'cost')
    list_filter = ('anesthesia_used', 'procedure_date')
    search_fields = ('record_number', 'patient__third_party__name', 'procedure__name', 'tooth_fdi')
    date_hierarchy = 'procedure_date'
