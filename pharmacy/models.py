"""
Modelos del módulo Farmacia
Sistema completo de inventario, lotes, vencimientos y dispensación
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta

from core.models import Company, User


class MedicineCategory(models.Model):
    """Categorías de medicamentos según clasificación farmacéutica"""

    CATEGORY_TYPE_CHOICES = [
        ('therapeutic', 'Terapéutica'),
        ('anatomical', 'Anatómica'),
        ('chemical', 'Química'),
        ('pharmacological', 'Farmacológica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    code = models.CharField(max_length=20, help_text="Código ATC o interno")
    name = models.CharField(max_length=200)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='therapeutic')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='pharmacy_categories_created')

    class Meta:
        db_table = 'pharmacy_medicine_categories'
        verbose_name = 'Categoría de Medicamento'
        verbose_name_plural = 'Categorías de Medicamentos'
        unique_together = [['company', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Medicine(models.Model):
    """
    Medicamento del formulario farmacéutico
    Incluye información completa según normativa INVIMA
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
        ('spray', 'Spray'),
        ('inhaler', 'Inhalador'),
        ('suppository', 'Supositorio'),
        ('patch', 'Parche'),
        ('powder', 'Polvo'),
        ('gel', 'Gel'),
        ('lotion', 'Loción'),
        ('other', 'Otro'),
    ]

    ADMINISTRATION_ROUTE_CHOICES = [
        ('oral', 'Oral'),
        ('sublingual', 'Sublingual'),
        ('intravenous', 'Intravenosa'),
        ('intramuscular', 'Intramuscular'),
        ('subcutaneous', 'Subcutánea'),
        ('topical', 'Tópica'),
        ('transdermal', 'Transdérmica'),
        ('ophthalmic', 'Oftálmica'),
        ('otic', 'Ótica'),
        ('nasal', 'Nasal'),
        ('rectal', 'Rectal'),
        ('vaginal', 'Vaginal'),
        ('inhalation', 'Inhalatoria'),
        ('other', 'Otra'),
    ]

    CONTROL_TYPE_CHOICES = [
        ('otc', 'Venta Libre'),
        ('prescription', 'Fórmula Médica'),
        ('controlled', 'Medicamento Controlado'),
        ('high_surveillance', 'Alta Vigilancia'),
        ('pos', 'POS'),
        ('no_pos', 'No POS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='medicines')

    # Identificación
    code = models.CharField(max_length=50, help_text="Código interno")
    cum_code = models.CharField(max_length=20, blank=True, help_text="Código Único de Medicamento - INVIMA")
    atc_code = models.CharField(max_length=20, blank=True, help_text="Código ATC")
    barcode = models.CharField(max_length=50, blank=True, help_text="Código de barras")

    # Información básica
    generic_name = models.CharField(max_length=300, help_text="Nombre genérico (DCI)")
    commercial_name = models.CharField(max_length=300, blank=True, help_text="Nombre comercial")
    active_ingredient = models.TextField(help_text="Principio activo y concentración")

    # Clasificación
    category = models.ForeignKey(MedicineCategory, on_delete=models.PROTECT, related_name='medicines')
    pharmaceutical_form = models.CharField(max_length=20, choices=PHARMACEUTICAL_FORM_CHOICES)
    administration_route = models.CharField(max_length=20, choices=ADMINISTRATION_ROUTE_CHOICES)
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES, default='prescription')

    # Información farmacológica
    concentration = models.CharField(max_length=100, help_text="Ej: 500mg, 10mg/ml")
    presentation = models.CharField(max_length=200, help_text="Ej: Caja x 30 tabletas")
    manufacturer = models.CharField(max_length=200, blank=True)
    sanitary_registration = models.CharField(max_length=100, blank=True, help_text="Registro Sanitario INVIMA")

    # Indicaciones
    therapeutic_indications = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    adverse_effects = models.TextField(blank=True)
    dosage_instructions = models.TextField(blank=True, help_text="Instrucciones de dosificación")

    # Control de inventario
    requires_refrigeration = models.BooleanField(default=False)
    requires_special_storage = models.BooleanField(default=False)
    storage_conditions = models.TextField(blank=True)

    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    # Precios
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Costo unitario")
    sale_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Precio de venta")
    pos_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True, help_text="Precio POS")

    # Estado
    is_active = models.BooleanField(default=True)
    is_generic = models.BooleanField(default=False)
    is_essential = models.BooleanField(default=False, help_text="Medicamento esencial")
    is_high_risk = models.BooleanField(default=False, help_text="Medicamento de alto riesgo")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='medicines_created')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='medicines_updated')

    class Meta:
        db_table = 'pharmacy_medicines'
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        unique_together = [['company', 'code']]
        ordering = ['generic_name']
        indexes = [
            models.Index(fields=['company', 'code']),
            models.Index(fields=['company', 'generic_name']),
            models.Index(fields=['barcode']),
            models.Index(fields=['cum_code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.generic_name}"

    def get_current_stock(self):
        """Obtiene el stock actual sumando todos los lotes activos"""
        return self.batches.filter(
            is_active=True,
            expiry_date__gt=timezone.now().date()
        ).aggregate(
            total=models.Sum('current_quantity')
        )['total'] or Decimal('0')

    def get_expired_stock(self):
        """Obtiene la cantidad de medicamento vencido"""
        return self.batches.filter(
            is_active=True,
            expiry_date__lte=timezone.now().date()
        ).aggregate(
            total=models.Sum('current_quantity')
        )['total'] or Decimal('0')

    def get_near_expiry_stock(self, days=90):
        """Obtiene medicamentos próximos a vencer"""
        threshold_date = timezone.now().date() + timedelta(days=days)
        return self.batches.filter(
            is_active=True,
            expiry_date__lte=threshold_date,
            expiry_date__gt=timezone.now().date()
        ).aggregate(
            total=models.Sum('current_quantity')
        )['total'] or Decimal('0')

    def needs_reorder(self):
        """Verifica si el medicamento necesita reabastecimiento"""
        current_stock = self.get_current_stock()
        return current_stock <= self.reorder_point

    def is_below_minimum(self):
        """Verifica si está por debajo del stock mínimo"""
        current_stock = self.get_current_stock()
        return current_stock < self.minimum_stock

    def is_above_maximum(self):
        """Verifica si está por encima del stock máximo"""
        current_stock = self.get_current_stock()
        return current_stock > self.maximum_stock


class MedicineBatch(models.Model):
    """
    Lote de medicamento con control de vencimiento
    Sistema FEFO (First Expired, First Out)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')

    # Identificación del lote
    batch_number = models.CharField(max_length=100, help_text="Número de lote del fabricante")
    internal_code = models.CharField(max_length=50, blank=True, help_text="Código interno del lote")

    # Fechas
    manufacturing_date = models.DateField(help_text="Fecha de fabricación")
    expiry_date = models.DateField(help_text="Fecha de vencimiento")
    reception_date = models.DateField(default=timezone.now, help_text="Fecha de recepción")

    # Cantidades
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reserved_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    # Costos
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, help_text="Costo unitario del lote")
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, help_text="Costo total del lote")

    # Proveedor
    supplier = models.CharField(max_length=200, blank=True)
    purchase_order = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)

    # Ubicación
    storage_location = models.CharField(max_length=200, blank=True, help_text="Ubicación física en bodega")

    # Control de calidad
    quality_approved = models.BooleanField(default=True)
    quality_notes = models.TextField(blank=True)
    quality_approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='batches_approved')
    quality_approved_date = models.DateTimeField(null=True, blank=True)

    # Estado
    is_active = models.BooleanField(default=True)
    is_quarantine = models.BooleanField(default=False, help_text="En cuarentena")
    quarantine_reason = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='batches_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacy_medicine_batches'
        verbose_name = 'Lote de Medicamento'
        verbose_name_plural = 'Lotes de Medicamentos'
        unique_together = [['company', 'medicine', 'batch_number']]
        ordering = ['expiry_date', 'batch_number']
        indexes = [
            models.Index(fields=['company', 'medicine', 'expiry_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"Lote {self.batch_number} - {self.medicine.generic_name}"

    def get_available_quantity(self):
        """Cantidad disponible para dispensar"""
        return self.current_quantity - self.reserved_quantity

    def is_expired(self):
        """Verifica si el lote está vencido"""
        return self.expiry_date <= timezone.now().date()

    def is_near_expiry(self, days=90):
        """Verifica si el lote está próximo a vencer"""
        threshold_date = timezone.now().date() + timedelta(days=days)
        return timezone.now().date() < self.expiry_date <= threshold_date

    def days_to_expiry(self):
        """Días hasta el vencimiento"""
        delta = self.expiry_date - timezone.now().date()
        return delta.days


class Dispensing(models.Model):
    """
    Dispensación de medicamentos a pacientes
    Control completo de entrega con trazabilidad
    """

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('prepared', 'Preparada'),
        ('delivered', 'Entregada'),
        ('cancelled', 'Anulada'),
        ('returned', 'Devuelta'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # Identificación
    dispensing_number = models.CharField(max_length=100, unique=True)
    dispensing_date = models.DateTimeField(default=timezone.now)

    # Paciente (usar third_parties)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT, related_name='pharmacy_dispensings')

    # Prescripción médica
    prescription_required = models.BooleanField(default=True)
    prescription_number = models.CharField(max_length=100, blank=True)
    prescription_date = models.DateField(null=True, blank=True)
    prescribing_physician = models.CharField(max_length=200, blank=True)
    physician_license = models.CharField(max_length=100, blank=True)
    diagnosis = models.CharField(max_length=500, blank=True)

    # Información adicional
    service_type = models.CharField(max_length=50, blank=True, help_text="Ambulatorio, Hospitalización, Urgencias")
    authorization_number = models.CharField(max_length=100, blank=True, help_text="Número de autorización de la EPS")
    payer = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT, null=True, blank=True, related_name='pharmacy_payer_dispensings', help_text="EPS o pagador")

    # Totales
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    copayment = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Copago del paciente")
    moderator_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Cuota moderadora")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Estado y entrega
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateTimeField(null=True, blank=True)
    delivered_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='dispensings_delivered')
    received_by_name = models.CharField(max_length=200, blank=True, help_text="Nombre de quien recibe")
    received_by_id = models.CharField(max_length=50, blank=True, help_text="Identificación de quien recibe")

    # Observaciones
    notes = models.TextField(blank=True)
    pharmacist_notes = models.TextField(blank=True, help_text="Recomendaciones del farmacéutico")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dispensings_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacy_dispensings'
        verbose_name = 'Dispensación'
        verbose_name_plural = 'Dispensaciones'
        ordering = ['-dispensing_date']
        indexes = [
            models.Index(fields=['company', 'dispensing_date']),
            models.Index(fields=['dispensing_number']),
            models.Index(fields=['patient']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.dispensing_number} - {self.patient}"

    def calculate_totals(self):
        """Calcula los totales de la dispensación"""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        self.total_amount = self.subtotal - self.copayment - self.moderator_fee
        self.save()

    def can_be_edited(self):
        """Verifica si la dispensación puede ser editada"""
        return self.status in ['pending', 'prepared']

    def mark_as_delivered(self, user, received_by_name, received_by_id):
        """Marca la dispensación como entregada"""
        self.status = 'delivered'
        self.delivery_date = timezone.now()
        self.delivered_by = user
        self.received_by_name = received_by_name
        self.received_by_id = received_by_id
        self.save()


class DispensingItem(models.Model):
    """Detalle de medicamentos dispensados"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispensing = models.ForeignKey(Dispensing, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    batch = models.ForeignKey(MedicineBatch, on_delete=models.PROTECT, related_name='dispensing_items')

    # Cantidades
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])

    # Precios
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    # Instrucciones
    dosage_instructions = models.TextField(blank=True, help_text="Posología")
    administration_instructions = models.TextField(blank=True, help_text="Instrucciones de administración")
    duration_days = models.IntegerField(null=True, blank=True, help_text="Duración del tratamiento en días")

    # Sustitución
    is_substitution = models.BooleanField(default=False, help_text="Indica si es sustitución por genérico")
    substitution_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pharmacy_dispensing_items'
        verbose_name = 'Item de Dispensación'
        verbose_name_plural = 'Items de Dispensación'
        ordering = ['id']

    def __str__(self):
        return f"{self.medicine.generic_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calcular totales
        self.subtotal = self.quantity * self.unit_price
        self.total = self.subtotal - self.discount
        super().save(*args, **kwargs)


class InventoryMovement(models.Model):
    """
    Movimientos de inventario
    Trazabilidad completa de entradas y salidas
    """

    MOVEMENT_TYPE_CHOICES = [
        ('entry', 'Entrada'),
        ('exit', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Traslado'),
        ('return', 'Devolución'),
        ('expiry', 'Vencimiento'),
        ('damage', 'Daño/Avería'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    movement_number = models.CharField(max_length=100, unique=True)
    movement_date = models.DateTimeField(default=timezone.now)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)

    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='movements')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.PROTECT, related_name='movements')

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    previous_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cantidad antes del movimiento")
    new_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cantidad después del movimiento")

    # Referencia
    reference_document = models.CharField(max_length=200, blank=True, help_text="Factura, remisión, etc.")
    dispensing = models.ForeignKey(Dispensing, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_movements')

    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='inventory_movements_created')

    class Meta:
        db_table = 'pharmacy_inventory_movements'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['company', 'movement_date']),
            models.Index(fields=['medicine']),
            models.Index(fields=['batch']),
            models.Index(fields=['movement_type']),
        ]

    def __str__(self):
        return f"{self.movement_number} - {self.movement_type} - {self.medicine.generic_name}"


class StockAlert(models.Model):
    """Alertas de inventario para control proactivo"""

    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Stock Bajo'),
        ('out_of_stock', 'Sin Stock'),
        ('near_expiry', 'Próximo a Vencer'),
        ('expired', 'Vencido'),
        ('overstock', 'Sobre Stock'),
        ('batch_quarantine', 'Lote en Cuarentena'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='alerts')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')

    message = models.TextField()
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='alerts_resolved')
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pharmacy_stock_alerts'
        verbose_name = 'Alerta de Stock'
        verbose_name_plural = 'Alertas de Stock'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['company', 'is_resolved']),
            models.Index(fields=['alert_type', 'priority']),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.medicine.generic_name}"
