"""
Management command para inicializar módulos del sistema.
"""

from django.core.management.base import BaseCommand
from core.models_modules import SystemModule, CompanyModule
from core.models import Company


class Command(BaseCommand):
    help = 'Inicializa los módulos del sistema y los activa para empresas existentes'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando módulos del sistema...')
        
        # Definir módulos del sistema
        # Formato: (code, name, category, url_pattern, icon_class, is_core, requires_category, requires_sector)
        modules_data = [
            # Módulos financieros (core) - Disponibles para todos
            ('accounting', 'Contabilidad', 'finance', 'accounting/', 'bi-calculator', True, '', ''),
            ('accounts_receivable', 'Cuentas por Cobrar', 'finance', 'accounts-receivable/', 'bi-arrow-right-circle', True, '', ''),
            ('accounts_payable', 'Cuentas por Pagar', 'finance', 'accounts-payable/', 'bi-arrow-left-circle', True, '', ''),
            ('treasury', 'Tesorería', 'finance', 'treasury/', 'bi-bank', True, '', ''),
            ('payroll', 'Nómina', 'finance', 'payroll/', 'bi-people-fill', True, '', ''),
            ('taxes', 'Impuestos', 'finance', 'taxes/', 'bi-receipt', True, '', ''),
            ('reports', 'Reportes', 'finance', 'reports/', 'bi-graph-up', True, '', ''),
            
            # Módulos operacionales generales
            ('inventory', 'Inventarios', 'operations', 'inventory/', 'bi-boxes', False, '', ''),
            ('production', 'Producción', 'manufacturing', 'production/', 'bi-gear-fill', False, 'manufactura', ''),
            
            # Módulos EXCLUSIVOS del sector público
            ('projects', 'Banco de Proyectos', 'operations', 'projects/', 'bi-briefcase', False, '', 'public'),
            ('budget', 'Presupuesto', 'operations', 'budget/', 'bi-pie-chart', False, '', 'public'),
            ('cdp', 'Certificados de Disponibilidad Presupuestal', 'operations', 'cdp/', 'bi-file-earmark-check', False, '', 'public'),
            
            # Módulos sector salud
            ('gynecology', 'Ginecología', 'healthcare', 'gynecology/', 'bi-heart-pulse', False, 'salud', ''),
            ('patients', 'Pacientes', 'healthcare', 'patients/', 'bi-people', False, 'salud', ''),
            ('medical_records', 'Historia Clínica', 'healthcare', 'medical-records/', 'bi-file-medical', False, 'salud', ''),
            
            # Módulos sector educación  
            ('students', 'Estudiantes', 'education', 'students/', 'bi-mortarboard', False, 'educacion', ''),
            ('academic', 'Académico', 'education', 'academic/', 'bi-journal-text', False, 'educacion', ''),
        ]
        
        created_count = 0
        for code, name, category, url_pattern, icon_class, is_core, requires_category, requires_sector in modules_data:
            module, created = SystemModule.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'url_pattern': url_pattern,
                    'icon_class': icon_class,
                    'is_core_module': is_core,
                    'requires_company_category': requires_category,
                    'requires_company_sector': requires_sector,
                    'is_available': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + Creado modulo: {name}')
            else:
                self.stdout.write(f'  - Ya existe: {name}')
        
        self.stdout.write(f'Total módulos creados: {created_count}')
        
        # Activar módulos para empresas existentes
        self.stdout.write('\nActivando módulos para empresas...')
        
        companies = Company.objects.filter(is_active=True)
        activated_count = 0
        
        for company in companies:
            self.stdout.write(f'\nProcesando empresa: {company.name}')
            
            # Obtener módulos disponibles para esta empresa
            available_modules = SystemModule.objects.filter(is_available=True)
            
            for module in available_modules:
                # Verificar si el módulo puede activarse para esta empresa
                if module.can_be_activated_for_company(company):
                    company_module, created = CompanyModule.objects.get_or_create(
                        company=company,
                        module=module,
                        defaults={
                            'is_enabled': True,
                            'enabled_by_id': company.created_by_id,
                        }
                    )
                    if created:
                        activated_count += 1
                        self.stdout.write(f'  + Activado: {module.name}')
                    else:
                        self.stdout.write(f'  - Ya activo: {module.name}')
                else:
                    self.stdout.write(f'  x No disponible: {module.name} (requiere {module.requires_company_category})')
        
        self.stdout.write(f'\nTotal activaciones: {activated_count}')
        self.stdout.write('Inicializacion completada exitosamente!')