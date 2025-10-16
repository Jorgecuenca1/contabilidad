"""
Admin del módulo Psicología
"""

from django.contrib import admin
from .models import (
    PsychologicalConsultation, TherapySession, PsychologicalAssessment,
    PsychologicalTest, TreatmentPlan, ProgressNote
)


@admin.register(PsychologicalConsultation)
class PsychologicalConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_number', 'patient', 'psychologist', 'consultation_date', 'status', 'suicide_risk')
    list_filter = ('status', 'suicide_risk', 'homicide_risk', 'consultation_date')
    search_fields = ('consultation_number', 'patient__third_party__name', 'patient__third_party__identification_number', 'diagnosis')
    date_hierarchy = 'consultation_date'
    readonly_fields = ('consultation_number', 'created_at', 'updated_at')


@admin.register(TherapySession)
class TherapySessionAdmin(admin.ModelAdmin):
    list_display = ('session_number', 'patient', 'psychologist', 'session_date', 'session_type', 'modality', 'status')
    list_filter = ('status', 'session_type', 'modality', 'homework_completed', 'session_date')
    search_fields = ('session_number', 'patient__third_party__name', 'patient__third_party__identification_number')
    date_hierarchy = 'session_date'
    readonly_fields = ('session_number', 'created_at', 'updated_at')


@admin.register(PsychologicalAssessment)
class PsychologicalAssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessment_number', 'patient', 'psychologist', 'assessment_date', 'assessment_type')
    list_filter = ('assessment_type', 'assessment_date')
    search_fields = ('assessment_number', 'patient__third_party__name', 'patient__third_party__identification_number', 'purpose')
    date_hierarchy = 'assessment_date'
    readonly_fields = ('assessment_number', 'created_at', 'updated_at')


@admin.register(PsychologicalTest)
class PsychologicalTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'assessment', 'raw_score', 'standardized_score', 'percentile')
    list_filter = ('test_category',)
    search_fields = ('test_name', 'test_category', 'assessment__patient__third_party__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'patient', 'psychologist', 'plan_date', 'start_date', 'status', 'estimated_sessions')
    list_filter = ('status', 'plan_date', 'start_date')
    search_fields = ('plan_number', 'patient__third_party__name', 'patient__third_party__identification_number', 'diagnosis')
    date_hierarchy = 'plan_date'
    readonly_fields = ('plan_number', 'created_at', 'updated_at')


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ('treatment_plan', 'note_date', 'created_by')
    list_filter = ('note_date',)
    search_fields = ('treatment_plan__patient__third_party__name', 'subjective', 'assessment')
    date_hierarchy = 'note_date'
    readonly_fields = ('created_at', 'updated_at')
