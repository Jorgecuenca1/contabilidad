"""
Modelos del Sistema de Información de Laboratorio (LIS).
Sistema completo para gestión de laboratorio clínico.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date, datetime

from core.models import Company, User
from third_parties.models import ThirdParty


class LabSection(models.Model):
    """
    Secciones del laboratorio (Hematología, Química, Microbiología, etc.).
    """
    SECTION_TYPES = [
        ('hematology', 'Hematología'),
        ('chemistry', 'Química Clínica'),
        ('microbiology', 'Microbiología'),
        ('pathology', 'Patología'),
        ('molecular', 'Diagnóstico Molecular'),
        ('blood_bank', 'Banco de Sangre'),
        ('immunology', 'Inmunología'),
        ('cytology', 'Citología'),
        ('toxicology', 'Toxicología'),
        ('parasitology', 'Parasitología'),
        ('mycology', 'Micología'),
        ('virology', 'Virología'),
        ('gynecology', 'Laboratorio de Ginecología'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='lab_sections')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    description = models.TextField(blank=True)
    
    # Configuración
    requires_special_handling = models.BooleanField(default=False)
    max_processing_time_hours = models.IntegerField(default=24)
    is_stat_available = models.BooleanField(default=True, help_text="Permite pruebas STAT/urgentes")
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'laboratory_sections'
        verbose_name = 'Sección de Laboratorio'
        verbose_name_plural = 'Secciones de Laboratorio'
        unique_together = ['company', 'code']
        ordering = ['section_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_section_type_display()})"


class TestCategory(models.Model):
    """
    Categorías de pruebas de laboratorio.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='test_categories')
    section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name='test_categories')
    
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración clínica
    requires_fasting = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laboratory_test_categories'
        verbose_name = 'Categoría de Prueba'
        verbose_name_plural = 'Categorías de Pruebas'
        unique_together = ['company', 'code']
        ordering = ['section', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.section.name}"


class LabTest(models.Model):
    """
    Catálogo de pruebas de laboratorio.
    """
    SPECIMEN_TYPES = [
        ('blood_serum', 'Suero'),
        ('blood_plasma', 'Plasma'),
        ('whole_blood', 'Sangre Total'),
        ('urine', 'Orina'),
        ('stool', 'Heces'),
        ('csf', 'Líquido Cefalorraquídeo'),
        ('sputum', 'Esputo'),
        ('wound_swab', 'Hisopo de Herida'),
        ('throat_swab', 'Hisopo Faríngeo'),
        ('vaginal_swab', 'Hisopo Vaginal'),
        ('cervical_sample', 'Muestra Cervical'),
        ('tissue', 'Tejido'),
        ('saliva', 'Saliva'),
        ('other', 'Otro'),
    ]
    
    RESULT_TYPES = [
        ('numeric', 'Numérico'),
        ('text', 'Texto'),
        ('positive_negative', 'Positivo/Negativo'),
        ('normal_abnormal', 'Normal/Anormal'),
        ('qualitative', 'Cualitativo'),
        ('culture', 'Cultivo'),
        ('morphology', 'Morfología'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='lab_tests')
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests')
    
    # Identificación
    code = models.CharField(max_length=20, help_text="Código interno del laboratorio")
    loinc_code = models.CharField(max_length=20, blank=True, help_text="Código LOINC estándar")
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    # Especificaciones técnicas
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    specimen_volume_ml = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.1)])
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    
    # Valores de referencia
    reference_range_min = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    reference_range_max = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    reference_range_text = models.TextField(blank=True, help_text="Para valores no numéricos")
    
    # Configuración clínica
    requires_fasting = models.BooleanField(default=False)
    fasting_hours = models.IntegerField(null=True, blank=True)
    processing_time_hours = models.IntegerField(default=24)
    stat_processing_time_hours = models.IntegerField(default=2)
    
    # Configuración de costos
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_stat_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'laboratory_tests'
        verbose_name = 'Prueba de Laboratorio'
        verbose_name_plural = 'Pruebas de Laboratorio'
        unique_together = ['company', 'code']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_reference_range_display(self):
        """Obtiene el rango de referencia formateado."""
        if self.result_type == 'numeric' and self.reference_range_min and self.reference_range_max:
            return f"{self.reference_range_min} - {self.reference_range_max} {self.unit_of_measure}"
        return self.reference_range_text


class TestPanel(models.Model):
    """
    Paneles de pruebas (conjunto de pruebas relacionadas).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='test_panels')
    
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tests = models.ManyToManyField(LabTest, related_name='panels')
    
    # Precios especiales para el panel
    panel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    panel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'laboratory_test_panels'
        verbose_name = 'Panel de Pruebas'
        verbose_name_plural = 'Paneles de Pruebas'
        unique_together = ['company', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class LabOrder(models.Model):
    """
    Órdenes de laboratorio.
    """
    PRIORITY_CHOICES = [
        ('routine', 'Rutina'),
        ('urgent', 'Urgente'),
        ('stat', 'STAT/Inmediato'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('collected', 'Recolectada'),
        ('processing', 'En Proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('rejected', 'Rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='lab_orders')
    
    # Identificación de la orden
    order_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name='lab_orders')
    
    # Información médica
    ordering_physician = models.CharField(max_length=200, help_text="Médico que ordena")
    clinical_indication = models.TextField(help_text="Indicación clínica")
    diagnosis_code = models.CharField(max_length=20, blank=True, help_text="Código CIE-10")
    
    # Configuración de la orden
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Fechas importantes
    ordered_date = models.DateTimeField(default=timezone.now)
    collection_date = models.DateTimeField(null=True, blank=True)
    expected_completion = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Facturación
    insurance_authorization = models.CharField(max_length=50, blank=True)
    is_billable = models.BooleanField(default=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_lab_orders')
    updated_at = models.DateTimeField(auto_now=True)
    
    # Conexión con citas médicas (por implementar cuando exista el módulo)
    # medical_appointment = models.ForeignKey(
    #     'medical_appointments.Appointment', 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True,
    #     related_name='lab_orders',
    #     help_text="Cita médica relacionada"
    # )
    
    class Meta:
        db_table = 'laboratory_orders'
        verbose_name = 'Orden de Laboratorio'
        verbose_name_plural = 'Órdenes de Laboratorio'
        ordering = ['-ordered_date']
    
    def __str__(self):
        return f"Orden {self.order_number} - {self.patient.get_full_name()}"
    
    def generate_order_number(self):
        """Genera número de orden único."""
        today = date.today()
        prefix = f"LAB{today.strftime('%Y%m%d')}"
        
        last_order = LabOrder.objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        
        if last_order:
            last_number = int(last_order.order_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        self.order_number = f"{prefix}{new_number:04d}"


class OrderItem(models.Model):
    """
    Items de la orden de laboratorio (pruebas solicitadas).
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('collected', 'Recolectada'),
        ('processing', 'En Proceso'),
        ('resulted', 'Con Resultado'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='order_items')
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=LabOrder.PRIORITY_CHOICES, default='routine')
    
    # Información específica
    special_instructions = models.TextField(blank=True)
    expected_completion = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laboratory_order_items'
        verbose_name = 'Item de Orden'
        verbose_name_plural = 'Items de Orden'
        unique_together = ['lab_order', 'test']
    
    def __str__(self):
        return f"{self.lab_order.order_number} - {self.test.name}"


class Specimen(models.Model):
    """
    Muestras de laboratorio.
    """
    STATUS_CHOICES = [
        ('collected', 'Recolectada'),
        ('received', 'Recibida'),
        ('processing', 'En Proceso'),
        ('completed', 'Procesada'),
        ('rejected', 'Rechazada'),
        ('discarded', 'Descartada'),
    ]
    
    REJECTION_REASONS = [
        ('insufficient_volume', 'Volumen Insuficiente'),
        ('hemolyzed', 'Hemolizada'),
        ('clotted', 'Coagulada'),
        ('contaminated', 'Contaminada'),
        ('incorrect_container', 'Contenedor Incorrecto'),
        ('unlabeled', 'Sin Etiqueta'),
        ('expired', 'Vencida'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='specimens')
    
    # Identificación
    specimen_id = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Información de la muestra
    specimen_type = models.CharField(max_length=20, choices=LabTest.SPECIMEN_TYPES)
    volume_ml = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    container_type = models.CharField(max_length=50)
    
    # Estado y procesamiento
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='collected')
    rejection_reason = models.CharField(max_length=30, choices=REJECTION_REASONS, blank=True)
    rejection_notes = models.TextField(blank=True)
    
    # Fechas de seguimiento
    collected_datetime = models.DateTimeField()
    received_datetime = models.DateTimeField(null=True, blank=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    completed_datetime = models.DateTimeField(null=True, blank=True)
    
    # Personal responsable
    collected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collected_specimens')
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='received_specimens')
    
    # Trazabilidad
    location = models.CharField(max_length=100, blank=True, help_text="Ubicación actual")
    temperature_storage = models.CharField(max_length=50, default='Temperatura ambiente')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'laboratory_specimens'
        verbose_name = 'Muestra de Laboratorio'
        verbose_name_plural = 'Muestras de Laboratorio'
        ordering = ['-collected_datetime']
    
    def __str__(self):
        return f"Muestra {self.specimen_id} - {self.get_specimen_type_display()}"


class TestResult(models.Model):
    """
    Resultados de pruebas de laboratorio.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('preliminary', 'Preliminar'),
        ('final', 'Final'),
        ('corrected', 'Corregido'),
        ('cancelled', 'Cancelado'),
    ]
    
    FLAG_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'Alto'),
        ('low', 'Bajo'),
        ('critical_high', 'Crítico Alto'),
        ('critical_low', 'Crítico Bajo'),
        ('abnormal', 'Anormal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='result')
    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name='results')
    
    # Resultado
    numeric_result = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    text_result = models.TextField(blank=True)
    flag = models.CharField(max_length=15, choices=FLAG_CHOICES, default='normal')
    
    # Metadatos del resultado
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reference_range_used = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True, help_text="Notas del técnico")
    interpretation = models.TextField(blank=True, help_text="Interpretación médica")
    
    # Control de calidad
    instrument_id = models.CharField(max_length=50, blank=True)
    qc_passed = models.BooleanField(default=True)
    qc_notes = models.TextField(blank=True)
    
    # Personal responsable
    tested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tested_results')
    verified_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='verified_results')
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_results')
    
    # Fechas importantes
    tested_datetime = models.DateTimeField(default=timezone.now)
    verified_datetime = models.DateTimeField(null=True, blank=True)
    approved_datetime = models.DateTimeField(null=True, blank=True)
    released_datetime = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'laboratory_test_results'
        verbose_name = 'Resultado de Prueba'
        verbose_name_plural = 'Resultados de Pruebas'
        ordering = ['-tested_datetime']
    
    def __str__(self):
        return f"Resultado {self.order_item.test.name} - {self.order_item.lab_order.patient.get_full_name()}"
    
    def get_result_display(self):
        """Obtiene el resultado formateado."""
        if self.order_item.test.result_type == 'numeric' and self.numeric_result is not None:
            return f"{self.numeric_result} {self.order_item.test.unit_of_measure}"
        return self.text_result
    
    def is_critical(self):
        """Determina si el resultado es crítico."""
        return self.flag in ['critical_high', 'critical_low']
    
    def is_abnormal(self):
        """Determina si el resultado está fuera del rango normal."""
        return self.flag != 'normal'


class CriticalValueAlert(models.Model):
    """
    Alertas de valores críticos.
    """
    NOTIFICATION_STATUS = [
        ('pending', 'Pendiente'),
        ('notified', 'Notificado'),
        ('acknowledged', 'Confirmado'),
        ('resolved', 'Resuelto'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_result = models.OneToOneField(TestResult, on_delete=models.CASCADE, related_name='critical_alert')
    
    # Información de la alerta
    alert_message = models.TextField()
    severity_level = models.CharField(max_length=20, default='high')
    
    # Estado de notificación
    notification_status = models.CharField(max_length=15, choices=NOTIFICATION_STATUS, default='pending')
    notified_to = models.CharField(max_length=200, help_text="A quién se notificó")
    notification_method = models.CharField(max_length=50, help_text="Método de notificación")
    
    # Fechas
    created_datetime = models.DateTimeField(auto_now_add=True)
    notified_datetime = models.DateTimeField(null=True, blank=True)
    acknowledged_datetime = models.DateTimeField(null=True, blank=True)
    resolved_datetime = models.DateTimeField(null=True, blank=True)
    
    # Personal responsable
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_alerts')
    acknowledged_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='acknowledged_alerts')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'laboratory_critical_alerts'
        verbose_name = 'Alerta de Valor Crítico'
        verbose_name_plural = 'Alertas de Valores Críticos'
        ordering = ['-created_datetime']
    
    def __str__(self):
        return f"Alerta Crítica - {self.test_result.order_item.test.name}"


class LabInstrument(models.Model):
    """
    Equipos e instrumentos de laboratorio.
    """
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('maintenance', 'En Mantenimiento'),
        ('calibration', 'En Calibración'),
        ('inactive', 'Inactivo'),
        ('retired', 'Retirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='lab_instruments')
    section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name='instruments')
    
    # Identificación
    serial_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    
    # Configuración técnica
    supported_tests = models.ManyToManyField(LabTest, blank=True, related_name='compatible_instruments')
    interface_type = models.CharField(max_length=50, blank=True, help_text="Tipo de interfaz (HL7, LIS, etc.)")
    
    # Estado y ubicación
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    location = models.CharField(max_length=200)
    installation_date = models.DateField()
    
    # Mantenimiento
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    last_calibration = models.DateField(null=True, blank=True)
    next_calibration = models.DateField(null=True, blank=True)
    
    # Información adicional
    warranty_expiry = models.DateField(null=True, blank=True)
    service_contract = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'laboratory_instruments'
        verbose_name = 'Instrumento de Laboratorio'
        verbose_name_plural = 'Instrumentos de Laboratorio'
        ordering = ['section', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.serial_number})"