"""
Modelos para el sistema de reportes.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User, Period


class ReportTemplate(models.Model):
    """
    Plantillas de reportes personalizables.
    """
    REPORT_TYPE_CHOICES = [
        ('balance_sheet', 'Balance General'),
        ('income_statement', 'Estado de Resultados'),
        ('cash_flow', 'Flujo de Efectivo'),
        ('trial_balance', 'Balance de Prueba'),
        ('general_ledger', 'Libro Mayor'),
        ('journal', 'Libro Diario'),
        ('aging_report', 'Cartera Vencida'),
        ('tax_report', 'Reporte de Impuestos'),
        ('payroll_report', 'Reporte de Nómina'),
        ('inventory_report', 'Reporte de Inventarios'),
        ('custom', 'Personalizado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='report_templates')
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Configuración del reporte
    template_config = models.JSONField(default=dict, help_text="Configuración JSON del template")
    sql_query = models.TextField(blank=True, help_text="Query SQL personalizada")
    
    # Formato
    page_format = models.CharField(max_length=10, default='A4')
    orientation = models.CharField(max_length=10, default='portrait', choices=[
        ('portrait', 'Vertical'),
        ('landscape', 'Horizontal')
    ])
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'reports_templates'
        verbose_name = 'Plantilla de Reporte'
        verbose_name_plural = 'Plantillas de Reportes'
        unique_together = ['company', 'name']
        ordering = ['report_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """
    Reportes generados y almacenados.
    """
    STATUS_CHOICES = [
        ('generating', 'Generando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='generated_reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.PROTECT)
    
    # Parámetros del reporte
    period_start = models.DateField()
    period_end = models.DateField()
    parameters = models.JSONField(default=dict, help_text="Parámetros específicos del reporte")
    
    # Archivos generados
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True)
    excel_file = models.FileField(upload_to='reports/excel/', blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    error_message = models.TextField(blank=True)
    
    # Metadatos
    file_size = models.IntegerField(default=0)
    generation_time = models.FloatField(default=0, help_text="Tiempo de generación en segundos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'reports_generated'
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['template', 'period_start']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.period_start} a {self.period_end}"