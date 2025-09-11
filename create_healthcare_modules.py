#!/usr/bin/env python
"""
Script para crear los módulos del sistema de salud separados.
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import transaction
from core.models import Company, User
from core.models_modules import SystemModule, CompanyModule


def create_healthcare_modules():
    """Crear módulos de salud separados."""
    print("=== CREANDO MODULOS DE SALUD SEPARADOS ===")
    
    # Módulos de salud especializados
    healthcare_modules = [
        {
            'code': 'medical_records',
            'name': 'Historia Clínica',
            'description': 'Gestión completa de historias clínicas por especialidad médica',
            'category': 'healthcare',
            'url_pattern': 'medical-records',
            'icon_class': 'bi-file-medical',
            'requires_company_category': 'salud',
        },
        {
            'code': 'medical_appointments',
            'name': 'Citas Médicas',
            'description': 'Sistema de agendamiento médico con selección de doctores por especialidad',
            'category': 'healthcare',
            'url_pattern': 'medical-appointments',
            'icon_class': 'bi-calendar-check',
            'requires_company_category': 'salud',
        },
        {
            'code': 'medical_procedures',
            'name': 'Procedimientos Médicos',
            'description': 'Gestión de procedimientos médicos con códigos CUPS',
            'category': 'healthcare',
            'url_pattern': 'medical-procedures',
            'icon_class': 'bi-clipboard2-pulse',
            'requires_company_category': 'salud',
        },
        {
            'code': 'gynecology',
            'name': 'Ginecología',
            'description': 'Módulo especializado en ginecología y obstetricia',
            'category': 'healthcare',
            'url_pattern': 'gynecology',
            'icon_class': 'bi-heart-pulse',
            'requires_company_category': 'salud',
        },
        {
            'code': 'laboratory',
            'name': 'Laboratorio Clínico',
            'description': 'Sistema de información de laboratorio (LIS) - Acceso solo para personal de laboratorio',
            'category': 'healthcare',
            'url_pattern': 'laboratory',
            'icon_class': 'bi-thermometer-half',
            'requires_company_category': 'salud',
            'requires_specific_role': 'laboratory',
        },
        # Módulos core que también deben estar disponibles
        {
            'code': 'core',
            'name': 'Configuración',
            'description': 'Configuración base del sistema',
            'category': 'finance',
            'url_pattern': 'core',
            'icon_class': 'bi-gear',
            'requires_company_category': '',
            'is_core_module': True,
        },
        {
            'code': 'payroll',
            'name': 'Nómina',
            'description': 'Gestión de empleados y nómina',
            'category': 'finance',
            'url_pattern': 'payroll',
            'icon_class': 'bi-people',
            'requires_company_category': '',
            'is_core_module': True,
        },
        {
            'code': 'third_parties',
            'name': 'Terceros',
            'description': 'Gestión de clientes, proveedores y pacientes',
            'category': 'finance',
            'url_pattern': 'third-parties',
            'icon_class': 'bi-person-lines-fill',
            'requires_company_category': '',
            'is_core_module': True,
        },
        {
            'code': 'accounting',
            'name': 'Contabilidad',
            'description': 'Módulo de contabilidad general',
            'category': 'finance',
            'url_pattern': 'accounting',
            'icon_class': 'bi-calculator',
            'requires_company_category': '',
            'is_core_module': True,
        },
        {
            'code': 'accounts_receivable',
            'name': 'Cuentas por Cobrar',
            'description': 'Gestión de cartera de clientes',
            'category': 'finance',
            'url_pattern': 'accounts-receivable',
            'icon_class': 'bi-cash-coin',
            'requires_company_category': '',
        },
        {
            'code': 'accounts_payable',
            'name': 'Cuentas por Pagar',
            'description': 'Gestión de obligaciones con proveedores',
            'category': 'finance',
            'url_pattern': 'accounts-payable',
            'icon_class': 'bi-credit-card',
            'requires_company_category': '',
        },
        {
            'code': 'treasury',
            'name': 'Tesorería',
            'description': 'Gestión de bancos y flujo de caja',
            'category': 'finance',
            'url_pattern': 'treasury',
            'icon_class': 'bi-bank',
            'requires_company_category': '',
        },
        {
            'code': 'taxes',
            'name': 'Impuestos',
            'description': 'Declaraciones y gestión tributaria',
            'category': 'finance',
            'url_pattern': 'taxes',
            'icon_class': 'bi-receipt',
            'requires_company_category': '',
        },
        {
            'code': 'reports',
            'name': 'Reportes',
            'description': 'Reportes financieros y operacionales',
            'category': 'finance',
            'url_pattern': 'reports',
            'icon_class': 'bi-graph-up',
            'requires_company_category': '',
        },
    ]
    
    for module_data in healthcare_modules:
        module, created = SystemModule.objects.get_or_create(
            code=module_data['code'],
            defaults={
                'name': module_data['name'],
                'description': module_data['description'],
                'category': module_data['category'],
                'url_pattern': module_data['url_pattern'],
                'icon_class': module_data['icon_class'],
                'requires_company_category': module_data['requires_company_category'],
                'is_core_module': module_data.get('is_core_module', False),
                'is_available': True,
            }
        )
        if created:
            print(f"[+] Módulo creado: {module_data['name']}")
        else:
            print(f"[-] Módulo existe: {module_data['name']}")
    
    # Activar módulos para empresas de salud
    healthcare_companies = Company.objects.filter(category='salud')
    admin_user = User.objects.filter(is_staff=True).first()
    
    if admin_user:
        for company in healthcare_companies:
            print(f"\n=== Activando módulos para {company.name} ===")
            
            # Activar todos los módulos para empresas de salud
            all_modules = SystemModule.objects.filter(is_available=True)
            
            for module in all_modules:
                if module.can_be_activated_for_company(company):
                    company_module, created = CompanyModule.objects.get_or_create(
                        company=company,
                        module=module,
                        defaults={
                            'is_enabled': True,
                            'enabled_by': admin_user,
                        }
                    )
                    if created:
                        print(f"[+] Activado: {module.name}")
                    else:
                        print(f"[-] Ya activo: {module.name}")
    
    print("\n=== MODULOS DE SALUD CONFIGURADOS ===")
    print("Módulos disponibles:")
    for module in SystemModule.objects.filter(category='healthcare'):
        print(f"* {module.name} - {module.description}")
    
    return True


if __name__ == "__main__":
    try:
        with transaction.atomic():
            create_healthcare_modules()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()