"""
Admin del módulo Telemedicina
Consultas virtuales, atención domiciliaria y firma digital
"""

from django.contrib import admin
from .models import (
    TelemedicineAppointment, VirtualConsultation, HomeCareVisit,
    MedicalDocument, DigitalSignature, TelemedicineStatistics
)


@admin.register(TelemedicineAppointment)
class TelemedicineAppointmentAdmin(admin.ModelAdmin):
    """Admin para Citas de Telemedicina"""
    list_display = [
        'appointment_number', 'patient', 'doctor', 'appointment_type',
        'scheduled_date', 'status', 'priority', 'created_at'
    ]
    list_filter = [
        'status', 'appointment_type', 'priority', 'company',
        'scheduled_date', 'confirmation_sent', 'reminder_sent'
    ]
    search_fields = [
        'appointment_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'doctor__first_name', 'doctor__last_name', 'reason', 'specialty'
    ]
    date_hierarchy = 'scheduled_date'
    readonly_fields = ['id', 'appointment_number', 'created_at', 'updated_at']
    raw_id_fields = ['patient', 'doctor', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'appointment_number', 'status'
            )
        }),
        ('Paciente y Médico', {
            'fields': (
                'patient', 'doctor'
            )
        }),
        ('Tipo y Programación', {
            'fields': (
                'appointment_type', 'scheduled_date', 'duration_minutes',
                'actual_start_time', 'actual_end_time'
            )
        }),
        ('Motivo y Detalles', {
            'fields': (
                'reason', 'specialty', 'priority', 'pre_consultation_notes'
            )
        }),
        ('Consulta Virtual (si aplica)', {
            'fields': (
                'meeting_link', 'meeting_platform', 'meeting_id', 'meeting_password'
            ),
            'classes': ('collapse',)
        }),
        ('Atención Domiciliaria (si aplica)', {
            'fields': (
                'home_address', 'home_city', 'home_phone', 'special_instructions'
            ),
            'classes': ('collapse',)
        }),
        ('Estado y Seguimiento', {
            'fields': (
                'confirmation_sent', 'reminder_sent', 'cancellation_reason'
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
        return qs.select_related('patient__third_party', 'doctor', 'company', 'created_by')


@admin.register(VirtualConsultation)
class VirtualConsultationAdmin(admin.ModelAdmin):
    """Admin para Consultas Virtuales"""
    list_display = [
        'consultation_number', 'patient', 'doctor', 'consultation_type',
        'consultation_date', 'duration_minutes', 'connection_quality', 'created_at'
    ]
    list_filter = [
        'consultation_type', 'connection_quality', 'company', 'consultation_date',
        'requires_in_person_visit', 'follow_up_required', 'medical_certificate_issued'
    ]
    search_fields = [
        'consultation_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'doctor__first_name', 'doctor__last_name', 'chief_complaint',
        'symptoms', 'diagnosis'
    ]
    date_hierarchy = 'consultation_date'
    readonly_fields = ['id', 'consultation_number', 'created_at', 'updated_at']
    raw_id_fields = ['patient', 'doctor', 'appointment', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'consultation_number', 'appointment'
            )
        }),
        ('Paciente y Médico', {
            'fields': (
                'patient', 'doctor', 'consultation_type', 'consultation_date', 'duration_minutes'
            )
        }),
        ('Motivo y Síntomas', {
            'fields': (
                'chief_complaint', 'symptoms', 'symptoms_duration'
            )
        }),
        ('Examen Remoto', {
            'fields': (
                'remote_examination', 'vital_signs_reported'
            )
        }),
        ('Diagnóstico y Tratamiento', {
            'fields': (
                'diagnosis', 'treatment_plan', 'medications_prescribed'
            )
        }),
        ('Recomendaciones', {
            'fields': (
                'recommendations', 'requires_in_person_visit',
                'follow_up_required', 'follow_up_date'
            )
        }),
        ('Exámenes Solicitados', {
            'fields': (
                'lab_tests_ordered', 'imaging_studies_ordered'
            ),
            'classes': ('collapse',)
        }),
        ('Incapacidades y Certificados', {
            'fields': (
                'sick_leave_days', 'medical_certificate_issued'
            ),
            'classes': ('collapse',)
        }),
        ('Calidad Técnica', {
            'fields': (
                'connection_quality', 'technical_issues'
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
        return qs.select_related('patient__third_party', 'doctor', 'company', 'appointment')


@admin.register(HomeCareVisit)
class HomeCareVisitAdmin(admin.ModelAdmin):
    """Admin para Atención Domiciliaria"""
    list_display = [
        'visit_number', 'patient', 'healthcare_professional', 'visit_type',
        'scheduled_date', 'status', 'city', 'patient_satisfaction', 'created_at'
    ]
    list_filter = [
        'status', 'visit_type', 'company', 'scheduled_date',
        'next_visit_required', 'patient_satisfaction'
    ]
    search_fields = [
        'visit_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'healthcare_professional__first_name', 'healthcare_professional__last_name',
        'address', 'city', 'neighborhood', 'visit_reason'
    ]
    date_hierarchy = 'scheduled_date'
    readonly_fields = ['id', 'visit_number', 'created_at', 'updated_at']
    raw_id_fields = ['patient', 'healthcare_professional', 'appointment', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'visit_number', 'status', 'appointment'
            )
        }),
        ('Paciente y Personal', {
            'fields': (
                'patient', 'healthcare_professional', 'accompanying_staff'
            )
        }),
        ('Tipo y Programación', {
            'fields': (
                'visit_type', 'scheduled_date', 'actual_arrival_time',
                'actual_departure_time', 'duration_minutes'
            )
        }),
        ('Dirección', {
            'fields': (
                'address', 'city', 'neighborhood', 'landmark_reference', 'contact_phone'
            )
        }),
        ('Motivo y Estado Inicial', {
            'fields': (
                'visit_reason', 'patient_condition_on_arrival'
            )
        }),
        ('Signos Vitales', {
            'fields': (
                'blood_pressure', 'heart_rate', 'respiratory_rate',
                'temperature', 'oxygen_saturation'
            )
        }),
        ('Procedimientos', {
            'fields': (
                'procedures_performed', 'medications_administered', 'medical_supplies_used'
            ),
            'classes': ('collapse',)
        }),
        ('Evaluación y Diagnóstico', {
            'fields': (
                'clinical_assessment', 'diagnosis', 'treatment_provided'
            )
        }),
        ('Instrucciones', {
            'fields': (
                'instructions_to_patient', 'instructions_to_caregiver',
                'next_visit_required', 'next_visit_date'
            )
        }),
        ('Satisfacción y Observaciones', {
            'fields': (
                'patient_satisfaction', 'observations', 'complications'
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
        return qs.select_related('patient__third_party', 'healthcare_professional', 'company')


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    """Admin para Documentos Médicos"""
    list_display = [
        'document_number', 'patient', 'document_type', 'document_title',
        'issue_date', 'is_digitally_signed', 'signed_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'company', 'is_digitally_signed',
        'issue_date', 'signature_date'
    ]
    search_fields = [
        'document_number', 'patient__third_party__first_name',
        'patient__third_party__last_name', 'patient__medical_record_number',
        'document_title', 'diagnosis', 'document_content'
    ]
    date_hierarchy = 'issue_date'
    readonly_fields = [
        'id', 'document_number', 'is_digitally_signed', 'signed_by',
        'signature_date', 'digital_signature_hash', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['patient', 'virtual_consultation', 'home_care_visit', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'document_number', 'patient'
            )
        }),
        ('Relaciones', {
            'fields': (
                'virtual_consultation', 'home_care_visit'
            )
        }),
        ('Tipo y Contenido', {
            'fields': (
                'document_type', 'document_title', 'document_content'
            )
        }),
        ('Información Médica', {
            'fields': (
                'diagnosis', 'observations'
            )
        }),
        ('Fechas', {
            'fields': (
                'issue_date', 'valid_until'
            )
        }),
        ('Firma Digital', {
            'fields': (
                'is_digitally_signed', 'signed_by', 'signature_date', 'digital_signature_hash'
            ),
            'classes': ('collapse',)
        }),
        ('Archivo PDF', {
            'fields': (
                'pdf_file_path',
            ),
            'classes': ('collapse',)
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
            'patient__third_party', 'virtual_consultation', 'home_care_visit',
            'signed_by', 'company'
        )


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    """Admin para Firmas Digitales"""
    list_display = [
        'document', 'signer', 'signature_date', 'signature_method',
        'ip_address', 'is_valid'
    ]
    list_filter = [
        'company', 'is_valid', 'signature_method', 'signature_date', 'verification_date'
    ]
    search_fields = [
        'document__document_number', 'signer__first_name', 'signer__last_name',
        'signature_hash', 'ip_address', 'certificate_serial'
    ]
    date_hierarchy = 'signature_date'
    readonly_fields = [
        'id', 'signature_date', 'signature_hash', 'ip_address',
        'device_info', 'verification_date'
    ]
    raw_id_fields = ['document', 'signer']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'document', 'signer'
            )
        }),
        ('Datos de la Firma', {
            'fields': (
                'signature_date', 'signature_hash', 'signature_method'
            )
        }),
        ('Información del Dispositivo', {
            'fields': (
                'ip_address', 'device_info'
            )
        }),
        ('Verificación', {
            'fields': (
                'is_valid', 'verification_date'
            )
        }),
        ('Certificado Digital', {
            'fields': (
                'certificate_serial', 'certificate_issuer'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': (
                'observations',
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('document', 'signer', 'company')


@admin.register(TelemedicineStatistics)
class TelemedicineStatisticsAdmin(admin.ModelAdmin):
    """Admin para Estadísticas de Telemedicina"""
    list_display = [
        'company', 'period_start', 'period_end', 'total_appointments',
        'completed_appointments', 'virtual_consultations_count',
        'home_care_visits_count', 'generated_date'
    ]
    list_filter = [
        'company', 'period_start', 'period_end', 'generated_date'
    ]
    search_fields = [
        'company__name'
    ]
    date_hierarchy = 'period_start'
    readonly_fields = ['id', 'generated_date']
    raw_id_fields = ['generated_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'period_start', 'period_end'
            )
        }),
        ('Estadísticas de Citas', {
            'fields': (
                'total_appointments', 'completed_appointments', 'cancelled_appointments'
            )
        }),
        ('Por Tipo', {
            'fields': (
                'virtual_consultations_count', 'home_care_visits_count'
            )
        }),
        ('Documentos', {
            'fields': (
                'documents_generated', 'digital_signatures_count'
            )
        }),
        ('Calidad', {
            'fields': (
                'average_consultation_duration', 'patient_satisfaction_average'
            )
        }),
        ('Datos Adicionales', {
            'fields': (
                'statistics_data',
            ),
            'classes': ('collapse',)
        }),
        ('Generación', {
            'fields': (
                'generated_date', 'generated_by'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'generated_by')
