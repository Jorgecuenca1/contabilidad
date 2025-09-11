"""
Comando para crear los módulos del sistema.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models_modules import SystemModule


class Command(BaseCommand):
    help = 'Crear módulos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('[CREANDO MODULOS DEL SISTEMA]')
        
        modules_to_create = [
            # Módulos Core
            {
                'code': 'accounting',
                'name': 'Contabilidad General',
                'description': 'Módulo completo de contabilidad con PUC colombiano, asientos contables, balances y estados financieros.',
                'category': 'finance',
                'url_pattern': 'accounting',
                'icon_class': 'bi-journal-bookmark',
                'is_core_module': True,
            },
            {
                'code': 'accounts_receivable',
                'name': 'Cuentas por Cobrar',
                'description': 'Gestión de facturas de venta, pagos de clientes, cartera y seguimiento de cobro.',
                'category': 'finance',
                'url_pattern': 'accounts_receivable',
                'icon_class': 'bi-person-check',
                'is_core_module': True,
            },
            {
                'code': 'accounts_payable',
                'name': 'Cuentas por Pagar',
                'description': 'Gestión de facturas de proveedores, pagos a proveedores y control de obligaciones.',
                'category': 'finance',
                'url_pattern': 'accounts_payable',
                'icon_class': 'bi-credit-card',
                'is_core_module': True,
            },
            {
                'code': 'treasury',
                'name': 'Tesorería',
                'description': 'Gestión de bancos, movimientos bancarios, conciliaciones y flujo de caja.',
                'category': 'finance',
                'url_pattern': 'treasury',
                'icon_class': 'bi-bank',
                'is_core_module': True,
            },
            {
                'code': 'payroll',
                'name': 'Nómina',
                'description': 'Sistema completo de nómina colombiana con seguridad social, prestaciones y PILA.',
                'category': 'operations',
                'url_pattern': 'payroll',
                'icon_class': 'bi-people',
                'is_core_module': True,
            },
            {
                'code': 'taxes',
                'name': 'Impuestos',
                'description': 'Gestión de declaraciones de IVA, Renta, ICA y cumplimiento tributario DIAN.',
                'category': 'finance',
                'url_pattern': 'taxes',
                'icon_class': 'bi-receipt-cutoff',
                'is_core_module': True,
            },
            {
                'code': 'inventory',
                'name': 'Inventarios',
                'description': 'Control de inventarios, entradas, salidas, valoración y kardex.',
                'category': 'operations',
                'url_pattern': 'inventory',
                'icon_class': 'bi-boxes',
                'is_core_module': False,
            },
            {
                'code': 'fixed_assets',
                'name': 'Activos Fijos',
                'description': 'Gestión de activos fijos, depreciaciones y mantenimientos.',
                'category': 'finance',
                'url_pattern': 'fixed_assets',
                'icon_class': 'bi-building',
                'is_core_module': False,
            },
            {
                'code': 'third_parties',
                'name': 'Terceros',
                'description': 'Gestión central de clientes, proveedores y terceros.',
                'category': 'operations',
                'url_pattern': 'third_parties',
                'icon_class': 'bi-person-lines-fill',
                'is_core_module': True,
            },
            
            # Módulos Especializados - Sector Salud
            {
                'code': 'gynecology',
                'name': 'Ginecología',
                'description': 'Módulo completo de ginecología para hospitales nivel 4: pacientes, citas, historias clínicas, procedimientos y seguimiento.',
                'category': 'healthcare',
                'url_pattern': 'gynecology',
                'icon_class': 'bi-heart-pulse',
                'requires_company_category': 'salud',
                'is_core_module': False,
            },
            {
                'code': 'cardiology',
                'name': 'Cardiología',
                'description': 'Módulo especializado en cardiología con electrocardiogramas, ecocardiogramas y seguimiento cardiovascular.',
                'category': 'healthcare',
                'url_pattern': 'cardiology',
                'icon_class': 'bi-heart',
                'requires_company_category': 'salud',
                'is_core_module': False,
            },
            {
                'code': 'emergency',
                'name': 'Urgencias',
                'description': 'Módulo de urgencias médicas con triage, atención inmediata y seguimiento de casos críticos.',
                'category': 'healthcare',
                'url_pattern': 'emergency',
                'icon_class': 'bi-hospital',
                'requires_company_category': 'salud',
                'is_core_module': False,
            },
            {
                'code': 'laboratory',
                'name': 'Laboratorio',
                'description': 'Gestión de laboratorio clínico con exámenes, resultados y control de calidad.',
                'category': 'healthcare',
                'url_pattern': 'laboratory',
                'icon_class': 'bi-thermometer',
                'requires_company_category': 'salud',
                'is_core_module': False,
            },
            
            # Módulos Especializados - Otros Sectores
            {
                'code': 'education',
                'name': 'Educación',
                'description': 'Módulo educativo con gestión de estudiantes, cursos, notas y matrículas.',
                'category': 'education',
                'url_pattern': 'education',
                'icon_class': 'bi-book',
                'requires_company_category': 'educacion',
                'is_core_module': False,
            },
            {
                'code': 'retail_pos',
                'name': 'Punto de Venta',
                'description': 'Sistema de punto de venta para retail con facturación electrónica.',
                'category': 'retail',
                'url_pattern': 'retail_pos',
                'icon_class': 'bi-shop',
                'is_core_module': False,
            },
            {
                'code': 'manufacturing',
                'name': 'Manufactura',
                'description': 'Módulo de manufactura con órdenes de producción, BOM y control de calidad.',
                'category': 'manufacturing',
                'url_pattern': 'manufacturing',
                'icon_class': 'bi-gear',
                'is_core_module': False,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for module_data in modules_to_create:
                module, created = SystemModule.objects.get_or_create(
                    code=module_data['code'],
                    defaults=module_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  [+] {module.name} creado')
                else:
                    # Actualizar datos si ya existe
                    for key, value in module_data.items():
                        if key != 'code':  # No actualizar el código
                            setattr(module, key, value)
                    module.save()
                    updated_count += 1
                    self.stdout.write(f'  [~] {module.name} actualizado')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] Módulos procesados: {created_count} creados, {updated_count} actualizados'
            )
        )