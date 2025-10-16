"""
Modelos del módulo Hospitalización
Gestión completa de camas, ingresos, egresos, estancias y evoluciones
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import timedelta

from core.models import Company, User
from patients.models import Patient


# ==================== INFRAESTRUCTURA HOSPITALARIA ====================

class Ward(models.Model):
    """Pabellón o Área Hospitalaria"""
    WARD_TYPE_CHOICES = [
        ('general', 'Hospitalización General'),
        ('pediatrics', 'Pediatría'),
        ('maternity', 'Maternidad'),
        ('icu', 'UCI (Unidad de Cuidados Intensivos)'),
        ('intermediate_care', 'Cuidados Intermedios'),
        ('surgery', 'Cirugía'),
        ('oncology', 'Oncología'),
        ('psychiatry', 'Psiquiatría'),
        ('isolation', 'Aislamiento'),
        ('emergency', 'Urgencias'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='wards')

    code = models.CharField(max_length=20, help_text="Código del pabellón")
    name = models.CharField(max_length=200)
    ward_type = models.CharField(max_length=30, choices=WARD_TYPE_CHOICES)
    floor = models.IntegerField(help_text="Piso donde se encuentra")
    building = models.CharField(max_length=100, blank=True, help_text="Edificio o torre")

    # Configuración
    bed_capacity = models.IntegerField(validators=[MinValueValidator(1)])
    has_intensive_care = models.BooleanField(default=False)
    has_isolation = models.BooleanField(default=False)

    # Responsables
    head_nurse = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='ward_head_nurse',
                                    help_text="Enfermera jefe")
    coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='ward_coordinator')

    observations = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='wards_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitalization_ward'
        verbose_name = 'Pabellón'
        verbose_name_plural = 'Pabellones'
        ordering = ['floor', 'name']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_available_beds_count(self):
        """Obtiene número de camas disponibles"""
        return self.beds.filter(status='available', is_active=True).count()

    def get_occupied_beds_count(self):
        """Obtiene número de camas ocupadas"""
        return self.beds.filter(status='occupied', is_active=True).count()

    def get_occupancy_rate(self):
        """Tasa de ocupación del pabellón"""
        total = self.beds.filter(is_active=True).count()
        if total == 0:
            return 0
        occupied = self.get_occupied_beds_count()
        return (occupied / total) * 100


class Bed(models.Model):
    """Cama Hospitalaria"""
    BED_TYPE_CHOICES = [
        ('standard', 'Estándar'),
        ('electric', 'Eléctrica'),
        ('icu', 'UCI'),
        ('pediatric', 'Pediátrica'),
        ('neonatal', 'Neonatal'),
        ('bariatric', 'Bariátrica'),
    ]

    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('occupied', 'Ocupada'),
        ('maintenance', 'En Mantenimiento'),
        ('cleaning', 'En Limpieza'),
        ('reserved', 'Reservada'),
        ('isolation', 'Aislamiento'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='beds')
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='beds')

    code = models.CharField(max_length=20, help_text="Código de la cama (ej: 201-A)")
    room_number = models.CharField(max_length=20, help_text="Número de habitación")
    bed_number = models.CharField(max_length=10, help_text="Número de cama en la habitación")

    bed_type = models.CharField(max_length=20, choices=BED_TYPE_CHOICES, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    # Características
    has_oxygen = models.BooleanField(default=False, help_text="Toma de oxígeno")
    has_suction = models.BooleanField(default=False, help_text="Succión")
    has_monitor = models.BooleanField(default=False, help_text="Monitor de signos vitales")
    has_ventilator = models.BooleanField(default=False, help_text="Ventilador mecánico")
    is_isolation_room = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False, help_text="Habitación privada")

    # Precios
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                      help_text="Tarifa diaria de la cama")

    observations = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='beds_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitalization_bed'
        verbose_name = 'Cama'
        verbose_name_plural = 'Camas'
        ordering = ['ward', 'room_number', 'bed_number']
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.code} - {self.ward.name} - Hab. {self.room_number}"

    def is_available(self):
        return self.status == 'available' and self.is_active

    def get_current_admission(self):
        """Obtiene la admisión actual si la cama está ocupada"""
        return self.admissions.filter(status='active').first()


# ==================== GESTIÓN DE HOSPITALIZACIONES ====================

class Admission(models.Model):
    """Ingreso/Admisión Hospitalaria"""
    ADMISSION_TYPE_CHOICES = [
        ('emergency', 'Urgencias'),
        ('programmed', 'Programada'),
        ('referral', 'Remitido'),
        ('newborn', 'Recién Nacido'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activa'),
        ('discharged', 'Egresado'),
        ('transferred', 'Transferido'),
        ('cancelled', 'Cancelada'),
    ]

    DISCHARGE_TYPE_CHOICES = [
        ('medical', 'Alta Médica'),
        ('voluntary', 'Alta Voluntaria'),
        ('death', 'Fallecimiento'),
        ('transfer', 'Traslado a otra Institución'),
        ('escape', 'Fuga'),
        ('administrative', 'Alta Administrativa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='admissions')

    # Identificación
    admission_number = models.CharField(max_length=50, unique=True,
                                         help_text="Número único de admisión")

    # Paciente
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='admissions')

    # Cama asignada
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='admissions')

    # Información de ingreso
    admission_date = models.DateTimeField(default=timezone.now)
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES)
    admission_diagnosis = models.TextField(help_text="Diagnóstico de ingreso")
    admission_reason = models.TextField(help_text="Motivo de hospitalización")

    # Médico responsable
    attending_physician = models.ForeignKey(User, on_delete=models.PROTECT,
                                             related_name='admissions_physician',
                                             help_text="Médico tratante")

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Información de egreso
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharge_type = models.CharField(max_length=20, choices=DISCHARGE_TYPE_CHOICES,
                                       null=True, blank=True)
    discharge_diagnosis = models.TextField(blank=True, help_text="Diagnóstico de egreso")
    discharge_summary = models.TextField(blank=True, help_text="Resumen de egreso")
    discharge_recommendations = models.TextField(blank=True,
                                                  help_text="Recomendaciones al alta")

    # Seguimiento
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    followup_observations = models.TextField(blank=True)

    # Facturación
    is_billed = models.BooleanField(default=False)
    total_stay_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='admissions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitalization_admission'
        verbose_name = 'Admisión'
        verbose_name_plural = 'Admisiones'
        ordering = ['-admission_date']

    def __str__(self):
        return f"{self.admission_number} - {self.patient.third_party.get_full_name()}"

    def get_stay_duration(self):
        """Calcula la duración de la estancia"""
        end_date = self.discharge_date if self.discharge_date else timezone.now()
        duration = end_date - self.admission_date
        return duration.days

    def get_stay_hours(self):
        """Calcula las horas de estancia"""
        end_date = self.discharge_date if self.discharge_date else timezone.now()
        duration = end_date - self.admission_date
        return int(duration.total_seconds() / 3600)

    def calculate_stay_cost(self):
        """Calcula el costo total de la estancia"""
        days = self.get_stay_duration()
        if days == 0:
            days = 1  # Mínimo 1 día

        bed_cost = self.bed.daily_rate * days

        # Sumar costos de servicios adicionales
        services_cost = sum([item.get_total() for item in self.service_items.all()])

        total = bed_cost + services_cost
        return total

    def can_discharge(self):
        """Verifica si se puede dar de alta"""
        return self.status == 'active'


class AdmissionTransfer(models.Model):
    """Traslado de paciente entre camas/pabellones"""
    TRANSFER_REASON_CHOICES = [
        ('medical', 'Razón Médica'),
        ('upgrade', 'Mejora de Condición'),
        ('downgrade', 'Estabilización'),
        ('isolation', 'Aislamiento'),
        ('patient_request', 'Solicitud del Paciente'),
        ('administrative', 'Administrativa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE,
                                   related_name='transfers')

    from_bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='transfers_from')
    to_bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='transfers_to')

    transfer_date = models.DateTimeField(default=timezone.now)
    transfer_reason = models.CharField(max_length=30, choices=TRANSFER_REASON_CHOICES)
    medical_justification = models.TextField(help_text="Justificación médica del traslado")

    authorized_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                       related_name='transfers_authorized',
                                       help_text="Médico que autoriza")
    executed_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                     related_name='transfers_executed',
                                     help_text="Personal que ejecuta el traslado")

    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        db_table = 'hospitalization_admission_transfer'
        verbose_name = 'Traslado'
        verbose_name_plural = 'Traslados'
        ordering = ['-transfer_date']

    def __str__(self):
        return f"Traslado {self.admission.admission_number} - {self.transfer_date}"


# ==================== EVOLUCIONES Y NOTAS MÉDICAS ====================

class MedicalEvolution(models.Model):
    """Evolución Médica"""
    EVOLUTION_TYPE_CHOICES = [
        ('daily', 'Evolución Diaria'),
        ('specialty', 'Interconsulta Especialidad'),
        ('surgery', 'Post-Quirúrgica'),
        ('emergency', 'Urgencias'),
        ('nursing', 'Nota de Enfermería'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE,
                                   related_name='evolutions')

    evolution_date = models.DateTimeField(default=timezone.now)
    evolution_type = models.CharField(max_length=20, choices=EVOLUTION_TYPE_CHOICES)

    # Signos vitales
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                       help_text="Temperatura °C")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Frecuencia cardíaca")
    respiratory_rate = models.IntegerField(null=True, blank=True,
                                            help_text="Frecuencia respiratoria")
    blood_pressure_sys = models.IntegerField(null=True, blank=True, help_text="Presión sistólica")
    blood_pressure_dia = models.IntegerField(null=True, blank=True, help_text="Presión diastólica")
    oxygen_saturation = models.IntegerField(null=True, blank=True, help_text="Saturación O2 %")

    # Evolución clínica
    subjective = models.TextField(help_text="Subjetivo (síntomas reportados)")
    objective = models.TextField(help_text="Objetivo (examen físico)")
    assessment = models.TextField(help_text="Análisis/Diagnóstico")
    plan = models.TextField(help_text="Plan de manejo")

    observations = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                    help_text="Profesional que registra")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hospitalization_medical_evolution'
        verbose_name = 'Evolución Médica'
        verbose_name_plural = 'Evoluciones Médicas'
        ordering = ['-evolution_date']

    def __str__(self):
        return f"Evolución {self.admission.admission_number} - {self.evolution_date}"

    def get_blood_pressure(self):
        if self.blood_pressure_sys and self.blood_pressure_dia:
            return f"{self.blood_pressure_sys}/{self.blood_pressure_dia}"
        return None


# ==================== ÓRDENES MÉDICAS ====================

class MedicalOrder(models.Model):
    """Orden Médica"""
    ORDER_TYPE_CHOICES = [
        ('medication', 'Medicamento'),
        ('procedure', 'Procedimiento'),
        ('lab', 'Laboratorio'),
        ('imaging', 'Imagenología'),
        ('diet', 'Dieta'),
        ('therapy', 'Terapia'),
        ('nursing', 'Cuidado de Enfermería'),
        ('consultation', 'Interconsulta'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('suspended', 'Suspendida'),
    ]

    PRIORITY_CHOICES = [
        ('routine', 'Rutina'),
        ('urgent', 'Urgente'),
        ('stat', 'STAT (Inmediato)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='orders')

    order_date = models.DateTimeField(default=timezone.now)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine')

    description = models.TextField(help_text="Descripción detallada de la orden")
    dosage = models.CharField(max_length=200, blank=True,
                               help_text="Dosis (para medicamentos)")
    frequency = models.CharField(max_length=100, blank=True,
                                  help_text="Frecuencia de administración")
    duration = models.CharField(max_length=100, blank=True,
                                 help_text="Duración del tratamiento")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Ejecución
    execution_date = models.DateTimeField(null=True, blank=True)
    execution_notes = models.TextField(blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='orders_executed')

    observations = models.TextField(blank=True)

    ordered_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                    related_name='orders_created',
                                    help_text="Médico que ordena")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitalization_medical_order'
        verbose_name = 'Orden Médica'
        verbose_name_plural = 'Órdenes Médicas'
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.get_order_type_display()} - {self.admission.admission_number}"


# ==================== SERVICIOS Y FACTURACIÓN ====================

class AdmissionServiceItem(models.Model):
    """Items de servicios consumidos durante la hospitalización"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE,
                                   related_name='service_items')

    service_date = models.DateTimeField(default=timezone.now)
    service_code = models.CharField(max_length=50, help_text="Código del servicio (CUPS/SOAT)")
    service_description = models.CharField(max_length=300)

    quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hospitalization_service_item'
        verbose_name = 'Item de Servicio'
        verbose_name_plural = 'Items de Servicios'
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.service_description} - {self.admission.admission_number}"

    def get_subtotal(self):
        return self.quantity * self.unit_price

    def get_discount(self):
        return self.get_subtotal() * (self.discount_percentage / 100)

    def get_total(self):
        return self.get_subtotal() - self.get_discount()
