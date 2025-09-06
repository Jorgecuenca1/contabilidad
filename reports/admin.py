"""
Configuración del admin para reportes.
"""

from django.contrib import admin
from .models import ReportTemplate, GeneratedReport


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'company', 'is_active', 'is_default', 'created_at']
    list_filter = ['report_type', 'is_active', 'is_default', 'company']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'name', 'report_type', 'description')
        }),
        ('Configuración', {
            'fields': ('template_config', 'sql_query', 'page_format', 'orientation')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['template', 'company', 'period_start', 'period_end', 'status', 'created_at', 'created_by']
    list_filter = ['status', 'company', 'template__report_type', 'created_at']
    search_fields = ['template__name', 'company__name']
    readonly_fields = ['created_at', 'file_size', 'generation_time', 'error_message']
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('company', 'template', 'period_start', 'period_end')
        }),
        ('Parámetros', {
            'fields': ('parameters',)
        }),
        ('Archivos Generados', {
            'fields': ('pdf_file', 'excel_file')
        }),
        ('Estado', {
            'fields': ('status', 'error_message')
        }),
        ('Metadatos', {
            'fields': ('file_size', 'generation_time', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Los reportes se generan desde las vistas, no desde el admin