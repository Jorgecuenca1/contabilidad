"""
Módulo de Facturación de Salud
Sistema completo de facturación de servicios de salud vinculado con RIPS
Adaptado para normativa colombiana - Resolución 3374/2000 y actualizaciones
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import uuid

from core.models import Company, User


class HealthTariff(models.Model):
    """
    Tarifarios de salud (SOAT, ISS, Particular, etc.)
    """
    TARIFF_TYPE_CHOICES = [
        ('soat', 'SOAT'),
        ('iss_2001', 'ISS 2001'),
        ('iss_2004', 'ISS 2004'),
        ('particular', 'Particular'),
        ('capita', 'Capitado'),
        ('evento', 'Evento'),
        ('paquete', 'Paquete'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='health_tariffs')

    name = models.CharField(max_length=200, verbose_name='Nombre del Tarifario')
    tariff_type = models.CharField(
        max_length=20,
        choices=TARIFF_TYPE_CHOICES,
        verbose_name='Tipo de Tarifario'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')

    # Configuración
    base_year = models.IntegerField(
        default=2024,
        verbose_name='Año Base',
        help_text='Año base del tarifario'
    )
    uvr_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor UVR',
        help_text='Valor de la Unidad de Valor Relativo'
    )
    smmlv_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor SMMLV',
        help_text='Salario Mínimo Mensual Legal Vigente'
    )

    # Incrementos/Descuentos
    global_increment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='% Incremento Global',
        help_text='Porcentaje de incremento o descuento sobre el tarifario base'
    )

    # Vigencia
    valid_from = models.DateField(verbose_name='Válido Desde')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Válido Hasta')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tariffs_created'
    )

    class Meta:
        verbose_name = 'Tarifario de Salud'
        verbose_name_plural = 'Tarifarios de Salud'
        ordering = ['-created_at']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_tariff_type_display()})"


class HealthInvoice(models.Model):
    """
    Factura de servicios de salud
    Documento de cobro con vinculación a RIPS
    """
    INVOICE_TYPE_CHOICES = [
        ('ambulatory', 'Consulta Externa/Ambulatoria'),
        ('hospitalization', 'Hospitalización'),
        ('urgency', 'Urgencias'),
        ('medication', 'Medicamentos'),
        ('procedure', 'Procedimientos'),
        ('mixed', 'Mixta'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('issued', 'Emitida'),
        ('sent', 'Enviada a Pagador'),
        ('glosa', 'Glosada'),
        ('glosa_response', 'Respuesta a Glosa'),
        ('partial_payment', 'Pago Parcial'),
        ('paid', 'Pagada'),
        ('cancelled', 'Anulada'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='health_invoices')

    # Numeración
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Factura'
    )
    invoice_prefix = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Prefijo'
    )
    consecutive_number = models.IntegerField(verbose_name='Número Consecutivo')

    # Resolución DIAN
    dian_resolution = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Resolución DIAN'
    )
    dian_resolution_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Resolución DIAN'
    )
    authorized_range_from = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Rango Autorizado Desde'
    )
    authorized_range_to = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Rango Autorizado Hasta'
    )

    # Fechas
    invoice_date = models.DateField(verbose_name='Fecha de Factura')
    service_date_from = models.DateField(verbose_name='Fecha Inicio Servicios')
    service_date_to = models.DateField(verbose_name='Fecha Fin Servicios')
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento'
    )

    # Clasificación
    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPE_CHOICES,
        verbose_name='Tipo de Factura'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado'
    )

    # Partes involucradas
    payer = models.ForeignKey(
        'third_parties.ThirdParty',
        on_delete=models.PROTECT,
        related_name='health_invoices_as_payer',
        verbose_name='Pagador (EPS/Aseguradora)',
        help_text='Entidad responsable del pago'
    )
    patient = models.ForeignKey(
        'third_parties.ThirdParty',
        on_delete=models.PROTECT,
        related_name='health_invoices_as_patient',
        null=True,
        blank=True,
        verbose_name='Paciente'
    )

    # Contrato
    contract_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Contrato',
        help_text='Contrato con la EPS/Pagador'
    )
    tariff = models.ForeignKey(
        HealthTariff,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Tarifario Aplicado'
    )

    # Modalidad de pago
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='credito',
        verbose_name='Forma de Pago'
    )
    payment_terms_days = models.IntegerField(
        default=30,
        verbose_name='Plazo de Pago (días)'
    )

    # Valores monetarios
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Subtotal'
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento'
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='IVA'
    )
    copayment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Copago',
        help_text='Copago del paciente'
    )
    moderator_fee_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cuota Moderadora'
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Total'
    )

    # Control de pagos
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Monto Pagado'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Saldo Pendiente'
    )

    # Vinculación RIPS
    rips_generated = models.BooleanField(
        default=False,
        verbose_name='RIPS Generados'
    )
    rips_generation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Generación RIPS'
    )
    rips_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ruta Archivo RIPS'
    )

    # Glosas
    has_glosa = models.BooleanField(default=False, verbose_name='Tiene Glosa')
    glosa_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Monto Glosado'
    )
    glosa_notes = models.TextField(blank=True, verbose_name='Observaciones Glosa')

    # Observaciones
    notes = models.TextField(blank=True, verbose_name='Observaciones')
    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas Internas',
        help_text='Notas privadas no visibles en la factura'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='health_invoices_created'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='health_invoices_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Factura de Salud'
        verbose_name_plural = 'Facturas de Salud'
        ordering = ['-invoice_date', '-consecutive_number']
        unique_together = ['company', 'invoice_number']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['payer', 'status']),
        ]

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.payer.nombre if hasattr(self.payer, 'nombre') else 'N/A'}"

    def save(self, *args, **kwargs):
        # Generar número de factura si no existe
        if not self.invoice_number:
            self.invoice_number = f"{self.invoice_prefix}{self.consecutive_number:08d}"

        # Calcular balance
        self.balance = self.total - self.paid_amount

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcular totales de la factura desde los items"""
        items = self.items.all()

        self.subtotal = sum(item.total_amount for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        self.balance = self.total - self.paid_amount

        self.save(update_fields=['subtotal', 'tax_amount', 'total', 'balance'])

    def approve_invoice(self, user):
        """Aprobar y emitir factura"""
        if self.status == 'draft':
            self.status = 'issued'
            self.approved_by = user
            self.approved_at = timezone.now()
            self.save()

    def mark_as_paid(self, amount):
        """Registrar pago"""
        self.paid_amount += amount
        self.balance = self.total - self.paid_amount

        if self.balance <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial_payment'

        self.save()

    def generate_rips(self, format='json'):
        """
        Generar archivos RIPS desde la factura
        Formatos soportados: 'json', 'txt', 'both'
        """
        from rips.utils import generate_rips_json, generate_rips_txt, save_rips_files
        from rips.models import RIPSFile, RIPSTransaction

        if self.status not in ['issued', 'sent', 'paid']:
            raise ValueError("Solo se pueden generar RIPS de facturas emitidas, enviadas o pagadas")

        # Generar datos RIPS
        rips_json_data = generate_rips_json(self)

        # Guardar archivo JSON
        json_path = None
        txt_path = None

        if format in ['json', 'both']:
            json_path = save_rips_files(rips_json_data, self, format='json')

        if format in ['txt', 'both']:
            txt_data = generate_rips_txt(self)
            # txt_path = save_rips_files(txt_data, self, format='txt')

        # Marcar factura como generada
        self.rips_generated = True
        self.rips_generation_date = timezone.now()
        if json_path:
            self.rips_file_path = json_path
        self.save(update_fields=['rips_generated', 'rips_generation_date', 'rips_file_path'])

        return {
            'json_path': json_path,
            'txt_path': txt_path,
            'data': rips_json_data
        }


class HealthInvoiceItem(models.Model):
    """
    Items/Líneas de detalle de una factura de salud
    """
    SERVICE_TYPE_CHOICES = [
        ('consultation', 'Consulta'),
        ('procedure', 'Procedimiento'),
        ('medication', 'Medicamento'),
        ('laboratory', 'Laboratorio'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('hospitalization', 'Hospitalización'),
        ('surgery', 'Cirugía'),
        ('other', 'Otro Servicio'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        HealthInvoice,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Identificación del servicio
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name='Tipo de Servicio'
    )

    # GenericForeignKey para referenciar el servicio original
    # (Dispensing, ImagingOrder, Admission, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Servicio Original'
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='ID del Servicio Original'
    )
    service_object = GenericForeignKey('content_type', 'object_id')
    service_code = models.CharField(
        max_length=20,
        verbose_name='Código del Servicio',
        help_text='Código CUPS, ATC, etc.'
    )
    service_name = models.CharField(
        max_length=500,
        verbose_name='Descripción del Servicio'
    )

    # Fecha del servicio
    service_date = models.DateField(verbose_name='Fecha del Servicio')

    # Diagnóstico relacionado
    diagnosis_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Código Diagnóstico CIE-10'
    )

    # Cantidades y valores
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Cantidad'
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Valor Unitario'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    # Impuestos
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='% IVA'
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor IVA'
    )

    # Copagos y cuotas moderadoras
    copayment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Copago'
    )
    moderator_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Cuota Moderadora'
    )

    # Autorización
    authorization_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Autorización'
    )

    # Glosa
    is_glosa = models.BooleanField(default=False, verbose_name='Glosado')
    glosa_reason = models.TextField(blank=True, verbose_name='Motivo de Glosa')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item de Factura de Salud'
        verbose_name_plural = 'Items de Facturas de Salud'
        ordering = ['service_date', 'service_code']

    def __str__(self):
        return f"{self.service_code} - {self.service_name}"

    def save(self, *args, **kwargs):
        # Calcular total del item
        self.total_amount = self.quantity * self.unit_price
        self.tax_amount = self.total_amount * (self.tax_rate / 100)

        super().save(*args, **kwargs)

        # Actualizar totales de la factura
        if self.invoice_id:
            self.invoice.calculate_totals()


class HealthPayment(models.Model):
    """
    Pagos recibidos de facturas de salud
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta Débito'),
        ('compensation', 'Compensación'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='health_payments')

    # Relación con factura
    invoice = models.ForeignKey(
        HealthInvoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # Información del pago
    payment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Pago'
    )
    payment_date = models.DateField(verbose_name='Fecha de Pago')
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Método de Pago'
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto Pagado'
    )

    # Referencia del pago
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Número de Referencia',
        help_text='Número de cheque, transferencia, etc.'
    )

    # Descuentos aplicados en el pago
    discount_applied = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Descuento Aplicado'
    )

    # Observaciones
    notes = models.TextField(blank=True, verbose_name='Observaciones')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='health_payments_created'
    )

    class Meta:
        verbose_name = 'Pago de Factura de Salud'
        verbose_name_plural = 'Pagos de Facturas de Salud'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Pago {self.payment_number} - ${self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Actualizar el monto pagado en la factura
        if self.invoice_id:
            self.invoice.mark_as_paid(self.amount)


class InvoiceGlosa(models.Model):
    """
    Glosas aplicadas a facturas de salud
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_review', 'En Revisión'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('partially_accepted', 'Parcialmente Aceptada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoice_glosas')

    invoice = models.ForeignKey(
        HealthInvoice,
        on_delete=models.CASCADE,
        related_name='glosas'
    )

    # Información de la glosa
    glosa_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Glosa'
    )
    glosa_date = models.DateField(verbose_name='Fecha de Glosa')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )

    # Monto glosado
    glosa_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto Glosado'
    )
    accepted_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Monto Aceptado'
    )

    # Motivo de la glosa
    reason = models.TextField(verbose_name='Motivo de la Glosa')
    response = models.TextField(blank=True, verbose_name='Respuesta a la Glosa')

    # Fechas importantes
    response_deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Límite de Respuesta'
    )
    response_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Respuesta'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='glosas_created'
    )

    class Meta:
        verbose_name = 'Glosa de Factura'
        verbose_name_plural = 'Glosas de Facturas'
        ordering = ['-glosa_date']

    def __str__(self):
        return f"Glosa {self.glosa_number} - ${self.glosa_amount}"
