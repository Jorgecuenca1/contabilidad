"""
Modelos para el módulo de Historia Clínica.
Sistema completo de registro médico por especialidades.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class MedicalRecord(models.Model):
    """
    Historia clínica del paciente por especialidad.
    """
    RECORD_TYPE_CHOICES = [
        ('general', 'Medicina General'),
        ('ginecologia', 'Ginecología'),
        ('laboratorio', 'Laboratorio'),
        ('pediatria', 'Pediatría'),
        ('cardiologia', 'Cardiología'),
        ('neurologia', 'Neurología'),
        ('dermatologia', 'Dermatología'),
        ('oftalmologia', 'Oftalmología'),
        ('otorrinolaringologia', 'Otorrinolaringología'),
        ('urologia', 'Urología'),
        ('traumatologia', 'Traumatología'),
        ('psiquiatria', 'Psiquiatría'),
        ('endocrinologia', 'Endocrinología'),
        ('gastroenterologia', 'Gastroenterología'),
        ('neumologia', 'Neumología'),
        ('reumatologia', 'Reumatología'),
        ('oncologia', 'Oncología'),
        ('cirugia_general', 'Cirugía General'),
        ('anestesiologia', 'Anestesiología'),
        ('radiologia', 'Radiología'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('transferred', 'Transferida'),
        ('closed', 'Cerrada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.CASCADE, 
                               limit_choices_to={'type': 'customer', 'is_patient': True})
    
    # Información básica
    record_number = models.CharField(max_length=20, unique=True)
    record_type = models.CharField(max_length=30, choices=RECORD_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Fechas importantes
    opening_date = models.DateTimeField(default=timezone.now)
    last_update = models.DateTimeField(auto_now=True)
    closing_date = models.DateTimeField(null=True, blank=True)
    
    # Médico responsable
    attending_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                          related_name='medical_records')
    
    # Información general del paciente
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Información médica general
    blood_type = models.CharField(max_length=5, blank=True, 
                                 choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                                         ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')])
    allergies = models.TextField(blank=True, help_text="Alergias conocidas")
    chronic_conditions = models.TextField(blank=True, help_text="Condiciones crónicas")
    current_medications = models.TextField(blank=True, help_text="Medicamentos actuales")
    family_history = models.TextField(blank=True, help_text="Antecedentes familiares")
    surgical_history = models.TextField(blank=True, help_text="Antecedentes quirúrgicos")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='medical_records_created')
    updated_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='medical_records_updated')
    
    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'
        unique_together = ['company', 'record_number']
        ordering = ['-last_update']
    
    def __str__(self):
        return f"HC {self.record_number} - {self.patient.name} ({self.get_record_type_display()})"
    
    def get_latest_consultation(self):
        """Obtiene la consulta más reciente."""
        return self.consultations.order_by('-consultation_date').first()
    
    def get_consultations_count(self):
        """Cuenta total de consultas."""
        return self.consultations.count()


class Consultation(models.Model):
    """
    Consulta médica individual dentro de la historia clínica.
    """
    CONSULTATION_TYPE_CHOICES = [
        ('primera_vez', 'Primera Vez'),
        ('control', 'Control'),
        ('urgencia', 'Urgencia'),
        ('cirugia', 'Cirugía'),
        ('procedimiento', 'Procedimiento'),
        ('interconsulta', 'Interconsulta'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_progress', 'En Curso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No Asistió'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='consultations')
    
    # Información de la consulta
    consultation_date = models.DateTimeField()
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Médico que atiende
    attending_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                          related_name='consultations')
    
    # Signos vitales
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                validators=[MinValueValidator(Decimal('0.1'))])
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                validators=[MinValueValidator(Decimal('0.1'))])
    blood_pressure_systolic = models.IntegerField(null=True, blank=True,
                                                 validators=[MinValueValidator(50), MaxValueValidator(300)])
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True,
                                                  validators=[MinValueValidator(30), MaxValueValidator(200)])
    heart_rate = models.IntegerField(null=True, blank=True,
                                   validators=[MinValueValidator(30), MaxValueValidator(220)])
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                    validators=[MinValueValidator(Decimal('30.0')), MaxValueValidator(Decimal('45.0'))])
    respiratory_rate = models.IntegerField(null=True, blank=True,
                                         validators=[MinValueValidator(5), MaxValueValidator(60)])
    oxygen_saturation = models.IntegerField(null=True, blank=True,
                                          validators=[MinValueValidator(50), MaxValueValidator(100)])
    
    # Consulta
    chief_complaint = models.TextField(help_text="Motivo de consulta")
    current_illness = models.TextField(blank=True, help_text="Enfermedad actual")
    physical_examination = models.TextField(blank=True, help_text="Examen físico")
    assessment = models.TextField(blank=True, help_text="Impresión diagnóstica")
    plan = models.TextField(blank=True, help_text="Plan de tratamiento")
    
    # Diagnósticos (CIE-10)
    primary_diagnosis_code = models.CharField(max_length=10, blank=True, help_text="Código CIE-10")
    primary_diagnosis_description = models.CharField(max_length=500, blank=True)
    secondary_diagnoses = models.TextField(blank=True, help_text="Diagnósticos secundarios (JSON)")
    
    # Medicamentos prescritos
    prescriptions = models.TextField(blank=True, help_text="Medicamentos prescritos")
    
    # Órdenes médicas
    lab_orders = models.TextField(blank=True, help_text="Órdenes de laboratorio")
    imaging_orders = models.TextField(blank=True, help_text="Órdenes de imágenes")
    
    # Seguimiento
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_instructions = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='consultations_created')
    
    class Meta:
        db_table = 'medical_consultations'
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-consultation_date']
    
    def __str__(self):
        return f"Consulta {self.consultation_date.strftime('%Y-%m-%d')} - {self.medical_record.patient.name}"
    
    def get_bmi(self):
        """Calcula el IMC si hay peso y altura."""
        if self.weight and self.height:
            height_m = float(self.height) / 100
            return float(self.weight) / (height_m ** 2)
        return None
    
    def get_blood_pressure(self):
        """Retorna la presión arterial formateada."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None


class MedicalAttachment(models.Model):
    """
    Archivos adjuntos a la historia clínica (imágenes, documentos, etc.).
    """
    ATTACHMENT_TYPE_CHOICES = [
        ('image', 'Imagen'),
        ('document', 'Documento'),
        ('lab_result', 'Resultado de Laboratorio'),
        ('imaging_study', 'Estudio de Imagen'),
        ('prescription', 'Prescripción'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='attachments')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='attachments')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='medical_records/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='attachments_created')
    
    class Meta:
        db_table = 'medical_attachments'
        verbose_name = 'Archivo Adjunto'
        verbose_name_plural = 'Archivos Adjuntos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.medical_record.patient.name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class SpecialtyTemplate(models.Model):
    """
    Plantillas de consulta por especialidad para estandarizar el registro.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=30, choices=MedicalRecord.RECORD_TYPE_CHOICES)
    
    # Plantillas de campos
    chief_complaint_template = models.TextField(blank=True)
    physical_examination_template = models.TextField(blank=True)
    assessment_template = models.TextField(blank=True)
    plan_template = models.TextField(blank=True)
    
    # Configuración de campos requeridos (JSON)
    required_vital_signs = models.JSONField(default=list, help_text="Lista de signos vitales requeridos")
    custom_fields = models.JSONField(default=dict, help_text="Campos personalizados por especialidad")
    
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='templates_created')
    
    class Meta:
        db_table = 'medical_specialty_templates'
        verbose_name = 'Plantilla de Especialidad'
        verbose_name_plural = 'Plantillas de Especialidad'
        unique_together = ['company', 'name', 'specialty']
    
    def __str__(self):
        return f"{self.name} - {self.get_specialty_display()}"