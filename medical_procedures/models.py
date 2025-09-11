"""
Modelos para el módulo de Procedimientos Médicos.
Sistema completo con códigos CUPS (Clasificación Única de Procedimientos en Salud).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class CUPSCode(models.Model):
    """
    Catálogo de códigos CUPS (Clasificación Única de Procedimientos en Salud).
    """
    COMPLEXITY_CHOICES = [
        ('baja', 'Baja Complejidad'),
        ('media', 'Media Complejidad'),
        ('alta', 'Alta Complejidad'),
        ('especial', 'Especial'),
    ]
    
    CATEGORY_CHOICES = [
        ('consulta', 'Consulta Externa'),
        ('procedimiento', 'Procedimiento'),
        ('cirugia', 'Cirugía'),
        ('laboratorio', 'Laboratorio'),
        ('imagenes', 'Imágenes Diagnósticas'),
        ('rehabilitacion', 'Rehabilitación'),
        ('urgencias', 'Urgencias'),
        ('hospitalizacion', 'Hospitalización'),
        ('ginecologia', 'Ginecología y Obstetricia'),
        ('pediatria', 'Pediatría'),
        ('odontologia', 'Odontología'),
        ('medicina_nuclear', 'Medicina Nuclear'),
        ('patologia', 'Patología'),
        ('otros', 'Otros'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Código CUPS
    cups_code = models.CharField(
        max_length=10, 
        unique=True,
        validators=[RegexValidator(r'^[0-9]{6}$', 'El código CUPS debe tener 6 dígitos')]
    )
    description = models.TextField(help_text="Descripción completa del procedimiento")
    short_description = models.CharField(max_length=200, help_text="Descripción corta")
    
    # Clasificación
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    complexity = models.CharField(max_length=10, choices=COMPLEXITY_CHOICES)
    specialty_required = models.CharField(max_length=50, blank=True, help_text="Especialidad médica requerida")
    
    # Configuración del procedimiento
    estimated_duration = models.IntegerField(default=30, help_text="Duración estimada en minutos")
    requires_anesthesia = models.BooleanField(default=False)
    requires_hospitalization = models.BooleanField(default=False)
    requires_pre_authorization = models.BooleanField(default=False)
    
    # Precios de referencia
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    professional_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    institutional_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Información adicional
    contraindications = models.TextField(blank=True, help_text="Contraindicaciones")
    preparation_instructions = models.TextField(blank=True, help_text="Instrucciones de preparación")
    post_procedure_care = models.TextField(blank=True, help_text="Cuidados post-procedimiento")
    
    # Control
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(default=timezone.now)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cups_codes'
        verbose_name = 'Código CUPS'
        verbose_name_plural = 'Códigos CUPS'
        ordering = ['cups_code']
    
    def __str__(self):
        return f"{self.cups_code} - {self.short_description}"
    
    def get_total_price(self):
        """Calcula el precio total del procedimiento."""
        return self.base_price + self.professional_fee + self.institutional_fee


class ProcedureTemplate(models.Model):
    """
    Plantillas de procedimientos por especialidad para estandarizar registros.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50)
    cups_codes = models.ManyToManyField(CUPSCode, related_name='templates')
    
    # Plantillas de documentación
    pre_procedure_template = models.TextField(blank=True, help_text="Plantilla pre-procedimiento")
    procedure_notes_template = models.TextField(blank=True, help_text="Plantilla de notas del procedimiento")
    post_procedure_template = models.TextField(blank=True, help_text="Plantilla post-procedimiento")
    
    # Configuración
    requires_informed_consent = models.BooleanField(default=True)
    required_supplies = models.JSONField(default=list, help_text="Lista de insumos requeridos")
    required_equipment = models.JSONField(default=list, help_text="Lista de equipos requeridos")
    
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='procedure_templates_created')
    
    class Meta:
        db_table = 'procedure_templates'
        verbose_name = 'Plantilla de Procedimiento'
        verbose_name_plural = 'Plantillas de Procedimientos'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.specialty}"


class MedicalProcedure(models.Model):
    """
    Registro de procedimientos médicos realizados.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Programado'),
        ('preparing', 'Preparando'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('complications', 'Con Complicaciones'),
        ('postponed', 'Postergado'),
    ]
    
    ANESTHESIA_TYPE_CHOICES = [
        ('none', 'Sin Anestesia'),
        ('local', 'Anestesia Local'),
        ('regional', 'Anestesia Regional'),
        ('general', 'Anestesia General'),
        ('sedation', 'Sedación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    # Información básica
    procedure_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.CASCADE,
                               limit_choices_to={'type': 'customer', 'is_patient': True})
    
    # Procedimiento
    cups_code = models.ForeignKey(CUPSCode, on_delete=models.PROTECT)
    template = models.ForeignKey(ProcedureTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Médicos involucrados
    primary_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, 
                                        related_name='primary_procedures')
    assistant_physicians = models.ManyToManyField('payroll.Employee', blank=True,
                                                related_name='assisted_procedures')
    anesthesiologist = models.ForeignKey('payroll.Employee', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='anesthesia_procedures')
    
    # Fechas y horarios
    scheduled_date = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Información médica
    indication = models.TextField(help_text="Indicación médica")
    pre_procedure_diagnosis = models.CharField(max_length=500, blank=True)
    post_procedure_diagnosis = models.CharField(max_length=500, blank=True)
    
    # Anestesia
    anesthesia_type = models.CharField(max_length=20, choices=ANESTHESIA_TYPE_CHOICES, default='none')
    anesthesia_notes = models.TextField(blank=True)
    
    # Documentación del procedimiento
    procedure_notes = models.TextField(blank=True, help_text="Notas detalladas del procedimiento")
    technique_used = models.TextField(blank=True, help_text="Técnica utilizada")
    findings = models.TextField(blank=True, help_text="Hallazgos")
    complications = models.TextField(blank=True, help_text="Complicaciones")
    
    # Materiales e insumos
    supplies_used = models.JSONField(default=list, help_text="Insumos utilizados")
    equipment_used = models.JSONField(default=list, help_text="Equipos utilizados")
    
    # Consentimiento informado
    informed_consent_signed = models.BooleanField(default=False)
    consent_signature_date = models.DateTimeField(null=True, blank=True)
    consent_witness = models.CharField(max_length=200, blank=True)
    
    # Seguimiento
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_instructions = models.TextField(blank=True)
    
    # Facturación
    is_billable = models.BooleanField(default=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_authorization = models.CharField(max_length=50, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='procedures_created')
    updated_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='procedures_updated')
    
    class Meta:
        db_table = 'medical_procedures'
        verbose_name = 'Procedimiento Médico'
        verbose_name_plural = 'Procedimientos Médicos'
        unique_together = ['company', 'procedure_number']
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Proc. #{self.procedure_number} - {self.patient.name} - {self.cups_code.short_description}"
    
    def get_duration(self):
        """Calcula la duración real del procedimiento."""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return f"{duration.total_seconds() // 60:.0f} minutos"
        return f"{self.cups_code.estimated_duration} minutos (estimado)"
    
    def is_overdue(self):
        """Verifica si el procedimiento está vencido."""
        return self.scheduled_date < timezone.now() and self.status == 'scheduled'
    
    def can_be_started(self):
        """Verifica si el procedimiento puede iniciarse."""
        return self.status == 'scheduled' and self.informed_consent_signed
    
    def get_total_cost(self):
        """Calcula el costo total incluyendo insumos."""
        base_cost = self.cups_code.get_total_price()
        # Aquí se podría agregar lógica para calcular costos de insumos
        return base_cost


class ProcedureImage(models.Model):
    """
    Imágenes tomadas durante el procedimiento.
    """
    IMAGE_TYPE_CHOICES = [
        ('pre_procedure', 'Pre-procedimiento'),
        ('during_procedure', 'Durante procedimiento'),
        ('post_procedure', 'Post-procedimiento'),
        ('complications', 'Complicaciones'),
        ('follow_up', 'Seguimiento'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    procedure = models.ForeignKey(MedicalProcedure, on_delete=models.CASCADE, related_name='images')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES)
    
    image = models.ImageField(upload_to='procedures/%Y/%m/')
    thumbnail = models.ImageField(upload_to='procedures/thumbnails/%Y/%m/', blank=True)
    
    # Metadatos
    capture_timestamp = models.DateTimeField(default=timezone.now)
    camera_settings = models.JSONField(default=dict, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='procedure_images_created')
    
    class Meta:
        db_table = 'procedure_images'
        verbose_name = 'Imagen de Procedimiento'
        verbose_name_plural = 'Imágenes de Procedimientos'
        ordering = ['capture_timestamp']
    
    def __str__(self):
        return f"{self.title} - {self.procedure.procedure_number}"


class ProcedureResult(models.Model):
    """
    Resultados y reportes de procedimientos.
    """
    RESULT_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Anormal'),
        ('inconclusive', 'No Concluyente'),
        ('requires_follow_up', 'Requiere Seguimiento'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    procedure = models.OneToOneField(MedicalProcedure, on_delete=models.CASCADE, related_name='result')
    
    # Resultado
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES)
    result_summary = models.TextField(help_text="Resumen de resultados")
    detailed_report = models.TextField(help_text="Reporte detallado")
    
    # Interpretación
    interpretation = models.TextField(blank=True, help_text="Interpretación médica")
    recommendations = models.TextField(blank=True, help_text="Recomendaciones")
    
    # Seguimiento
    requires_additional_studies = models.BooleanField(default=False)
    additional_studies_notes = models.TextField(blank=True)
    
    # Reporte firmado
    report_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='procedure_results_created')
    
    class Meta:
        db_table = 'procedure_results'
        verbose_name = 'Resultado de Procedimiento'
        verbose_name_plural = 'Resultados de Procedimientos'
    
    def __str__(self):
        return f"Resultado - {self.procedure.procedure_number} - {self.get_result_type_display()}"