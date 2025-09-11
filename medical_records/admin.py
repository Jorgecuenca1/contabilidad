from django.contrib import admin
from .models import MedicalRecord, Consultation, MedicalAttachment, SpecialtyTemplate


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['record_number', 'patient', 'record_type', 'attending_physician', 'status', 'last_update']
    list_filter = ['record_type', 'status', 'company']
    search_fields = ['record_number', 'patient__name', 'attending_physician__first_name', 'attending_physician__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['consultation_date', 'medical_record', 'consultation_type', 'attending_physician', 'status']
    list_filter = ['consultation_type', 'status', 'consultation_date']
    search_fields = ['medical_record__record_number', 'medical_record__patient__name', 'chief_complaint']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(MedicalAttachment)
class MedicalAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'medical_record', 'attachment_type', 'created_at']
    list_filter = ['attachment_type', 'created_at']
    search_fields = ['title', 'medical_record__record_number']


@admin.register(SpecialtyTemplate)
class SpecialtyTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'company', 'is_active']
    list_filter = ['specialty', 'is_active', 'company']
    search_fields = ['name']