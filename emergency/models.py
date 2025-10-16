"""
Modelos del módulo Urgencias
Sistema de urgencias médicas con triage y admisión
"""

from django.db import models
from django.db.models import Max
import uuid
from core.models import Company, User
from patients.models import Patient


class TriageAssessment(models.Model):
    """
    Evaluación de Triage
    Clasificación inicial del paciente según gravedad
    """
    TRIAGE_LEVEL_CHOICES = [
        ('I', 'Nivel I - Resucitación (Rojo)'),
        ('II', 'Nivel II - Emergencia (Naranja)'),
        ('III', 'Nivel III - Urgencia (Amarillo)'),
        ('IV', 'Nivel IV - Urgencia Menor (Verde)'),
        ('V', 'Nivel V - No Urgente (Azul)'),
    ]

    ARRIVAL_MODE_CHOICES = [
        ('walking', 'Caminando'),
        ('wheelchair', 'Silla de Ruedas'),
        ('stretcher', 'Camilla'),
        ('ambulance', 'Ambulancia'),
        ('police', 'Policía'),
        ('other', 'Otro'),
    ]

    CONSCIOUSNESS_LEVEL_CHOICES = [
        ('alert', 'Alerta'),
        ('verbal', 'Responde a Voz'),
        ('pain', 'Responde al Dolor'),
        ('unresponsive', 'No Responde'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='triage_assessments')
    triage_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Triage')

    # Información del paciente
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='triage_assessments', verbose_name='Paciente')

    # Fecha y hora
    arrival_datetime = models.DateTimeField(verbose_name='Fecha y Hora de Llegada')
    triage_datetime = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Triage')

    # Datos de llegada
    arrival_mode = models.CharField(max_length=20, choices=ARRIVAL_MODE_CHOICES, verbose_name='Modo de Llegada')
    accompanied_by = models.CharField(max_length=200, blank=True, verbose_name='Acompañado por')

    # Motivo de consulta
    chief_complaint = models.TextField(verbose_name='Motivo de Consulta')
    symptom_duration = models.CharField(max_length=100, blank=True, verbose_name='Duración de Síntomas')

    # Signos vitales en triage
    blood_pressure = models.CharField(max_length=20, blank=True, verbose_name='Presión Arterial')
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Cardíaca (lpm)')
    respiratory_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Respiratoria (rpm)')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Temperatura (°C)')
    oxygen_saturation = models.IntegerField(null=True, blank=True, verbose_name='Saturación O2 (%)')
    pain_scale = models.IntegerField(null=True, blank=True, verbose_name='Escala de Dolor (0-10)')

    # Evaluación
    consciousness_level = models.CharField(max_length=20, choices=CONSCIOUSNESS_LEVEL_CHOICES, default='alert', verbose_name='Nivel de Consciencia')
    glasgow_score = models.IntegerField(null=True, blank=True, verbose_name='Escala de Glasgow')

    # Clasificación de triage
    triage_level = models.CharField(max_length=5, choices=TRIAGE_LEVEL_CHOICES, verbose_name='Nivel de Triage')
    triage_color = models.CharField(max_length=20, editable=False, verbose_name='Color de Triage')
    priority_time = models.IntegerField(help_text='Tiempo máximo de espera en minutos', verbose_name='Tiempo Prioridad (min)')

    # Observaciones y signos de alarma
    warning_signs = models.TextField(blank=True, verbose_name='Signos de Alarma')
    allergies = models.TextField(blank=True, verbose_name='Alergias Conocidas')
    current_medications = models.TextField(blank=True, verbose_name='Medicación Actual')

    # Personal y notas
    triage_nurse = models.ForeignKey(User, on_delete=models.PROTECT, related_name='triage_assessments_performed', verbose_name='Enfermera de Triage')
    observations = models.TextField(blank=True, verbose_name='Observaciones de Triage')

    # Estado
    patient_called = models.BooleanField(default=False, verbose_name='Paciente Llamado')
    call_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Llamado')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='triage_assessments_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emergency_triage'
        verbose_name = 'Triage'
        verbose_name_plural = 'Triages'
        ordering = ['triage_level', '-arrival_datetime']
        indexes = [
            models.Index(fields=['company', 'triage_level']),
            models.Index(fields=['patient', 'arrival_datetime']),
        ]

    def __str__(self):
        return f"{self.triage_number} - Nivel {self.triage_level}"

    def save(self, *args, **kwargs):
        if not self.triage_number:
            last_triage = TriageAssessment.objects.filter(company=self.company).aggregate(
                last_number=Max('triage_number')
            )
            if last_triage['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_triage['last_number'])))
                    self.triage_number = f"TRI-{last_num + 1:07d}"
                except ValueError:
                    self.triage_number = "TRI-0000001"
            else:
                self.triage_number = "TRI-0000001"

        # Asignar color según nivel
        color_map = {
            'I': 'Rojo',
            'II': 'Naranja',
            'III': 'Amarillo',
            'IV': 'Verde',
            'V': 'Azul',
        }
        self.triage_color = color_map.get(self.triage_level, 'Sin Color')

        # Asignar tiempo de prioridad según nivel
        time_map = {
            'I': 0,      # Inmediato
            'II': 15,    # 15 minutos
            'III': 30,   # 30 minutos
            'IV': 60,    # 60 minutos
            'V': 120,    # 120 minutos
        }
        if not self.priority_time:
            self.priority_time = time_map.get(self.triage_level, 60)

        super().save(*args, **kwargs)


class EmergencyAdmission(models.Model):
    """
    Admisión a Urgencias
    Registro de ingreso del paciente a urgencias
    """
    STATUS_CHOICES = [
        ('waiting', 'En Espera'),
        ('in_attention', 'En Atención'),
        ('observation', 'En Observación'),
        ('discharged', 'Alta'),
        ('hospitalized', 'Hospitalizado'),
        ('transferred', 'Trasladado'),
        ('deceased', 'Fallecido'),
        ('left_without_attention', 'Salió sin Atención'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_admissions')
    admission_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Admisión')

    # Relación con triage
    triage = models.OneToOneField(TriageAssessment, on_delete=models.PROTECT, related_name='admission', verbose_name='Triage')

    # Información del paciente
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='emergency_admissions')

    # Fechas y tiempos
    admission_datetime = models.DateTimeField(verbose_name='Fecha y Hora de Admisión')
    attention_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Inicio de Atención')
    attention_end_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Fin de Atención')

    # Ubicación en urgencias
    emergency_area = models.CharField(max_length=100, blank=True, verbose_name='Área de Urgencias')
    bed_number = models.CharField(max_length=20, blank=True, verbose_name='Número de Camilla/Cama')

    # Personal médico asignado
    attending_physician = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_admissions_as_physician', verbose_name='Médico Tratante')
    assigned_nurse = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_admissions_as_nurse', null=True, blank=True, verbose_name='Enfermera Asignada')

    # Estado de la admisión
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='waiting', verbose_name='Estado')

    # Información de seguro y autorización
    insurance_company = models.CharField(max_length=200, blank=True, verbose_name='Aseguradora/EPS')
    authorization_number = models.CharField(max_length=100, blank=True, verbose_name='Número de Autorización')
    requires_authorization = models.BooleanField(default=False, verbose_name='Requiere Autorización')

    # Observaciones
    admission_notes = models.TextField(blank=True, verbose_name='Notas de Admisión')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_admissions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emergency_admission'
        verbose_name = 'Admisión de Urgencias'
        verbose_name_plural = 'Admisiones de Urgencias'
        ordering = ['-admission_datetime']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['patient', 'admission_datetime']),
        ]

    def __str__(self):
        return f"{self.admission_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.admission_number:
            last_admission = EmergencyAdmission.objects.filter(company=self.company).aggregate(
                last_number=Max('admission_number')
            )
            if last_admission['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_admission['last_number'])))
                    self.admission_number = f"URG-{last_num + 1:07d}"
                except ValueError:
                    self.admission_number = "URG-0000001"
            else:
                self.admission_number = "URG-0000001"

        super().save(*args, **kwargs)


class VitalSignsRecord(models.Model):
    """
    Registro de Signos Vitales
    Monitoreo continuo de signos vitales durante la estancia
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_vital_signs')
    admission = models.ForeignKey(EmergencyAdmission, on_delete=models.CASCADE, related_name='vital_signs_records', verbose_name='Admisión')

    # Fecha y hora del registro
    recorded_datetime = models.DateTimeField(verbose_name='Fecha y Hora de Registro')

    # Signos vitales
    blood_pressure_systolic = models.IntegerField(null=True, blank=True, verbose_name='Presión Sistólica (mmHg)')
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True, verbose_name='Presión Diastólica (mmHg)')
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Cardíaca (lpm)')
    respiratory_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Respiratoria (rpm)')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Temperatura (°C)')
    oxygen_saturation = models.IntegerField(null=True, blank=True, verbose_name='Saturación O2 (%)')
    pain_scale = models.IntegerField(null=True, blank=True, verbose_name='Escala de Dolor (0-10)')

    # Datos adicionales
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso (kg)')
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Talla (cm)')
    glasgow_score = models.IntegerField(null=True, blank=True, verbose_name='Escala de Glasgow')

    # Observaciones
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    # Personal que registra
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='vital_signs_recorded')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_vital_signs'
        verbose_name = 'Registro de Signos Vitales'
        verbose_name_plural = 'Registros de Signos Vitales'
        ordering = ['-recorded_datetime']

    def __str__(self):
        return f"Signos Vitales - {self.admission.admission_number} - {self.recorded_datetime}"


class EmergencyAttention(models.Model):
    """
    Atención de Urgencias
    Registro médico completo de la atención
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_attentions')
    attention_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Atención')

    # Relación con admisión
    admission = models.OneToOneField(EmergencyAdmission, on_delete=models.PROTECT, related_name='attention', verbose_name='Admisión')
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='emergency_attentions')

    # Atención médica
    physician = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_attentions_as_physician')
    attention_date = models.DateTimeField(verbose_name='Fecha de Atención')

    # Anamnesis
    current_illness = models.TextField(verbose_name='Enfermedad Actual')
    review_of_systems = models.TextField(blank=True, verbose_name='Revisión por Sistemas')
    personal_history = models.TextField(blank=True, verbose_name='Antecedentes Personales')
    family_history = models.TextField(blank=True, verbose_name='Antecedentes Familiares')
    allergies = models.TextField(blank=True, verbose_name='Alergias')
    current_medications = models.TextField(blank=True, verbose_name='Medicamentos Actuales')

    # Examen físico
    general_appearance = models.TextField(blank=True, verbose_name='Apariencia General')
    physical_examination = models.TextField(verbose_name='Examen Físico')
    cardiovascular_exam = models.TextField(blank=True, verbose_name='Examen Cardiovascular')
    respiratory_exam = models.TextField(blank=True, verbose_name='Examen Respiratorio')
    abdominal_exam = models.TextField(blank=True, verbose_name='Examen Abdominal')
    neurological_exam = models.TextField(blank=True, verbose_name='Examen Neurológico')

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico')
    differential_diagnosis = models.TextField(blank=True, verbose_name='Diagnóstico Diferencial')

    # Plan de tratamiento
    treatment_plan = models.TextField(verbose_name='Plan de Tratamiento')
    medications_prescribed = models.TextField(blank=True, verbose_name='Medicamentos Prescritos')
    procedures_indicated = models.TextField(blank=True, verbose_name='Procedimientos Indicados')

    # Estudios solicitados
    lab_tests_ordered = models.TextField(blank=True, verbose_name='Laboratorios Solicitados')
    imaging_studies_ordered = models.TextField(blank=True, verbose_name='Estudios de Imagen Solicitados')

    # Evolución y pronóstico
    clinical_evolution = models.TextField(blank=True, verbose_name='Evolución Clínica')
    prognosis = models.TextField(blank=True, verbose_name='Pronóstico')

    # Observaciones
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_attentions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emergency_attention'
        verbose_name = 'Atención de Urgencias'
        verbose_name_plural = 'Atenciones de Urgencias'
        ordering = ['-attention_date']

    def __str__(self):
        return f"{self.attention_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.attention_number:
            last_attention = EmergencyAttention.objects.filter(company=self.company).aggregate(
                last_number=Max('attention_number')
            )
            if last_attention['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_attention['last_number'])))
                    self.attention_number = f"ATN-{last_num + 1:07d}"
                except ValueError:
                    self.attention_number = "ATN-0000001"
            else:
                self.attention_number = "ATN-0000001"

        super().save(*args, **kwargs)


class EmergencyProcedure(models.Model):
    """
    Procedimientos de Urgencias
    Registro de procedimientos realizados
    """
    PROCEDURE_TYPE_CHOICES = [
        ('suture', 'Sutura'),
        ('wound_care', 'Curación de Herida'),
        ('immobilization', 'Inmovilización'),
        ('catheter', 'Cateterización'),
        ('intubation', 'Intubación'),
        ('defibrillation', 'Desfibrilación'),
        ('minor_surgery', 'Cirugía Menor'),
        ('drainage', 'Drenaje'),
        ('injection', 'Inyección'),
        ('iv_therapy', 'Terapia IV'),
        ('oxygen_therapy', 'Oxigenoterapia'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_procedures')
    admission = models.ForeignKey(EmergencyAdmission, on_delete=models.CASCADE, related_name='procedures', verbose_name='Admisión')

    # Información del procedimiento
    procedure_type = models.CharField(max_length=30, choices=PROCEDURE_TYPE_CHOICES, verbose_name='Tipo de Procedimiento')
    procedure_name = models.CharField(max_length=200, verbose_name='Nombre del Procedimiento')
    procedure_datetime = models.DateTimeField(verbose_name='Fecha y Hora del Procedimiento')

    # Descripción
    indication = models.TextField(verbose_name='Indicación')
    procedure_description = models.TextField(verbose_name='Descripción del Procedimiento')
    materials_used = models.TextField(blank=True, verbose_name='Materiales Utilizados')

    # Personal
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_procedures_performed', verbose_name='Realizado por')
    assisted_by = models.TextField(blank=True, verbose_name='Asistido por')

    # Resultado
    complications = models.TextField(blank=True, verbose_name='Complicaciones')
    outcome = models.TextField(blank=True, verbose_name='Resultado')
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_procedures_created')

    class Meta:
        db_table = 'emergency_procedure'
        verbose_name = 'Procedimiento de Urgencias'
        verbose_name_plural = 'Procedimientos de Urgencias'
        ordering = ['-procedure_datetime']

    def __str__(self):
        return f"{self.procedure_name} - {self.admission.admission_number}"


class EmergencyDischarge(models.Model):
    """
    Alta de Urgencias
    Registro de salida del paciente de urgencias
    """
    DISCHARGE_TYPE_CHOICES = [
        ('home', 'Alta a Domicilio'),
        ('hospitalization', 'Hospitalización'),
        ('observation', 'Pase a Observación'),
        ('transfer', 'Traslado a Otra Institución'),
        ('deceased', 'Fallecido'),
        ('voluntary', 'Alta Voluntaria'),
        ('left_without_attention', 'Salió sin Atención Médica'),
    ]

    DISCHARGE_CONDITION_CHOICES = [
        ('improved', 'Mejorado'),
        ('stable', 'Estable'),
        ('same', 'Sin Cambios'),
        ('worsened', 'Empeorado'),
        ('deceased', 'Fallecido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_discharges')
    discharge_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Alta')

    # Relación con admisión
    admission = models.OneToOneField(EmergencyAdmission, on_delete=models.PROTECT, related_name='discharge', verbose_name='Admisión')
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='emergency_discharges')

    # Información del alta
    discharge_datetime = models.DateTimeField(verbose_name='Fecha y Hora de Alta')
    discharge_type = models.CharField(max_length=30, choices=DISCHARGE_TYPE_CHOICES, verbose_name='Tipo de Alta')
    discharge_condition = models.CharField(max_length=20, choices=DISCHARGE_CONDITION_CHOICES, verbose_name='Condición al Alta')

    # Diagnóstico final
    final_diagnosis = models.TextField(verbose_name='Diagnóstico Final')

    # Tratamiento y recomendaciones
    treatment_received = models.TextField(verbose_name='Tratamiento Recibido')
    discharge_medications = models.TextField(blank=True, verbose_name='Medicamentos al Alta')
    recommendations = models.TextField(verbose_name='Recomendaciones al Alta')
    warning_signs = models.TextField(blank=True, verbose_name='Signos de Alarma')

    # Seguimiento
    follow_up_required = models.BooleanField(default=False, verbose_name='Requiere Seguimiento')
    follow_up_specialty = models.CharField(max_length=100, blank=True, verbose_name='Especialidad de Seguimiento')
    follow_up_days = models.IntegerField(null=True, blank=True, verbose_name='Seguimiento en X Días')

    # Incapacidad
    sick_leave_days = models.IntegerField(null=True, blank=True, verbose_name='Días de Incapacidad')

    # Hospitalización (si aplica)
    hospitalization_service = models.CharField(max_length=100, blank=True, verbose_name='Servicio de Hospitalización')
    bed_assigned = models.CharField(max_length=50, blank=True, verbose_name='Cama Asignada')

    # Traslado (si aplica)
    transfer_institution = models.CharField(max_length=200, blank=True, verbose_name='Institución de Traslado')
    transfer_reason = models.TextField(blank=True, verbose_name='Razón del Traslado')

    # Personal
    discharge_physician = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_discharges_as_physician', verbose_name='Médico que da el Alta')

    # Observaciones
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='emergency_discharges_created')

    class Meta:
        db_table = 'emergency_discharge'
        verbose_name = 'Alta de Urgencias'
        verbose_name_plural = 'Altas de Urgencias'
        ordering = ['-discharge_datetime']

    def __str__(self):
        return f"{self.discharge_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.discharge_number:
            last_discharge = EmergencyDischarge.objects.filter(company=self.company).aggregate(
                last_number=Max('discharge_number')
            )
            if last_discharge['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_discharge['last_number'])))
                    self.discharge_number = f"ALTA-{last_num + 1:07d}"
                except ValueError:
                    self.discharge_number = "ALTA-0000001"
            else:
                self.discharge_number = "ALTA-0000001"

        super().save(*args, **kwargs)
