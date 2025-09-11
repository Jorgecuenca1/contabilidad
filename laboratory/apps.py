"""
Configuración de la aplicación Laboratory.
"""

from django.apps import AppConfig


class LaboratoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'laboratory'
    verbose_name = 'Sistema de Información de Laboratorio (LIS)'