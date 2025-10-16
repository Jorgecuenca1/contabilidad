"""
Admin del módulo de Pacientes
"""

from django.contrib import admin
from .models import Patient, EPS, PatientInsuranceHistory, PatientDocument


@admin.register(EPS)
class EPSAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'regime', 'is_active']
    list_filter = ['regime', 'is_active']
    search_fields = ['code', 'name', 'nit']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['medical_record_number', 'get_full_name', 'get_age_string', 'eps', 'is_active']
    list_filter = ['is_active', 'regime_type', 'eps']
    search_fields = ['medical_record_number', 'third_party__first_name', 'third_party__last_name', 'third_party__document_number']
    raw_id_fields = ['third_party', 'eps']


@admin.register(PatientInsuranceHistory)
class PatientInsuranceHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'eps', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    raw_id_fields = ['patient', 'eps']


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'document_type', 'title', 'issue_date', 'is_active']
    list_filter = ['document_type', 'is_active']
    raw_id_fields = ['patient']
