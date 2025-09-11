"""
Modelos del núcleo del sistema de contabilidad multiempresa.
Incluye usuarios, empresas, períodos fiscales y configuraciones base.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import hashlib


class User(AbstractUser):
    """
    Usuario personalizado del sistema con roles y permisos granulares.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador del Sistema'),
        ('contador', 'Contador'),
        ('dueno_empresa', 'Dueño de Empresa'),
        ('auxiliar_contable', 'Auxiliar Contable'),
        ('tesorero', 'Tesorero'),
        ('jefe_nomina', 'Jefe de Nómina'),
        ('auditor', 'Auditor'),
        ('cliente', 'Cliente/Proveedor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='auxiliar_contable')
    phone = models.CharField(max_length=20, blank=True)
    document_type = models.CharField(max_length=10, default='CC')
    document_number = models.CharField(max_length=20, unique=True)
    is_active_2fa = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    companies = models.ManyToManyField('Company', through='UserCompanyPermission', blank=True)
    default_company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_users')
    owned_company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='owners', help_text='Empresa propietaria para usuarios dueño de empresa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_accessible_companies(self):
        """Obtiene las empresas a las que el usuario tiene acceso según su rol."""
        if self.role == 'dueno_empresa':
            # Dueños de empresa solo ven su propia empresa
            return Company.objects.filter(id=self.owned_company_id) if self.owned_company else Company.objects.none()
        elif self.role in ['admin', 'contador']:
            # Administradores y contadores pueden ver todas las empresas o las asignadas
            if self.role == 'admin':
                return Company.objects.filter(is_active=True)
            else:
                # Contadores ven las empresas donde tienen permisos
                return Company.objects.filter(
                    usercompanypermission__user=self,
                    is_active=True
                ).distinct()
        else:
            # Otros roles ven solo las empresas asignadas específicamente
            return Company.objects.filter(
                usercompanypermission__user=self,
                is_active=True
            ).distinct()
    
    def can_access_company(self, company):
        """Verifica si el usuario puede acceder a una empresa específica."""
        return company in self.get_accessible_companies()


class Country(models.Model):
    """
    Países para localización del sistema contable.
    """
    code = models.CharField(max_length=3, primary_key=True)  # ISO 3166-1 alpha-3
    name = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=3)  # ISO 4217
    currency_symbol = models.CharField(max_length=5)
    tax_id_regex = models.CharField(max_length=100, help_text="Regex para validar NIT/RUC")
    
    # Configuraciones específicas del país
    chart_of_accounts_template = models.TextField(blank=True, help_text="Template JSON del plan de cuentas")
    tax_configuration = models.JSONField(default=dict, help_text="Configuración de impuestos del país")
    
    class Meta:
        db_table = 'core_countries'
        verbose_name = 'País'
        verbose_name_plural = 'Países'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Company(models.Model):
    """
    Empresa/Tenant del sistema multiempresa.
    Cada empresa tiene su propia contabilidad segregada.
    """
    REGIME_CHOICES = [
        ('simplified', 'Régimen Simplificado'),
        ('common', 'Régimen Común'),
        ('special', 'Régimen Especial'),
        ('public', 'Sector Público'),
    ]
    
    SECTOR_CHOICES = [
        ('private', 'Sector Privado'),
        ('public', 'Sector Público'),
        ('mixed', 'Economía Mixta'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20, unique=True, help_text="NIT/RUC")
    tax_id_dv = models.CharField(max_length=2, blank=True, help_text="Dígito de verificación")
    
    # Localización
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Contacto
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Configuración contable
    regime = models.CharField(max_length=20, choices=REGIME_CHOICES)
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, default='private')
    functional_currency = models.CharField(max_length=3, default='COP')
    
    # Configuración fiscal
    fiscal_year_start = models.DateField(help_text="Inicio del año fiscal")
    fiscal_year_end = models.DateField(help_text="Fin del año fiscal")
    
    # Representante legal
    legal_representative = models.CharField(max_length=200)
    legal_rep_document = models.CharField(max_length=20)
    
    # Configuraciones
    logo = models.ImageField(upload_to='company_logos/', blank=True)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, help_text="Configuraciones específicas de la empresa")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='companies_created')
    
    class Meta:
        db_table = 'core_companies'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.tax_id})"
    
    def get_current_fiscal_year(self):
        """Obtiene el año fiscal actual basado en la fecha."""
        today = timezone.now().date()
        if today >= self.fiscal_year_start and today <= self.fiscal_year_end:
            return self.fiscal_year_start.year
        elif today > self.fiscal_year_end:
            return self.fiscal_year_start.year + 1
        else:
            return self.fiscal_year_start.year - 1


# Importar modelos extendidos
from .models_extended import (
    FiscalYear, Period, UserCompanyPermission, Currency, 
    ExchangeRate, AuditLog, SystemConfiguration
)
