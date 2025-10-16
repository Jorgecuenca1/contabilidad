"""
Sistema de habilitación/deshabilitación de módulos por empresa
Permite que cada empresa active solo los módulos que necesita
"""

from django.db import models
import uuid

from .models import Company, User


class CompanyModule(models.Model):
    """
    Configuración de módulos habilitados por empresa
    """
    MODULE_CHOICES = [
        # Módulos contables
        ('accounting', 'Contabilidad'),
        ('accounts_receivable', 'Cuentas por Cobrar'),
        ('accounts_payable', 'Cuentas por Pagar'),
        ('treasury', 'Tesorería'),
        ('inventory', 'Inventario'),
        ('fixed_assets', 'Activos Fijos'),
        ('payroll', 'Nómina'),
        ('taxes', 'Impuestos'),
        ('public_sector', 'Sector Público'),
        ('reports', 'Reportes'),
        ('budget', 'Presupuesto'),
        ('third_parties', 'Terceros'),

        # Módulos de salud básicos
        ('gynecology', 'Ginecología'),
        ('laboratory', 'Laboratorio'),
        ('medical_records', 'Historias Clínicas'),
        ('medical_appointments', 'Citas Médicas'),
        ('medical_procedures', 'Procedimientos Médicos'),

        # Módulos IPS completos
        ('patients', 'Gestión de Pacientes'),
        ('diagnostics', 'Diagnósticos CIE-10'),
        ('catalogs', 'Catálogos CUPS/CUMS'),
        ('rips', 'Generador RIPS'),
        ('emergency', 'Urgencias'),
        ('hospitalization', 'Hospitalización'),
        ('surgery', 'Cirugías'),
        ('blood_bank', 'Banco de Sangre'),
        ('occupational_health', 'Salud Ocupacional'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('ophthalmology', 'Oftalmología'),
        ('dentistry', 'Odontología'),
        ('psychology', 'Psicología'),
        ('rehabilitation', 'Rehabilitación'),
        ('authorizations', 'Autorizaciones EPS'),
        ('pharmacy', 'Farmacia'),
        ('billing_health', 'Facturación Salud'),
        ('health_reports', 'Reportes Clínicos'),
        ('telemedicine', 'Telemedicina'),
    ]

    CATEGORY_CHOICES = [
        ('core', 'Módulo Básico'),
        ('business', 'Módulo Empresarial'),
        ('health', 'Módulo de Salud'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='enabled_modules')

    module_code = models.CharField(max_length=50, choices=MODULE_CHOICES)
    module_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='business')

    is_enabled = models.BooleanField(default=True, help_text="Módulo habilitado para esta empresa")
    is_required = models.BooleanField(default=False, help_text="Módulo requerido (no se puede deshabilitar)")

    # Configuración del módulo
    config = models.JSONField(default=dict, help_text="Configuración específica del módulo")

    # Auditoría
    enabled_at = models.DateTimeField(auto_now_add=True)
    enabled_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modules_enabled')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_company_modules'
        verbose_name = 'Módulo de Empresa'
        verbose_name_plural = 'Módulos de Empresa'
        unique_together = ['company', 'module_code']
        ordering = ['module_category', 'module_code']

    def __str__(self):
        return f"{self.company.name} - {self.get_module_code_display()}"

    @classmethod
    def get_health_modules(cls):
        """Retorna lista de códigos de módulos de salud"""
        return [code for code, name in cls.MODULE_CHOICES if cls.is_health_module(code)]

    @classmethod
    def is_health_module(cls, module_code):
        """Verifica si un módulo es de salud"""
        health_modules = [
            'gynecology', 'laboratory', 'medical_records', 'medical_appointments',
            'medical_procedures', 'patients', 'diagnostics', 'catalogs', 'rips',
            'emergency', 'hospitalization', 'surgery', 'blood_bank',
            'occupational_health', 'imaging', 'ophthalmology', 'dentistry',
            'psychology', 'rehabilitation', 'authorizations', 'pharmacy',
            'billing_health', 'health_reports', 'telemedicine',
        ]
        return module_code in health_modules

    @classmethod
    def get_core_modules(cls):
        """Retorna lista de módulos core que siempre están habilitados"""
        return ['accounting', 'reports', 'third_parties']

    def can_disable(self):
        """Verifica si el módulo puede ser deshabilitado"""
        if self.is_required:
            return False
        if self.module_code in self.get_core_modules():
            return False
        return True


class ModuleDependency(models.Model):
    """
    Dependencias entre módulos
    Define qué módulos requieren otros módulos
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    module_code = models.CharField(max_length=50, help_text="Módulo que tiene la dependencia")
    depends_on = models.CharField(max_length=50, help_text="Módulo del que depende")

    is_required = models.BooleanField(default=True, help_text="Dependencia obligatoria")
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_module_dependencies'
        verbose_name = 'Dependencia de Módulo'
        verbose_name_plural = 'Dependencias de Módulos'
        unique_together = ['module_code', 'depends_on']

    def __str__(self):
        return f"{self.module_code} → {self.depends_on}"


def enable_default_modules_for_company(company, user):
    """
    Habilita los módulos por defecto para una empresa según su categoría
    """
    from .models_company_modules import CompanyModule

    # Módulos core siempre habilitados
    core_modules = ['accounting', 'reports', 'third_parties']

    # Módulos empresariales estándar
    business_modules = [
        'accounts_receivable', 'accounts_payable', 'treasury',
        'inventory', 'payroll', 'taxes'
    ]

    # Módulos de salud si es IPS
    health_modules = []
    if company.category == 'salud':
        health_modules = [
            'patients', 'diagnostics', 'medical_records',
            'medical_appointments', 'medical_procedures',
            'laboratory', 'rips', 'authorizations', 'pharmacy',
            'billing_health'
        ]

    # Crear registros
    all_modules = core_modules + business_modules + (health_modules if health_modules else [])

    for module_code in all_modules:
        CompanyModule.objects.get_or_create(
            company=company,
            module_code=module_code,
            defaults={
                'is_enabled': True,
                'is_required': module_code in core_modules,
                'enabled_by': user,
                'module_category': 'health' if module_code in CompanyModule.get_health_modules() else 'business',
            }
        )

    return True
