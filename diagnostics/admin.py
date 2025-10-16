"""
Configuración del Admin para el módulo de Diagnósticos CIE-10
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CIE10Version, CIE10Chapter, CIE10Group, CIE10Diagnosis,
    FavoriteDiagnosis, DiagnosisImportLog
)


@admin.register(CIE10Version)
class CIE10VersionAdmin(admin.ModelAdmin):
    """
    Administración de versiones del catálogo CIE-10
    """
    list_display = [
        'version_code', 'name', 'release_date', 'is_current_badge',
        'is_active_badge', 'diagnosis_count', 'created_at'
    ]
    list_filter = ['is_current', 'is_active', 'release_date']
    search_fields = ['version_code', 'name', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'release_date'

    fieldsets = (
        ('Información General', {
            'fields': ('version_code', 'name', 'release_date', 'description')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_current')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def is_current_badge(self, obj):
        if obj.is_current:
            return format_html('<span style="color: green;">✓ Actual</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_current_badge.short_description = 'Actual'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    is_active_badge.short_description = 'Estado'

    def diagnosis_count(self, obj):
        count = obj.diagnoses.count()
        return format_html('<strong>{}</strong> diagnósticos', count)
    diagnosis_count.short_description = 'Diagnósticos'

    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CIE10Chapter)
class CIE10ChapterAdmin(admin.ModelAdmin):
    """
    Administración de capítulos CIE-10
    """
    list_display = [
        'code', 'name', 'code_range', 'version', 'order', 'groups_count', 'diagnoses_count'
    ]
    list_filter = ['version']
    search_fields = ['code', 'name']
    ordering = ['order', 'code']

    fieldsets = (
        ('Información del Capítulo', {
            'fields': ('version', 'code', 'name', 'order')
        }),
        ('Rango de Códigos', {
            'fields': ('code_range_start', 'code_range_end')
        }),
    )

    def code_range(self, obj):
        return f"{obj.code_range_start} - {obj.code_range_end}"
    code_range.short_description = 'Rango'

    def groups_count(self, obj):
        count = obj.groups.count()
        return format_html('<span>{} grupos</span>', count)
    groups_count.short_description = 'Grupos'

    def diagnoses_count(self, obj):
        count = obj.diagnoses.count()
        return format_html('<strong>{}</strong>', count)
    diagnoses_count.short_description = 'Diagnósticos'


@admin.register(CIE10Group)
class CIE10GroupAdmin(admin.ModelAdmin):
    """
    Administración de grupos CIE-10
    """
    list_display = [
        'code_range', 'name', 'chapter', 'order', 'diagnoses_count'
    ]
    list_filter = ['chapter', 'chapter__version']
    search_fields = ['name', 'code_range_start', 'code_range_end']
    ordering = ['order', 'code_range_start']

    fieldsets = (
        ('Información del Grupo', {
            'fields': ('chapter', 'name', 'order')
        }),
        ('Rango de Códigos', {
            'fields': ('code_range_start', 'code_range_end')
        }),
    )

    def code_range(self, obj):
        return f"{obj.code_range_start} - {obj.code_range_end}"
    code_range.short_description = 'Rango'

    def diagnoses_count(self, obj):
        count = obj.diagnoses.count()
        return format_html('<strong>{}</strong>', count)
    diagnoses_count.short_description = 'Diagnósticos'


@admin.register(CIE10Diagnosis)
class CIE10DiagnosisAdmin(admin.ModelAdmin):
    """
    Administración de diagnósticos CIE-10
    """
    list_display = [
        'code', 'name_truncated', 'chapter', 'gender_badge', 'special_flags',
        'is_active_badge', 'use_count', 'last_used'
    ]
    list_filter = [
        'is_active', 'is_deprecated', 'applicable_gender', 'chapter', 'version',
        'high_cost', 'mandatory_notification', 'rare_disease', 'chronic_disease'
    ]
    search_fields = ['code', 'name', 'synonyms']
    readonly_fields = ['use_count', 'last_used', 'created_at', 'updated_at']
    raw_id_fields = ['chapter', 'group', 'parent']
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Información Básica', {
            'fields': ('version', 'code', 'name', 'chapter', 'group', 'parent')
        }),
        ('Clasificación', {
            'fields': ('level', 'is_category', 'is_subcategory')
        }),
        ('Aplicabilidad', {
            'fields': ('applicable_gender', 'min_age_days', 'max_age_days', 'use_in', 'death_type')
        }),
        ('Características Especiales (Colombia)', {
            'fields': (
                'mandatory_notification', 'high_cost', 'rare_disease',
                'chronic_disease', 'requires_authorization'
            )
        }),
        ('Descripciones y Notas', {
            'fields': ('includes', 'excludes', 'notes', 'synonyms'),
            'classes': ('collapse',)
        }),
        ('Vigencia', {
            'fields': ('valid_from', 'valid_until', 'is_active', 'is_deprecated')
        }),
        ('Estadísticas', {
            'fields': ('use_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def name_truncated(self, obj):
        if len(obj.name) > 60:
            return f"{obj.name[:60]}..."
        return obj.name
    name_truncated.short_description = 'Nombre'

    def gender_badge(self, obj):
        colors = {
            'A': 'blue',
            'M': 'green',
            'F': 'purple'
        }
        color = colors.get(obj.applicable_gender, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_applicable_gender_display()
        )
    gender_badge.short_description = 'Sexo'

    def special_flags(self, obj):
        flags = []
        if obj.high_cost:
            flags.append('<span style="color: red; font-weight: bold;">💰 Alto Costo</span>')
        if obj.mandatory_notification:
            flags.append('<span style="color: orange; font-weight: bold;">⚠️ Notificación</span>')
        if obj.rare_disease:
            flags.append('<span style="color: purple;">🔬 Rara</span>')
        if obj.chronic_disease:
            flags.append('<span style="color: brown;">⏱️ Crónica</span>')

        if flags:
            return mark_safe(' '.join(flags))
        return '-'
    special_flags.short_description = 'Características'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    is_active_badge.short_description = 'Estado'


@admin.register(FavoriteDiagnosis)
class FavoriteDiagnosisAdmin(admin.ModelAdmin):
    """
    Administración de diagnósticos favoritos
    """
    list_display = [
        'user', 'diagnosis_code', 'diagnosis_name', 'specialty', 'order', 'created_at'
    ]
    list_filter = ['specialty', 'company', 'user']
    search_fields = ['user__username', 'diagnosis__code', 'diagnosis__name']
    raw_id_fields = ['diagnosis']
    ordering = ['order', 'diagnosis__code']

    def diagnosis_code(self, obj):
        return obj.diagnosis.code
    diagnosis_code.short_description = 'Código'

    def diagnosis_name(self, obj):
        if len(obj.diagnosis.name) > 50:
            return f"{obj.diagnosis.name[:50]}..."
        return obj.diagnosis.name
    diagnosis_name.short_description = 'Diagnóstico'


@admin.register(DiagnosisImportLog)
class DiagnosisImportLogAdmin(admin.ModelAdmin):
    """
    Administración de logs de importación
    """
    list_display = [
        'file_name', 'version', 'status_badge', 'stats', 'success_rate_display',
        'duration', 'imported_by', 'started_at'
    ]
    list_filter = ['status', 'file_type', 'version', 'started_at']
    search_fields = ['file_name', 'imported_by__username']
    readonly_fields = [
        'file_name', 'file_type', 'total_records', 'successful_imports',
        'failed_imports', 'skipped_imports', 'updated_records', 'status',
        'progress_percentage', 'error_log', 'import_notes', 'summary',
        'started_at', 'completed_at', 'duration_seconds', 'imported_by'
    ]
    date_hierarchy = 'started_at'
    ordering = ['-started_at']

    fieldsets = (
        ('Información del Archivo', {
            'fields': ('file_name', 'file_type', 'file_path', 'version', 'company')
        }),
        ('Estadísticas de Importación', {
            'fields': (
                'total_records', 'successful_imports', 'failed_imports',
                'skipped_imports', 'updated_records'
            )
        }),
        ('Estado', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Detalles', {
            'fields': ('summary', 'import_notes', 'error_log'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('imported_by', 'started_at', 'completed_at', 'duration_seconds')
        }),
    )

    def stats(self, obj):
        return format_html(
            'Éxito: <strong style="color: green;">{}</strong> | '
            'Fallo: <strong style="color: red;">{}</strong> | '
            'Omitidos: <strong>{}</strong>',
            obj.successful_imports, obj.failed_imports, obj.skipped_imports
        )
    stats.short_description = 'Estadísticas'

    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'partial': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def success_rate_display(self, obj):
        rate = obj.calculate_success_rate()
        color = 'green' if rate >= 90 else ('orange' if rate >= 70 else 'red')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, rate
        )
    success_rate_display.short_description = 'Tasa de Éxito'

    def duration(self, obj):
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        return '-'
    duration.short_description = 'Duración'

    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False

    def has_change_permission(self, request, obj=None):
        # Los logs solo se pueden ver, no editar
        return False
