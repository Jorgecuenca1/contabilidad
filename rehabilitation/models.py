"""
Modelos del módulo Rehabilitación Física (Fisioterapia)
Sistema completo de consultas, evaluaciones, planes y sesiones de rehabilitación
"""

from django.db import models
from django.utils import timezone
import uuid
from core.models import Company, User
from patients.models import Patient


class RehabilitationConsultation(models.Model):
    """Consulta de rehabilitación/fisioterapia inicial"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='rehabilitation_consultations')
    physiotherapist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_consultations_as_therapist')

    consultation_date = models.DateTimeField(default=timezone.now)

    # Motivo de consulta
    chief_complaint = models.TextField(verbose_name='Motivo de consulta')
    injury_mechanism = models.TextField(blank=True, verbose_name='Mecanismo de lesión')
    onset_date = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio de síntomas')

    # Evaluación del dolor
    PAIN_LEVEL_CHOICES = [(i, str(i)) for i in range(11)]  # 0-10
    pain_level = models.IntegerField(
        choices=PAIN_LEVEL_CHOICES, 
        default=0, 
        verbose_name='Nivel de dolor (0-10)'
    )
    pain_location = models.CharField(max_length=200, blank=True, verbose_name='Ubicación del dolor')
    pain_description = models.TextField(blank=True, verbose_name='Descripción del dolor')

    # Antecedentes
    medical_history = models.TextField(blank=True, verbose_name='Antecedentes médicos')
    surgical_history = models.TextField(blank=True, verbose_name='Antecedentes quirúrgicos')
    medications = models.TextField(blank=True, verbose_name='Medicamentos actuales')
    previous_treatments = models.TextField(blank=True, verbose_name='Tratamientos previos')

    # Limitaciones funcionales
    functional_limitations = models.TextField(blank=True, verbose_name='Limitaciones funcionales')

    # Examen físico
    physical_exam_findings = models.TextField(blank=True, verbose_name='Hallazgos del examen físico')

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico fisioterapéutico')

    # Objetivos del tratamiento
    treatment_goals = models.TextField(blank=True, verbose_name='Objetivos del tratamiento')

    # Observaciones
    observations = models.TextField(blank=True)

    # Estado
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_consultation'
        verbose_name = 'Consulta de Rehabilitación'
        verbose_name_plural = 'Consultas de Rehabilitación'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"{self.consultation_number} - {self.patient}"


class PhysicalAssessment(models.Model):
    """Evaluación física detallada"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(
        RehabilitationConsultation, 
        on_delete=models.CASCADE, 
        related_name='physical_assessment'
    )

    # Análisis postural
    posture_analysis = models.TextField(blank=True, verbose_name='Análisis postural')
    
    # Análisis de marcha
    gait_analysis = models.TextField(blank=True, verbose_name='Análisis de marcha')

    # Rango de movimiento (ROM)
    range_of_motion_findings = models.TextField(blank=True, verbose_name='Hallazgos de ROM')

    # Fuerza muscular
    muscle_strength_findings = models.TextField(blank=True, verbose_name='Evaluación de fuerza muscular')

    # Flexibilidad
    flexibility_assessment = models.TextField(blank=True, verbose_name='Evaluación de flexibilidad')

    # Balance/Equilibrio
    balance_assessment = models.TextField(blank=True, verbose_name='Evaluación de balance')

    # Coordinación
    coordination_assessment = models.TextField(blank=True, verbose_name='Evaluación de coordinación')

    # Palpación
    palpation_findings = models.TextField(blank=True, verbose_name='Hallazgos de palpación')

    # Pruebas especiales
    special_tests_performed = models.TextField(blank=True, verbose_name='Pruebas especiales realizadas')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='physical_assessments_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_physical_assessment'
        verbose_name = 'Evaluación Física'
        verbose_name_plural = 'Evaluaciones Físicas'

    def __str__(self):
        return f"Evaluación Física - {self.consultation.consultation_number}"


class RehabilitationPlan(models.Model):
    """Plan de rehabilitación"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    plan_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(
        RehabilitationConsultation, 
        on_delete=models.CASCADE, 
        related_name='rehabilitation_plans'
    )
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='rehabilitation_plans')
    physiotherapist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_plans_as_therapist')

    plan_date = models.DateField(default=timezone.now)
    start_date = models.DateField(verbose_name='Fecha de inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha estimada de finalización')

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico')

    # Objetivos
    short_term_goals = models.TextField(verbose_name='Objetivos a corto plazo')
    long_term_goals = models.TextField(verbose_name='Objetivos a largo plazo')

    # Modalidades terapéuticas
    treatment_modalities = models.TextField(
        verbose_name='Modalidades terapéuticas',
        help_text='Calor, frío, ultrasonido, TENS, láser, electroterapia, etc.'
    )

    # Técnicas de terapia manual
    manual_therapy_techniques = models.TextField(
        blank=True,
        verbose_name='Técnicas de terapia manual',
        help_text='Masaje, movilizaciones, manipulaciones, etc.'
    )

    # Ejercicios terapéuticos
    therapeutic_exercises_description = models.TextField(
        blank=True,
        verbose_name='Descripción de ejercicios terapéuticos'
    )

    # Frecuencia
    frequency_per_week = models.IntegerField(
        default=3,
        verbose_name='Sesiones por semana'
    )
    estimated_sessions = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name='Número estimado de sesiones totales'
    )

    # Precauciones y contraindicaciones
    precautions = models.TextField(blank=True, verbose_name='Precauciones')
    contraindications = models.TextField(blank=True, verbose_name='Contraindicaciones')

    # Observaciones
    observations = models.TextField(blank=True)

    # Estado
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('discontinued', 'Discontinuado'),
        ('on_hold', 'En pausa'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_plans_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_plan'
        verbose_name = 'Plan de Rehabilitación'
        verbose_name_plural = 'Planes de Rehabilitación'
        ordering = ['-plan_date']

    def __str__(self):
        return f"{self.plan_number} - {self.patient}"


class RehabilitationSession(models.Model):
    """Sesión de rehabilitación/fisioterapia"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    session_number = models.CharField(max_length=50, unique=True)
    plan = models.ForeignKey(
        RehabilitationPlan,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='rehabilitation_sessions')
    physiotherapist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_sessions_as_therapist')

    session_date = models.DateTimeField(default=timezone.now)
    session_duration = models.IntegerField(default=60, verbose_name='Duración (minutos)')
    session_number_in_plan = models.IntegerField(default=1, verbose_name='Número de sesión')

    # Evaluación del dolor
    PAIN_LEVEL_CHOICES = [(i, str(i)) for i in range(11)]  # 0-10
    pain_level_pre = models.IntegerField(
        choices=PAIN_LEVEL_CHOICES,
        null=True,
        blank=True,
        verbose_name='Dolor pre-sesión (0-10)'
    )
    pain_level_post = models.IntegerField(
        choices=PAIN_LEVEL_CHOICES,
        null=True,
        blank=True,
        verbose_name='Dolor post-sesión (0-10)'
    )

    # Modalidades aplicadas
    modalities_applied = models.TextField(
        blank=True,
        verbose_name='Modalidades aplicadas',
        help_text='Descripción de modalidades físicas aplicadas'
    )

    # Terapia manual
    manual_therapy_performed = models.TextField(
        blank=True,
        verbose_name='Terapia manual realizada'
    )

    # Ejercicios realizados
    exercises_performed = models.TextField(
        blank=True,
        verbose_name='Ejercicios realizados'
    )

    # Tolerancia del paciente
    patient_tolerance = models.TextField(
        blank=True,
        verbose_name='Tolerancia del paciente',
        help_text='Cómo toleró el paciente la sesión'
    )

    # Respuesta del paciente
    patient_response = models.TextField(
        blank=True,
        verbose_name='Respuesta del paciente',
        help_text='Respuesta observada durante y después de la sesión'
    )

    # Tareas para el hogar
    homework_assigned = models.TextField(
        blank=True,
        verbose_name='Ejercicios/tareas asignadas para el hogar'
    )

    # Objetivos para la próxima sesión
    next_session_goals = models.TextField(
        blank=True,
        verbose_name='Objetivos para próxima sesión'
    )

    # Observaciones
    observations = models.TextField(blank=True)

    # Estado
    STATUS_CHOICES = [
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No asistió'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rehab_sessions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_session'
        verbose_name = 'Sesión de Rehabilitación'
        verbose_name_plural = 'Sesiones de Rehabilitación'
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.session_number} - {self.patient} ({self.session_date.strftime('%d/%m/%Y')})"


class ExercisePrescription(models.Model):
    """Prescripción de ejercicios para el plan de rehabilitación"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    plan = models.ForeignKey(
        RehabilitationPlan,
        on_delete=models.CASCADE,
        related_name='exercises'
    )

    # Información del ejercicio
    exercise_name = models.CharField(max_length=200, verbose_name='Nombre del ejercicio')

    EXERCISE_TYPE_CHOICES = [
        ('stretching', 'Estiramiento'),
        ('strengthening', 'Fortalecimiento'),
        ('balance', 'Equilibrio/Balance'),
        ('cardio', 'Cardiovascular'),
        ('functional', 'Funcional'),
        ('proprioception', 'Propiocepción'),
        ('coordination', 'Coordinación'),
    ]
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        verbose_name='Tipo de ejercicio'
    )

    # Descripción
    description = models.TextField(verbose_name='Descripción detallada')

    # Dosificación
    sets = models.IntegerField(null=True, blank=True, verbose_name='Series')
    repetitions = models.IntegerField(null=True, blank=True, verbose_name='Repeticiones')
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name='Duración (segundos)')

    # Frecuencia
    frequency_per_day = models.IntegerField(default=1, verbose_name='Veces por día')
    days_per_week = models.IntegerField(default=3, verbose_name='Días por semana')

    # Intensidad/Resistencia
    resistance_level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nivel de resistencia',
        help_text='Ej: banda elástica roja, 5kg, peso corporal'
    )

    # Progresión
    progression_criteria = models.TextField(
        blank=True,
        verbose_name='Criterios de progresión',
        help_text='Cuándo y cómo aumentar la dificultad'
    )

    # Precauciones
    precautions = models.TextField(blank=True, verbose_name='Precauciones específicas')

    # Estado
    is_active = models.BooleanField(default=True, verbose_name='Ejercicio activo')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='exercises_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_exercise_prescription'
        verbose_name = 'Prescripción de Ejercicio'
        verbose_name_plural = 'Prescripciones de Ejercicios'
        ordering = ['exercise_type', 'exercise_name']

    def __str__(self):
        return f"{self.exercise_name} - {self.plan.patient}"


class ProgressMeasurement(models.Model):
    """Medición de progreso del paciente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    plan = models.ForeignKey(
        RehabilitationPlan,
        on_delete=models.CASCADE,
        related_name='progress_measurements'
    )

    measurement_date = models.DateField(default=timezone.now)
    measured_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='progress_measurements_conducted'
    )

    # Evaluación del dolor
    PAIN_LEVEL_CHOICES = [(i, str(i)) for i in range(11)]  # 0-10
    pain_level = models.IntegerField(
        choices=PAIN_LEVEL_CHOICES,
        null=True,
        blank=True,
        verbose_name='Nivel de dolor actual (0-10)'
    )

    # Mediciones de ROM
    rom_measurements = models.TextField(
        blank=True,
        verbose_name='Mediciones de rango de movimiento',
        help_text='Ej: Flexión de hombro: 150°, Extensión de rodilla: 0°'
    )

    # Mediciones de fuerza
    strength_measurements = models.TextField(
        blank=True,
        verbose_name='Mediciones de fuerza',
        help_text='Ej: Cuádriceps 4/5, Bíceps 5/5'
    )

    # Resultados de pruebas funcionales
    functional_tests_results = models.TextField(
        blank=True,
        verbose_name='Resultados de pruebas funcionales',
        help_text='Ej: Test de marcha de 6 minutos: 450m'
    )

    # Mejoría reportada por el paciente
    patient_reported_improvement = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Mejoría reportada por paciente (%)',
        help_text='0-100%'
    )

    # Evaluación del terapeuta
    therapist_assessment = models.TextField(
        blank=True,
        verbose_name='Evaluación del terapeuta'
    )

    # Notas objetivas de progreso
    objective_progress_notes = models.TextField(
        blank=True,
        verbose_name='Notas objetivas de progreso'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='progress_measurements_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitation_progress_measurement'
        verbose_name = 'Medición de Progreso'
        verbose_name_plural = 'Mediciones de Progreso'
        ordering = ['-measurement_date']

    def __str__(self):
        return f"Progreso - {self.plan.patient} ({self.measurement_date.strftime('%d/%m/%Y')})"
