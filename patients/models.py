"""
Modelos del módulo de Pacientes - Maestro completo de pacientes para IPS.
Extiende el modelo de terceros con información médica completa.
Cumple con normativa colombiana (Res. 1995/1999, Ley 1581/2012 Habeas Data)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from datetime import date

from core.models import Company, User
from third_parties.models import ThirdParty


class EPS(models.Model):
    """
    Entidades Promotoras de Salud (EPS) Colombia
    """
    REGIME_CHOICES = [
        ('contributivo', 'Régimen Contributivo'),
        ('subsidiado', 'Régimen Subsidiado'),
        ('especial', 'Régimen Especial'),
        ('excepcion', 'Régimen de Excepción'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='eps_list')

    code = models.CharField(max_length=20, help_text="Código habilitación RIPS")
    nit = models.CharField(max_length=20, help_text="NIT de la EPS")
    name = models.CharField(max_length=200, help_text="Nombre de la EPS")
    regime = models.CharField(max_length=20, choices=REGIME_CHOICES)

    # Contacto
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Configuración para facturación
    requires_authorization = models.BooleanField(default=True, help_text="Requiere autorización previa")
    max_days_authorization = models.IntegerField(default=15, help_text="Días máximos para autorizar")
    payment_term_days = models.IntegerField(default=60, help_text="Plazo de pago en días")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='eps_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients_eps'
        verbose_name = 'EPS'
        verbose_name_plural = 'EPS'
        unique_together = ['company', 'code']
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Patient(models.Model):
    """
    Paciente - Registro maestro completo
    Extiende ThirdParty con información médica y de aseguramiento
    """
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A Positivo'), ('A-', 'A Negativo'),
        ('B+', 'B Positivo'), ('B-', 'B Negativo'),
        ('AB+', 'AB Positivo'), ('AB-', 'AB Negativo'),
        ('O+', 'O Positivo'), ('O-', 'O Negativo'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('soltero', 'Soltero(a)'),
        ('casado', 'Casado(a)'),
        ('union_libre', 'Unión Libre'),
        ('viudo', 'Viudo(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('separado', 'Separado(a)'),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('preescolar', 'Preescolar'),
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('tecnico', 'Técnico'),
        ('tecnologo', 'Tecnólogo'),
        ('profesional', 'Profesional'),
        ('posgrado', 'Posgrado'),
    ]

    REGIME_TYPE_CHOICES = [
        ('contributivo', 'Régimen Contributivo'),
        ('subsidiado', 'Régimen Subsidiado'),
        ('especial', 'Régimen Especial'),
        ('particular', 'Particular'),
        ('otro', 'Otro'),
    ]

    ETHNICITY_CHOICES = [
        ('mestizo', 'Mestizo'),
        ('indigena', 'Indígena'),
        ('afrodescendiente', 'Afrodescendiente'),
        ('rom', 'ROM (Gitano)'),
        ('raizal', 'Raizal del Archipiélago'),
        ('palenquero', 'Palenquero'),
        ('otro', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='patients')

    # Relación con el sistema de terceros
    third_party = models.OneToOneField(ThirdParty, on_delete=models.CASCADE, related_name='general_patient_profile')

    # Identificación única del paciente
    medical_record_number = models.CharField(max_length=50, help_text="Número de historia clínica único")

    # Información demográfica adicional
    birth_municipality = models.CharField(max_length=100, blank=True, help_text="Municipio de nacimiento")
    birth_department = models.CharField(max_length=100, blank=True, help_text="Departamento de nacimiento")
    birth_country = models.CharField(max_length=100, default='Colombia')

    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    ethnicity = models.CharField(max_length=30, choices=ETHNICITY_CHOICES, blank=True)

    # Información de aseguramiento
    regime_type = models.CharField(max_length=20, choices=REGIME_TYPE_CHOICES, default='contributivo')
    eps = models.ForeignKey(EPS, on_delete=models.PROTECT, null=True, blank=True, related_name='patients')
    insurance_number = models.CharField(max_length=50, blank=True, help_text="Número de afiliación a EPS")
    insurance_status = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('retirado', 'Retirado'),
    ], default='activo')

    # Medicina prepagada o póliza adicional
    has_prepaid_medicine = models.BooleanField(default=False)
    prepaid_medicine_name = models.CharField(max_length=200, blank=True)
    prepaid_insurance_number = models.CharField(max_length=50, blank=True)

    # Información médica básica
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    rh_factor = models.CharField(max_length=10, blank=True, help_text="Factor RH")

    # Alergias y condiciones importantes
    allergies = models.TextField(blank=True, help_text="Alergias conocidas (medicamentos, alimentos, otros)")
    chronic_diseases = models.TextField(blank=True, help_text="Enfermedades crónicas")
    disabilities = models.TextField(blank=True, help_text="Discapacidades")

    # Antecedentes
    family_history = models.TextField(blank=True, help_text="Antecedentes familiares")
    surgical_history = models.TextField(blank=True, help_text="Antecedentes quirúrgicos")
    traumatic_history = models.TextField(blank=True, help_text="Antecedentes traumáticos")

    # Contacto de emergencia
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)
    emergency_contact_phone2 = models.CharField(max_length=50, blank=True)

    # Información de responsable (para menores o personas dependientes)
    has_responsible = models.BooleanField(default=False)
    responsible_name = models.CharField(max_length=200, blank=True)
    responsible_document_type = models.CharField(max_length=10, blank=True)
    responsible_document_number = models.CharField(max_length=20, blank=True)
    responsible_relationship = models.CharField(max_length=100, blank=True)
    responsible_phone = models.CharField(max_length=50, blank=True)

    # Consentimientos y autorizaciones
    informed_consent_signed = models.BooleanField(default=False, help_text="Consentimiento informado firmado")
    informed_consent_date = models.DateField(null=True, blank=True)
    data_treatment_authorized = models.BooleanField(default=False, help_text="Autorización tratamiento datos (Habeas Data)")
    data_treatment_date = models.DateField(null=True, blank=True)

    # Fotografía del paciente
    photo = models.ImageField(upload_to='patients/photos/%Y/%m/', blank=True, null=True)

    # Información administrativa
    registration_date = models.DateField(default=timezone.now)
    last_visit_date = models.DateField(null=True, blank=True)
    total_visits = models.IntegerField(default=0)

    # Estado del paciente
    is_active = models.BooleanField(default=True)
    is_deceased = models.BooleanField(default=False)
    deceased_date = models.DateField(null=True, blank=True)
    deceased_cause = models.TextField(blank=True)

    # Observaciones
    notes = models.TextField(blank=True, help_text="Observaciones generales")
    internal_notes = models.TextField(blank=True, help_text="Notas internas (no visibles en historia)")

    # Deduplicación
    duplicate_check_hash = models.CharField(max_length=64, blank=True, help_text="Hash para detectar duplicados")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='patients_created')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients_updated')

    class Meta:
        db_table = 'patients'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        unique_together = ['company', 'medical_record_number']
        ordering = ['-last_visit_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'medical_record_number']),
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['eps', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - HC: {self.medical_record_number}"

    def get_full_name(self):
        """Retorna el nombre completo del paciente"""
        return self.third_party.get_full_name()

    def get_age(self):
        """Calcula la edad del paciente"""
        if self.third_party.birth_date:
            today = date.today()
            born = self.third_party.birth_date
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None

    def get_age_string(self):
        """Retorna la edad en formato legible"""
        age = self.get_age()
        if age is None:
            return "Edad no registrada"
        if age < 1:
            # Calcular meses para bebés
            if self.third_party.birth_date:
                today = date.today()
                months = (today.year - self.third_party.birth_date.year) * 12 + today.month - self.third_party.birth_date.month
                if months < 1:
                    days = (today - self.third_party.birth_date).days
                    return f"{days} días"
                return f"{months} meses"
        return f"{age} años"

    def is_minor(self):
        """Verifica si el paciente es menor de edad"""
        age = self.get_age()
        return age is not None and age < 18

    def requires_responsible(self):
        """Verifica si requiere responsable"""
        return self.is_minor() or self.has_responsible

    def update_visit_count(self):
        """Actualiza el contador de visitas y última fecha"""
        self.total_visits += 1
        self.last_visit_date = date.today()
        self.save(update_fields=['total_visits', 'last_visit_date'])

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        # Si es menor de edad, debe tener responsable
        if self.is_minor() and not self.has_responsible:
            raise ValidationError("Los pacientes menores de edad deben tener un responsable asignado.")

        # Si está fallecido, la fecha de fallecimiento es obligatoria
        if self.is_deceased and not self.deceased_date:
            raise ValidationError("Debe especificar la fecha de fallecimiento.")

        # La fecha de fallecimiento no puede ser futura
        if self.deceased_date and self.deceased_date > date.today():
            raise ValidationError("La fecha de fallecimiento no puede ser futura.")

    def save(self, *args, **kwargs):
        # Generar hash para deduplicación
        if not self.duplicate_check_hash:
            import hashlib
            data = f"{self.third_party.document_number}{self.third_party.first_name}{self.third_party.last_name}"
            self.duplicate_check_hash = hashlib.md5(data.encode()).hexdigest()

        super().save(*args, **kwargs)


class PatientInsuranceHistory(models.Model):
    """
    Historial de cambios de aseguramiento del paciente
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_history')

    eps = models.ForeignKey(EPS, on_delete=models.PROTECT)
    regime_type = models.CharField(max_length=20, choices=Patient.REGIME_TYPE_CHOICES)
    insurance_number = models.CharField(max_length=50)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    is_current = models.BooleanField(default=True)
    change_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        db_table = 'patients_insurance_history'
        verbose_name = 'Historial de Aseguramiento'
        verbose_name_plural = 'Historiales de Aseguramiento'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.eps.name} ({self.start_date})"


class PatientDocument(models.Model):
    """
    Documentos del paciente (consentimientos, autorizaciones, etc.)
    """
    DOCUMENT_TYPE_CHOICES = [
        ('consent', 'Consentimiento Informado'),
        ('authorization', 'Autorización Tratamiento Datos'),
        ('id_copy', 'Copia Documento Identidad'),
        ('eps_card', 'Carnet EPS'),
        ('medical_order', 'Orden Médica Externa'),
        ('lab_result', 'Resultado Laboratorio Externo'),
        ('imaging', 'Imagen Diagnóstica Externa'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='patients/documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)

    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        db_table = 'patients_documents'
        verbose_name = 'Documento del Paciente'
        verbose_name_plural = 'Documentos del Paciente'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
