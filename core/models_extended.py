"""
Modelos extendidos del núcleo - Continuación de models.py
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import hashlib
from .models import User, Company


class FiscalYear(models.Model):
    """
    Año fiscal de una empresa.
    """
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
        ('locked', 'Bloqueado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fiscal_years')
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    
    # Control de cierre
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_fiscal_years'
        verbose_name = 'Año Fiscal'
        verbose_name_plural = 'Años Fiscales'
        unique_together = ['company', 'year']
        ordering = ['-year']
    
    def __str__(self):
        return f"{self.company.name} - {self.year}"


class Period(models.Model):
    """
    Período contable (mensual) dentro de un año fiscal.
    """
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
        ('locked', 'Bloqueado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods')
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    
    # Control de cierre
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_periods'
        verbose_name = 'Período'
        verbose_name_plural = 'Períodos'
        unique_together = ['fiscal_year', 'month']
        ordering = ['-fiscal_year__year', '-month']
    
    def __str__(self):
        return f"{self.fiscal_year.company.name} - {self.fiscal_year.year}/{self.month:02d}"


class UserCompanyPermission(models.Model):
    """
    Permisos granulares de usuarios por empresa.
    """
    PERMISSION_CHOICES = [
        ('read', 'Solo Lectura'),
        ('write', 'Lectura y Escritura'),
        ('approve', 'Aprobar'),
        ('admin', 'Administrador'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_CHOICES)
    
    # Permisos específicos por módulo
    can_access_accounting = models.BooleanField(default=False)
    can_access_receivables = models.BooleanField(default=False)
    can_access_payables = models.BooleanField(default=False)
    can_access_treasury = models.BooleanField(default=False)
    can_access_inventory = models.BooleanField(default=False)
    can_access_fixed_assets = models.BooleanField(default=False)
    can_access_payroll = models.BooleanField(default=False)
    can_access_taxes = models.BooleanField(default=False)
    can_access_reports = models.BooleanField(default=False)
    can_access_public_sector = models.BooleanField(default=False)
    
    # Restricciones adicionales
    cost_centers = models.JSONField(default=list, help_text="Centros de costo permitidos")
    max_amount_approval = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_user_company_permissions'
        verbose_name = 'Permiso Usuario-Empresa'
        verbose_name_plural = 'Permisos Usuario-Empresa'
        unique_together = ['user', 'company']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.permission_level})"


class Currency(models.Model):
    """
    Monedas del sistema para manejo multimoneda.
    """
    code = models.CharField(max_length=3, primary_key=True)  # ISO 4217
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=5)
    decimal_places = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_currencies'
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ExchangeRate(models.Model):
    """
    Tipos de cambio históricos para conversión de monedas.
    """
    RATE_TYPE_CHOICES = [
        ('official', 'Oficial'),
        ('market', 'Mercado'),
        ('custom', 'Personalizada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='exchange_rates')
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_from')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_to')
    
    date = models.DateField()
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    rate_type = models.CharField(max_length=10, choices=RATE_TYPE_CHOICES, default='official')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'core_exchange_rates'
        verbose_name = 'Tipo de Cambio'
        verbose_name_plural = 'Tipos de Cambio'
        unique_together = ['company', 'from_currency', 'to_currency', 'date', 'rate_type']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.from_currency.code}/{self.to_currency.code} - {self.rate} ({self.date})"


class AuditLog(models.Model):
    """
    Log de auditoría para trazabilidad completa del sistema.
    """
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('approve', 'Aprobar'),
        ('reject', 'Rechazar'),
        ('post', 'Contabilizar'),
        ('reverse', 'Reversar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    
    # Datos del cambio
    changes = models.JSONField(default=dict, help_text="Cambios realizados")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Hash para integridad
    hash_value = models.CharField(max_length=64, editable=False)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_audit_logs'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def save(self, *args, **kwargs):
        """Genera hash para integridad del log."""
        if not self.hash_value:
            data = f"{self.company_id}{self.user_id}{self.action}{self.model_name}{self.object_id}{self.timestamp}"
            self.hash_value = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.action} {self.model_name} ({self.timestamp})"


class SystemConfiguration(models.Model):
    """
    Configuraciones globales del sistema.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'core_system_configurations'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

