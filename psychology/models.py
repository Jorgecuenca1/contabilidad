"""
Modelos del módulo Psicología
Sistema completo de consulta psicológica, sesiones terapéuticas y seguimiento
"""

from django.db import models
from django.utils import timezone
import uuid
from core.models import Company, User
from patients.models import Patient


class PsychologicalConsultation(models.Model):
    """Consulta psicológica inicial"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='psychological_consultations')
    psychologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='consultations_as_psychologist')

    consultation_date = models.DateTimeField(default=timezone.now)

    # Motivo de consulta
    chief_complaint = models.TextField(verbose_name='Motivo de consulta')
    referred_by = models.CharField(max_length=200, blank=True, verbose_name='Referido por')

    # Historia personal
    personal_history = models.TextField(blank=True, verbose_name='Historia personal')
    family_history = models.TextField(blank=True, verbose_name='Historia familiar')
    medical_history = models.TextField(blank=True, verbose_name='Historia médica')
    psychiatric_history = models.TextField(blank=True, verbose_name='Antecedentes psiquiátricos')

    # Medicación actual
    current_medications = models.TextField(blank=True, verbose_name='Medicación actual')
    substance_use = models.TextField(blank=True, verbose_name='Uso de sustancias')

    # Examen mental
    appearance = models.TextField(blank=True, verbose_name='Apariencia general')
    behavior = models.TextField(blank=True, verbose_name='Conducta')
    speech = models.TextField(blank=True, verbose_name='Lenguaje')
    mood = models.CharField(max_length=100, blank=True, verbose_name='Estado de ánimo')
    affect = models.CharField(max_length=100, blank=True, verbose_name='Afecto')
    thought_process = models.TextField(blank=True, verbose_name='Proceso de pensamiento')
    thought_content = models.TextField(blank=True, verbose_name='Contenido del pensamiento')
    perception = models.TextField(blank=True, verbose_name='Percepción')
    cognition = models.TextField(blank=True, verbose_name='Cognición')
    insight = models.CharField(max_length=100, blank=True, verbose_name='Insight')
    judgment = models.CharField(max_length=100, blank=True, verbose_name='Juicio')

    # Riesgo
    suicide_risk = models.CharField(max_length=20, choices=[
        ('none', 'Sin riesgo'),
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ], default='none', verbose_name='Riesgo suicida')

    homicide_risk = models.CharField(max_length=20, choices=[
        ('none', 'Sin riesgo'),
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ], default='none', verbose_name='Riesgo homicida')

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico/Impresión clínica')
    dsm_code = models.CharField(max_length=20, blank=True, verbose_name='Código DSM-5')

    # Plan
    treatment_recommendations = models.TextField(verbose_name='Recomendaciones de tratamiento')
    therapy_type = models.CharField(max_length=100, blank=True, verbose_name='Tipo de terapia recomendada')
    frequency = models.CharField(max_length=100, blank=True, verbose_name='Frecuencia recomendada')

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
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='psych_consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_consultation'
        verbose_name = 'Consulta Psicológica'
        verbose_name_plural = 'Consultas Psicológicas'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"{self.consultation_number} - {self.patient}"


class TherapySession(models.Model):
    """Sesión terapéutica"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    session_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(PsychologicalConsultation, on_delete=models.CASCADE, related_name='therapy_sessions', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='therapy_sessions')
    psychologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sessions_as_psychologist')

    session_date = models.DateTimeField(default=timezone.now)
    session_duration = models.IntegerField(default=60, verbose_name='Duración (minutos)')

    # Tipo de sesión
    SESSION_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('couple', 'Pareja'),
        ('family', 'Familiar'),
        ('group', 'Grupal'),
    ]
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='individual')

    # Modalidad
    MODALITY_CHOICES = [
        ('in_person', 'Presencial'),
        ('virtual', 'Virtual'),
        ('phone', 'Telefónica'),
    ]
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='in_person')

    # Contenido de la sesión
    presenting_issues = models.TextField(verbose_name='Temas presentados')
    interventions = models.TextField(verbose_name='Intervenciones realizadas')
    patient_response = models.TextField(blank=True, verbose_name='Respuesta del paciente')

    # Progreso
    progress_summary = models.TextField(blank=True, verbose_name='Resumen de progreso')
    goals_addressed = models.TextField(blank=True, verbose_name='Objetivos abordados')

    # Tareas
    homework_assigned = models.TextField(blank=True, verbose_name='Tareas asignadas')
    homework_completed = models.BooleanField(default=False, verbose_name='Tareas previas completadas')

    # Siguiente sesión
    next_session_date = models.DateField(null=True, blank=True, verbose_name='Próxima sesión')
    next_session_goals = models.TextField(blank=True, verbose_name='Objetivos próxima sesión')

    # Observaciones
    observations = models.TextField(blank=True)

    # Estado
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No asistió'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='therapy_sessions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_therapy_session'
        verbose_name = 'Sesión Terapéutica'
        verbose_name_plural = 'Sesiones Terapéuticas'
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.session_number} - {self.patient} ({self.session_date.strftime('%d/%m/%Y')})"


class PsychologicalAssessment(models.Model):
    """Evaluación psicológica"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    assessment_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(PsychologicalConsultation, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='psychological_assessments')
    psychologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assessments_conducted')

    assessment_date = models.DateField(default=timezone.now)

    # Tipo de evaluación
    ASSESSMENT_TYPE_CHOICES = [
        ('cognitive', 'Evaluación Cognitiva'),
        ('personality', 'Evaluación de Personalidad'),
        ('neuropsychological', 'Evaluación Neuropsicológica'),
        ('vocational', 'Evaluación Vocacional'),
        ('forensic', 'Evaluación Forense'),
        ('clinical', 'Evaluación Clínica'),
    ]
    assessment_type = models.CharField(max_length=30, choices=ASSESSMENT_TYPE_CHOICES)

    # Propósito
    purpose = models.TextField(verbose_name='Propósito de la evaluación')

    # Resultados
    results_summary = models.TextField(verbose_name='Resumen de resultados')
    interpretations = models.TextField(verbose_name='Interpretación')
    conclusions = models.TextField(verbose_name='Conclusiones')
    recommendations = models.TextField(verbose_name='Recomendaciones')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assessments_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_assessment'
        verbose_name = 'Evaluación Psicológica'
        verbose_name_plural = 'Evaluaciones Psicológicas'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.assessment_number} - {self.patient}"


class PsychologicalTest(models.Model):
    """Pruebas psicológicas aplicadas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    assessment = models.ForeignKey(PsychologicalAssessment, on_delete=models.CASCADE, related_name='tests')

    # Información de la prueba
    test_name = models.CharField(max_length=200, verbose_name='Nombre de la prueba')
    test_category = models.CharField(max_length=100, blank=True, verbose_name='Categoría')

    # Resultados
    raw_score = models.CharField(max_length=50, blank=True, verbose_name='Puntaje bruto')
    standardized_score = models.CharField(max_length=50, blank=True, verbose_name='Puntaje estandarizado')
    percentile = models.IntegerField(null=True, blank=True, verbose_name='Percentil')

    # Interpretación
    interpretation = models.TextField(verbose_name='Interpretación')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tests_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_test'
        verbose_name = 'Prueba Psicológica'
        verbose_name_plural = 'Pruebas Psicológicas'
        ordering = ['test_name']

    def __str__(self):
        return f"{self.test_name} - {self.assessment.patient}"


class TreatmentPlan(models.Model):
    """Plan de tratamiento psicológico"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='psychology_treatment_plans')

    plan_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(PsychologicalConsultation, on_delete=models.CASCADE, related_name='treatment_plans')
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='psychology_treatment_plans')
    psychologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='psychology_plans_as_psychologist')

    plan_date = models.DateField(default=timezone.now)
    start_date = models.DateField(verbose_name='Fecha de inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha estimada de finalización')

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico')

    # Objetivos
    long_term_goals = models.TextField(verbose_name='Objetivos a largo plazo')
    short_term_goals = models.TextField(verbose_name='Objetivos a corto plazo')

    # Intervenciones
    therapeutic_approach = models.CharField(max_length=200, verbose_name='Enfoque terapéutico')
    interventions = models.TextField(verbose_name='Intervenciones planificadas')

    # Frecuencia
    session_frequency = models.CharField(max_length=100, verbose_name='Frecuencia de sesiones')
    estimated_sessions = models.IntegerField(null=True, blank=True, verbose_name='Sesiones estimadas')

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
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='psychology_plans_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_treatment_plan'
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-plan_date']

    def __str__(self):
        return f"{self.plan_number} - {self.patient}"


class ProgressNote(models.Model):
    """Nota de progreso/evolución"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    treatment_plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='progress_notes')
    session = models.OneToOneField(TherapySession, on_delete=models.CASCADE, related_name='progress_note', null=True, blank=True)

    note_date = models.DateField(default=timezone.now)

    # SOAP Format
    subjective = models.TextField(verbose_name='Subjetivo (S)', help_text='Lo que el paciente reporta')
    objective = models.TextField(verbose_name='Objetivo (O)', help_text='Observaciones del terapeuta')
    assessment = models.TextField(verbose_name='Evaluación (A)', help_text='Interpretación clínica')
    plan = models.TextField(verbose_name='Plan (P)', help_text='Pasos a seguir')

    # Progreso hacia objetivos
    goals_progress = models.TextField(blank=True, verbose_name='Progreso hacia objetivos')

    # Cambios en el plan
    plan_modifications = models.TextField(blank=True, verbose_name='Modificaciones al plan')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='progress_notes_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'psychology_progress_note'
        verbose_name = 'Nota de Progreso'
        verbose_name_plural = 'Notas de Progreso'
        ordering = ['-note_date']

    def __str__(self):
        return f"Nota - {self.treatment_plan.patient} ({self.note_date.strftime('%d/%m/%Y')})"
