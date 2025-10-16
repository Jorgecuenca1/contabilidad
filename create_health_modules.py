#!/usr/bin/env python
"""
Script para crear la estructura básica de los módulos de salud restantes
"""

import os

# Definición de módulos con su configuración
MODULES_CONFIG = {
    'catalogs': {
        'verbose_name': 'Catálogos CUPS/CUMS',
        'description': 'Cat\u00e1logos centralizados CUPS (procedimientos) y CUMS (medicamentos)',
    },
    'rips': {
        'verbose_name': 'Generador RIPS',
        'description': 'Generaci\u00f3n autom\u00e1tica de archivos RIPS para SISPRO',
    },
    'emergency': {
        'verbose_name': 'Urgencias',
        'description': 'M\u00f3dulo de urgencias con triage y admisi\u00f3n',
    },
    'hospitalization': {
        'verbose_name': 'Hospitalizaci\u00f3n',
        'description': 'Gesti\u00f3n de camas, ingresos y hospitalizaci\u00f3n',
    },
    'surgery': {
        'verbose_name': 'Quir\u00f3fano',
        'description': 'Programaci\u00f3n quir\u00fargica y control de salas',
    },
    'blood_bank': {
        'verbose_name': 'Banco de Sangre',
        'description': 'Gesti\u00f3n de donantes y hemocomponentes',
    },
    'occupational_health': {
        'verbose_name': 'Salud Ocupacional',
        'description': 'Ex\u00e1menes ocupacionales y aptitud laboral',
    },
    'imaging': {
        'verbose_name': 'Im\u00e1genes Diagn\u00f3sticas',
        'description': 'Radiolog\u00eda e im\u00e1genes m\u00e9dicas',
    },
    'ophthalmology': {
        'verbose_name': 'Oftalmolog\u00eda',
        'description': 'Consulta oftalmol\u00f3gica especializada',
    },
    'dentistry': {
        'verbose_name': 'Odontolog\u00eda',
        'description': 'Consulta odontol\u00f3gica y odontograma',
    },
    'psychology': {
        'verbose_name': 'Psicolog\u00eda',
        'description': 'Consulta psicol\u00f3gica y seguimiento',
    },
    'rehabilitation': {
        'verbose_name': 'Rehabilitaci\u00f3n',
        'description': 'Fisioterapia y rehabilitaci\u00f3n',
    },
    'authorizations': {
        'verbose_name': 'Autorizaciones EPS',
        'description': 'Gesti\u00f3n de autorizaciones de servicios',
    },
    'pharmacy': {
        'verbose_name': 'Farmacia',
        'description': 'Inventario y dispensaci\u00f3n de medicamentos',
    },
    'billing_health': {
        'verbose_name': 'Facturaci\u00f3n Salud',
        'description': 'Facturaci\u00f3n de servicios de salud',
    },
    'health_reports': {
        'verbose_name': 'Reportes Cl\u00ednicos',
        'description': 'Reportes e indicadores cl\u00ednicos',
    },
    'telemedicine': {
        'verbose_name': 'Telemedicina',
        'description': 'Consultas virtuales y atenci\u00f3n domiciliaria',
    },
}


def create_module_files(module_name, config):
    """Crea los archivos básicos de un módulo"""

    # __init__.py
    init_content = f'''"""
{config['verbose_name']} - {config['description']}
"""

default_app_config = '{module_name}.apps.{module_name.capitalize()}Config'
'''

    # apps.py
    apps_content = f'''from django.apps import AppConfig


class {module_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{module_name}'
    verbose_name = '{config['verbose_name']}'
'''

    # models.py básico
    models_content = f'''"""
Modelos del módulo {config['verbose_name']}
{config['description']}
"""

from django.db import models
import uuid
from core.models import Company, User


class {module_name.capitalize()}Module(models.Model):
    """Modelo base del módulo {config['verbose_name']}"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '{module_name}_base'
        verbose_name = '{config['verbose_name']}'
        verbose_name_plural = '{config['verbose_name']}'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
'''

    # views.py básico
    views_content = f'''"""
Vistas del módulo {config['verbose_name']}
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def index(request):
    """Vista principal del módulo"""
    company = request.session.get('company')
    if not company:
        messages.error(request, 'Debe seleccionar una empresa')
        return redirect('core:select_company')

    context = {{
        'module_name': '{config['verbose_name']}',
    }}
    return render(request, '{module_name}/index.html', context)
'''

    # urls.py
    urls_content = f'''"""
URLs del módulo {config['verbose_name']}
"""

from django.urls import path
from . import views

app_name = '{module_name}'

urlpatterns = [
    path('', views.index, name='index'),
]
'''

    # admin.py
    admin_content = f'''"""
Admin del módulo {config['verbose_name']}
"""

from django.contrib import admin
from .models import {module_name.capitalize()}Module


@admin.register({module_name.capitalize()}Module)
class {module_name.capitalize()}ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
'''

    # Crear archivos
    with open(f'{module_name}/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    with open(f'{module_name}/apps.py', 'w', encoding='utf-8') as f:
        f.write(apps_content)

    with open(f'{module_name}/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

    with open(f'{module_name}/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)

    with open(f'{module_name}/urls.py', 'w', encoding='utf-8') as f:
        f.write(urls_content)

    with open(f'{module_name}/admin.py', 'w', encoding='utf-8') as f:
        f.write(admin_content)

    # Crear directorios
    os.makedirs(f'{module_name}/migrations', exist_ok=True)
    os.makedirs(f'{module_name}/templates/{module_name}', exist_ok=True)

    # migrations/__init__.py
    with open(f'{module_name}/migrations/__init__.py', 'w') as f:
        f.write(f'# Migrations for {module_name} module\n')

    print(f'OK - Modulo {module_name} creado exitosamente')


if __name__ == '__main__':
    for module_name, config in MODULES_CONFIG.items():
        try:
            create_module_files(module_name, config)
        except Exception as e:
            print(f'ERROR - Error creando {module_name}: {e}')

    print('\nOK - Todos los modulos creados exitosamente!')
