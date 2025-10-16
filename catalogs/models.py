"""
Modelos del módulo Catálogos CUPS/CUMS
Catálogos centralizados de procedimientos (CUPS) y medicamentos (CUMS)
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class CUPSProcedure(models.Model):
    """
    Catálogo de Procedimientos en Salud (CUPS)
    Clasificación Única de Procedimientos en Salud - Colombia
    """
    CATEGORY_CHOICES = [
        ('consultation', 'Consulta'),
        ('surgery', 'Cirugía'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('laboratory', 'Laboratorio Clínico'),
        ('therapy', 'Terapia/Rehabilitación'),
        ('hospitalization', 'Hospitalización'),
        ('emergency', 'Urgencias'),
        ('procedure', 'Procedimiento'),
        ('other', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('deprecated', 'Obsoleto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Código CUPS oficial
    cups_code = models.CharField(max_length=20, db_index=True, help_text="Código CUPS oficial")

    # Descripción
    description = models.CharField(max_length=500, help_text="Descripción completa del procedimiento")
    short_description = models.CharField(max_length=200, blank=True)

    # Categorización
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True)

    # Clasificación jerárquica
    chapter = models.CharField(max_length=100, blank=True, help_text="Capítulo del CUPS")
    section = models.CharField(max_length=100, blank=True, help_text="Sección del CUPS")

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    effective_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    # Información adicional
    requires_authorization = models.BooleanField(default=False,
                                                help_text="Requiere autorización previa de EPS")
    requires_specialist = models.BooleanField(default=False)
    estimated_duration_minutes = models.IntegerField(null=True, blank=True)

    # Notas técnicas
    technical_notes = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)

    # Uso y favoritos
    usage_count = models.IntegerField(default=0, help_text="Contador de uso")
    is_favorite = models.BooleanField(default=False)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='cups_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogs_cups_procedures'
        verbose_name = 'Procedimiento CUPS'
        verbose_name_plural = 'Procedimientos CUPS'
        unique_together = ['company', 'cups_code']
        ordering = ['cups_code']
        indexes = [
            models.Index(fields=['cups_code']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.cups_code} - {self.description[:50]}"


class CUMSMedication(models.Model):
    """
    Catálogo de Medicamentos (CUMS)
    Clasificación Única de Medicamentos - Colombia
    """
    PHARMACEUTICAL_FORM_CHOICES = [
        ('tablet', 'Tableta'),
        ('capsule', 'Cápsula'),
        ('syrup', 'Jarabe'),
        ('suspension', 'Suspensión'),
        ('solution', 'Solución'),
        ('injection', 'Inyectable'),
        ('cream', 'Crema'),
        ('ointment', 'Ungüento'),
        ('drops', 'Gotas'),
        ('inhaler', 'Inhalador'),
        ('patch', 'Parche'),
        ('suppository', 'Supositorio'),
        ('other', 'Otro'),
    ]

    ADMINISTRATION_ROUTE_CHOICES = [
        ('oral', 'Oral'),
        ('iv', 'Intravenosa'),
        ('im', 'Intramuscular'),
        ('sc', 'Subcutánea'),
        ('topical', 'Tópica'),
        ('inhalation', 'Inhalación'),
        ('ophthalmic', 'Oftálmica'),
        ('otic', 'Ótica'),
        ('nasal', 'Nasal'),
        ('rectal', 'Rectal'),
        ('vaginal', 'Vaginal'),
        ('other', 'Otra'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('controlled', 'Controlado'),
        ('discontinued', 'Descontinuado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Código CUMS oficial
    cums_code = models.CharField(max_length=20, db_index=True, help_text="Código CUMS oficial")

    # Nombre del medicamento
    generic_name = models.CharField(max_length=300, help_text="Nombre genérico (principio activo)")
    commercial_name = models.CharField(max_length=300, blank=True, help_text="Nombre comercial")

    # Presentación
    pharmaceutical_form = models.CharField(max_length=30, choices=PHARMACEUTICAL_FORM_CHOICES)
    concentration = models.CharField(max_length=100, help_text="Ej: 500mg, 250mg/5ml")
    presentation = models.CharField(max_length=200, help_text="Ej: Caja x 30 tabletas")

    # Administración
    administration_route = models.CharField(max_length=30, choices=ADMINISTRATION_ROUTE_CHOICES)

    # Fabricante
    manufacturer = models.CharField(max_length=200, blank=True)
    importer = models.CharField(max_length=200, blank=True)

    # Registro sanitario
    sanitary_registration = models.CharField(max_length=50, blank=True, help_text="INVIMA")
    registration_date = models.DateField(null=True, blank=True)
    registration_expiry = models.DateField(null=True, blank=True)

    # Clasificación
    atc_code = models.CharField(max_length=20, blank=True, help_text="Código ATC")
    therapeutic_group = models.CharField(max_length=200, blank=True)

    # Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    requires_prescription = models.BooleanField(default=True)
    is_controlled_substance = models.BooleanField(default=False)
    pos_medication = models.BooleanField(default=True, help_text="Medicamento POS")

    # Información clínica
    indications = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    adverse_effects = models.TextField(blank=True)
    dosage_instructions = models.TextField(blank=True)

    # Uso y favoritos
    usage_count = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='cums_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogs_cums_medications'
        verbose_name = 'Medicamento CUMS'
        verbose_name_plural = 'Medicamentos CUMS'
        unique_together = ['company', 'cums_code']
        ordering = ['generic_name']
        indexes = [
            models.Index(fields=['cums_code']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['commercial_name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        name = self.commercial_name if self.commercial_name else self.generic_name
        return f"{self.cums_code} - {name} ({self.concentration})"


class ProcedureTariff(models.Model):
    """
    Tarifas de procedimientos CUPS por EPS/Contrato
    """
    TARIFF_TYPE_CHOICES = [
        ('soat', 'SOAT'),
        ('iss_2001', 'ISS 2001'),
        ('iss_2004', 'ISS 2004'),
        ('particular', 'Particular'),
        ('negotiated', 'Negociado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Procedimiento
    cups_procedure = models.ForeignKey(CUPSProcedure, on_delete=models.CASCADE, related_name='tariffs')

    # Tipo de tarifa y aseguradora
    tariff_type = models.CharField(max_length=30, choices=TARIFF_TYPE_CHOICES, default='iss_2001')
    eps = models.ForeignKey('patients.EPS', on_delete=models.PROTECT,
                           null=True, blank=True, related_name='procedure_tariffs')
    contract_number = models.CharField(max_length=100, blank=True)

    # Valores
    base_value = models.DecimalField(max_digits=12, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    percentage_adjustment = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'),
                                               help_text="Porcentaje sobre valor base (100% = sin ajuste)")
    final_value = models.DecimalField(max_digits=12, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])

    # Vigencia
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='proc_tariffs_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogs_procedure_tariffs'
        verbose_name = 'Tarifa de Procedimiento'
        verbose_name_plural = 'Tarifas de Procedimientos'
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['cups_procedure', 'eps']),
            models.Index(fields=['effective_date']),
        ]

    def __str__(self):
        eps_name = self.eps.name if self.eps else "General"
        return f"{self.cups_procedure.cups_code} - {eps_name}: ${self.final_value}"

    def save(self, *args, **kwargs):
        # Calcular valor final automáticamente
        self.final_value = self.base_value * (self.percentage_adjustment / Decimal('100.00'))
        super().save(*args, **kwargs)


class MedicationPrice(models.Model):
    """
    Precios de medicamentos CUMS
    """
    PRICE_TYPE_CHOICES = [
        ('pos', 'POS'),
        ('no_pos', 'No POS'),
        ('particular', 'Particular'),
        ('negotiated', 'Negociado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    # Medicamento
    cums_medication = models.ForeignKey(CUMSMedication, on_delete=models.CASCADE, related_name='prices')

    # Tipo de precio
    price_type = models.CharField(max_length=30, choices=PRICE_TYPE_CHOICES, default='pos')
    eps = models.ForeignKey('patients.EPS', on_delete=models.PROTECT,
                           null=True, blank=True, related_name='medication_prices')

    # Precios
    unit_price = models.DecimalField(max_digits=12, decimal_places=2,
                                    validators=[MinValueValidator(Decimal('0.00'))],
                                    help_text="Precio por unidad (tableta, ampolla, etc.)")
    presentation_price = models.DecimalField(max_digits=12, decimal_places=2,
                                            validators=[MinValueValidator(Decimal('0.00'))],
                                            help_text="Precio por presentación comercial")

    # Precio regulado
    maximum_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                       help_text="Precio máximo regulado (si aplica)")

    # Vigencia
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='med_prices_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogs_medication_prices'
        verbose_name = 'Precio de Medicamento'
        verbose_name_plural = 'Precios de Medicamentos'
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['cums_medication', 'eps']),
            models.Index(fields=['effective_date']),
        ]

    def __str__(self):
        eps_name = self.eps.name if self.eps else "General"
        return f"{self.cums_medication.generic_name} - {eps_name}: ${self.unit_price}"


class CatalogImportLog(models.Model):
    """
    Registro de importaciones de catálogos CUPS/CUMS
    """
    IMPORT_TYPE_CHOICES = [
        ('cups', 'CUPS'),
        ('cums', 'CUMS'),
        ('tariffs', 'Tarifas'),
        ('prices', 'Precios'),
    ]

    STATUS_CHOICES = [
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('partial', 'Parcial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    import_type = models.CharField(max_length=30, choices=IMPORT_TYPE_CHOICES)
    import_date = models.DateTimeField(auto_now_add=True)

    # Archivo importado
    source_file = models.FileField(upload_to='catalog_imports/%Y/%m/', null=True, blank=True)
    file_name = models.CharField(max_length=300)

    # Resultados
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    total_records = models.IntegerField(default=0)
    imported_records = models.IntegerField(default=0)
    updated_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)

    # Auditoría
    imported_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='catalog_imports')

    class Meta:
        db_table = 'catalogs_import_logs'
        verbose_name = 'Registro de Importación'
        verbose_name_plural = 'Registros de Importaciones'
        ordering = ['-import_date']

    def __str__(self):
        return f"{self.get_import_type_display()} - {self.import_date.strftime('%Y-%m-%d %H:%M')}"


class FavoriteCatalogItem(models.Model):
    """
    Items favoritos del catálogo por usuario/especialidad
    """
    ITEM_TYPE_CHOICES = [
        ('cups', 'Procedimiento CUPS'),
        ('cums', 'Medicamento CUMS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='favorite_catalog_items')

    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    cups_procedure = models.ForeignKey(CUPSProcedure, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='favorited_by')
    cums_medication = models.ForeignKey(CUMSMedication, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='favorited_by')

    # Agrupación por especialidad
    specialty = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)

    # Orden de favoritos
    sort_order = models.IntegerField(default=0)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalogs_favorites'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ['user', 'item_type', 'cups_procedure', 'cums_medication']
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        if self.item_type == 'cups' and self.cups_procedure:
            return f"{self.user.username} - {self.cups_procedure.cups_code}"
        elif self.item_type == 'cums' and self.cums_medication:
            return f"{self.user.username} - {self.cums_medication.cums_code}"
        return f"{self.user.username} - {self.item_type}"
