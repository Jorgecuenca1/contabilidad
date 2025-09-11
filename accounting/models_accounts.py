"""
Modelos de cuentas contables y plan de cuentas.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from core.models import Company, User, Currency


class AccountType(models.Model):
    """
    Tipos de cuenta contable (Activo, Pasivo, Patrimonio, Ingresos, Gastos).
    """
    TYPE_CHOICES = [
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Patrimonio'),
        ('income', 'Ingresos'),
        ('expense', 'Gastos'),
        ('cost', 'Costos'),
    ]
    
    NATURE_CHOICES = [
        ('debit', 'Débito'),
        ('credit', 'Crédito'),
    ]
    
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES)
    is_balance_sheet = models.BooleanField(default=True, help_text="Aparece en balance general")
    is_income_statement = models.BooleanField(default=False, help_text="Aparece en estado de resultados")
    
    class Meta:
        db_table = 'accounting_account_types'
        verbose_name = 'Tipo de Cuenta'
        verbose_name_plural = 'Tipos de Cuenta'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ChartOfAccounts(models.Model):
    """
    Plan de cuentas maestro por empresa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='chart_of_accounts')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    account_code_length = models.IntegerField(default=6, help_text="Longitud del código de cuenta")
    cost_center_required = models.BooleanField(default=False)
    project_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_chart_of_accounts'
        verbose_name = 'Plan de Cuentas'
        verbose_name_plural = 'Planes de Cuentas'
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Account(models.Model):
    """
    Cuenta contable individual dentro del plan de cuentas.
    Soporta cuentas estándar del PUC colombiano (compartidas) y cuentas personalizadas por empresa.
    """
    CONTROL_CHOICES = [
        ('none', 'Sin Control'),
        ('receivables', 'Cuentas por Cobrar'),
        ('payables', 'Cuentas por Pagar'),
        ('inventory', 'Inventarios'),
        ('fixed_assets', 'Activos Fijos'),
        ('bank', 'Bancos'),
        ('cash', 'Caja'),
        ('tax', 'Impuestos'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart_of_accounts = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)
    
    # Soporte para PUC colombiano compartido vs cuentas personalizadas
    is_custom = models.BooleanField(default=False, help_text="True para cuentas personalizadas de empresa, False para PUC estándar colombiano")
    custom_company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, 
                                      help_text="Empresa propietaria de cuenta personalizada (null para PUC estándar)")
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    control_type = models.CharField(max_length=20, choices=CONTROL_CHOICES, default='none')
    
    # Comportamiento
    is_active = models.BooleanField(default=True)
    is_detail = models.BooleanField(default=True, help_text="Permite movimientos directos")
    requires_third_party = models.BooleanField(default=False)
    requires_cost_center = models.BooleanField(default=False)
    requires_project = models.BooleanField(default=False)
    
    # Configuración de moneda
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True)
    allow_multi_currency = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_accounts'
        verbose_name = 'Cuenta Contable'
        verbose_name_plural = 'Cuentas Contables'
        constraints = [
            # Las cuentas estándar del PUC no pueden tener duplicados de código
            models.UniqueConstraint(
                fields=['code'],
                condition=models.Q(is_custom=False),
                name='unique_puc_standard_code'
            ),
            # Las cuentas personalizadas no pueden tener duplicados por empresa
            models.UniqueConstraint(
                fields=['custom_company', 'code'],
                condition=models.Q(is_custom=True),
                name='unique_custom_company_code'
            ),
        ]
        ordering = ['code']
        indexes = [
            models.Index(fields=['chart_of_accounts', 'code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active', 'is_detail']),
            models.Index(fields=['is_custom', 'custom_company']),
        ]
    
    def __str__(self):
        prefix = "[PERSONALIZADA] " if self.is_custom else ""
        return f"{prefix}{self.code} - {self.name}"
    
    @classmethod
    def get_company_accounts(cls, company):
        """
        Obtiene todas las cuentas visibles para una empresa:
        - Cuentas estándar del PUC colombiano (is_custom=False)
        - Cuentas personalizadas de la empresa (is_custom=True, custom_company=company)
        """
        from django.db.models import Q
        return cls.objects.filter(
            Q(is_custom=False) | Q(is_custom=True, custom_company=company)
        ).order_by('code')
    
    def get_full_code(self):
        """Obtiene el código completo incluyendo jerarquía."""
        if self.parent:
            return f"{self.parent.get_full_code()}.{self.code}"
        return self.code
    
    def clean(self):
        """Validaciones del modelo para el PUC colombiano."""
        from django.core.exceptions import ValidationError
        
        # Validar estructura del código PUC
        if not self.code.isdigit():
            raise ValidationError("El código de cuenta debe contener solo números según el PUC colombiano")
        
        # Validar longitud según nivel
        if self.level == 1 and len(self.code) != 1:
            raise ValidationError("Las cuentas de nivel 1 deben tener 1 dígito (1-6)")
        elif self.level == 2 and len(self.code) != 2:
            raise ValidationError("Las cuentas de nivel 2 deben tener 2 dígitos")
        elif self.level == 3 and len(self.code) != 4:
            raise ValidationError("Las cuentas de nivel 3 deben tener 4 dígitos")
        elif self.level == 4 and len(self.code) != 6:
            raise ValidationError("Las cuentas de nivel 4 deben tener 6 dígitos")
        
        # Validar clase de cuenta según primer dígito (PUC colombiano)
        if len(self.code) >= 1:
            first_digit = self.code[0]
            if first_digit == '1' and self.account_type.code != '1':
                raise ValidationError("Las cuentas que inician con 1 deben ser de tipo Activo")
            elif first_digit == '2' and self.account_type.code != '2':
                raise ValidationError("Las cuentas que inician con 2 deben ser de tipo Pasivo")
            elif first_digit == '3' and self.account_type.code != '3':
                raise ValidationError("Las cuentas que inician con 3 deben ser de tipo Patrimonio")
            elif first_digit == '4' and self.account_type.code != '4':
                raise ValidationError("Las cuentas que inician con 4 deben ser de tipo Ingresos")
            elif first_digit == '5' and self.account_type.code != '5':
                raise ValidationError("Las cuentas que inician con 5 deben ser de tipo Gastos")
            elif first_digit == '6' and self.account_type.code != '6':
                raise ValidationError("Las cuentas que inician con 6 deben ser de tipo Costos")
    
    def save(self, *args, **kwargs):
        """Override save para aplicar validaciones del PUC."""
        self.full_clean()  # Ejecuta clean()
        super().save(*args, **kwargs)


class CostCenter(models.Model):
    """
    Centros de costo para segmentación de la información contable.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    
    # Jerarquía
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=1)
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Presupuesto
    has_budget = models.BooleanField(default=False)
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cost_centers_created')
    
    class Meta:
        db_table = 'accounting_cost_centers'
        verbose_name = 'Centro de Costo'
        verbose_name_plural = 'Centros de Costo'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Project(models.Model):
    """
    Proyectos para segmentación adicional de la información contable.
    """
    STATUS_CHOICES = [
        ('planning', 'Planificación'),
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuración
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Responsables
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Presupuesto
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='projects_created')
    
    class Meta:
        db_table = 'accounting_projects'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
