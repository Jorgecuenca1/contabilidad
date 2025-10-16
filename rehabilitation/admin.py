"""
Admin del módulo Rehabilitación
"""

from django.contrib import admin
from .models import (
    RehabilitationConsultation, PhysicalAssessment, RehabilitationPlan,
    RehabilitationSession, ExercisePrescription, ProgressMeasurement
)


@admin.register(RehabilitationConsultation)
class RehabilitationConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_number', 'patient', 'physiotherapist', 'consultation_date', 'pain_level', 'status')
    list_filter = ('status', 'pain_level', 'consultation_date')
    search_fields = ('consultation_number', 'patient__third_party__name', 'patient__third_party__identification_number', 'diagnosis')
    date_hierarchy = 'consultation_date'
    readonly_fields = ('consultation_number', 'created_at', 'updated_at')


@admin.register(PhysicalAssessment)
class PhysicalAssessmentAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'created_at', 'created_by')
    search_fields = ('consultation__consultation_number', 'consultation__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RehabilitationPlan)
class RehabilitationPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'patient', 'physiotherapist', 'plan_date', 'start_date', 'frequency_per_week', 'status')
    list_filter = ('status', 'plan_date', 'start_date')
    search_fields = ('plan_number', 'patient__third_party__name', 'patient__third_party__identification_number', 'diagnosis')
    date_hierarchy = 'plan_date'
    readonly_fields = ('plan_number', 'created_at', 'updated_at')


@admin.register(RehabilitationSession)
class RehabilitationSessionAdmin(admin.ModelAdmin):
    list_display = ('session_number', 'patient', 'physiotherapist', 'session_date', 'pain_level_pre', 'pain_level_post', 'status')
    list_filter = ('status', 'session_date')
    search_fields = ('session_number', 'patient__third_party__name', 'patient__third_party__identification_number')
    date_hierarchy = 'session_date'
    readonly_fields = ('session_number', 'created_at', 'updated_at')


@admin.register(ExercisePrescription)
class ExercisePrescriptionAdmin(admin.ModelAdmin):
    list_display = ('exercise_name', 'exercise_type', 'plan', 'sets', 'repetitions', 'is_active')
    list_filter = ('exercise_type', 'is_active')
    search_fields = ('exercise_name', 'plan__patient__third_party__name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProgressMeasurement)
class ProgressMeasurementAdmin(admin.ModelAdmin):
    list_display = ('plan', 'measurement_date', 'pain_level', 'patient_reported_improvement', 'measured_by')
    list_filter = ('measurement_date', 'pain_level')
    search_fields = ('plan__patient__third_party__name', 'therapist_assessment')
    date_hierarchy = 'measurement_date'
    readonly_fields = ('created_at', 'updated_at')
