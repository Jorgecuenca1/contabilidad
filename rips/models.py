"""
Modelos para el módulo RIPS
Sistema completo de generación de RIPS según normativa colombiana
Resolución 3374/2000, Resolución 256/2016, Resolución 247/2014
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import uuid
import json

from core.models import Company, User


class AttentionEpisode(models.Model):
    """
    Episodio de Atención - Agrupa todos los servicios prestados al paciente
    desde su admisión hasta su egreso/cierre del episodio
    """
    STATUS_CHOICES = [
        ('active', 'Activo - En Atención'),
        ('closed', 'Cerrado - Listo para Facturar'),
        ('billed', 'Facturado'),
        ('cancelled', 'Cancelado'),
    ]

    EPISODE_TYPE_CHOICES = [
        ('ambulatory', 'Ambulatorio/Consulta Externa'),
        ('emergency', 'Urgencias'),
        ('hospitalization', 'Hospitalización'),
        ('home_care', 'Atención Domiciliaria'),
        ('surgery', 'Cirugía Programada'),
        ('telemedicine', 'Telemedicina'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='attention_episodes')

    # Identificación
    episode_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Episodio'
    )
    episode_type = models.CharField(
        max_length=20,
        choices=EPISODE_TYPE_CHOICES,
        verbose_name='Tipo de Episodio'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Estado'
    )

    # Paciente
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='attention_episodes',
        verbose_name='Paciente'
    )

    # EPS/Pagador
    payer = models.ForeignKey(
        'third_parties.ThirdParty',
        on_delete=models.PROTECT,
        related_name='attention_episodes_as_payer',
        verbose_name='Pagador (EPS)',
        help_text='Entidad responsable del pago'
    )

    # Fechas del episodio
    admission_date = models.DateTimeField(
        verbose_name='Fecha/Hora de Admisión',
        help_text='Inicio del episodio de atención'
    )
    discharge_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha/Hora de Egreso',
        help_text='Cierre del episodio de atención'
    )

    # Diagnósticos del episodio
    admission_diagnosis = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico de Ingreso (CIE-10)'
    )
    discharge_diagnosis = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico de Egreso (CIE-10)'
    )

    # Autorización
    authorization_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Autorización EPS'
    )

    # Vinculación con hospitalización si aplica
    admission = models.OneToOneField(
        'hospitalization.Admission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episode',
        verbose_name='Admisión Hospitalaria Relacionada'
    )

    # Costos totales
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Costo Total del Episodio'
    )

    # Facturación
    invoice = models.OneToOneField(
        'billing_health.HealthInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episode',
        verbose_name='Factura Generada'
    )
    is_billed = models.BooleanField(default=False, verbose_name='Facturado')
    billing_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Facturación')

    # Observaciones
    notes = models.TextField(blank=True, verbose_name='Observaciones')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='episodes_created'
    )
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episodes_closed'
    )

    class Meta:
        verbose_name = 'Episodio de Atención'
        verbose_name_plural = 'Episodios de Atención'
        ordering = ['-admission_date']
        indexes = [
            models.Index(fields=['episode_number']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.episode_number} - {self.patient}"

    def close_episode(self, user):
        """Cerrar episodio de atención"""
        if self.status == 'active':
            self.status = 'closed'
            self.discharge_date = timezone.now()
            self.closed_by = user
            self.calculate_total_cost()
            self.save()

    def calculate_total_cost(self):
        """Calcular costo total del episodio sumando todos los servicios"""
        total = Decimal('0.00')

        # Sumar servicios vinculados
        for service in self.services.all():
            total += service.get_service_cost()

        self.total_cost = total
        self.save(update_fields=['total_cost'])
        return total

    def generate_invoice(self, user):
        """Generar factura automáticamente desde el episodio"""
        from billing_health.models import HealthInvoice, HealthInvoiceItem

        if self.is_billed:
            raise ValueError("Este episodio ya ha sido facturado")

        if self.status not in ['closed']:
            raise ValueError("Solo se pueden facturar episodios cerrados")

        # Crear factura
        from datetime import date
        invoice_date = date.today()

        # Generar número de factura
        last_invoice = HealthInvoice.objects.filter(
            company=self.company
        ).order_by('-consecutive_number').first()

        consecutive = (last_invoice.consecutive_number + 1) if last_invoice else 1
        invoice_number = f"FAC-{consecutive:08d}"

        invoice = HealthInvoice.objects.create(
            company=self.company,
            invoice_number=invoice_number,
            consecutive_number=consecutive,
            invoice_date=invoice_date,
            service_date_from=self.admission_date.date(),
            service_date_to=self.discharge_date.date() if self.discharge_date else invoice_date,
            invoice_type=self.episode_type,
            payer=self.payer,
            patient=self.patient.third_party,
            status='draft',
            created_by=user
        )

        # Crear items desde los servicios del episodio
        for service in self.services.all():
            service.create_invoice_item(invoice)

        # Calcular totales
        invoice.calculate_totals()

        # Vincular factura al episodio
        self.invoice = invoice
        self.is_billed = True
        self.billing_date = timezone.now()
        self.status = 'billed'
        self.save()

        return invoice


class EpisodeService(models.Model):
    """
    Servicio vinculado a un episodio de atención
    Usa GenericForeignKey para referenciar cualquier tipo de servicio
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
    episode = models.ForeignKey(
        AttentionEpisode,
        on_delete=models.CASCADE,
        related_name='services'
    )

    # Tipo de servicio
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name='Tipo de Servicio'
    )

    # GenericForeignKey para referenciar el servicio original
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    service_object = GenericForeignKey('content_type', 'object_id')

    # Costo del servicio
    service_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Costo del Servicio'
    )

    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='episode_services_added'
    )

    class Meta:
        verbose_name = 'Servicio del Episodio'
        verbose_name_plural = 'Servicios del Episodio'
        ordering = ['added_at']
        indexes = [
            models.Index(fields=['episode', 'service_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.episode.episode_number}"

    def get_service_cost(self):
        """Obtener costo del servicio desde el objeto original"""
        if self.service_cost > 0:
            return self.service_cost

        # Intentar obtener costo del servicio original
        service = self.service_object
        if service:
            if hasattr(service, 'total_amount'):
                return service.total_amount
            elif hasattr(service, 'total_cost'):
                return service.total_cost
            elif hasattr(service, 'total_stay_cost'):
                return service.total_stay_cost

        return Decimal('0.00')

    def create_invoice_item(self, invoice):
        """Crear item de factura desde este servicio"""
        from billing_health.models import HealthInvoiceItem

        service = self.service_object
        if not service:
            return None

        # Datos base del item
        item_data = {
            'invoice': invoice,
            'service_type': self.service_type,
            'quantity': 1,
            'unit_price': self.get_service_cost(),
        }

        # Extraer datos específicos según el tipo de servicio
        if self.service_type == 'medication':
            # Dispensing (pharmacy)
            item_data['service_code'] = getattr(service, 'prescription_number', '')
            item_data['service_name'] = 'Medicamentos dispensados'
            item_data['service_date'] = service.dispensing_date
            item_data['diagnosis_code'] = getattr(service, 'diagnosis', '')
            item_data['authorization_number'] = getattr(service, 'authorization_number', '')

        elif self.service_type == 'imaging':
            # ImagingOrder
            item_data['service_code'] = getattr(service, 'procedure_code', '')
            item_data['service_name'] = service.procedure_description
            item_data['service_date'] = service.scheduled_date or service.created_at.date()
            item_data['authorization_number'] = ''

        elif self.service_type == 'hospitalization':
            # Admission
            item_data['service_code'] = 'HOSP001'
            item_data['service_name'] = f"Hospitalización - {service.get_admission_type_display()}"
            item_data['service_date'] = service.admission_date.date()
            item_data['diagnosis_code'] = service.admission_diagnosis
            item_data['authorization_number'] = ''

        else:
            # Servicio genérico
            item_data['service_code'] = 'SERV001'
            item_data['service_name'] = f"{self.get_service_type_display()}"
            item_data['service_date'] = self.added_at.date()

        # Crear el item
        return HealthInvoiceItem.objects.create(**item_data)


class RIPSFile(models.Model):
    """
    Archivo RIPS generado
    Contiene una o más facturas y genera archivos en formato JSON/TXT
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('generated', 'Generado'),
        ('sent', 'Enviado a EPS'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('glosa', 'Con Glosa'),
    ]

    FORMAT_CHOICES = [
        ('json', 'JSON (Moderno)'),
        ('txt', 'TXT (Pipe-delimited)'),
        ('xml', 'XML'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='rips_files')

    # Identificación
    file_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Archivo RIPS'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado'
    )

    # Periodo de facturación
    period_start = models.DateField(verbose_name='Inicio del Periodo')
    period_end = models.DateField(verbose_name='Fin del Periodo')

    # Prestador (IPS)
    provider_nit = models.CharField(
        max_length=20,
        verbose_name='NIT del Prestador',
        help_text='NIT de la IPS que presta los servicios'
    )
    provider_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Código de Habilitación',
        help_text='Código de habilitación de la IPS'
    )

    # Formato del archivo
    file_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='json',
        verbose_name='Formato del Archivo'
    )

    # Archivos generados
    json_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ruta Archivo JSON'
    )
    txt_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ruta Archivo TXT'
    )
    xml_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ruta Archivo XML'
    )

    # Estadísticas
    total_invoices = models.IntegerField(default=0, verbose_name='Total Facturas')
    total_patients = models.IntegerField(default=0, verbose_name='Total Pacientes')
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    # Control de envío
    sent_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Envío')
    sent_to = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Enviado a',
        help_text='EPS/Entidad destinataria'
    )
    response_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Respuesta')
    response_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Archivo de Respuesta'
    )

    # Observaciones
    notes = models.TextField(blank=True, verbose_name='Observaciones')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rips_files_created'
    )
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Generación')
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rips_files_generated'
    )

    class Meta:
        verbose_name = 'Archivo RIPS'
        verbose_name_plural = 'Archivos RIPS'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file_number']),
            models.Index(fields=['status']),
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"RIPS {self.file_number} - {self.period_start} a {self.period_end}"


class RIPSTransaction(models.Model):
    """
    Transacción RIPS - Corresponde a una factura individual dentro del archivo RIPS
    """
    NOTE_TYPE_CHOICES = [
        (None, 'N/A - Factura Normal'),
        ('debit', 'Nota Débito'),
        ('credit', 'Nota Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rips_file = models.ForeignKey(
        RIPSFile,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # Factura relacionada
    invoice = models.ForeignKey(
        'billing_health.HealthInvoice',
        on_delete=models.PROTECT,
        related_name='rips_transactions'
    )

    # Tipo de nota
    note_type = models.CharField(
        max_length=10,
        choices=NOTE_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name='Tipo de Nota'
    )
    note_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Nota'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transacción RIPS'
        verbose_name_plural = 'Transacciones RIPS'
        ordering = ['created_at']

    def __str__(self):
        return f"RIPS {self.invoice.invoice_number}"


# Modelos para los registros RIPS individuales

class RIPSConsulta(models.Model):
    """
    Registro AC - Consultas
    Resolución 3374/2000
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        RIPSTransaction,
        on_delete=models.CASCADE,
        related_name='consultas'
    )

    # Prestador
    cod_prestador = models.CharField(max_length=20, verbose_name='Código Prestador')

    # Fecha y hora de atención
    fecha_inicio_atencion = models.DateTimeField(verbose_name='Fecha/Hora Inicio Atención')

    # Autorización
    num_autorizacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Autorización'
    )

    # Código de consulta (CUPS)
    cod_consulta = models.CharField(max_length=20, verbose_name='Código Consulta (CUPS)')

    # Modalidad y grupo de servicios
    modalidad_grupo_servicio_tec_sal = models.CharField(
        max_length=2,
        verbose_name='Modalidad Grupo Servicio',
        help_text='01=Intramural, 02=Extramural'
    )
    grupo_servicios = models.CharField(
        max_length=2,
        verbose_name='Grupo de Servicios',
        help_text='01=Consulta Externa, 02=Apoyo Diagnóstico, etc.'
    )
    cod_servicio = models.IntegerField(verbose_name='Código del Servicio')

    # Finalidad y causa
    finalidad_tecnologia_salud = models.CharField(
        max_length=2,
        verbose_name='Finalidad Tecnología Salud',
        help_text='01=Diagnóstico, 02=Tratamiento, etc.'
    )
    causa_motivo_atencion = models.CharField(
        max_length=2,
        verbose_name='Causa Externa',
        help_text='01=Accidente de trabajo, 02=Accidente tránsito, etc.'
    )

    # Diagnósticos (CIE-10)
    cod_diagnostico_principal = models.CharField(max_length=10, verbose_name='Diagnóstico Principal')
    cod_diagnostico_relacionado1 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico Relacionado 1'
    )
    cod_diagnostico_relacionado2 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico Relacionado 2'
    )
    cod_diagnostico_relacionado3 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico Relacionado 3'
    )
    tipo_diagnostico_principal = models.CharField(
        max_length=2,
        verbose_name='Tipo Diagnóstico',
        help_text='01=Impresión Diagnóstica, 02=Confirmado Nuevo, 03=Confirmado Repetido'
    )

    # Profesional que atiende
    tipo_documento_identificacion = models.CharField(
        max_length=2,
        verbose_name='Tipo Documento Profesional'
    )
    num_documento_identificacion = models.CharField(
        max_length=20,
        verbose_name='Número Documento Profesional'
    )

    # Valores
    vr_servicio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Valor del Servicio'
    )
    concepto_recaudo = models.CharField(
        max_length=2,
        verbose_name='Concepto de Recaudo',
        help_text='01=Copago, 02=Cuota moderadora, etc.'
    )
    valor_pago_moderador = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Pago Moderador'
    )
    num_fev_pago_moderador = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número FEV Pago Moderador'
    )

    # Consecutivo
    consecutivo = models.IntegerField(verbose_name='Consecutivo')

    class Meta:
        verbose_name = 'RIPS Consulta'
        verbose_name_plural = 'RIPS Consultas'
        ordering = ['consecutivo']

    def __str__(self):
        return f"Consulta {self.cod_consulta} - {self.fecha_inicio_atencion}"


class RIPSProcedimiento(models.Model):
    """
    Registro AP - Procedimientos
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        RIPSTransaction,
        on_delete=models.CASCADE,
        related_name='procedimientos'
    )

    # Prestador
    cod_prestador = models.CharField(max_length=20, verbose_name='Código Prestador')

    # Fecha de atención
    fecha_inicio_atencion = models.DateTimeField(verbose_name='Fecha/Hora Inicio Atención')

    # MIPRES
    id_mipres = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='ID MIPRES',
        help_text='Para medicamentos de alto costo'
    )
    num_autorizacion = models.CharField(max_length=50, blank=True, verbose_name='Número de Autorización')

    # Código del procedimiento (CUPS)
    cod_procedimiento = models.CharField(max_length=20, verbose_name='Código Procedimiento (CUPS)')

    # Vía de ingreso
    via_ingreso_servicio_salud = models.CharField(
        max_length=2,
        verbose_name='Vía de Ingreso',
        help_text='01=Consulta Externa, 02=Urgencias, 03=Hospitalización, 04=Nacido en Institución'
    )

    # Modalidad y grupo
    modalidad_grupo_servicio_tec_sal = models.CharField(max_length=2, verbose_name='Modalidad Grupo Servicio')
    grupo_servicios = models.CharField(max_length=2, verbose_name='Grupo de Servicios')
    cod_servicio = models.IntegerField(verbose_name='Código del Servicio')

    # Finalidad
    finalidad_tecnologia_salud = models.CharField(max_length=2, verbose_name='Finalidad Tecnología Salud')

    # Profesional
    tipo_documento_identificacion = models.CharField(max_length=2, verbose_name='Tipo Documento Profesional')
    num_documento_identificacion = models.CharField(max_length=20, verbose_name='Número Documento Profesional')

    # Diagnósticos
    cod_diagnostico_principal = models.CharField(max_length=10, verbose_name='Diagnóstico Principal')
    cod_diagnostico_relacionado = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico Relacionado'
    )
    cod_complicacion = models.CharField(max_length=10, blank=True, verbose_name='Complicación')

    # Valores
    vr_servicio = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor del Servicio')
    concepto_recaudo = models.CharField(max_length=2, verbose_name='Concepto de Recaudo')
    valor_pago_moderador = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Pago Moderador'
    )
    num_fev_pago_moderador = models.CharField(max_length=50, blank=True, verbose_name='Número FEV Pago Moderador')

    # Consecutivo
    consecutivo = models.IntegerField(verbose_name='Consecutivo')

    class Meta:
        verbose_name = 'RIPS Procedimiento'
        verbose_name_plural = 'RIPS Procedimientos'
        ordering = ['consecutivo']

    def __str__(self):
        return f"Procedimiento {self.cod_procedimiento} - {self.fecha_inicio_atencion}"


class RIPSMedicamento(models.Model):
    """
    Registro AM - Medicamentos
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        RIPSTransaction,
        on_delete=models.CASCADE,
        related_name='medicamentos'
    )

    # Prestador
    cod_prestador = models.CharField(max_length=20, verbose_name='Código Prestador')

    # Autorización y MIPRES
    num_autorizacion = models.CharField(max_length=50, blank=True, verbose_name='Número de Autorización')
    id_mipres = models.CharField(max_length=50, blank=True, verbose_name='ID MIPRES')

    # Fecha de dispensación/administración
    fecha_dispens_admon = models.DateTimeField(verbose_name='Fecha Dispensación/Administración')

    # Diagnóstico
    cod_diagnostico_principal = models.CharField(max_length=10, verbose_name='Diagnóstico Principal')
    cod_diagnostico_relacionado = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Diagnóstico Relacionado'
    )

    # Tipo de medicamento
    tipo_medicamento = models.CharField(
        max_length=2,
        verbose_name='Tipo Medicamento',
        help_text='01=POS, 02=No POS'
    )

    # Código y nombre del medicamento
    cod_tecnologia_salud = models.CharField(
        max_length=50,
        verbose_name='Código Tecnología Salud',
        help_text='Código CUM o ATC'
    )
    nom_tecnologia_salud = models.CharField(max_length=500, verbose_name='Nombre Medicamento')

    # Concentración y forma farmacéutica
    concentracion_medicamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Concentración'
    )
    unidad_medida = models.IntegerField(verbose_name='Unidad de Medida')
    forma_farmaceutica = models.CharField(max_length=20, verbose_name='Forma Farmacéutica')
    unidad_min_dispensa = models.IntegerField(verbose_name='Unidad Mínima Dispensación')

    # Cantidad y días de tratamiento
    cantidad_medicamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Cantidad Medicamento'
    )
    dias_tratamiento = models.IntegerField(verbose_name='Días de Tratamiento')

    # Paciente
    tipo_documento_identificacion = models.CharField(max_length=2, verbose_name='Tipo Documento Paciente')
    num_documento_identificacion = models.CharField(max_length=20, verbose_name='Número Documento Paciente')

    # Valores
    vr_unit_medicamento = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor Unitario')
    vr_servicio = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor Total')
    concepto_recaudo = models.CharField(max_length=2, verbose_name='Concepto de Recaudo')
    valor_pago_moderador = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Pago Moderador'
    )
    num_fev_pago_moderador = models.CharField(max_length=50, blank=True, verbose_name='Número FEV Pago Moderador')

    # Consecutivo
    consecutivo = models.IntegerField(verbose_name='Consecutivo')

    class Meta:
        verbose_name = 'RIPS Medicamento'
        verbose_name_plural = 'RIPS Medicamentos'
        ordering = ['consecutivo']

    def __str__(self):
        return f"Medicamento {self.nom_tecnologia_salud}"


class RIPSOtrosServicios(models.Model):
    """
    Registro AT - Otros Servicios (Insumos, Dispositivos)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        RIPSTransaction,
        on_delete=models.CASCADE,
        related_name='otros_servicios'
    )

    # Prestador
    cod_prestador = models.CharField(max_length=20, verbose_name='Código Prestador')

    # Autorización y MIPRES
    num_autorizacion = models.CharField(max_length=50, blank=True, verbose_name='Número de Autorización')
    id_mipres = models.CharField(max_length=50, blank=True, verbose_name='ID MIPRES')

    # Fecha
    fecha_suministro_tecnologia = models.DateTimeField(verbose_name='Fecha Suministro')

    # Tipo de servicio
    tipo_os = models.CharField(
        max_length=2,
        verbose_name='Tipo Otro Servicio',
        help_text='01=Insumo, 02=Dispositivo, 03=Prótesis, 04=Órtesis'
    )

    # Código y nombre
    cod_tecnologia_salud = models.CharField(max_length=50, verbose_name='Código Tecnología Salud')
    nom_tecnologia_salud = models.CharField(max_length=500, verbose_name='Nombre Tecnología')

    # Cantidad
    cantidad_os = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Cantidad')

    # Paciente
    tipo_documento_identificacion = models.CharField(max_length=2, verbose_name='Tipo Documento Paciente')
    num_documento_identificacion = models.CharField(max_length=20, verbose_name='Número Documento Paciente')

    # Valores
    vr_unit_os = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor Unitario')
    vr_servicio = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor Total')
    concepto_recaudo = models.CharField(max_length=2, verbose_name='Concepto de Recaudo')
    valor_pago_moderador = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Valor Pago Moderador'
    )
    num_fev_pago_moderador = models.CharField(max_length=50, blank=True, verbose_name='Número FEV Pago Moderador')

    # Consecutivo
    consecutivo = models.IntegerField(verbose_name='Consecutivo')

    class Meta:
        verbose_name = 'RIPS Otro Servicio'
        verbose_name_plural = 'RIPS Otros Servicios'
        ordering = ['consecutivo']

    def __str__(self):
        return f"Otro Servicio {self.nom_tecnologia_salud}"


class RIPSUsuario(models.Model):
    """
    Registro de Usuario/Paciente en RIPS
    Datos demográficos del paciente
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        RIPSTransaction,
        on_delete=models.CASCADE,
        related_name='usuarios'
    )

    # Identificación
    tipo_documento_identificacion = models.CharField(
        max_length=2,
        verbose_name='Tipo Documento',
        help_text='CC, TI, CE, PA, RC, MS, AS, CD, etc.'
    )
    num_documento_identificacion = models.CharField(max_length=20, verbose_name='Número Documento')

    # Tipo de usuario
    tipo_usuario = models.CharField(
        max_length=2,
        verbose_name='Tipo de Usuario',
        help_text='01=Contributivo, 02=Subsidiado, 03=Vinculado, 04=Particular, etc.'
    )

    # Datos demográficos
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento')
    cod_sexo = models.CharField(max_length=1, verbose_name='Sexo', help_text='M o F')

    # Residencia
    cod_pais_residencia = models.CharField(max_length=3, verbose_name='Código País Residencia')
    cod_municipio_residencia = models.CharField(max_length=5, verbose_name='Código Municipio Residencia')
    cod_zona_territorial_residencia = models.CharField(
        max_length=2,
        verbose_name='Zona Territorial',
        help_text='01=Urbana, 02=Rural'
    )

    # Incapacidad
    incapacidad = models.CharField(
        max_length=2,
        verbose_name='Incapacidad',
        help_text='SI o NO'
    )

    # Consecutivo
    consecutivo = models.IntegerField(verbose_name='Consecutivo')

    # País de origen
    cod_pais_origen = models.CharField(max_length=3, verbose_name='Código País Origen')

    class Meta:
        verbose_name = 'RIPS Usuario'
        verbose_name_plural = 'RIPS Usuarios'
        ordering = ['consecutivo']

    def __str__(self):
        return f"Usuario {self.num_documento_identificacion}"
