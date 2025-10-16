"""
Modelos del módulo Autorizaciones EPS
Gestión completa de solicitudes, aprobaciones y contrarreferencias con aseguradoras
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class AuthorizationRequest(models.Model):
    """
    Solicitud de autorización a EPS
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('submitted', 'Enviada'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobada'),
        ('partial_approved', 'Aprobada Parcialmente'),
        ('denied', 'Negada'),
        ('cancelled', 'Cancelada'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    SERVICE_TYPE_CHOICES = [
        ('consultation', 'Consulta'),
        ('procedure', 'Procedimiento'),
        ('surgery', 'Cirugía'),
        ('hospitalization', 'Hospitalización'),
        ('imaging', 'Imagenología'),
        ('laboratory', 'Laboratorio'),
        ('medication', 'Medicamentos'),
        ('therapy', 'Terapia'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Información básica
    authorization_number = models.CharField(max_length=50, unique=True)
    eps = models.ForeignKey('patients.EPS', on_delete=models.PROTECT, related_name='authorization_requests')
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               limit_choices_to={'type': 'customer', 'is_patient': True})

    # Médico solicitante
    requesting_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                            related_name='authorization_requests')

    # Detalles de la solicitud
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    cups_code = models.CharField(max_length=20, blank=True, help_text="Código CUPS del procedimiento")
    service_description = models.TextField(help_text="Descripción del servicio solicitado")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    # Diagnóstico
    diagnosis_code = models.CharField(max_length=10, help_text="Código CIE-10")
    diagnosis_description = models.CharField(max_length=500)

    # Justificación médica
    medical_justification = models.TextField(help_text="Justificación médica de la solicitud")
    clinical_history_summary = models.TextField(blank=True)

    # Estado y fechas
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    request_date = models.DateTimeField(default=timezone.now)
    submission_date = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    # Respuesta de la EPS
    eps_response = models.TextField(blank=True)
    eps_authorization_number = models.CharField(max_length=100, blank=True)
    approved_quantity = models.IntegerField(null=True, blank=True)
    denial_reason = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='auth_requests_created')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='auth_requests_updated',
                                   null=True, blank=True)

    class Meta:
        db_table = 'authorizations_requests'
        verbose_name = 'Solicitud de Autorización'
        verbose_name_plural = 'Solicitudes de Autorización'
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.authorization_number} - {self.patient} - {self.get_status_display()}"

    def is_expired(self):
        """Verifica si la autorización está vencida"""
        if self.expiration_date and self.status == 'approved':
            return timezone.now().date() > self.expiration_date
        return False

    def approve(self, eps_auth_number, approved_qty, expiration_days, user):
        """Aprueba la autorización"""
        self.status = 'approved' if approved_qty >= self.quantity else 'partial_approved'
        self.eps_authorization_number = eps_auth_number
        self.approved_quantity = approved_qty
        self.response_date = timezone.now()
        self.expiration_date = (timezone.now() + timezone.timedelta(days=expiration_days)).date()
        self.updated_by = user
        self.save()

    def deny(self, reason, user):
        """Niega la autorización"""
        self.status = 'denied'
        self.denial_reason = reason
        self.response_date = timezone.now()
        self.updated_by = user
        self.save()


class CounterReferral(models.Model):
    """
    Contrarreferencia - Respuesta a una autorización o referencia
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('received', 'Recibida por EPS'),
        ('closed', 'Cerrada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Relación con la autorización original
    authorization_request = models.ForeignKey(AuthorizationRequest, on_delete=models.PROTECT,
                                             related_name='counter_referrals')

    # Información básica
    counter_referral_number = models.CharField(max_length=50, unique=True)
    eps = models.ForeignKey('patients.EPS', on_delete=models.PROTECT)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               limit_choices_to={'type': 'customer', 'is_patient': True})

    # Médico que envía la contrarreferencia
    referring_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                           related_name='counter_referrals')

    # Detalles de la atención realizada
    service_date = models.DateField(help_text="Fecha en que se prestó el servicio")
    services_provided = models.TextField(help_text="Descripción de los servicios prestados")

    # Resultados y evolución
    treatment_results = models.TextField(help_text="Resultados del tratamiento")
    patient_evolution = models.TextField(blank=True, help_text="Evolución del paciente")
    final_diagnosis = models.CharField(max_length=500, help_text="Diagnóstico final")

    # Recomendaciones
    recommendations = models.TextField(help_text="Recomendaciones para el médico tratante")
    requires_followup = models.BooleanField(default=False)
    followup_instructions = models.TextField(blank=True)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Fechas
    creation_date = models.DateTimeField(default=timezone.now)
    sent_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='counter_refs_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authorizations_counter_referrals'
        verbose_name = 'Contrarreferencia'
        verbose_name_plural = 'Contrarreferencias'
        ordering = ['-creation_date']

    def __str__(self):
        return f"{self.counter_referral_number} - {self.patient}"

    def mark_as_sent(self):
        """Marca la contrarreferencia como enviada"""
        self.status = 'sent'
        self.sent_date = timezone.now()
        self.save()


class AuthorizationAttachment(models.Model):
    """
    Documentos adjuntos a solicitudes de autorización
    """
    DOCUMENT_TYPE_CHOICES = [
        ('medical_order', 'Orden Médica'),
        ('clinical_history', 'Historia Clínica'),
        ('lab_results', 'Resultados de Laboratorio'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('consent', 'Consentimiento Informado'),
        ('eps_response', 'Respuesta EPS'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Puede estar adjunto a una solicitud o una contrarreferencia
    authorization_request = models.ForeignKey(AuthorizationRequest, on_delete=models.CASCADE,
                                             related_name='attachments', null=True, blank=True)
    counter_referral = models.ForeignKey(CounterReferral, on_delete=models.CASCADE,
                                        related_name='attachments', null=True, blank=True)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='authorizations/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)

    class Meta:
        db_table = 'authorizations_attachments'
        verbose_name = 'Documento Adjunto'
        verbose_name_plural = 'Documentos Adjuntos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class AuthorizationUsage(models.Model):
    """
    Registro de uso de autorizaciones aprobadas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    authorization_request = models.ForeignKey(AuthorizationRequest, on_delete=models.PROTECT,
                                             related_name='usage_records')

    usage_date = models.DateTimeField(default=timezone.now)
    quantity_used = models.IntegerField(validators=[MinValueValidator(1)])

    # Relación con atención médica
    medical_record = models.ForeignKey('medical_records.MedicalRecord', on_delete=models.PROTECT,
                                      null=True, blank=True)
    consultation = models.ForeignKey('medical_records.Consultation', on_delete=models.PROTECT,
                                    null=True, blank=True)

    notes = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)

    class Meta:
        db_table = 'authorizations_usage'
        verbose_name = 'Uso de Autorización'
        verbose_name_plural = 'Usos de Autorizaciones'
        ordering = ['-usage_date']

    def __str__(self):
        return f"{self.authorization_request.authorization_number} - {self.quantity_used} usado(s)"
