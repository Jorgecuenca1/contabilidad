"""
Modelos del módulo Oftalmología
Sistema completo de consulta oftalmológica especializada
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid
from core.models import Company, User
from patients.models import Patient


class OphthalConsultation(models.Model):
    """Consulta oftalmológica"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='ophthal_consultations')
    ophthalmologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ophthal_consultations_as_doctor')

    consultation_date = models.DateTimeField(default=timezone.now)

    # Motivo de consulta
    chief_complaint = models.TextField(verbose_name='Motivo de consulta')

    # Antecedentes
    ocular_history = models.TextField(verbose_name='Antecedentes oculares', blank=True)
    family_ocular_history = models.TextField(verbose_name='Antecedentes oculares familiares', blank=True)
    systemic_history = models.TextField(verbose_name='Antecedentes sistémicos', blank=True)
    current_medications = models.TextField(verbose_name='Medicamentos actuales', blank=True)
    allergies = models.TextField(verbose_name='Alergias', blank=True)

    # Síntomas
    symptoms = models.TextField(verbose_name='Síntomas', blank=True)

    # Uso de lentes
    uses_glasses = models.BooleanField(default=False, verbose_name='Usa lentes')
    uses_contact_lenses = models.BooleanField(default=False, verbose_name='Usa lentes de contacto')

    # Diagnóstico
    diagnosis_right_eye = models.TextField(verbose_name='Diagnóstico OD', blank=True)
    diagnosis_left_eye = models.TextField(verbose_name='Diagnóstico OI', blank=True)
    diagnosis_both_eyes = models.TextField(verbose_name='Diagnóstico AO', blank=True)

    # Plan de tratamiento
    treatment_plan = models.TextField(verbose_name='Plan de tratamiento', blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    # Próxima cita
    next_appointment = models.DateField(null=True, blank=True, verbose_name='Próxima cita')

    # Estado
    STATUS_CHOICES = [
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ophthal_consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_consultation'
        verbose_name = 'Consulta Oftalmológica'
        verbose_name_plural = 'Consultas Oftalmológicas'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"{self.consultation_number} - {self.patient}"


class VisualAcuity(models.Model):
    """Agudeza visual"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(OphthalConsultation, on_delete=models.CASCADE, related_name='visual_acuity')

    # Ojo Derecho (OD) - Sin Corrección
    od_distance_sc = models.CharField(max_length=20, blank=True, verbose_name='OD Distancia SC', help_text='Ej: 20/20, 20/40')
    od_near_sc = models.CharField(max_length=20, blank=True, verbose_name='OD Cerca SC')

    # Ojo Derecho (OD) - Con Corrección
    od_distance_cc = models.CharField(max_length=20, blank=True, verbose_name='OD Distancia CC')
    od_near_cc = models.CharField(max_length=20, blank=True, verbose_name='OD Cerca CC')

    # Ojo Izquierdo (OI) - Sin Corrección
    os_distance_sc = models.CharField(max_length=20, blank=True, verbose_name='OI Distancia SC')
    os_near_sc = models.CharField(max_length=20, blank=True, verbose_name='OI Cerca SC')

    # Ojo Izquierdo (OI) - Con Corrección
    os_distance_cc = models.CharField(max_length=20, blank=True, verbose_name='OI Distancia CC')
    os_near_cc = models.CharField(max_length=20, blank=True, verbose_name='OI Cerca CC')

    # Ambos Ojos (AO) - Sin Corrección
    ou_distance_sc = models.CharField(max_length=20, blank=True, verbose_name='AO Distancia SC')
    ou_near_sc = models.CharField(max_length=20, blank=True, verbose_name='AO Cerca SC')

    # Ambos Ojos (AO) - Con Corrección
    ou_distance_cc = models.CharField(max_length=20, blank=True, verbose_name='AO Distancia CC')
    ou_near_cc = models.CharField(max_length=20, blank=True, verbose_name='AO Cerca CC')

    # Agujero estenopeico
    od_pinhole = models.CharField(max_length=20, blank=True, verbose_name='OD Estenopeico')
    os_pinhole = models.CharField(max_length=20, blank=True, verbose_name='OI Estenopeico')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='visual_acuities_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_visual_acuity'
        verbose_name = 'Agudeza Visual'
        verbose_name_plural = 'Agudezas Visuales'

    def __str__(self):
        return f"Agudeza Visual - {self.consultation.consultation_number}"


class Refraction(models.Model):
    """Refracción (Examen de la vista para lentes)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(OphthalConsultation, on_delete=models.CASCADE, related_name='refraction')

    # Ojo Derecho (OD)
    od_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OD Esfera', help_text='Dioptrías')
    od_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OD Cilindro')
    od_axis = models.IntegerField(null=True, blank=True, verbose_name='OD Eje', help_text='0-180 grados')
    od_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='OD Adición', help_text='Para presbicia')
    od_prism = models.CharField(max_length=50, blank=True, verbose_name='OD Prisma')

    # Ojo Izquierdo (OI)
    os_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OI Esfera')
    os_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OI Cilindro')
    os_axis = models.IntegerField(null=True, blank=True, verbose_name='OI Eje')
    os_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='OI Adición')
    os_prism = models.CharField(max_length=50, blank=True, verbose_name='OI Prisma')

    # Distancia pupilar
    pd_distance = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='DP Distancia', help_text='mm')
    pd_near = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='DP Cerca', help_text='mm')

    # Tipo de refracción
    REFRACTION_TYPE_CHOICES = [
        ('subjective', 'Subjetiva'),
        ('objective', 'Objetiva (Retinoscopia/Autorefractor)'),
        ('cycloplegic', 'Ciclopléjica'),
    ]
    refraction_type = models.CharField(max_length=20, choices=REFRACTION_TYPE_CHOICES, default='subjective')

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='refractions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_refraction'
        verbose_name = 'Refracción'
        verbose_name_plural = 'Refracciones'

    def __str__(self):
        return f"Refracción - {self.consultation.consultation_number}"


class IntraocularPressure(models.Model):
    """Presión intraocular (Tonometría)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(OphthalConsultation, on_delete=models.CASCADE, related_name='intraocular_pressure')

    # Presión intraocular
    od_pressure = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='PIO OD', help_text='mmHg')
    os_pressure = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='PIO OI', help_text='mmHg')

    # Método de medición
    METHOD_CHOICES = [
        ('goldmann', 'Tonometría de Goldmann (Aplanación)'),
        ('pneumatic', 'Tonometría Neumática'),
        ('perkins', 'Tonometría de Perkins'),
        ('icare', 'Tonometría de Rebote (iCare)'),
        ('tono_pen', 'Tono-Pen'),
    ]
    measurement_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='goldmann')

    # Hora de medición (importante para glaucoma)
    measurement_time = models.TimeField(null=True, blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='pressures_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_intraocular_pressure'
        verbose_name = 'Presión Intraocular'
        verbose_name_plural = 'Presiones Intraoculares'

    def __str__(self):
        return f"PIO - {self.consultation.consultation_number}"


class Biomicroscopy(models.Model):
    """Biomicroscopía (Examen con lámpara de hendidura)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(OphthalConsultation, on_delete=models.CASCADE, related_name='biomicroscopy')

    # Segmento Anterior OD
    od_lids_lashes = models.TextField(verbose_name='OD Párpados y Pestañas', blank=True)
    od_conjunctiva = models.TextField(verbose_name='OD Conjuntiva', blank=True)
    od_cornea = models.TextField(verbose_name='OD Córnea', blank=True)
    od_anterior_chamber = models.TextField(verbose_name='OD Cámara Anterior', blank=True)
    od_iris = models.TextField(verbose_name='OD Iris', blank=True)
    od_lens = models.TextField(verbose_name='OD Cristalino', blank=True)

    # Segmento Anterior OI
    os_lids_lashes = models.TextField(verbose_name='OI Párpados y Pestañas', blank=True)
    os_conjunctiva = models.TextField(verbose_name='OI Conjuntiva', blank=True)
    os_cornea = models.TextField(verbose_name='OI Córnea', blank=True)
    os_anterior_chamber = models.TextField(verbose_name='OI Cámara Anterior', blank=True)
    os_iris = models.TextField(verbose_name='OI Iris', blank=True)
    os_lens = models.TextField(verbose_name='OI Cristalino', blank=True)

    # Observaciones generales
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='biomicroscopies_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_biomicroscopy'
        verbose_name = 'Biomicroscopía'
        verbose_name_plural = 'Biomicroscopías'

    def __str__(self):
        return f"Biomicroscopía - {self.consultation.consultation_number}"


class FundusExam(models.Model):
    """Examen de fondo de ojo (Oftalmoscopía)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    consultation = models.OneToOneField(OphthalConsultation, on_delete=models.CASCADE, related_name='fundus_exam')

    # Método de examen
    METHOD_CHOICES = [
        ('direct', 'Oftalmoscopía Directa'),
        ('indirect', 'Oftalmoscopía Indirecta'),
        ('slit_lamp', 'Biomicroscopía con Lente'),
    ]
    examination_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='direct')

    # Dilatación pupilar
    pupil_dilation = models.BooleanField(default=False, verbose_name='Dilatación pupilar')
    dilating_agent = models.CharField(max_length=100, blank=True, verbose_name='Midriático usado')

    # Hallazgos OD
    od_media = models.TextField(verbose_name='OD Medios', blank=True, help_text='Claridad de medios')
    od_optic_disc = models.TextField(verbose_name='OD Disco Óptico', blank=True)
    od_cup_disc_ratio = models.CharField(max_length=10, blank=True, verbose_name='OD Relación E/D', help_text='Ej: 0.3')
    od_vessels = models.TextField(verbose_name='OD Vasos', blank=True)
    od_macula = models.TextField(verbose_name='OD Mácula', blank=True)
    od_periphery = models.TextField(verbose_name='OD Periferia', blank=True)

    # Hallazgos OI
    os_media = models.TextField(verbose_name='OI Medios', blank=True)
    os_optic_disc = models.TextField(verbose_name='OI Disco Óptico', blank=True)
    os_cup_disc_ratio = models.CharField(max_length=10, blank=True, verbose_name='OI Relación E/D')
    os_vessels = models.TextField(verbose_name='OI Vasos', blank=True)
    os_macula = models.TextField(verbose_name='OI Mácula', blank=True)
    os_periphery = models.TextField(verbose_name='OI Periferia', blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fundus_exams_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_fundus_exam'
        verbose_name = 'Fondo de Ojo'
        verbose_name_plural = 'Fondos de Ojo'

    def __str__(self):
        return f"Fondo de Ojo - {self.consultation.consultation_number}"


class LensPrescription(models.Model):
    """Prescripción de lentes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    prescription_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(OphthalConsultation, on_delete=models.CASCADE, related_name='lens_prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='lens_prescriptions')
    ophthalmologist = models.ForeignKey(User, on_delete=models.PROTECT, related_name='lens_prescriptions_issued')

    prescription_date = models.DateField(default=timezone.now)

    # Tipo de lentes
    LENS_TYPE_CHOICES = [
        ('single_vision', 'Visión Sencilla'),
        ('bifocal', 'Bifocal'),
        ('progressive', 'Progresivo'),
        ('reading', 'Solo Lectura'),
        ('distance', 'Solo Distancia'),
    ]
    lens_type = models.CharField(max_length=20, choices=LENS_TYPE_CHOICES)

    # Uso
    USAGE_CHOICES = [
        ('full_time', 'Uso Permanente'),
        ('distance', 'Solo Distancia'),
        ('near', 'Solo Cerca'),
        ('computer', 'Computadora'),
    ]
    recommended_usage = models.CharField(max_length=20, choices=USAGE_CHOICES, default='full_time')

    # Especificaciones del lente OD
    od_sphere = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='OD Esfera')
    od_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OD Cilindro')
    od_axis = models.IntegerField(null=True, blank=True, verbose_name='OD Eje')
    od_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='OD Adición')

    # Especificaciones del lente OI
    os_sphere = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='OI Esfera')
    os_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='OI Cilindro')
    os_axis = models.IntegerField(null=True, blank=True, verbose_name='OI Eje')
    os_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='OI Adición')

    # Distancia pupilar
    pd_distance = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='DP Distancia', help_text='mm')
    pd_near = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='DP Cerca', help_text='mm')

    # Recomendaciones especiales
    anti_reflective = models.BooleanField(default=False, verbose_name='Antirreflejo')
    photochromic = models.BooleanField(default=False, verbose_name='Fotocromático')
    blue_filter = models.BooleanField(default=False, verbose_name='Filtro azul')
    polarized = models.BooleanField(default=False, verbose_name='Polarizado')

    # Material recomendado
    MATERIAL_CHOICES = [
        ('plastic', 'Plástico (CR-39)'),
        ('polycarbonate', 'Policarbonato'),
        ('high_index', 'Alto Índice'),
        ('trivex', 'Trivex'),
    ]
    recommended_material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, blank=True)

    # Observaciones
    observations = models.TextField(blank=True)

    # Validez
    valid_until = models.DateField(null=True, blank=True, verbose_name='Válida hasta')

    # Estado
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='prescriptions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ophthalmology_lens_prescription'
        verbose_name = 'Prescripción de Lentes'
        verbose_name_plural = 'Prescripciones de Lentes'
        ordering = ['-prescription_date']

    def __str__(self):
        return f"{self.prescription_number} - {self.patient}"
