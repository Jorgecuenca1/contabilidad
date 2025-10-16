"""
Modelos del módulo de Cirugías y Quirófano
Programación quirúrgica, control de salas, notas de anestesia y trazabilidad
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class OperatingRoom(models.Model):
    """
    Salas de Quirófano
    """
    ROOM_TYPE_CHOICES = [
        ('general', 'Cirugía General'),
        ('specialized', 'Cirugía Especializada'),
        ('trauma', 'Sala de Trauma'),
        ('ambulatory', 'Cirugía Ambulatoria'),
        ('cardiac', 'Cirugía Cardíaca'),
        ('neurosurgery', 'Neurocirugía'),
    ]

    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('in_use', 'En Uso'),
        ('cleaning', 'En Limpieza'),
        ('maintenance', 'Mantenimiento'),
        ('out_of_service', 'Fuera de Servicio'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    room_number = models.CharField(max_length=50, unique=True)
    room_name = models.CharField(max_length=200)
    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES)
    floor = models.CharField(max_length=50, blank=True)
    building = models.CharField(max_length=100, blank=True)

    capacity = models.IntegerField(default=1, help_text="Número de mesas quirúrgicas")
    has_laminar_flow = models.BooleanField(default=False)
    has_specialized_equipment = models.BooleanField(default=False)
    equipment_description = models.TextField(blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='operating_rooms_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgery_operating_rooms'
        verbose_name = 'Sala de Quirófano'
        verbose_name_plural = 'Salas de Quirófano'
        ordering = ['room_number']

    def __str__(self):
        return f"{self.room_number} - {self.room_name}"


class SurgicalProcedure(models.Model):
    """
    Catálogo de Procedimientos Quirúrgicos
    """
    COMPLEXITY_CHOICES = [
        ('low', 'Baja Complejidad'),
        ('medium', 'Mediana Complejidad'),
        ('high', 'Alta Complejidad'),
        ('very_high', 'Muy Alta Complejidad'),
    ]

    SPECIALTY_CHOICES = [
        ('general', 'Cirugía General'),
        ('orthopedics', 'Ortopedia'),
        ('neurosurgery', 'Neurocirugía'),
        ('cardiac', 'Cirugía Cardíaca'),
        ('vascular', 'Cirugía Vascular'),
        ('plastic', 'Cirugía Plástica'),
        ('gynecology', 'Ginecología'),
        ('urology', 'Urología'),
        ('ophthalmology', 'Oftalmología'),
        ('ent', 'Otorrinolaringología'),
        ('thoracic', 'Cirugía Torácica'),
        ('pediatric', 'Cirugía Pediátrica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    code = models.CharField(max_length=50, unique=True, help_text="Código CUPS o interno")
    name = models.CharField(max_length=300)
    specialty = models.CharField(max_length=30, choices=SPECIALTY_CHOICES)
    complexity = models.CharField(max_length=20, choices=COMPLEXITY_CHOICES)

    description = models.TextField(blank=True)
    estimated_duration_minutes = models.IntegerField(help_text="Duración estimada en minutos")

    requires_icu = models.BooleanField(default=False, verbose_name="Requiere UCI")
    requires_blood_bank = models.BooleanField(default=False, verbose_name="Requiere Banco de Sangre")
    requires_specialized_equipment = models.BooleanField(default=False)
    equipment_needed = models.TextField(blank=True)

    pre_operative_instructions = models.TextField(blank=True)
    post_operative_instructions = models.TextField(blank=True)

    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='surgical_procedures_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgery_procedures'
        verbose_name = 'Procedimiento Quirúrgico'
        verbose_name_plural = 'Procedimientos Quirúrgicos'
        ordering = ['specialty', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Surgery(models.Model):
    """
    Programación Quirúrgica
    """
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('in_preparation', 'En Preparación'),
        ('in_progress', 'En Curso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('postponed', 'Pospuesta'),
    ]

    URGENCY_CHOICES = [
        ('elective', 'Electiva'),
        ('urgent', 'Urgente'),
        ('emergency', 'Emergencia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    surgery_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT, related_name='surgeries')

    # Programación
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    estimated_duration = models.IntegerField(help_text="Duración estimada en minutos")

    # Sala y Equipo
    operating_room = models.ForeignKey(OperatingRoom, on_delete=models.PROTECT, related_name='surgeries')
    surgical_procedure = models.ForeignKey(SurgicalProcedure, on_delete=models.PROTECT, related_name='surgeries')

    # Equipo Médico
    surgeon = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, related_name='surgeries_as_surgeon')
    assistant_surgeon = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                         related_name='surgeries_as_assistant', null=True, blank=True)
    anesthesiologist = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                        related_name='surgeries_as_anesthesiologist')
    scrub_nurse = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='surgeries_as_scrub_nurse', null=True, blank=True)
    circulating_nurse = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                         related_name='surgeries_as_circulating_nurse', null=True, blank=True)

    # Clasificación
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='elective')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='scheduled')

    # Diagnósticos
    pre_operative_diagnosis = models.CharField(max_length=500)
    pre_operative_diagnosis_code = models.CharField(max_length=20, blank=True, help_text="Código CIE-10")

    post_operative_diagnosis = models.CharField(max_length=500, blank=True)
    post_operative_diagnosis_code = models.CharField(max_length=20, blank=True)

    # Indicación Quirúrgica
    surgical_indication = models.TextField(help_text="Indicación quirúrgica")

    # Información Pre-Operatoria
    informed_consent_signed = models.BooleanField(default=False)
    pre_anesthetic_evaluation = models.BooleanField(default=False)
    required_blood_units = models.IntegerField(default=0)
    blood_reserved = models.BooleanField(default=False)

    # Tiempos Quirúrgicos
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    anesthesia_start_time = models.DateTimeField(null=True, blank=True)
    anesthesia_end_time = models.DateTimeField(null=True, blank=True)

    # Descripción Quirúrgica
    surgical_findings = models.TextField(blank=True)
    surgical_technique = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    surgical_specimen = models.TextField(blank=True, help_text="Especímenes enviados a patología")

    # Post-Operatorio
    estimated_blood_loss = models.IntegerField(null=True, blank=True, help_text="Pérdida sanguínea en ml")
    transfusion_required = models.BooleanField(default=False)
    units_transfused = models.IntegerField(default=0)

    destination_after_surgery = models.CharField(max_length=100, blank=True,
                                                help_text="Ej: UCI, Recuperación, Piso")
    post_operative_orders = models.TextField(blank=True)

    # Notas
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='surgeries_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgeries'
        verbose_name = 'Cirugía'
        verbose_name_plural = 'Cirugías'
        ordering = ['-scheduled_date', '-scheduled_time']

    def __str__(self):
        return f"{self.surgery_number} - {self.patient.nombre} - {self.scheduled_date}"

    @property
    def actual_duration_minutes(self):
        """Calcula la duración real de la cirugía"""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return int(duration.total_seconds() / 60)
        return None


class AnesthesiaNote(models.Model):
    """
    Nota de Anestesia
    """
    ANESTHESIA_TYPE_CHOICES = [
        ('general', 'Anestesia General'),
        ('regional', 'Anestesia Regional'),
        ('spinal', 'Anestesia Raquídea'),
        ('epidural', 'Anestesia Epidural'),
        ('combined', 'Anestesia Combinada'),
        ('local', 'Anestesia Local'),
        ('sedation', 'Sedación'),
    ]

    ASA_CLASSIFICATION_CHOICES = [
        ('I', 'ASA I - Paciente sano'),
        ('II', 'ASA II - Enfermedad sistémica leve'),
        ('III', 'ASA III - Enfermedad sistémica grave'),
        ('IV', 'ASA IV - Enfermedad sistémica grave amenazante'),
        ('V', 'ASA V - Paciente moribundo'),
        ('E', 'E - Emergencia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    surgery = models.OneToOneField(Surgery, on_delete=models.CASCADE, related_name='anesthesia_note')
    anesthesiologist = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                        related_name='anesthesia_notes')

    # Evaluación Pre-Anestésica
    pre_anesthetic_evaluation_date = models.DateTimeField()
    asa_classification = models.CharField(max_length=10, choices=ASA_CLASSIFICATION_CHOICES)

    # Antecedentes Relevantes
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    previous_anesthesia = models.TextField(blank=True)
    anesthetic_risk = models.TextField(blank=True)

    # Ayuno
    fasting_hours = models.IntegerField(help_text="Horas de ayuno")

    # Signos Vitales Pre-Operatorios
    pre_weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pre_blood_pressure_systolic = models.IntegerField()
    pre_blood_pressure_diastolic = models.IntegerField()
    pre_heart_rate = models.IntegerField()
    pre_respiratory_rate = models.IntegerField()
    pre_oxygen_saturation = models.IntegerField()
    pre_temperature = models.DecimalField(max_digits=4, decimal_places=1)

    # Plan Anestésico
    anesthesia_type = models.CharField(max_length=30, choices=ANESTHESIA_TYPE_CHOICES)
    anesthetic_technique = models.TextField()
    airway_management = models.CharField(max_length=200, blank=True)
    intubation_details = models.TextField(blank=True)

    # Medicamentos Utilizados
    medications_administered = models.TextField(help_text="Medicamentos anestésicos y dosis")
    fluids_administered = models.TextField(help_text="Líquidos IV administrados")

    # Monitoreo
    monitoring_type = models.TextField(help_text="Tipo de monitoreo utilizado")

    # Signos Vitales Intra-Operatorios (Registro Final)
    intra_blood_pressure_min_systolic = models.IntegerField(null=True, blank=True)
    intra_blood_pressure_max_systolic = models.IntegerField(null=True, blank=True)
    intra_heart_rate_min = models.IntegerField(null=True, blank=True)
    intra_heart_rate_max = models.IntegerField(null=True, blank=True)
    intra_oxygen_saturation_min = models.IntegerField(null=True, blank=True)

    # Eventos Adversos
    adverse_events = models.TextField(blank=True)
    complications = models.TextField(blank=True)

    # Post-Anestesia
    emergence_time = models.DateTimeField(null=True, blank=True)
    extubation_time = models.DateTimeField(null=True, blank=True)
    recovery_room_time = models.DateTimeField(null=True, blank=True)

    post_op_orders = models.TextField(blank=True)
    analgesia_plan = models.TextField(blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='anesthesia_notes_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgery_anesthesia_notes'
        verbose_name = 'Nota de Anestesia'
        verbose_name_plural = 'Notas de Anestesia'
        ordering = ['-created_at']

    def __str__(self):
        return f"Anestesia {self.surgery.surgery_number} - {self.get_anesthesia_type_display()}"


class SurgicalSupply(models.Model):
    """
    Insumos y Materiales Quirúrgicos Utilizados
    """
    SUPPLY_TYPE_CHOICES = [
        ('suture', 'Material de Sutura'),
        ('implant', 'Implante'),
        ('prosthesis', 'Prótesis'),
        ('mesh', 'Malla'),
        ('drainage', 'Drenaje'),
        ('catheter', 'Catéter'),
        ('medication', 'Medicamento'),
        ('disposable', 'Material Desechable'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE, related_name='supplies_used')

    supply_type = models.CharField(max_length=30, choices=SUPPLY_TYPE_CHOICES)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=50, default='unidad')

    lot_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    manufacturer = models.CharField(max_length=200, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='surgical_supplies_created')

    class Meta:
        db_table = 'surgery_supplies'
        verbose_name = 'Insumo Quirúrgico'
        verbose_name_plural = 'Insumos Quirúrgicos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.surgery.surgery_number}"

    @property
    def total_cost(self):
        """Calcula el costo total del insumo"""
        return self.quantity * self.unit_cost


class PostOperativeNote(models.Model):
    """
    Nota Post-Operatoria Inmediata
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    surgery = models.OneToOneField(Surgery, on_delete=models.CASCADE, related_name='post_operative_note')
    written_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                  related_name='post_operative_notes')

    note_datetime = models.DateTimeField(default=timezone.now)

    # Condición del Paciente
    patient_condition = models.TextField(help_text="Condición general del paciente al salir de quirófano")
    consciousness_level = models.CharField(max_length=200)
    vital_signs_stable = models.BooleanField(default=True)

    # Signos Vitales Post-Operatorios
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    oxygen_saturation = models.IntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)

    # Manejo de Dolor
    pain_scale = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)],
                                    help_text="Escala de dolor 0-10")
    analgesic_plan = models.TextField()

    # Drenajes y Sondas
    drains_in_place = models.TextField(blank=True)
    catheters_in_place = models.TextField(blank=True)

    # Órdenes Post-Operatorias
    diet_orders = models.CharField(max_length=200)
    activity_orders = models.TextField()
    medication_orders = models.TextField()
    laboratory_orders = models.TextField(blank=True)
    imaging_orders = models.TextField(blank=True)

    # Control y Seguimiento
    follow_up_instructions = models.TextField()
    warning_signs = models.TextField(help_text="Signos de alarma")

    next_evaluation_time = models.DateTimeField(help_text="Próxima evaluación médica")

    # Observaciones
    observations = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='post_op_notes_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgery_post_operative_notes'
        verbose_name = 'Nota Post-Operatoria'
        verbose_name_plural = 'Notas Post-Operatorias'
        ordering = ['-created_at']

    def __str__(self):
        return f"Post-Op {self.surgery.surgery_number} - {self.note_datetime.strftime('%Y-%m-%d %H:%M')}"
