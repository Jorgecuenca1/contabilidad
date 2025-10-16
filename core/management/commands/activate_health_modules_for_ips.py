"""
Management command para activar automáticamente módulos de salud
para empresas categoría 'salud' (IPS)
"""

from django.core.management.base import BaseCommand
from core.models import Company, User
from core.models_modules import SystemModule, CompanyModule


class Command(BaseCommand):
    help = 'Activa automáticamente módulos de salud para empresas IPS'

    def handle(self, *args, **options):
        self.stdout.write('Activando módulos de salud para empresas IPS...\n')

        # Obtener empresas de salud
        health_companies = Company.objects.filter(category='salud', is_active=True)

        if not health_companies.exists():
            self.stdout.write(self.style.WARNING('No se encontraron empresas de categoría "salud"'))
            return

        # Obtener módulos de salud
        health_modules = SystemModule.objects.filter(
            category='healthcare',
            is_available=True
        )

        if not health_modules.exists():
            self.stdout.write(self.style.WARNING('No se encontraron módulos de salud'))
            self.stdout.write(self.style.WARNING('Ejecuta primero: python manage.py load_health_modules'))
            return

        # Obtener un superadmin para asignar como 'enabled_by'
        admin_user = User.objects.filter(role='superadmin').first()
        if not admin_user:
            admin_user = User.objects.filter(role='admin').first()

        if not admin_user:
            self.stdout.write(self.style.ERROR('No se encontró un usuario administrador'))
            return

        total_activated = 0
        total_already_active = 0

        for company in health_companies:
            self.stdout.write(f'\n  Empresa: {company.name}')
            self.stdout.write(f'  Categoria: {company.get_category_display()}')

            activated_count = 0
            already_active_count = 0

            for module in health_modules:
                # Verificar si el módulo puede activarse para esta empresa
                if not module.can_be_activated_for_company(company):
                    continue

                # Crear o actualizar el módulo de empresa
                company_module, created = CompanyModule.objects.get_or_create(
                    company=company,
                    module=module,
                    defaults={
                        'is_enabled': True,
                        'enabled_by': admin_user,
                    }
                )

                if created:
                    activated_count += 1
                    total_activated += 1
                    self.stdout.write(self.style.SUCCESS(f'    [+] {module.name}'))
                else:
                    if not company_module.is_enabled:
                        company_module.is_enabled = True
                        company_module.save()
                        activated_count += 1
                        total_activated += 1
                        self.stdout.write(self.style.SUCCESS(f'    [+] {module.name} (reactivado)'))
                    else:
                        already_active_count += 1
                        total_already_active += 1

            self.stdout.write(f'  Resumen: {activated_count} activados, {already_active_count} ya activos')

        self.stdout.write(self.style.SUCCESS(f'\n[OK] Proceso completado:'))
        self.stdout.write(self.style.SUCCESS(f'  - Empresas procesadas: {health_companies.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - Modulos activados: {total_activated}'))
        self.stdout.write(self.style.SUCCESS(f'  - Modulos ya activos: {total_already_active}'))
        self.stdout.write(self.style.SUCCESS(f'  - Total: {total_activated + total_already_active}'))
