"""
Modelos para el módulo de Citas Médicas.
Sistema completo de gestión de citas con selección de médicos por especialidad.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
import uuid


class DoctorSchedule(models.Model):
    """
    Horario de trabajo de los médicos por día de la semana.
    """
    WEEKDAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    doctor = models.ForeignKey('payroll.Employee', on_delete=models.CASCADE, related_name='schedules')
    
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_duration = models.IntegerField(default=30, help_text="Duración de cita en minutos")
    
    # Configuración de citas
    max_appointments_per_slot = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='schedules_created')
    
    class Meta:
        db_table = 'doctor_schedules'
        verbose_name = 'Horario de Médico'
        verbose_name_plural = 'Horarios de Médicos'
        unique_together = ['doctor', 'weekday', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
    
    def get_available_slots(self, date):
        """Obtiene los slots disponibles para una fecha específica."""
        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        
        while current_time < end_time:
            # Verificar cuántas citas hay en este slot
            existing_appointments = MedicalAppointment.objects.filter(
                doctor=self.doctor,
                appointment_date=current_time,
                status__in=['confirmed', 'in_progress']
            ).count()
            
            if existing_appointments < self.max_appointments_per_slot:
                slots.append(current_time.time())
            
            current_time += timedelta(minutes=self.appointment_duration)
        
        return slots


class AppointmentType(models.Model):
    """
    Tipos de cita médica disponibles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    specialty = models.CharField(max_length=30, help_text="Especialidad médica requerida")
    
    # Configuración
    duration_minutes = models.IntegerField(default=30, validators=[MinValueValidator(15)])
    requires_authorization = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)
    
    # Precios
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='appointment_types_created')
    
    class Meta:
        db_table = 'appointment_types'
        verbose_name = 'Tipo de Cita'
        verbose_name_plural = 'Tipos de Cita'
        unique_together = ['company', 'code']
    
    def __str__(self):
        return f"{self.name} ({self.specialty})"


class MedicalAppointment(models.Model):
    """
    Cita médica con selección de doctor por especialidad.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('in_progress', 'En Curso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No Asistió'),
        ('rescheduled', 'Reprogramada'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    # Información básica
    appointment_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.CASCADE,
                               limit_choices_to={'type': 'customer', 'is_patient': True})
    
    # Cita
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.PROTECT)
    doctor = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, related_name='appointments')
    appointment_date = models.DateTimeField()
    estimated_duration = models.IntegerField(default=30, help_text="Duración estimada en minutos")
    
    # Estado y prioridad
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Detalles
    chief_complaint = models.TextField(help_text="Motivo de consulta")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    # Autorización y seguros
    authorization_number = models.CharField(max_length=50, blank=True)
    insurance_info = models.JSONField(default=dict, help_text="Información del seguro")
    
    # Contacto
    patient_phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    
    # Reprogramación
    original_appointment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='rescheduled_appointments')
    reschedule_reason = models.TextField(blank=True)
    
    # Resultados
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    consultation_summary = models.TextField(blank=True)
    
    # Facturación
    is_billable = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='appointments_created')
    updated_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='appointments_updated')
    
    class Meta:
        db_table = 'medical_appointments'
        verbose_name = 'Cita Médica'
        verbose_name_plural = 'Citas Médicas'
        unique_together = ['company', 'appointment_number']
        ordering = ['appointment_date']
    
    def __str__(self):
        return f"Cita #{self.appointment_number} - {self.patient.name} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"
    
    def get_duration_display(self):
        """Retorna la duración formateada."""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return f"{duration.total_seconds() // 60:.0f} minutos"
        return f"{self.estimated_duration} minutos (estimado)"
    
    def can_be_rescheduled(self):
        """Verifica si la cita puede ser reprogramada."""
        return self.status in ['pending', 'confirmed'] and self.appointment_date > timezone.now()
    
    def can_be_cancelled(self):
        """Verifica si la cita puede ser cancelada."""
        return self.status not in ['completed', 'cancelled', 'no_show']
    
    def is_overdue(self):
        """Verifica si la cita está vencida."""
        return self.appointment_date < timezone.now() and self.status in ['pending', 'confirmed']
    
    def get_patient_age_at_appointment(self):
        """Calcula la edad del paciente al momento de la cita."""
        if hasattr(self.patient, 'patient_profile') and self.patient.patient_profile.birth_date:
            birth_date = self.patient.patient_profile.birth_date
            appointment_date = self.appointment_date.date()
            age = appointment_date.year - birth_date.year
            if appointment_date < birth_date.replace(year=appointment_date.year):
                age -= 1
            return age
        return None


class AppointmentReminder(models.Model):
    """
    Recordatorios automáticos para citas médicas.
    """
    REMINDER_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('call', 'Llamada'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(MedicalAppointment, on_delete=models.CASCADE, related_name='reminders')
    
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPE_CHOICES)
    scheduled_time = models.DateTimeField()
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'appointment_reminders'
        verbose_name = 'Recordatorio de Cita'
        verbose_name_plural = 'Recordatorios de Citas'
    
    def __str__(self):
        return f"Recordatorio {self.get_reminder_type_display()} - Cita #{self.appointment.appointment_number}"


class WaitingList(models.Model):
    """
    Lista de espera para citas médicas cuando no hay disponibilidad.
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('notified', 'Notificado'),
        ('scheduled', 'Agendada'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.CASCADE,
                               limit_choices_to={'type': 'customer', 'is_patient': True})
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.CASCADE)
    preferred_doctor = models.ForeignKey('payroll.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Preferencias de fecha
    preferred_date_start = models.DateField()
    preferred_date_end = models.DateField()
    preferred_time_start = models.TimeField(null=True, blank=True)
    preferred_time_end = models.TimeField(null=True, blank=True)
    
    # Información de contacto
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=10, choices=MedicalAppointment.PRIORITY_CHOICES, default='normal')
    
    # Notas
    notes = models.TextField(blank=True)
    
    # Seguimiento
    notified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='waiting_lists_created')
    
    class Meta:
        db_table = 'appointment_waiting_list'
        verbose_name = 'Lista de Espera'
        verbose_name_plural = 'Listas de Espera'
        ordering = ['priority', 'created_at']
    
    def __str__(self):
        return f"Lista de espera - {self.patient.name} - {self.appointment_type.name}"