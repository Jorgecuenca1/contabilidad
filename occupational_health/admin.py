"""
Admin del módulo Salud Ocupacional
"""

from django.contrib import admin
from .models import (
    OccupationalExam, LaboratoryTest, WorkAptitude,
    OccupationalRisk, HealthRecommendation, CompanyReport
)


@admin.register(OccupationalExam)
class OccupationalExamAdmin(admin.ModelAdmin):
    """Administración de exámenes ocupacionales"""
    list_display = [
        'exam_number', 'patient', 'company_name', 'job_position',
        'exam_type', 'exam_date', 'status', 'examiner', 'created_at'
    ]
    list_filter = ['exam_type', 'status', 'exam_date', 'created_at', 'company']
    search_fields = [
        'exam_number', 'patient__third_party__name',
        'patient__third_party__identification_number',
        'company_name', 'job_position', 'work_area', 'diagnosis'
    ]
    date_hierarchy = 'exam_date'
    readonly_fields = ['exam_number', 'bmi', 'created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'company', 'exam_number', 'patient', 'exam_type',
                'exam_date', 'examiner', 'status'
            )
        }),
        ('Información Laboral', {
            'fields': (
                'company_name', 'job_position', 'work_area',
                'years_in_position', 'work_schedule'
            )
        }),
        ('Historia Ocupacional', {
            'fields': (
                'previous_jobs', 'occupational_exposures', 'use_of_ppe'
            )
        }),
        ('Antecedentes', {
            'fields': (
                'personal_medical_history', 'family_medical_history',
                'current_medications', 'allergies'
            )
        }),
        ('Hábitos', {
            'fields': ('smoking', 'alcohol', 'physical_activity')
        }),
        ('Examen Físico General', {
            'fields': (
                'blood_pressure', 'heart_rate', 'respiratory_rate',
                'temperature', 'weight', 'height', 'bmi'
            )
        }),
        ('Examen por Sistemas', {
            'fields': (
                'head_neck_exam', 'cardiovascular_exam', 'respiratory_exam',
                'abdominal_exam', 'musculoskeletal_exam', 'neurological_exam',
                'dermatological_exam'
            )
        }),
        ('Exámenes Complementarios', {
            'fields': (
                'laboratory_tests_ordered', 'imaging_studies_ordered',
                'other_tests_ordered'
            )
        }),
        ('Resultados', {
            'fields': ('diagnosis', 'findings', 'observations')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('patient__third_party', 'examiner', 'company', 'created_by')


@admin.register(LaboratoryTest)
class LaboratoryTestAdmin(admin.ModelAdmin):
    """Administración de exámenes de laboratorio"""
    list_display = [
        'exam', 'test_name', 'test_type', 'test_date',
        'result_status', 'laboratory_name', 'created_at'
    ]
    list_filter = ['test_type', 'result_status', 'test_date', 'company']
    search_fields = [
        'test_name', 'exam__exam_number',
        'exam__patient__third_party__name', 'laboratory_name'
    ]
    date_hierarchy = 'test_date'
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': ('company', 'exam', 'test_type', 'test_name', 'test_date')
        }),
        ('Resultados', {
            'fields': (
                'result_value', 'result_status', 'reference_values',
                'interpretation'
            )
        }),
        ('Laboratorio', {
            'fields': ('laboratory_name', 'performed_by')
        }),
        ('Observaciones', {
            'fields': ('observations',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('exam__patient__third_party', 'company', 'created_by')


@admin.register(WorkAptitude)
class WorkAptitudeAdmin(admin.ModelAdmin):
    """Administración de aptitudes laborales"""
    list_display = [
        'aptitude_number', 'exam', 'aptitude', 'issue_date',
        'valid_until', 'requires_follow_up', 'issued_by', 'created_at'
    ]
    list_filter = ['aptitude', 'requires_follow_up', 'issue_date', 'company']
    search_fields = [
        'aptitude_number', 'exam__exam_number',
        'exam__patient__third_party__name',
        'exam__patient__third_party__identification_number'
    ]
    date_hierarchy = 'issue_date'
    readonly_fields = ['aptitude_number', 'created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'company', 'aptitude_number', 'exam', 'aptitude',
                'issue_date', 'valid_until'
            )
        }),
        ('Restricciones y Recomendaciones', {
            'fields': ('restrictions', 'recommendations', 'medical_justification')
        }),
        ('Seguimiento', {
            'fields': (
                'requires_follow_up', 'follow_up_date', 'follow_up_notes'
            )
        }),
        ('Observaciones', {
            'fields': ('observations',)
        }),
        ('Auditoría', {
            'fields': ('issued_by', 'created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('exam__patient__third_party', 'issued_by', 'company', 'created_by')


@admin.register(OccupationalRisk)
class OccupationalRiskAdmin(admin.ModelAdmin):
    """Administración de riesgos ocupacionales"""
    list_display = [
        'exam', 'risk_type', 'risk_level', 'exposure_time',
        'created_at'
    ]
    list_filter = ['risk_type', 'risk_level', 'created_at', 'company']
    search_fields = [
        'exam__exam_number', 'exam__patient__third_party__name',
        'risk_description', 'control_measures'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'company', 'exam', 'risk_type', 'risk_level',
                'exposure_time'
            )
        }),
        ('Descripción del Riesgo', {
            'fields': ('risk_description',)
        }),
        ('Medidas de Control', {
            'fields': ('control_measures', 'recommended_controls')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('exam__patient__third_party', 'company', 'created_by')


@admin.register(HealthRecommendation)
class HealthRecommendationAdmin(admin.ModelAdmin):
    """Administración de recomendaciones de salud"""
    list_display = [
        'exam', 'category', 'priority', 'implementation_deadline',
        'implemented', 'responsible_person', 'created_at'
    ]
    list_filter = [
        'category', 'priority', 'implemented',
        'implementation_deadline', 'company'
    ]
    search_fields = [
        'exam__exam_number', 'exam__patient__third_party__name',
        'recommendation', 'responsible_person'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'company', 'exam', 'category', 'priority',
                'implementation_deadline', 'responsible_person'
            )
        }),
        ('Recomendación', {
            'fields': ('recommendation',)
        }),
        ('Implementación', {
            'fields': (
                'implemented', 'implementation_date', 'implementation_notes'
            )
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('exam__patient__third_party', 'company', 'created_by')


@admin.register(CompanyReport)
class CompanyReportAdmin(admin.ModelAdmin):
    """Administración de reportes empresariales"""
    list_display = [
        'report_number', 'report_type', 'report_title', 'client_company',
        'period_start', 'period_end', 'status', 'generated_date', 'created_at'
    ]
    list_filter = [
        'report_type', 'status', 'period_start', 'period_end',
        'generated_date', 'sent_date', 'company'
    ]
    search_fields = [
        'report_number', 'report_title', 'client_company',
        'summary', 'findings', 'recommendations'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = ['report_number', 'statistics', 'created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'company', 'report_number', 'report_type', 'report_title',
                'status'
            )
        }),
        ('Período y Filtros', {
            'fields': (
                'period_start', 'period_end', 'client_company',
                'work_area_filter', 'job_position_filter'
            )
        }),
        ('Contenido del Reporte', {
            'fields': (
                'summary', 'findings', 'statistics', 'recommendations',
                'conclusions'
            )
        }),
        ('Anexos', {
            'fields': ('attachments_description',)
        }),
        ('Estado y Envío', {
            'fields': (
                'generated_date', 'sent_date', 'recipient'
            )
        }),
        ('Observaciones', {
            'fields': ('observations',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'created_by')
