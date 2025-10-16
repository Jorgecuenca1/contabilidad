"""
Modelos del módulo Telemedicina
Consultas virtuales, atención domiciliaria y firma digital
"""

from django.db import models
from django.db.models import Max
import uuid
from core.models import Company, User
from patients.models import Patient


class TelemedicineAppointment(models.Model):
    """
    Cita de Telemedicina
    Programación de consultas virtuales o atención domiciliaria
    """
    APPOINTMENT_TYPE_CHOICES = [
        ('virtual', 'Consulta Virtual'),
        ('home_care', 'Atención Domiciliaria'),
        ('phone', 'Consulta Telefónica'),
        ('chat', 'Consulta por Chat'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No Asistió'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='telemedicine_appointments')
    appointment_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Cita')

    # Información del paciente y médico
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='telemedicine_appointments', verbose_name='Paciente')
    doctor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='telemedicine_appointments_as_doctor', verbose_name='Médico')

    # Tipo y fecha
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, verbose_name='Tipo de Consulta')
    scheduled_date = models.DateTimeField(verbose_name='Fecha y Hora Programada')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Inicio Real')
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Fin Real')
    duration_minutes = models.IntegerField(default=30, verbose_name='Duración (minutos)')

    # Motivo y detalles
    reason = models.TextField(verbose_name='Motivo de Consulta')
    specialty = models.CharField(max_length=100, blank=True, verbose_name='Especialidad')
    priority = models.CharField(max_length=20, choices=[
        ('routine', 'Rutina'),
        ('urgent', 'Urgente'),
        ('emergency', 'Emergencia'),
    ], default='routine', verbose_name='Prioridad')

    # Para consultas virtuales
    meeting_link = models.URLField(max_length=500, blank=True, verbose_name='Enlace de Reunión')
    meeting_platform = models.CharField(max_length=50, blank=True, verbose_name='Plataforma',
                                       help_text='Zoom, Teams, Google Meet, etc.')
    meeting_id = models.CharField(max_length=100, blank=True, verbose_name='ID de Reunión')
    meeting_password = models.CharField(max_length=100, blank=True, verbose_name='Contraseña de Reunión')

    # Para atención domiciliaria
    home_address = models.TextField(blank=True, verbose_name='Dirección Domiciliaria')
    home_city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    home_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono de Contacto')
    special_instructions = models.TextField(blank=True, verbose_name='Instrucciones Especiales')

    # Estado y seguimiento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='Estado')
    confirmation_sent = models.BooleanField(default=False, verbose_name='Confirmación Enviada')
    reminder_sent = models.BooleanField(default=False, verbose_name='Recordatorio Enviado')

    # Notas
    pre_consultation_notes = models.TextField(blank=True, verbose_name='Notas Pre-Consulta')
    cancellation_reason = models.TextField(blank=True, verbose_name='Razón de Cancelación')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='telemedicine_appointments_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telemedicine_appointment'
        verbose_name = 'Cita de Telemedicina'
        verbose_name_plural = 'Citas de Telemedicina'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['patient', 'scheduled_date']),
            models.Index(fields=['doctor', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.appointment_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.appointment_number:
            # Auto-generar número de cita
            last_appointment = TelemedicineAppointment.objects.filter(company=self.company).aggregate(
                last_number=Max('appointment_number')
            )
            if last_appointment['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_appointment['last_number'])))
                    self.appointment_number = f"TELE-{last_num + 1:07d}"
                except ValueError:
                    self.appointment_number = "TELE-0000001"
            else:
                self.appointment_number = "TELE-0000001"

        super().save(*args, **kwargs)


class VirtualConsultation(models.Model):
    """
    Consulta Virtual Completada
    Registro de la consulta virtual realizada
    """
    CONSULTATION_TYPE_CHOICES = [
        ('video', 'Videollamada'),
        ('phone', 'Telefónica'),
        ('chat', 'Chat'),
        ('mixed', 'Mixta'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='virtual_consultations')
    consultation_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Consulta')

    # Relación con cita
    appointment = models.OneToOneField(TelemedicineAppointment, on_delete=models.PROTECT,
                                      related_name='virtual_consultation', null=True, blank=True,
                                      verbose_name='Cita Asociada')

    # Información básica
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='virtual_consultations')
    doctor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='virtual_consultations_as_doctor')
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES, default='video')
    consultation_date = models.DateTimeField(verbose_name='Fecha de Consulta')
    duration_minutes = models.IntegerField(verbose_name='Duración (minutos)')

    # Motivo y síntomas
    chief_complaint = models.TextField(verbose_name='Motivo de Consulta')
    symptoms = models.TextField(verbose_name='Síntomas Presentados')
    symptoms_duration = models.CharField(max_length=100, blank=True, verbose_name='Duración de Síntomas')

    # Examen y evaluación remota
    remote_examination = models.TextField(blank=True, verbose_name='Examen Remoto',
                                         help_text='Inspección visual, evaluación de síntomas observables')
    vital_signs_reported = models.TextField(blank=True, verbose_name='Signos Vitales Reportados por Paciente')

    # Diagnóstico y tratamiento
    diagnosis = models.TextField(verbose_name='Diagnóstico')
    treatment_plan = models.TextField(verbose_name='Plan de Tratamiento')
    medications_prescribed = models.TextField(blank=True, verbose_name='Medicamentos Prescritos')

    # Recomendaciones y seguimiento
    recommendations = models.TextField(blank=True, verbose_name='Recomendaciones')
    requires_in_person_visit = models.BooleanField(default=False, verbose_name='Requiere Visita Presencial')
    follow_up_required = models.BooleanField(default=False, verbose_name='Requiere Seguimiento')
    follow_up_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Seguimiento')

    # Exámenes y estudios solicitados
    lab_tests_ordered = models.TextField(blank=True, verbose_name='Laboratorios Solicitados')
    imaging_studies_ordered = models.TextField(blank=True, verbose_name='Estudios de Imagen Solicitados')

    # Incapacidades y certificados
    sick_leave_days = models.IntegerField(null=True, blank=True, verbose_name='Días de Incapacidad')
    medical_certificate_issued = models.BooleanField(default=False, verbose_name='Certificado Médico Emitido')

    # Calidad de conexión y observaciones técnicas
    connection_quality = models.CharField(max_length=20, choices=[
        ('excellent', 'Excelente'),
        ('good', 'Buena'),
        ('fair', 'Regular'),
        ('poor', 'Mala'),
    ], default='good', verbose_name='Calidad de Conexión')
    technical_issues = models.TextField(blank=True, verbose_name='Problemas Técnicos')

    observations = models.TextField(blank=True, verbose_name='Observaciones Generales')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='virtual_consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telemedicine_virtual_consultation'
        verbose_name = 'Consulta Virtual'
        verbose_name_plural = 'Consultas Virtuales'
        ordering = ['-consultation_date']
        indexes = [
            models.Index(fields=['company', 'consultation_date']),
            models.Index(fields=['patient', 'consultation_date']),
        ]

    def __str__(self):
        return f"{self.consultation_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.consultation_number:
            last_consultation = VirtualConsultation.objects.filter(company=self.company).aggregate(
                last_number=Max('consultation_number')
            )
            if last_consultation['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_consultation['last_number'])))
                    self.consultation_number = f"VC-{last_num + 1:07d}"
                except ValueError:
                    self.consultation_number = "VC-0000001"
            else:
                self.consultation_number = "VC-0000001"

        super().save(*args, **kwargs)


class HomeCareVisit(models.Model):
    """
    Atención Domiciliaria
    Registro de visitas médicas a domicilio
    """
    VISIT_TYPE_CHOICES = [
        ('medical_consultation', 'Consulta Médica'),
        ('nursing_care', 'Cuidado de Enfermería'),
        ('therapy', 'Terapia'),
        ('follow_up', 'Seguimiento'),
        ('emergency', 'Emergencia'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_route', 'En Ruta'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='home_care_visits')
    visit_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Visita')

    # Relación con cita
    appointment = models.OneToOneField(TelemedicineAppointment, on_delete=models.PROTECT,
                                      related_name='home_care_visit', null=True, blank=True,
                                      verbose_name='Cita Asociada')

    # Información del paciente y personal
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='home_care_visits')
    healthcare_professional = models.ForeignKey(User, on_delete=models.PROTECT,
                                               related_name='home_care_visits_as_professional',
                                               verbose_name='Profesional de Salud')
    accompanying_staff = models.TextField(blank=True, verbose_name='Personal Acompañante',
                                         help_text='Auxiliares, enfermeras, etc.')

    # Tipo y fechas
    visit_type = models.CharField(max_length=30, choices=VISIT_TYPE_CHOICES, verbose_name='Tipo de Visita')
    scheduled_date = models.DateTimeField(verbose_name='Fecha y Hora Programada')
    actual_arrival_time = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Llegada')
    actual_departure_time = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Salida')
    duration_minutes = models.IntegerField(null=True, blank=True, verbose_name='Duración (minutos)')

    # Dirección
    address = models.TextField(verbose_name='Dirección Completa')
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    neighborhood = models.CharField(max_length=100, blank=True, verbose_name='Barrio')
    landmark_reference = models.TextField(blank=True, verbose_name='Referencias de Ubicación')
    contact_phone = models.CharField(max_length=20, verbose_name='Teléfono de Contacto')

    # Motivo y evaluación
    visit_reason = models.TextField(verbose_name='Motivo de la Visita')
    patient_condition_on_arrival = models.TextField(blank=True, verbose_name='Estado del Paciente al Llegar')

    # Signos vitales tomados
    blood_pressure = models.CharField(max_length=20, blank=True, verbose_name='Presión Arterial')
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Cardíaca')
    respiratory_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia Respiratoria')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Temperatura')
    oxygen_saturation = models.IntegerField(null=True, blank=True, verbose_name='Saturación de Oxígeno (%)')

    # Procedimientos realizados
    procedures_performed = models.TextField(blank=True, verbose_name='Procedimientos Realizados')
    medications_administered = models.TextField(blank=True, verbose_name='Medicamentos Administrados')
    medical_supplies_used = models.TextField(blank=True, verbose_name='Insumos Médicos Utilizados')

    # Evaluación y diagnóstico
    clinical_assessment = models.TextField(verbose_name='Evaluación Clínica')
    diagnosis = models.TextField(blank=True, verbose_name='Diagnóstico')
    treatment_provided = models.TextField(blank=True, verbose_name='Tratamiento Proporcionado')

    # Instrucciones y seguimiento
    instructions_to_patient = models.TextField(blank=True, verbose_name='Instrucciones al Paciente/Familia')
    instructions_to_caregiver = models.TextField(blank=True, verbose_name='Instrucciones al Cuidador')
    next_visit_required = models.BooleanField(default=False, verbose_name='Requiere Próxima Visita')
    next_visit_date = models.DateField(null=True, blank=True, verbose_name='Fecha Próxima Visita')

    # Estado y observaciones
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='Estado')
    patient_satisfaction = models.CharField(max_length=20, choices=[
        ('excellent', 'Excelente'),
        ('good', 'Buena'),
        ('fair', 'Regular'),
        ('poor', 'Mala'),
    ], blank=True, verbose_name='Satisfacción del Paciente')

    observations = models.TextField(blank=True, verbose_name='Observaciones')
    complications = models.TextField(blank=True, verbose_name='Complicaciones o Incidentes')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='home_care_visits_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telemedicine_home_care_visit'
        verbose_name = 'Atención Domiciliaria'
        verbose_name_plural = 'Atenciones Domiciliarias'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['patient', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.visit_number} - {self.patient.third_party.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.visit_number:
            last_visit = HomeCareVisit.objects.filter(company=self.company).aggregate(
                last_number=Max('visit_number')
            )
            if last_visit['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_visit['last_number'])))
                    self.visit_number = f"HC-{last_num + 1:07d}"
                except ValueError:
                    self.visit_number = "HC-0000001"
            else:
                self.visit_number = "HC-0000001"

        super().save(*args, **kwargs)


class MedicalDocument(models.Model):
    """
    Documentos Médicos Generados
    Prescripciones, certificados, órdenes, etc.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('prescription', 'Receta Médica'),
        ('medical_certificate', 'Certificado Médico'),
        ('sick_leave', 'Incapacidad'),
        ('lab_order', 'Orden de Laboratorio'),
        ('imaging_order', 'Orden de Imagen'),
        ('referral', 'Remisión'),
        ('medical_report', 'Informe Médico'),
        ('consent', 'Consentimiento Informado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='telemedicine_documents')
    document_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Documento')

    # Relaciones
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='telemedicine_documents')
    virtual_consultation = models.ForeignKey(VirtualConsultation, on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='documents')
    home_care_visit = models.ForeignKey(HomeCareVisit, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='documents')

    # Tipo y contenido
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, verbose_name='Tipo de Documento')
    document_title = models.CharField(max_length=200, verbose_name='Título del Documento')
    document_content = models.TextField(verbose_name='Contenido del Documento')

    # Información médica
    diagnosis = models.TextField(blank=True, verbose_name='Diagnóstico')
    observations = models.TextField(blank=True, verbose_name='Observaciones')

    # Fechas
    issue_date = models.DateField(verbose_name='Fecha de Emisión')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Válido Hasta')

    # Firma digital
    is_digitally_signed = models.BooleanField(default=False, verbose_name='Firmado Digitalmente')
    signed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='signed_documents',
                                  null=True, blank=True, verbose_name='Firmado Por')
    signature_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Firma')
    digital_signature_hash = models.CharField(max_length=256, blank=True, verbose_name='Hash de Firma Digital')

    # Archivo PDF generado
    pdf_file_path = models.CharField(max_length=500, blank=True, verbose_name='Ruta del Archivo PDF')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='telemedicine_documents_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telemedicine_document'
        verbose_name = 'Documento Médico'
        verbose_name_plural = 'Documentos Médicos'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['company', 'document_type']),
            models.Index(fields=['patient', 'issue_date']),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if not self.document_number:
            last_doc = MedicalDocument.objects.filter(company=self.company).aggregate(
                last_number=Max('document_number')
            )
            if last_doc['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_doc['last_number'])))
                    self.document_number = f"DOC-{last_num + 1:07d}"
                except ValueError:
                    self.document_number = "DOC-0000001"
            else:
                self.document_number = "DOC-0000001"

        super().save(*args, **kwargs)


class DigitalSignature(models.Model):
    """
    Registro de Firmas Digitales
    Para trazabilidad y auditoría de documentos firmados
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='digital_signatures')

    # Documento firmado
    document = models.ForeignKey(MedicalDocument, on_delete=models.PROTECT, related_name='signatures')

    # Información del firmante
    signer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='digital_signatures_made')
    signature_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Firma')

    # Datos técnicos de la firma
    signature_hash = models.CharField(max_length=256, verbose_name='Hash de Firma', unique=True)
    signature_method = models.CharField(max_length=50, default='SHA256', verbose_name='Método de Firma')
    ip_address = models.GenericIPAddressField(verbose_name='Dirección IP')
    device_info = models.TextField(blank=True, verbose_name='Información del Dispositivo')

    # Verificación
    is_valid = models.BooleanField(default=True, verbose_name='Firma Válida')
    verification_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Verificación')

    # Certificado digital (si aplica)
    certificate_serial = models.CharField(max_length=100, blank=True, verbose_name='Serial del Certificado')
    certificate_issuer = models.CharField(max_length=200, blank=True, verbose_name='Emisor del Certificado')

    observations = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        db_table = 'telemedicine_digital_signature'
        verbose_name = 'Firma Digital'
        verbose_name_plural = 'Firmas Digitales'
        ordering = ['-signature_date']

    def __str__(self):
        return f"Firma de {self.signer.get_full_name()} - {self.document.document_number}"


class TelemedicineStatistics(models.Model):
    """
    Estadísticas del Módulo de Telemedicina
    Para reporting y análisis
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='telemedicine_statistics')

    # Período
    period_start = models.DateField(verbose_name='Período Desde')
    period_end = models.DateField(verbose_name='Período Hasta')

    # Estadísticas de citas
    total_appointments = models.IntegerField(default=0, verbose_name='Total de Citas')
    completed_appointments = models.IntegerField(default=0, verbose_name='Citas Completadas')
    cancelled_appointments = models.IntegerField(default=0, verbose_name='Citas Canceladas')

    # Por tipo
    virtual_consultations_count = models.IntegerField(default=0, verbose_name='Consultas Virtuales')
    home_care_visits_count = models.IntegerField(default=0, verbose_name='Atenciones Domiciliarias')

    # Documentos y firmas
    documents_generated = models.IntegerField(default=0, verbose_name='Documentos Generados')
    digital_signatures_count = models.IntegerField(default=0, verbose_name='Firmas Digitales')

    # Calidad
    average_consultation_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                       verbose_name='Duración Promedio (minutos)')
    patient_satisfaction_average = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True,
                                                      verbose_name='Satisfacción Promedio')

    # JSON para datos adicionales
    statistics_data = models.JSONField(default=dict, blank=True, verbose_name='Datos Estadísticos Adicionales')

    generated_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Generación')
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='telemedicine_stats_generated')

    class Meta:
        db_table = 'telemedicine_statistics'
        verbose_name = 'Estadísticas de Telemedicina'
        verbose_name_plural = 'Estadísticas de Telemedicina'
        ordering = ['-period_start']

    def __str__(self):
        return f"Estadísticas {self.period_start} - {self.period_end}"
