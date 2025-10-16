"""
Modelos del módulo Imágenes Diagnósticas
Gestión completa de radiología, TAC, ecografías, resonancias e integración DICOM
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from core.models import Company, User
from patients.models import Patient


# ==================== CATÁLOGOS Y CONFIGURACIÓN ====================

class ImagingModality(models.Model):
    """Modalidades de Imágenes Diagnósticas"""
    MODALITY_CHOICES = [
        ('RX', 'Radiografía'),
        ('CT', 'Tomografía Computarizada (TAC)'),
        ('MR', 'Resonancia Magnética'),
        ('US', 'Ecografía/Ultrasonido'),
        ('MG', 'Mamografía'),
        ('NM', 'Medicina Nuclear'),
        ('PT', 'PET'),
        ('XA', 'Angiografía'),
        ('DX', 'Radiografía Digital'),
        ('CR', 'Radiografía Computarizada'),
        ('FL', 'Fluoroscopia'),
        ('BI', 'Biopsia Guiada por Imagen'),
        ('DG', 'Densitometría Ósea'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='imaging_modalities')

    code = models.CharField(max_length=10, help_text="Código DICOM de modalidad")
    name = models.CharField(max_length=200)
    modality_type = models.CharField(max_length=5, choices=MODALITY_CHOICES)
    description = models.TextField(blank=True)

    # Configuración técnica
    requires_contrast = models.BooleanField(default=False, help_text="Requiere medio de contraste")
    requires_sedation = models.BooleanField(default=False, help_text="Puede requerir sedación")
    requires_fasting = models.BooleanField(default=False, help_text="Requiere ayuno")
    preparation_instructions = models.TextField(blank=True, help_text="Instrucciones de preparación")

    # Tiempo y costos
    average_duration_minutes = models.IntegerField(default=30, help_text="Duración promedio en minutos")
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modalities_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_modality'
        verbose_name = 'Modalidad de Imagen'
        verbose_name_plural = 'Modalidades de Imágenes'
        ordering = ['name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ImagingEquipment(models.Model):
    """Equipos de Imágenes Diagnósticas"""
    STATUS_CHOICES = [
        ('operational', 'Operacional'),
        ('maintenance', 'En Mantenimiento'),
        ('calibration', 'En Calibración'),
        ('out_of_service', 'Fuera de Servicio'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='imaging_equipment')

    code = models.CharField(max_length=50, help_text="Código interno del equipo")
    name = models.CharField(max_length=200)
    modality = models.ForeignKey(ImagingModality, on_delete=models.PROTECT, related_name='equipment')

    # Información técnica
    manufacturer = models.CharField(max_length=200, blank=True, help_text="Fabricante")
    model = models.CharField(max_length=200, blank=True)
    serial_number = models.CharField(max_length=200, blank=True)
    installation_date = models.DateField(null=True, blank=True)

    # Ubicación
    room_location = models.CharField(max_length=100, help_text="Sala donde está ubicado")
    building = models.CharField(max_length=100, blank=True)

    # Estado y mantenimiento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)

    # DICOM Integration
    dicom_ae_title = models.CharField(max_length=16, blank=True, help_text="AE Title DICOM")
    dicom_ip_address = models.GenericIPAddressField(null=True, blank=True)
    dicom_port = models.IntegerField(null=True, blank=True, default=104)

    observations = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='equipment_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_equipment'
        verbose_name = 'Equipo de Imagen'
        verbose_name_plural = 'Equipos de Imágenes'
        ordering = ['name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_operational(self):
        return self.status == 'operational' and self.is_active


# ==================== ÓRDENES Y ESTUDIOS ====================

class ImagingOrder(models.Model):
    """Orden de Estudio de Imágenes"""
    PRIORITY_CHOICES = [
        ('routine', 'Rutina'),
        ('urgent', 'Urgente'),
        ('stat', 'STAT (Inmediato)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('scheduled', 'Agendada'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('reported', 'Informada'),
        ('delivered', 'Entregada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='imaging_orders')

    order_number = models.CharField(max_length=50, unique=True, help_text="Número único de orden")

    # Paciente
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='imaging_orders')

    # Modalidad y procedimiento
    modality = models.ForeignKey(ImagingModality, on_delete=models.PROTECT, related_name='orders')
    procedure_description = models.TextField(help_text="Descripción del procedimiento solicitado")
    anatomical_region = models.CharField(max_length=200, help_text="Región anatómica a estudiar")

    # Información clínica
    clinical_indication = models.TextField(help_text="Indicación clínica / Motivo del estudio")
    clinical_history = models.TextField(blank=True, help_text="Historia clínica relevante")
    previous_studies = models.TextField(blank=True, help_text="Estudios previos relevantes")

    # Médico solicitante
    ordering_physician = models.ForeignKey(User, on_delete=models.PROTECT,
                                            related_name='imaging_orders_requested',
                                            help_text="Médico que solicita el estudio")
    ordering_date = models.DateTimeField(default=timezone.now)

    # Prioridad y programación
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    scheduled_equipment = models.ForeignKey(ImagingEquipment, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='scheduled_orders')

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Contraindicaciones y alergias
    has_allergies = models.BooleanField(default=False)
    allergies_description = models.TextField(blank=True)
    has_contraindications = models.BooleanField(default=False)
    contraindications_description = models.TextField(blank=True)

    # Consentimiento
    informed_consent_signed = models.BooleanField(default=False)
    consent_signed_date = models.DateTimeField(null=True, blank=True)

    # Facturación
    is_billed = models.BooleanField(default=False)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='imaging_orders_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_order'
        verbose_name = 'Orden de Imagen'
        verbose_name_plural = 'Órdenes de Imágenes'
        ordering = ['-ordering_date']

    def __str__(self):
        return f"{self.order_number} - {self.patient.third_party.get_full_name()}"

    def can_schedule(self):
        return self.status == 'pending' and not self.scheduled_date

    def can_perform(self):
        return self.status in ['scheduled', 'pending'] and self.informed_consent_signed


class ImagingStudy(models.Model):
    """Estudio de Imagen Realizado"""
    STATUS_CHOICES = [
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Fallido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='imaging_studies')
    order = models.ForeignKey(ImagingOrder, on_delete=models.PROTECT, related_name='studies')

    study_number = models.CharField(max_length=50, unique=True, help_text="Número del estudio")

    # Información del estudio
    study_date = models.DateTimeField(default=timezone.now)
    equipment_used = models.ForeignKey(ImagingEquipment, on_delete=models.PROTECT, related_name='studies')

    # Personal
    performing_technologist = models.ForeignKey(User, on_delete=models.PROTECT,
                                                 related_name='studies_performed',
                                                 help_text="Tecnólogo que realiza el estudio")
    radiologist_assigned = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                              related_name='studies_to_read',
                                              help_text="Radiólogo asignado")

    # Detalles técnicos
    contrast_used = models.BooleanField(default=False)
    contrast_type = models.CharField(max_length=200, blank=True)
    contrast_volume_ml = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    sedation_used = models.BooleanField(default=False)
    sedation_type = models.CharField(max_length=200, blank=True)

    # Parámetros técnicos del estudio
    kvp = models.IntegerField(null=True, blank=True, help_text="Kilovoltaje pico (para RX/CT)")
    mas = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                               help_text="Miliamperios-segundo")
    slice_thickness_mm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                              help_text="Grosor de corte en mm (para CT/MR)")

    # Número de imágenes
    number_of_images = models.IntegerField(default=0)
    number_of_series = models.IntegerField(default=1)

    # DICOM
    study_instance_uid = models.CharField(max_length=200, blank=True, help_text="UID del estudio DICOM")
    dicom_stored = models.BooleanField(default=False, help_text="Imágenes almacenadas en PACS")

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    completion_date = models.DateTimeField(null=True, blank=True)

    technical_notes = models.TextField(blank=True, help_text="Notas técnicas del tecnólogo")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='studies_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_study'
        verbose_name = 'Estudio de Imagen'
        verbose_name_plural = 'Estudios de Imágenes'
        ordering = ['-study_date']

    def __str__(self):
        return f"{self.study_number} - {self.order.order_number}"


class ImagingReport(models.Model):
    """Informe Radiológico"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('preliminary', 'Preliminar'),
        ('final', 'Final'),
        ('amended', 'Enmendado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='imaging_reports')
    study = models.OneToOneField(ImagingStudy, on_delete=models.PROTECT, related_name='report')

    report_number = models.CharField(max_length=50, unique=True)

    # Radiólogo
    radiologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='radiology_reports')
    report_date = models.DateTimeField(default=timezone.now)

    # Informe estructurado
    technique = models.TextField(help_text="Técnica utilizada")
    findings = models.TextField(help_text="Hallazgos")
    impression = models.TextField(help_text="Impresión / Conclusión")
    recommendations = models.TextField(blank=True, help_text="Recomendaciones")

    # Clasificación
    is_normal = models.BooleanField(default=False, help_text="Estudio normal")
    is_critical = models.BooleanField(default=False, help_text="Hallazgos críticos")
    critical_finding_notified = models.BooleanField(default=False)
    notification_date = models.DateTimeField(null=True, blank=True)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    finalized_date = models.DateTimeField(null=True, blank=True)

    # Firma digital
    digitally_signed = models.BooleanField(default=False)
    signature_date = models.DateTimeField(null=True, blank=True)

    # Transcripción
    transcribed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='reports_transcribed')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reports_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_report'
        verbose_name = 'Informe Radiológico'
        verbose_name_plural = 'Informes Radiológicos'
        ordering = ['-report_date']

    def __str__(self):
        return f"{self.report_number} - {self.study.study_number}"

    def can_finalize(self):
        return self.status in ['draft', 'preliminary']


class ImagingImage(models.Model):
    """Imágenes del Estudio"""
    IMAGE_TYPE_CHOICES = [
        ('dicom', 'DICOM'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('pdf', 'PDF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name='images')

    series_number = models.IntegerField(default=1)
    instance_number = models.IntegerField(default=1)

    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default='dicom')
    file_path = models.CharField(max_length=500, help_text="Ruta del archivo en el servidor")
    file_size_bytes = models.BigIntegerField(default=0)

    # DICOM específico
    sop_instance_uid = models.CharField(max_length=200, blank=True)
    series_instance_uid = models.CharField(max_length=200, blank=True)

    # Metadata
    acquisition_date = models.DateTimeField(null=True, blank=True)
    image_description = models.CharField(max_length=200, blank=True)

    # Thumbnails
    thumbnail_path = models.CharField(max_length=500, blank=True)

    is_key_image = models.BooleanField(default=False, help_text="Imagen clave para el informe")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imaging_image'
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'
        ordering = ['series_number', 'instance_number']

    def __str__(self):
        return f"Serie {self.series_number} - Imagen {self.instance_number}"


# ==================== CONTROL DE CALIDAD ====================

class QualityControlCheck(models.Model):
    """Control de Calidad de Equipos"""
    CHECK_TYPE_CHOICES = [
        ('daily', 'Control Diario'),
        ('weekly', 'Control Semanal'),
        ('monthly', 'Control Mensual'),
        ('annual', 'Control Anual'),
        ('maintenance', 'Post-Mantenimiento'),
    ]

    RESULT_CHOICES = [
        ('passed', 'Aprobado'),
        ('failed', 'Fallido'),
        ('warning', 'Advertencia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    equipment = models.ForeignKey(ImagingEquipment, on_delete=models.CASCADE, related_name='quality_checks')

    check_date = models.DateTimeField(default=timezone.now)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPE_CHOICES)

    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='qc_checks_performed')

    # Resultados
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    measurements = models.TextField(help_text="Mediciones y valores obtenidos")
    observations = models.TextField(blank=True)

    corrective_actions = models.TextField(blank=True, help_text="Acciones correctivas tomadas")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imaging_quality_control'
        verbose_name = 'Control de Calidad'
        verbose_name_plural = 'Controles de Calidad'
        ordering = ['-check_date']

    def __str__(self):
        return f"{self.equipment.name} - {self.check_date.date()}"
