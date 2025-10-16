"""
Admin del módulo Urgencias
Sistema de urgencias médicas con triage, admisión y atención
"""

from django.contrib import admin
from .models import (
    TriageAssessment, EmergencyAdmission, VitalSignsRecord,
    EmergencyAttention, EmergencyProcedure, EmergencyDischarge
)


class VitalSignsRecordInline(admin.TabularInline):
    """Inline para signos vitales en admisión"""
    model = VitalSignsRecord
    extra = 0
    readonly_fields = ['recorded_datetime', 'created_at']
    fields = [
        'recorded_datetime', 'blood_pressure_systolic', 'blood_pressure_diastolic',
        'heart_rate', 'respiratory_rate', 'temperature', 'oxygen_saturation',
        'pain_scale', 'recorded_by'
    ]
    raw_id_fields = ['recorded_by']


class EmergencyProcedureInline(admin.TabularInline):
    """Inline para procedimientos en admisión"""
    model = EmergencyProcedure
    extra = 0
    readonly_fields = ['created_at']
    fields = [
        'procedure_type', 'procedure_name', 'procedure_datetime',
        'performed_by', 'outcome'
    ]
    raw_id_fields = ['performed_by', 'created_by']


@admin.register(TriageAssessment)
class TriageAssessmentAdmin(admin.ModelAdmin):
    """Admin para Evaluaciones de Triage"""
    list_display = [
        'triage_number', 'patient', 'triage_level', 'triage_color',
        'arrival_datetime', 'triage_datetime', 'patient_called', 'created_at'
    ]
    list_filter = [
        'triage_level', 'arrival_mode', 'consciousness_level',
        'patient_called', 'company', 'arrival_datetime', 'triage_datetime'
    ]
    search_fields = [
        'triage_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'chief_complaint', 'observations'
    ]
    date_hierarchy = 'arrival_datetime'
    readonly_fields = [
        'id', 'triage_number', 'triage_color', 'priority_time',
        'triage_datetime', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['patient', 'triage_nurse', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'triage_number', 'triage_color', 'patient'
            )
        }),
        ('Llegada', {
            'fields': (
                'arrival_datetime', 'triage_datetime', 'arrival_mode', 'accompanied_by'
            )
        }),
        ('Motivo de Consulta', {
            'fields': (
                'chief_complaint', 'symptom_duration'
            )
        }),
        ('Signos Vitales', {
            'fields': (
                'blood_pressure', 'heart_rate', 'respiratory_rate',
                'temperature', 'oxygen_saturation', 'pain_scale'
            )
        }),
        ('Evaluación Neurológica', {
            'fields': (
                'consciousness_level', 'glasgow_score'
            )
        }),
        ('Clasificación de Triage', {
            'fields': (
                'triage_level', 'priority_time'
            )
        }),
        ('Información Clínica', {
            'fields': (
                'warning_signs', 'allergies', 'current_medications'
            ),
            'classes': ('collapse',)
        }),
        ('Personal y Observaciones', {
            'fields': (
                'triage_nurse', 'observations'
            )
        }),
        ('Estado', {
            'fields': (
                'patient_called', 'call_datetime'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('patient__third_party', 'triage_nurse', 'company', 'created_by')


@admin.register(EmergencyAdmission)
class EmergencyAdmissionAdmin(admin.ModelAdmin):
    """Admin para Admisiones de Urgencias"""
    list_display = [
        'admission_number', 'patient', 'status', 'triage',
        'attending_physician', 'admission_datetime', 'emergency_area',
        'bed_number', 'created_at'
    ]
    list_filter = [
        'status', 'company', 'admission_datetime', 'requires_authorization',
        'emergency_area'
    ]
    search_fields = [
        'admission_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'triage__triage_number', 'emergency_area', 'bed_number',
        'insurance_company', 'authorization_number'
    ]
    date_hierarchy = 'admission_datetime'
    readonly_fields = [
        'id', 'admission_number', 'created_at', 'updated_at'
    ]
    raw_id_fields = [
        'patient', 'triage', 'attending_physician', 'assigned_nurse', 'created_by'
    ]
    inlines = [VitalSignsRecordInline, EmergencyProcedureInline]

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'admission_number', 'status'
            )
        }),
        ('Paciente y Triage', {
            'fields': (
                'patient', 'triage'
            )
        }),
        ('Fechas y Tiempos', {
            'fields': (
                'admission_datetime', 'attention_start_datetime', 'attention_end_datetime'
            )
        }),
        ('Ubicación', {
            'fields': (
                'emergency_area', 'bed_number'
            )
        }),
        ('Personal Médico', {
            'fields': (
                'attending_physician', 'assigned_nurse'
            )
        }),
        ('Información de Seguro', {
            'fields': (
                'insurance_company', 'authorization_number', 'requires_authorization'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': (
                'admission_notes',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient__third_party', 'triage', 'attending_physician',
            'assigned_nurse', 'company', 'created_by'
        )


@admin.register(VitalSignsRecord)
class VitalSignsRecordAdmin(admin.ModelAdmin):
    """Admin para Registros de Signos Vitales"""
    list_display = [
        'admission', 'recorded_datetime', 'blood_pressure_systolic',
        'blood_pressure_diastolic', 'heart_rate', 'respiratory_rate',
        'temperature', 'oxygen_saturation', 'pain_scale', 'recorded_by'
    ]
    list_filter = [
        'company', 'recorded_datetime', 'admission__status'
    ]
    search_fields = [
        'admission__admission_number', 'admission__patient__third_party__first_name',
        'admission__patient__third_party__last_name', 'observations'
    ]
    date_hierarchy = 'recorded_datetime'
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['admission', 'recorded_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'admission', 'recorded_datetime'
            )
        }),
        ('Presión Arterial', {
            'fields': (
                'blood_pressure_systolic', 'blood_pressure_diastolic'
            )
        }),
        ('Signos Vitales', {
            'fields': (
                'heart_rate', 'respiratory_rate', 'temperature', 'oxygen_saturation'
            )
        }),
        ('Evaluación del Dolor', {
            'fields': (
                'pain_scale',
            )
        }),
        ('Datos Antropométricos', {
            'fields': (
                'weight', 'height'
            ),
            'classes': ('collapse',)
        }),
        ('Evaluación Neurológica', {
            'fields': (
                'glasgow_score',
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': (
                'observations',
            )
        }),
        ('Personal', {
            'fields': (
                'recorded_by', 'created_at'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('admission__patient__third_party', 'recorded_by', 'company')


@admin.register(EmergencyAttention)
class EmergencyAttentionAdmin(admin.ModelAdmin):
    """Admin para Atenciones de Urgencias"""
    list_display = [
        'attention_number', 'patient', 'physician', 'admission',
        'attention_date', 'created_at'
    ]
    list_filter = [
        'company', 'attention_date', 'physician'
    ]
    search_fields = [
        'attention_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'admission__admission_number', 'physician__first_name',
        'physician__last_name', 'diagnosis', 'current_illness'
    ]
    date_hierarchy = 'attention_date'
    readonly_fields = ['id', 'attention_number', 'created_at', 'updated_at']
    raw_id_fields = ['patient', 'admission', 'physician', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'attention_number', 'admission'
            )
        }),
        ('Paciente y Médico', {
            'fields': (
                'patient', 'physician', 'attention_date'
            )
        }),
        ('Anamnesis', {
            'fields': (
                'current_illness', 'review_of_systems', 'personal_history',
                'family_history', 'allergies', 'current_medications'
            )
        }),
        ('Examen Físico', {
            'fields': (
                'general_appearance', 'physical_examination'
            )
        }),
        ('Examen por Sistemas', {
            'fields': (
                'cardiovascular_exam', 'respiratory_exam',
                'abdominal_exam', 'neurological_exam'
            ),
            'classes': ('collapse',)
        }),
        ('Diagnóstico', {
            'fields': (
                'diagnosis', 'differential_diagnosis'
            )
        }),
        ('Plan de Tratamiento', {
            'fields': (
                'treatment_plan', 'medications_prescribed', 'procedures_indicated'
            )
        }),
        ('Estudios Solicitados', {
            'fields': (
                'lab_tests_ordered', 'imaging_studies_ordered'
            ),
            'classes': ('collapse',)
        }),
        ('Evolución y Pronóstico', {
            'fields': (
                'clinical_evolution', 'prognosis'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': (
                'observations',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient__third_party', 'admission', 'physician', 'company', 'created_by'
        )


@admin.register(EmergencyProcedure)
class EmergencyProcedureAdmin(admin.ModelAdmin):
    """Admin para Procedimientos de Urgencias"""
    list_display = [
        'admission', 'procedure_type', 'procedure_name', 'procedure_datetime',
        'performed_by', 'outcome', 'created_at'
    ]
    list_filter = [
        'procedure_type', 'company', 'procedure_datetime'
    ]
    search_fields = [
        'admission__admission_number', 'admission__patient__third_party__first_name',
        'admission__patient__third_party__last_name', 'procedure_name',
        'indication', 'procedure_description', 'outcome'
    ]
    date_hierarchy = 'procedure_datetime'
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['admission', 'performed_by', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'admission'
            )
        }),
        ('Tipo y Nombre', {
            'fields': (
                'procedure_type', 'procedure_name', 'procedure_datetime'
            )
        }),
        ('Descripción', {
            'fields': (
                'indication', 'procedure_description', 'materials_used'
            )
        }),
        ('Personal', {
            'fields': (
                'performed_by', 'assisted_by'
            )
        }),
        ('Resultado', {
            'fields': (
                'complications', 'outcome', 'observations'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'admission__patient__third_party', 'performed_by', 'company', 'created_by'
        )


@admin.register(EmergencyDischarge)
class EmergencyDischargeAdmin(admin.ModelAdmin):
    """Admin para Altas de Urgencias"""
    list_display = [
        'discharge_number', 'patient', 'discharge_type', 'discharge_condition',
        'admission', 'discharge_datetime', 'discharge_physician', 'created_at'
    ]
    list_filter = [
        'discharge_type', 'discharge_condition', 'company', 'discharge_datetime',
        'follow_up_required'
    ]
    search_fields = [
        'discharge_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'admission__admission_number', 'final_diagnosis', 'recommendations'
    ]
    date_hierarchy = 'discharge_datetime'
    readonly_fields = ['id', 'discharge_number', 'created_at']
    raw_id_fields = ['patient', 'admission', 'discharge_physician', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'discharge_number'
            )
        }),
        ('Paciente y Admisión', {
            'fields': (
                'patient', 'admission'
            )
        }),
        ('Información del Alta', {
            'fields': (
                'discharge_datetime', 'discharge_type', 'discharge_condition'
            )
        }),
        ('Diagnóstico Final', {
            'fields': (
                'final_diagnosis',
            )
        }),
        ('Tratamiento y Recomendaciones', {
            'fields': (
                'treatment_received', 'discharge_medications',
                'recommendations', 'warning_signs'
            )
        }),
        ('Seguimiento', {
            'fields': (
                'follow_up_required', 'follow_up_specialty', 'follow_up_days'
            ),
            'classes': ('collapse',)
        }),
        ('Incapacidad', {
            'fields': (
                'sick_leave_days',
            ),
            'classes': ('collapse',)
        }),
        ('Hospitalización (si aplica)', {
            'fields': (
                'hospitalization_service', 'bed_assigned'
            ),
            'classes': ('collapse',)
        }),
        ('Traslado (si aplica)', {
            'fields': (
                'transfer_institution', 'transfer_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Personal Médico', {
            'fields': (
                'discharge_physician',
            )
        }),
        ('Observaciones', {
            'fields': (
                'observations',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient__third_party', 'admission', 'discharge_physician', 'company', 'created_by'
        )
