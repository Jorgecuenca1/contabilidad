"""
Modelos del módulo Odontología
Sistema completo de odontograma y tratamientos dentales
"""

from django.db import models
from django.utils import timezone
import uuid
from core.models import Company, User
from patients.models import Patient


class DentalProcedureType(models.Model):
    """Tipos de procedimientos odontológicos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    CATEGORY_CHOICES = [
        ('preventive', 'Preventiva'),
        ('restorative', 'Operatoria/Restauración'),
        ('endodontic', 'Endodoncia'),
        ('periodontic', 'Periodoncia'),
        ('surgery', 'Cirugía'),
        ('prosthetic', 'Prótesis'),
        ('orthodontic', 'Ortodoncia'),
        ('pediatric', 'Odontopediatría'),
        ('cosmetic', 'Estética'),
        ('other', 'Otro'),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_duration = models.IntegerField(help_text='Duración en minutos', default=30)

    requires_anesthesia = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dental_procedures_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_procedure_type'
        verbose_name = 'Tipo de Procedimiento Dental'
        verbose_name_plural = 'Tipos de Procedimientos Dentales'
        ordering = ['category', 'name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class DentalCondition(models.Model):
    """Condiciones/Diagnósticos dentales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Color para representación en odontograma
    color = models.CharField(max_length=7, default='#FF0000', help_text='Color hexadecimal')
    symbol = models.CharField(max_length=10, blank=True, help_text='Símbolo para odontograma')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dental_conditions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_condition'
        verbose_name = 'Condición Dental'
        verbose_name_plural = 'Condiciones Dentales'
        ordering = ['name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"


class DentalConsultation(models.Model):
    """Consulta odontológica"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='dental_consultations')
    dentist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dental_consultations_as_dentist')

    consultation_date = models.DateTimeField(default=timezone.now)

    # Motivo de consulta
    chief_complaint = models.TextField(verbose_name='Motivo de consulta')

    # Anamnesis
    current_illness = models.TextField(verbose_name='Enfermedad actual', blank=True)
    dental_history = models.TextField(verbose_name='Antecedentes odontológicos', blank=True)
    medical_history = models.TextField(verbose_name='Antecedentes médicos', blank=True)

    # Examen clínico
    extraoral_examination = models.TextField(verbose_name='Examen extraoral', blank=True)
    intraoral_examination = models.TextField(verbose_name='Examen intraoral', blank=True)

    # Higiene oral
    HYGIENE_CHOICES = [
        ('excellent', 'Excelente'),
        ('good', 'Buena'),
        ('fair', 'Regular'),
        ('poor', 'Mala'),
    ]
    oral_hygiene = models.CharField(max_length=20, choices=HYGIENE_CHOICES, blank=True)

    # Diagnóstico
    diagnosis = models.TextField(verbose_name='Diagnóstico')

    # Observaciones
    observations = models.TextField(blank=True)

    # Estado
    STATUS_CHOICES = [
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dental_consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_consultation'
        verbose_name = 'Consulta Odontológica'
        verbose_name_plural = 'Consultas Odontológicas'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"{self.consultation_number} - {self.patient}"


class Odontogram(models.Model):
    """Odontograma del paciente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='odontograms')
    consultation = models.ForeignKey(DentalConsultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='odontograms')

    odontogram_date = models.DateField(default=timezone.now)

    # Tipo de dentición
    DENTITION_CHOICES = [
        ('deciduous', 'Decidua (Temporal)'),
        ('mixed', 'Mixta'),
        ('permanent', 'Permanente'),
    ]
    dentition_type = models.CharField(max_length=20, choices=DENTITION_CHOICES, default='permanent')

    # Observaciones generales
    general_observations = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='odontograms_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_odontogram'
        verbose_name = 'Odontograma'
        verbose_name_plural = 'Odontogramas'
        ordering = ['-odontogram_date']

    def __str__(self):
        return f"Odontograma - {self.patient} - {self.odontogram_date}"


class OdontogramTooth(models.Model):
    """Estado individual de cada diente en el odontograma"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    odontogram = models.ForeignKey(Odontogram, on_delete=models.CASCADE, related_name='teeth')

    # Nomenclatura FDI (ISO 3950) - Sistema internacional estándar
    # Permanentes: 11-18 (superior derecho), 21-28 (superior izquierdo),
    #              31-38 (inferior izquierdo), 41-48 (inferior derecho)
    # Deciduos: 51-55, 61-65, 71-75, 81-85
    fdi_number = models.CharField(max_length=2, help_text='Número FDI (ej: 11, 21, 46)')

    # Ubicación
    QUADRANT_CHOICES = [
        ('1', 'Cuadrante 1 - Superior Derecho'),
        ('2', 'Cuadrante 2 - Superior Izquierdo'),
        ('3', 'Cuadrante 3 - Inferior Izquierdo'),
        ('4', 'Cuadrante 4 - Inferior Derecho'),
        ('5', 'Cuadrante 5 - Superior Derecho Deciduo'),
        ('6', 'Cuadrante 6 - Superior Izquierdo Deciduo'),
        ('7', 'Cuadrante 7 - Inferior Izquierdo Deciduo'),
        ('8', 'Cuadrante 8 - Inferior Derecho Deciduo'),
    ]
    quadrant = models.CharField(max_length=1, choices=QUADRANT_CHOICES)

    # Tipo de diente
    TOOTH_TYPE_CHOICES = [
        ('incisor', 'Incisivo'),
        ('canine', 'Canino'),
        ('premolar', 'Premolar'),
        ('molar', 'Molar'),
    ]
    tooth_type = models.CharField(max_length=20, choices=TOOTH_TYPE_CHOICES, blank=True)

    # Estado del diente
    STATE_CHOICES = [
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('extracted', 'Extraído'),
        ('congenital_absence', 'Ausencia Congénita'),
        ('unerupted', 'Sin Erupcionar'),
        ('impacted', 'Impactado'),
    ]
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default='present')

    # Condiciones del diente (puede tener múltiples)
    conditions = models.ManyToManyField(DentalCondition, blank=True, related_name='odontogram_teeth')

    # Superficies afectadas
    # O = Oclusal, M = Mesial, D = Distal, V = Vestibular, L/P = Lingual/Palatino
    surface_mesial = models.BooleanField(default=False, verbose_name='Superficie Mesial (M)')
    surface_distal = models.BooleanField(default=False, verbose_name='Superficie Distal (D)')
    surface_occlusal = models.BooleanField(default=False, verbose_name='Superficie Oclusal (O)')
    surface_vestibular = models.BooleanField(default=False, verbose_name='Superficie Vestibular (V)')
    surface_lingual = models.BooleanField(default=False, verbose_name='Superficie Lingual/Palatina (L/P)')

    # Observaciones específicas del diente
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='odontogram_teeth_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_odontogram_tooth'
        verbose_name = 'Diente en Odontograma'
        verbose_name_plural = 'Dientes en Odontograma'
        ordering = ['fdi_number']
        unique_together = [['odontogram', 'fdi_number']]

    def __str__(self):
        return f"Diente {self.fdi_number}"

    def get_surfaces_affected(self):
        """Retorna lista de superficies afectadas"""
        surfaces = []
        if self.surface_mesial:
            surfaces.append('M')
        if self.surface_distal:
            surfaces.append('D')
        if self.surface_occlusal:
            surfaces.append('O')
        if self.surface_vestibular:
            surfaces.append('V')
        if self.surface_lingual:
            surfaces.append('L')
        return ''.join(surfaces) if surfaces else 'Ninguna'


class TreatmentPlan(models.Model):
    """Plan de tratamiento odontológico"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    plan_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='dental_treatment_plans')
    consultation = models.ForeignKey(DentalConsultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='treatment_plans')
    odontogram = models.ForeignKey(Odontogram, on_delete=models.SET_NULL, null=True, blank=True, related_name='treatment_plans')

    dentist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='treatment_plans_as_dentist')

    plan_date = models.DateField(default=timezone.now)

    # Diagnóstico general
    diagnosis = models.TextField()

    # Objetivos del tratamiento
    treatment_objectives = models.TextField(blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    # Costos
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Estado del plan
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Consentimiento
    patient_consent = models.BooleanField(default=False, verbose_name='Consentimiento del paciente')
    consent_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='treatment_plans_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_treatment_plan'
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-plan_date']

    def __str__(self):
        return f"{self.plan_number} - {self.patient}"

    def calculate_total_cost(self):
        """Calcula el costo total del plan"""
        total = sum(item.total_cost for item in self.items.all())
        self.total_estimated_cost = total
        return total


class TreatmentPlanItem(models.Model):
    """Ítem individual del plan de tratamiento"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    treatment_plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='items')

    # Procedimiento
    procedure = models.ForeignKey(DentalProcedureType, on_delete=models.PROTECT, related_name='treatment_plan_items')

    # Diente(s) afectado(s) - puede ser NULL si es un procedimiento general
    tooth_fdi = models.CharField(max_length=2, blank=True, help_text='Número FDI del diente')

    # Superficies (si aplica)
    surfaces = models.CharField(max_length=10, blank=True, help_text='Ej: MOD, V, L')

    # Descripción específica
    description = models.TextField(blank=True)

    # Prioridad
    PRIORITY_CHOICES = [
        ('urgent', 'Urgente'),
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Secuencia en el plan
    sequence = models.IntegerField(default=1)

    # Costos
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Estado del ítem
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Fecha de realización
    completion_date = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='treatment_items_completed')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='treatment_plan_items_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_treatment_plan_item'
        verbose_name = 'Ítem de Plan de Tratamiento'
        verbose_name_plural = 'Ítems de Plan de Tratamiento'
        ordering = ['sequence', 'created_at']

    def __str__(self):
        tooth_info = f" - Diente {self.tooth_fdi}" if self.tooth_fdi else ""
        return f"{self.procedure.name}{tooth_info}"

    def save(self, *args, **kwargs):
        # Calcular costo total
        self.total_cost = self.unit_cost * self.quantity
        super().save(*args, **kwargs)


class DentalProcedureRecord(models.Model):
    """Registro de procedimientos realizados"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    record_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='dental_procedures')
    consultation = models.ForeignKey(DentalConsultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='procedures')
    treatment_plan_item = models.ForeignKey(TreatmentPlanItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='procedure_records')

    # Profesional
    dentist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='procedures_performed')

    # Procedimiento
    procedure = models.ForeignKey(DentalProcedureType, on_delete=models.PROTECT, related_name='procedure_records')

    procedure_date = models.DateField(default=timezone.now)

    # Diente tratado
    tooth_fdi = models.CharField(max_length=2, blank=True)
    surfaces = models.CharField(max_length=10, blank=True)

    # Detalles del procedimiento
    anesthesia_used = models.BooleanField(default=False)
    anesthesia_type = models.CharField(max_length=100, blank=True)

    materials_used = models.TextField(blank=True, verbose_name='Materiales utilizados')

    procedure_notes = models.TextField(blank=True, verbose_name='Notas del procedimiento')

    # Complicaciones
    complications = models.TextField(blank=True)

    # Indicaciones post-procedimiento
    post_procedure_instructions = models.TextField(blank=True, verbose_name='Indicaciones')

    # Próxima cita
    next_appointment_date = models.DateField(null=True, blank=True)

    # Costo
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='procedure_records_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dentistry_procedure_record'
        verbose_name = 'Registro de Procedimiento'
        verbose_name_plural = 'Registros de Procedimientos'
        ordering = ['-procedure_date']

    def __str__(self):
        return f"{self.record_number} - {self.procedure.name}"
