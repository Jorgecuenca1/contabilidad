"""
Modelos para el Sistema de Presupuesto Público Colombiano
Incluye CDP, RP, Obligaciones, PAC y gestión presupuestal completa
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import Company, User
from accounting.models import JournalEntry, ChartOfAccounts


class BudgetPeriod(models.Model):
    """Vigencia Presupuestal"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_periods')
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    name = models.CharField(max_length=100)
    initial_budget = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    current_budget = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Proyecto'),
        ('approved', 'Aprobado'),
        ('active', 'En Ejecución'),
        ('closed', 'Cerrado')
    ], default='draft')
    approval_date = models.DateField(null=True, blank=True)
    approval_document = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_budget_periods')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['company', 'year']]
        ordering = ['-year']
    
    def __str__(self):
        return f"Vigencia {self.year} - {self.company.name}"


class BudgetRubro(models.Model):
    """Rubro Presupuestal según clasificación del Ministerio de Hacienda"""
    RUBRO_TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
        ('investment', 'Inversión')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_rubros')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='rubros')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rubro_type = models.CharField(max_length=20, choices=RUBRO_TYPE_CHOICES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    
    # Presupuesto
    initial_appropriation = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Apropiación Inicial")
    additions = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Adiciones")
    reductions = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Reducciones")
    current_appropriation = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Apropiación Vigente")
    
    # Ejecución
    cdp_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="CDP Expedidos")
    rp_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="RP Expedidos")
    obligations = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Obligaciones")
    payments = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Pagos")
    
    # Cuentas contables asociadas
    income_account = models.ForeignKey(ChartOfAccounts, null=True, blank=True, on_delete=models.SET_NULL, related_name='budget_income_rubros')
    expense_account = models.ForeignKey(ChartOfAccounts, null=True, blank=True, on_delete=models.SET_NULL, related_name='budget_expense_rubros')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        unique_together = [['company', 'period', 'code']]
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def available_appropriation(self):
        """Apropiación Disponible"""
        return self.current_appropriation - self.cdp_amount
    
    @property
    def available_cdp(self):
        """Saldo CDP Disponible"""
        return self.cdp_amount - self.rp_amount
    
    @property
    def available_rp(self):
        """Saldo RP Disponible"""
        return self.rp_amount - self.obligations
    
    def update_current_appropriation(self):
        """Actualiza la apropiación vigente"""
        self.current_appropriation = self.initial_appropriation + self.additions - self.reductions
        self.save()
    
    def validate_colombian_compliance(self):
        """Valida cumplimiento normativo colombiano"""
        errors = []
        
        # Validar que no se excedan las apropiaciones
        if self.cdp_amount > self.current_appropriation:
            errors.append("Los CDP no pueden exceder la apropiación vigente")
        
        # Validar que los RP no excedan los CDP
        if self.rp_amount > self.cdp_amount:
            errors.append("Los RP no pueden exceder los CDP expedidos")
        
        # Validar que las obligaciones no excedan los RP
        if self.obligations > self.rp_amount:
            errors.append("Las obligaciones no pueden exceder los RP")
        
        # Validar que los pagos no excedan las obligaciones
        if self.payments > self.obligations:
            errors.append("Los pagos no pueden exceder las obligaciones")
        
        return errors
    
    @property
    def execution_percentage(self):
        """Porcentaje de ejecución presupuestal"""
        if self.current_appropriation > 0:
            return (self.obligations / self.current_appropriation) * 100
        return 0


class CDP(models.Model):
    """Certificado de Disponibilidad Presupuestal"""
    STATE_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('partial', 'Parcialmente Comprometido'),
        ('committed', 'Comprometido'),
        ('expired', 'Anulado/Vencido'),
        ('cancelled', 'Cancelado')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_cdps')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='cdps')
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    concept = models.TextField(verbose_name="Concepto/Objeto")
    request_area = models.CharField(max_length=100, verbose_name="Área Solicitante")
    request_person = models.CharField(max_length=100, verbose_name="Solicitante")
    
    # Información adicional
    project = models.CharField(max_length=200, blank=True, verbose_name="Proyecto")
    contract_modality = models.CharField(max_length=100, blank=True, verbose_name="Modalidad de Contratación")
    
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    committed_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    available_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='draft')
    expiry_date = models.DateField(null=True, blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cdps')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_cdps')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    observations = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-number']
        verbose_name = "CDP"
        verbose_name_plural = "CDPs"
    
    def __str__(self):
        return f"CDP {self.number} - {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        self.available_amount = self.total_amount - self.committed_amount
        super().save(*args, **kwargs)
    
    def generate_number(self):
        """Genera número consecutivo de CDP"""
        year = timezone.now().year
        last_cdp = CDP.objects.filter(
            company=self.company,
            date__year=year
        ).order_by('-number').first()
        
        if last_cdp and last_cdp.number:
            try:
                last_number = int(last_cdp.number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        
        return f"CDP-{year}-{str(new_number).zfill(5)}"
    
    def validate_cdp_requirements(self):
        """Valida requisitos de CDP según normativa colombiana"""
        errors = []
        
        # Validar que tenga concepto específico
        if not self.concept or len(self.concept.strip()) < 10:
            errors.append("El CDP debe tener un concepto específico mínimo de 10 caracteres")
        
        # Validar que tenga área y solicitante
        if not self.request_area or not self.request_person:
            errors.append("El CDP debe especificar área solicitante y responsable")
        
        # Validar que tenga valor positivo
        if self.total_amount <= 0:
            errors.append("El CDP debe tener un valor positivo")
        
        # Validar que no esté vencido
        if self.expiry_date and self.expiry_date < timezone.now().date():
            errors.append("El CDP está vencido y no puede ser utilizado")
        
        # Validar disponibilidad presupuestal
        total_required = 0
        for detail in self.details.all():
            if detail.amount > detail.rubro.available_appropriation:
                errors.append(f"Rubro {detail.rubro.code}: Insuficiente apropiación disponible")
            total_required += detail.amount
        
        if abs(total_required - self.total_amount) > 0.01:
            errors.append("El total del CDP no coincide con el detalle por rubros")
        
        return errors
    
    def can_be_committed(self, amount):
        """Verifica si el CDP puede comprometer un monto específico"""
        return self.state == 'approved' and self.available_amount >= amount
    
    @property
    def days_to_expire(self):
        """Días restantes hasta vencimiento"""
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days
        # Si no tiene fecha de vencimiento, usar fin de vigencia fiscal
        year_end = timezone.now().date().replace(month=12, day=31)
        return (year_end - timezone.now().date()).days


class CDPDetail(models.Model):
    """Detalle de CDP por Rubro Presupuestal"""
    cdp = models.ForeignKey(CDP, on_delete=models.CASCADE, related_name='details')
    rubro = models.ForeignKey(BudgetRubro, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    committed_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    class Meta:
        unique_together = [['cdp', 'rubro']]
    
    def __str__(self):
        return f"{self.cdp.number} - {self.rubro.code}"
    
    @property
    def available_amount(self):
        return self.amount - self.committed_amount


class RP(models.Model):
    """Registro Presupuestal - Compromiso"""
    STATE_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('partial', 'Parcialmente Ejecutado'),
        ('executed', 'Ejecutado'),
        ('cancelled', 'Anulado'),
        ('reversed', 'Reversado')
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('service', 'Prestación de Servicios'),
        ('supply', 'Suministro'),
        ('work', 'Obra'),
        ('consulting', 'Consultoría'),
        ('intervention', 'Interventoría'),
        ('lease', 'Arrendamiento'),
        ('insurance', 'Seguros'),
        ('agreement', 'Convenio'),
        ('purchase_order', 'Orden de Compra'),
        ('service_order', 'Orden de Servicio'),
        ('other', 'Otro')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_rps')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='rps')
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    
    # Información del beneficiario
    beneficiary_type = models.CharField(max_length=20, choices=[
        ('person', 'Persona Natural'),
        ('company', 'Persona Jurídica')
    ])
    beneficiary_id = models.CharField(max_length=20, verbose_name="NIT/CC")
    beneficiary_name = models.CharField(max_length=200)
    
    # Información del compromiso
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPE_CHOICES)
    contract_number = models.CharField(max_length=100, blank=True)
    concept = models.TextField()
    
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    obligated_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='draft')
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_rps')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_rps')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    observations = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-number']
        verbose_name = "RP"
        verbose_name_plural = "RPs"
    
    def __str__(self):
        return f"RP {self.number} - {self.beneficiary_name}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)
    
    def generate_number(self):
        """Genera número consecutivo de RP"""
        year = timezone.now().year
        last_rp = RP.objects.filter(
            company=self.company,
            date__year=year
        ).order_by('-number').first()
        
        if last_rp and last_rp.number:
            try:
                last_number = int(last_rp.number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        
        return f"RP-{year}-{str(new_number).zfill(5)}"
    
    @property
    def available_amount(self):
        """Saldo disponible para obligar"""
        return self.total_amount - self.obligated_amount


class RPDetail(models.Model):
    """Detalle de RP por CDP y Rubro"""
    rp = models.ForeignKey(RP, on_delete=models.CASCADE, related_name='details')
    cdp = models.ForeignKey(CDP, on_delete=models.PROTECT)
    cdp_detail = models.ForeignKey(CDPDetail, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = [['rp', 'cdp_detail']]
    
    def __str__(self):
        return f"{self.rp.number} - {self.cdp.number}"


class BudgetObligation(models.Model):
    """Obligación Presupuestal"""
    STATE_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobada'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagada'),
        ('cancelled', 'Anulada')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_obligations')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='obligations')
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    
    rp = models.ForeignKey(RP, on_delete=models.PROTECT, related_name='obligations')
    
    # Información de la obligación
    concept = models.TextField()
    invoice_number = models.CharField(max_length=50, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    gross_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    deductions = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=20, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='draft')
    
    # Información contable
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_obligations')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_obligations')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    observations = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-number']
    
    def __str__(self):
        return f"Obligación {self.number} - {self.rp.beneficiary_name}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        self.net_amount = self.gross_amount - self.deductions
        super().save(*args, **kwargs)
    
    def generate_number(self):
        """Genera número consecutivo de Obligación"""
        year = timezone.now().year
        last_ob = BudgetObligation.objects.filter(
            company=self.company,
            date__year=year
        ).order_by('-number').first()
        
        if last_ob and last_ob.number:
            try:
                last_number = int(last_ob.number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        
        return f"OB-{year}-{str(new_number).zfill(5)}"


class PAC(models.Model):
    """Plan Anual Mensualizado de Caja"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='pacs')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='pacs')
    rubro = models.ForeignKey(BudgetRubro, on_delete=models.CASCADE, related_name='pacs')
    
    # Programación mensual
    january = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    february = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    march = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    april = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    may = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    june = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    july = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    august = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    september = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    october = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    november = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    december = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    total_programmed = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'period', 'rubro']]
        ordering = ['rubro__code']
    
    def __str__(self):
        return f"PAC {self.period.year} - {self.rubro.name}"
    
    def save(self, *args, **kwargs):
        self.total_programmed = (
            self.january + self.february + self.march + self.april + 
            self.may + self.june + self.july + self.august + 
            self.september + self.october + self.november + self.december
        )
        super().save(*args, **kwargs)
    
    def get_month_value(self, month):
        """Obtiene el valor programado para un mes específico"""
        month_fields = {
            1: self.january, 2: self.february, 3: self.march,
            4: self.april, 5: self.may, 6: self.june,
            7: self.july, 8: self.august, 9: self.september,
            10: self.october, 11: self.november, 12: self.december
        }
        return month_fields.get(month, 0)


class BudgetModification(models.Model):
    """Modificaciones Presupuestales (Traslados, Adiciones, Reducciones)"""
    MODIFICATION_TYPE_CHOICES = [
        ('addition', 'Adición'),
        ('reduction', 'Reducción'),
        ('transfer', 'Traslado'),
        ('credit', 'Crédito'),
        ('counterCredit', 'Contracrédito')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budget_modifications')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='modifications')
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    modification_type = models.CharField(max_length=20, choices=MODIFICATION_TYPE_CHOICES)
    
    # Documentos de soporte
    act_number = models.CharField(max_length=100, verbose_name="Número de Acto Administrativo")
    act_date = models.DateField(verbose_name="Fecha del Acto")
    
    concept = models.TextField()
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    
    state = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('applied', 'Aplicado'),
        ('cancelled', 'Anulado')
    ], default='draft')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_budget_modifications')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_budget_modifications')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date', '-number']
    
    def __str__(self):
        return f"{self.get_modification_type_display()} {self.number}"


class BudgetModificationDetail(models.Model):
    """Detalle de Modificación Presupuestal"""
    modification = models.ForeignKey(BudgetModification, on_delete=models.CASCADE, related_name='details')
    rubro = models.ForeignKey(BudgetRubro, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=10, choices=[
        ('debit', 'Débito'),
        ('credit', 'Crédito')
    ])
    amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.modification.number} - {self.rubro.code}"


class BudgetExecution(models.Model):
    """Vista consolidada de Ejecución Presupuestal"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE)
    rubro = models.ForeignKey(BudgetRubro, on_delete=models.CASCADE)
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    
    # Ingresos
    income_budget = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    income_executed = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    income_collected = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Gastos
    appropriation = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cdp = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    rp = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    obligations = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    payments = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'period', 'rubro', 'month', 'year']]
        ordering = ['year', 'month', 'rubro__code']
    
    def __str__(self):
        return f"Ejecución {self.year}-{self.month:02d} - {self.rubro.name}"
    
    @property
    def execution_percentage(self):
        """Porcentaje de ejecución presupuestal"""
        if self.rubro.rubro_type == 'income':
            if self.income_budget > 0:
                return (self.income_executed / self.income_budget) * 100
        else:
            if self.appropriation > 0:
                return (self.obligations / self.appropriation) * 100
        return 0