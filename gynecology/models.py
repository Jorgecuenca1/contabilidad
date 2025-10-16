"""
Modelos del módulo de Ginecología para Hospital Nivel 4.
Integrado con el sistema de terceros para manejo de pacientes.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from datetime import date, datetime

from core.models import Company, User
from third_parties.models import ThirdParty


class Patient(models.Model):
    """
    Paciente ginecológica.
    Utiliza el sistema de terceros existente como base.
    """
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    INSURANCE_CHOICES = [
        ('eps', 'EPS'),
        ('prepagada', 'Medicina Prepagada'),
        ('particular', 'Particular'),
        ('soat', 'SOAT'),
        ('poliza', 'Póliza de Seguros'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_patients')
    
    # Relación con terceros (el paciente es un cliente en el sistema de terceros)
    third_party = models.OneToOneField(ThirdParty, on_delete=models.CASCADE, related_name='gynecology_patient_profile')
    
    # Información médica específica
    medical_record_number = models.CharField(max_length=50, help_text="Número de historia clínica")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    
    # Información de aseguramiento
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_CHOICES, default='eps')
    eps_name = models.CharField(max_length=200, blank=True, help_text="Nombre de la EPS")
    insurance_number = models.CharField(max_length=50, blank=True, help_text="Número de afiliación")
    
    # Contacto de emergencia
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Información obstétrica básica
    pregnancies = models.IntegerField(default=0, help_text="Gestaciones")
    births = models.IntegerField(default=0, help_text="Partos")
    abortions = models.IntegerField(default=0, help_text="Abortos")
    cesarean_sections = models.IntegerField(default=0, help_text="Cesáreas")
    
    # Estado del paciente
    is_active = models.BooleanField(default=True)
    registration_date = models.DateField(auto_now_add=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_patients')
    
    class Meta:
        db_table = 'gynecology_patients'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        unique_together = ['company', 'medical_record_number']
        ordering = ['third_party__first_name', 'third_party__last_name']
    
    def __str__(self):
        return f"{self.third_party.get_full_name()} - HC: {self.medical_record_number}"
    
    def get_full_name(self):
        return self.third_party.get_full_name()
    
    def get_age(self):
        if self.third_party.birth_date:
            today = date.today()
            return today.year - self.third_party.birth_date.year - ((today.month, today.day) < (self.third_party.birth_date.month, self.third_party.birth_date.day))
        return None


class GynecologyConsultationType(models.Model):
    """
    Tipos de consulta ginecológica.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_consultation_types')
    
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración de la consulta
    duration_minutes = models.IntegerField(default=30, help_text="Duración estimada en minutos")
    requires_preparation = models.BooleanField(default=False, help_text="Requiere preparación especial")
    preparation_instructions = models.TextField(blank=True)
    
    # Tarifas
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'gynecology_consultation_types'
        verbose_name = 'Tipo de Consulta'
        verbose_name_plural = 'Tipos de Consulta'
        unique_together = ['company', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class GynecologyProcedure(models.Model):
    """
    Procedimientos ginecológicos.
    """
    PROCEDURE_CATEGORY_CHOICES = [
        ('diagnostico', 'Procedimientos Diagnósticos'),
        ('terapeutico', 'Procedimientos Terapéuticos'),
        ('quirurgico_menor', 'Cirugía Menor'),
        ('quirurgico_mayor', 'Cirugía Mayor'),
        ('ambulatorio', 'Procedimientos Ambulatorios'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_procedures')
    
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=PROCEDURE_CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Configuración del procedimiento
    requires_anesthesia = models.BooleanField(default=False)
    requires_hospitalization = models.BooleanField(default=False)
    estimated_duration = models.IntegerField(help_text="Duración estimada en minutos")
    
    # Instrucciones
    pre_procedure_instructions = models.TextField(blank=True)
    post_procedure_instructions = models.TextField(blank=True)
    
    # Tarifas
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'gynecology_procedures'
        verbose_name = 'Procedimiento Ginecológico'
        verbose_name_plural = 'Procedimientos Ginecológicos'
        unique_together = ['company', 'code']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class GynecologyAppointment(models.Model):
    """
    Citas ginecológicas.
    """
    APPOINTMENT_TYPE_CHOICES = [
        ('consulta', 'Consulta Externa'),
        ('control', 'Control'),
        ('procedimiento', 'Procedimiento'),
        ('cirugia', 'Cirugía'),
        ('urgencia', 'Urgencia'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('in_progress', 'En Curso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'Inasistencia'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_appointments')
    
    # Información básica
    appointment_number = models.CharField(max_length=50, help_text="Número de cita")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    
    # Fecha y hora
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    estimated_duration = models.IntegerField(default=30, help_text="Duración estimada en minutos")
    
    # Tipo de cita
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES)
    consultation_type = models.ForeignKey(GynecologyConsultationType, on_delete=models.PROTECT, null=True, blank=True)
    procedure = models.ForeignKey(GynecologyProcedure, on_delete=models.PROTECT, null=True, blank=True)
    
    # Médico asignado (del sistema de empleados con especialidad)
    attending_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, 
                                           help_text="Médico especialista asignado")
    
    # Motivo y observaciones
    chief_complaint = models.TextField(help_text="Motivo de consulta")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Control de tiempo
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_appointments')
    
    class Meta:
        db_table = 'gynecology_appointments'
        verbose_name = 'Cita Ginecológica'
        verbose_name_plural = 'Citas Ginecológicas'
        unique_together = ['company', 'appointment_number']
        ordering = ['appointment_date', 'appointment_time']
    
    def __str__(self):
        return f"Cita {self.appointment_number} - {self.patient.get_full_name()} - {self.appointment_date}"
    
    def get_full_datetime(self):
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    def is_past_due(self):
        return self.get_full_datetime() < timezone.now()


class GynecologyMedicalRecord(models.Model):
    """
    Historia clínica ginecológica.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_medical_records')
    
    # Relación con la cita
    appointment = models.OneToOneField(GynecologyAppointment, on_delete=models.CASCADE, related_name='medical_record')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    
    # Anamnesis ginecológica
    menarche_age = models.IntegerField(null=True, blank=True, help_text="Edad de menarquia")
    last_menstrual_period = models.DateField(null=True, blank=True, help_text="Fecha última menstruación")
    menstrual_cycle_days = models.IntegerField(null=True, blank=True, help_text="Días del ciclo menstrual")
    sexually_active = models.BooleanField(null=True, blank=True)
    contraceptive_method = models.CharField(max_length=200, blank=True)
    
    # Antecedentes obstétricos
    obstetric_history = models.TextField(blank=True, help_text="Historia obstétrica detallada")
    
    # Examen físico
    general_appearance = models.TextField(blank=True)
    vital_signs = models.JSONField(default=dict, help_text="Signos vitales")
    breast_examination = models.TextField(blank=True, help_text="Examen de mamas")
    gynecological_examination = models.TextField(blank=True, help_text="Examen ginecológico")
    
    # Hallazgos
    clinical_findings = models.TextField(blank=True, help_text="Hallazgos clínicos")
    
    # Diagnósticos
    primary_diagnosis = models.CharField(max_length=500, help_text="Diagnóstico principal")
    secondary_diagnoses = models.TextField(blank=True, help_text="Diagnósticos secundarios")
    
    # Tratamiento y plan
    treatment_plan = models.TextField(blank=True, help_text="Plan de tratamiento")
    medications = models.TextField(blank=True, help_text="Medicamentos prescritos")
    recommendations = models.TextField(blank=True, help_text="Recomendaciones")
    
    # Seguimiento
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'gynecology_medical_records'
        verbose_name = 'Historia Clínica Ginecológica'
        verbose_name_plural = 'Historias Clínicas Ginecológicas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"HC {self.patient.medical_record_number} - {self.created_at.date()}"


class GynecologyLabResult(models.Model):
    """
    Resultados de laboratorio específicos de ginecología.
    """
    RESULT_TYPE_CHOICES = [
        ('citologia', 'Citología Cervical'),
        ('colposcopia', 'Colposcopia'),
        ('biopsia', 'Biopsia'),
        ('ecografia', 'Ecografía Ginecológica'),
        ('hormonal', 'Perfil Hormonal'),
        ('cultivo', 'Cultivo Vaginal'),
        ('marcadores', 'Marcadores Tumorales'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gynecology_lab_results')
    
    # Relaciones
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    medical_record = models.ForeignKey(GynecologyMedicalRecord, on_delete=models.CASCADE, 
                                     related_name='lab_results', null=True, blank=True)
    
    # Información del estudio
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES)
    study_name = models.CharField(max_length=200)
    study_date = models.DateField()
    
    # Resultados
    results = models.TextField(help_text="Resultados del estudio")
    interpretation = models.TextField(blank=True, help_text="Interpretación del resultado")
    
    # Estado
    is_abnormal = models.BooleanField(default=False)
    requires_follow_up = models.BooleanField(default=False)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'gynecology_lab_results'
        verbose_name = 'Resultado de Laboratorio'
        verbose_name_plural = 'Resultados de Laboratorio'
        ordering = ['-study_date']
    
    def __str__(self):
        return f"{self.study_name} - {self.patient.get_full_name()} - {self.study_date}"