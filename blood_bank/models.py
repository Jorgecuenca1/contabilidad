"""
Modelos del módulo Banco de Sangre
Gestión completa de donantes, hemocomponentes, compatibilidad e inventario
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Donor(models.Model):
    """
    Donante de sangre
    """
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido Temporalmente'),
        ('permanently_deferred', 'Diferido Permanente'),
        ('inactive', 'Inactivo'),
    ]

    DONOR_TYPE_CHOICES = [
        ('voluntary', 'Voluntario'),
        ('directed', 'Dirigido'),
        ('autologous', 'Autólogo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Información del donante (puede o no estar en sistema como paciente)
    third_party = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                                   null=True, blank=True,
                                   help_text="Si el donante está registrado en el sistema")

    # Información básica (si no está en third_parties)
    document_type = models.CharField(max_length=20, blank=True)
    document_number = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True,
                             choices=[('M', 'Masculino'), ('F', 'Femenino')])
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=300, blank=True)

    # Información del donante
    donor_code = models.CharField(max_length=50, unique=True)
    donor_type = models.CharField(max_length=20, choices=DONOR_TYPE_CHOICES, default='voluntary')
    blood_type = models.CharField(max_length=5,
                                 choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                                         ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')])
    rh_factor = models.CharField(max_length=10,
                                choices=[('positive', 'Positivo'), ('negative', 'Negativo')])

    # Estado
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    deferral_reason = models.TextField(blank=True)
    deferral_end_date = models.DateField(null=True, blank=True)

    # Estadísticas
    total_donations = models.IntegerField(default=0)
    last_donation_date = models.DateField(null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='donors_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blood_bank_donors'
        verbose_name = 'Donante'
        verbose_name_plural = 'Donantes'
        ordering = ['-last_donation_date']

    def __str__(self):
        if self.third_party:
            return f"{self.donor_code} - {self.third_party.get_full_name()} ({self.blood_type})"
        return f"{self.donor_code} - {self.first_name} {self.last_name} ({self.blood_type})"

    def can_donate(self):
        """Verifica si el donante puede donar"""
        if self.status == 'permanently_deferred':
            return False
        if self.status == 'suspended' and self.deferral_end_date:
            return timezone.now().date() > self.deferral_end_date
        return self.status == 'active'


class Donation(models.Model):
    """
    Registro de donación de sangre
    """
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_process', 'En Proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('adverse_reaction', 'Reacción Adversa'),
    ]

    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Sangre Total'),
        ('plateletpheresis', 'Plaquetaféresis'),
        ('plasmapheresis', 'Plasmaféresis'),
        ('double_red_cell', 'Doble Glóbulo Rojo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    donation_number = models.CharField(max_length=50, unique=True)
    donor = models.ForeignKey(Donor, on_delete=models.PROTECT, related_name='donations')

    # Información de la donación
    donation_type = models.CharField(max_length=30, choices=DONATION_TYPE_CHOICES, default='whole_blood')
    donation_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Evaluación pre-donación
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                   validators=[MinValueValidator(Decimal('30.0'))])
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                    help_text="Hemoglobina en g/dL")
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    pre_donation_approved = models.BooleanField(default=False)
    pre_donation_notes = models.TextField(blank=True)

    # Volumen extraído
    volume_ml = models.IntegerField(null=True, blank=True,
                                   validators=[MinValueValidator(50), MaxValueValidator(500)])

    # Personal que atendió
    phlebotomist = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='donations_performed')
    supervising_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                             related_name='donations_supervised',
                                             null=True, blank=True)

    # Reacciones adversas
    adverse_reaction = models.BooleanField(default=False)
    adverse_reaction_description = models.TextField(blank=True)

    # Notas
    notes = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='donations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blood_bank_donations'
        verbose_name = 'Donación'
        verbose_name_plural = 'Donaciones'
        ordering = ['-donation_date']

    def __str__(self):
        return f"{self.donation_number} - {self.donor} - {self.donation_date.strftime('%Y-%m-%d')}"


class BloodComponent(models.Model):
    """
    Hemocomponente derivado de una donación
    """
    COMPONENT_TYPE_CHOICES = [
        ('whole_blood', 'Sangre Total'),
        ('packed_red_cells', 'Glóbulos Rojos Empaquetados'),
        ('platelet_concentrate', 'Concentrado Plaquetario'),
        ('fresh_frozen_plasma', 'Plasma Fresco Congelado'),
        ('cryoprecipitate', 'Crioprecipitado'),
        ('granulocytes', 'Granulocitos'),
    ]

    STATUS_CHOICES = [
        ('quarantine', 'En Cuarentena'),
        ('available', 'Disponible'),
        ('reserved', 'Reservado'),
        ('issued', 'Despachado'),
        ('expired', 'Vencido'),
        ('discarded', 'Descartado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Identificación
    component_code = models.CharField(max_length=50, unique=True)
    donation = models.ForeignKey(Donation, on_delete=models.PROTECT, related_name='components')

    # Tipo de componente
    component_type = models.CharField(max_length=30, choices=COMPONENT_TYPE_CHOICES)
    blood_type = models.CharField(max_length=5,
                                 choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                                         ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')])

    # Volumen y almacenamiento
    volume_ml = models.IntegerField(validators=[MinValueValidator(1)])
    storage_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            help_text="Temperatura en °C")

    # Fechas importantes
    collection_date = models.DateTimeField()
    expiration_date = models.DateTimeField()

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='quarantine')
    discard_reason = models.TextField(blank=True)

    # Ubicación en banco
    storage_location = models.CharField(max_length=100, blank=True,
                                       help_text="Refrigerador/Freezer #, Rack, Posición")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='components_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blood_bank_components'
        verbose_name = 'Hemocomponente'
        verbose_name_plural = 'Hemocomponentes'
        ordering = ['expiration_date']

    def __str__(self):
        return f"{self.component_code} - {self.get_component_type_display()} ({self.blood_type})"

    def is_expired(self):
        """Verifica si el componente está vencido"""
        return timezone.now() > self.expiration_date

    def days_until_expiration(self):
        """Días restantes hasta el vencimiento"""
        if self.is_expired():
            return 0
        delta = self.expiration_date - timezone.now()
        return delta.days


class ScreeningTest(models.Model):
    """
    Pruebas de cribado (screening) obligatorias para donaciones
    """
    TEST_TYPE_CHOICES = [
        ('hiv', 'VIH'),
        ('hepatitis_b', 'Hepatitis B (HBsAg)'),
        ('hepatitis_c', 'Hepatitis C (Anti-HCV)'),
        ('syphilis', 'Sífilis (VDRL/RPR)'),
        ('chagas', 'Chagas (T. cruzi)'),
        ('htlv', 'HTLV I/II'),
    ]

    RESULT_CHOICES = [
        ('negative', 'Negativo'),
        ('positive', 'Positivo'),
        ('indeterminate', 'Indeterminado'),
        ('pending', 'Pendiente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='screening_tests')

    test_type = models.CharField(max_length=30, choices=TEST_TYPE_CHOICES)
    test_date = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')

    # Detalles del resultado
    result_value = models.CharField(max_length=100, blank=True)
    result_notes = models.TextField(blank=True)

    # Laboratorio
    performed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='screening_tests_performed')
    equipment_used = models.CharField(max_length=200, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)

    class Meta:
        db_table = 'blood_bank_screening_tests'
        verbose_name = 'Prueba de Cribado'
        verbose_name_plural = 'Pruebas de Cribado'
        unique_together = ['donation', 'test_type']
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.donation.donation_number} - {self.get_test_type_display()}: {self.get_result_display()}"


class CompatibilityTest(models.Model):
    """
    Pruebas de compatibilidad pre-transfusión
    """
    TEST_TYPE_CHOICES = [
        ('abo_rh', 'ABO/Rh'),
        ('crossmatch', 'Prueba Cruzada (Crossmatch)'),
        ('antibody_screen', 'Rastreo de Anticuerpos'),
        ('direct_coombs', 'Coombs Directo'),
        ('indirect_coombs', 'Coombs Indirecto'),
    ]

    RESULT_CHOICES = [
        ('compatible', 'Compatible'),
        ('incompatible', 'Incompatible'),
        ('pending', 'Pendiente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Paciente receptor
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               limit_choices_to={'type': 'customer', 'is_patient': True})

    # Componente a transfundir
    blood_component = models.ForeignKey(BloodComponent, on_delete=models.PROTECT,
                                       related_name='compatibility_tests')

    test_type = models.CharField(max_length=30, choices=TEST_TYPE_CHOICES)
    test_date = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')

    # Detalles
    result_details = models.TextField(blank=True)

    # Personal
    performed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='compatibility_tests_performed')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)

    class Meta:
        db_table = 'blood_bank_compatibility_tests'
        verbose_name = 'Prueba de Compatibilidad'
        verbose_name_plural = 'Pruebas de Compatibilidad'
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.patient} - {self.blood_component.component_code} - {self.get_result_display()}"


class Transfusion(models.Model):
    """
    Registro de transfusión de hemocomponentes
    """
    STATUS_CHOICES = [
        ('ordered', 'Ordenada'),
        ('prepared', 'Preparada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('stopped', 'Detenida'),
        ('adverse_reaction', 'Reacción Adversa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    transfusion_number = models.CharField(max_length=50, unique=True)

    # Paciente
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               limit_choices_to={'type': 'customer', 'is_patient': True},
                               related_name='transfusions')
    medical_record = models.ForeignKey('medical_records.MedicalRecord', on_delete=models.PROTECT,
                                      null=True, blank=True)

    # Componente transfundido
    blood_component = models.ForeignKey(BloodComponent, on_delete=models.PROTECT,
                                       related_name='transfusions')

    # Orden médica
    ordering_physician = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                          related_name='transfusions_ordered')
    indication = models.TextField(help_text="Indicación médica para la transfusión")

    # Ejecución
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    administering_nurse = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                           related_name='transfusions_administered',
                                           null=True, blank=True)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')

    # Reacciones adversas
    adverse_reaction = models.BooleanField(default=False)
    adverse_reaction_type = models.CharField(max_length=200, blank=True)
    adverse_reaction_description = models.TextField(blank=True)
    adverse_reaction_management = models.TextField(blank=True)

    # Notas
    notes = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='transfusions_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blood_bank_transfusions'
        verbose_name = 'Transfusión'
        verbose_name_plural = 'Transfusiones'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transfusion_number} - {self.patient} - {self.blood_component}"

    def duration_minutes(self):
        """Calcula la duración de la transfusión en minutos"""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return None
