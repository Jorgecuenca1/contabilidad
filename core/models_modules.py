"""
Modelos para la gestión de módulos del sistema.
"""

from django.db import models
import uuid

from .models import Company, User


class SystemModule(models.Model):
    """
    Módulos del sistema que pueden ser activados/desactivados por empresa.
    """
    MODULE_CATEGORIES = [
        ('finance', 'Financiero'),
        ('operations', 'Operacional'),
        ('healthcare', 'Sector Salud'),
        ('education', 'Sector Educación'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufactura'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=MODULE_CATEGORIES)
    
    # URL del módulo
    url_pattern = models.CharField(max_length=100, help_text="Patrón de URL del módulo (ej: 'gynecology')")
    icon_class = models.CharField(max_length=50, default='bi-puzzle', help_text="Clase CSS del ícono (Bootstrap Icons)")
    
    # Configuración de activación
    requires_company_category = models.CharField(max_length=20, blank=True, help_text="Categoría de empresa requerida")
    is_core_module = models.BooleanField(default=False, help_text="Módulo core que no se puede desactivar")
    
    # Estado
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_system_modules'
        verbose_name = 'Módulo del Sistema'
        verbose_name_plural = 'Módulos del Sistema'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name}"
    
    def can_be_activated_for_company(self, company):
        """Verificar si el módulo puede activarse para una empresa."""
        if not self.is_available:
            return False
        
        if self.requires_company_category:
            return company.category == self.requires_company_category
        
        return True


class CompanyModule(models.Model):
    """
    Módulos activados por empresa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='active_modules')
    module = models.ForeignKey(SystemModule, on_delete=models.CASCADE)
    
    is_enabled = models.BooleanField(default=True)
    enabled_at = models.DateTimeField(auto_now_add=True)
    enabled_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'core_company_modules'
        verbose_name = 'Módulo de Empresa'
        verbose_name_plural = 'Módulos de Empresa'
        unique_together = ['company', 'module']
        ordering = ['module__category', 'module__name']
    
    def __str__(self):
        return f"{self.company.name} - {self.module.name}"


class UserModulePermission(models.Model):
    """
    Permisos de usuarios para módulos específicos.
    """
    PERMISSION_LEVELS = [
        ('view', 'Solo Ver'),
        ('edit', 'Ver y Editar'),
        ('admin', 'Administrador del Módulo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_permissions')
    company_module = models.ForeignKey(CompanyModule, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_LEVELS, default='view')
    
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='granted_permissions')
    
    class Meta:
        db_table = 'core_user_module_permissions'
        verbose_name = 'Permiso de Módulo'
        verbose_name_plural = 'Permisos de Módulos'
        unique_together = ['user', 'company_module']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company_module.module.name} ({self.permission_level})"