"""
Comando para otorgar permisos completos a todos los usuarios admin en todos los módulos.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import Company
from core.models_modules import SystemModule, CompanyModule, UserModulePermission

User = get_user_model()


class Command(BaseCommand):
    help = 'Otorga permisos completos a usuarios admin en todos los módulos de todas las empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Usuario específico (opcional, por defecto aplica a todos los admin)',
            default=None
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            with transaction.atomic():
                # Obtener usuarios admin
                if username:
                    admin_users = User.objects.filter(username=username, role__in=['superadmin', 'admin'])
                    if not admin_users.exists():
                        self.stdout.write(
                            self.style.ERROR(f'Usuario {username} no encontrado o no es admin')
                        )
                        return
                else:
                    admin_users = User.objects.filter(role__in=['superadmin', 'admin'])
                
                # Obtener todas las empresas
                companies = Company.objects.filter(is_active=True)
                
                # Obtener todos los módulos disponibles
                modules = SystemModule.objects.filter(is_available=True)
                
                total_permissions_created = 0
                total_permissions_updated = 0
                
                for admin_user in admin_users:
                    self.stdout.write(f'\n=== Procesando usuario: {admin_user.username} ===')
                    
                    for company in companies:
                        # Verificar que el usuario tenga acceso a la empresa
                        if not admin_user.can_access_company(company):
                            continue
                            
                        self.stdout.write(f'  Empresa: {company.name}')
                        
                        for module in modules:
                            # Verificar si el módulo puede ser activado para esta empresa
                            if not module.can_be_activated_for_company(company):
                                continue
                            
                            # Asegurar que el módulo esté activado para la empresa
                            company_module, created = CompanyModule.objects.get_or_create(
                                company=company,
                                module=module,
                                defaults={
                                    'is_enabled': True,
                                    'enabled_by': admin_user,
                                }
                            )
                            
                            if not company_module.is_enabled:
                                company_module.is_enabled = True
                                company_module.save()
                            
                            # Crear o actualizar permisos del usuario
                            user_permission, perm_created = UserModulePermission.objects.get_or_create(
                                user=admin_user,
                                company_module=company_module,
                                defaults={
                                    'permission_level': 'admin',
                                    'granted_by': admin_user,
                                }
                            )
                            
                            if perm_created:
                                total_permissions_created += 1
                                self.stdout.write(f'    + Creado permiso: {module.name}')
                            else:
                                # Actualizar permisos existentes para asegurar acceso completo
                                if user_permission.permission_level != 'admin':
                                    user_permission.permission_level = 'admin'
                                    user_permission.save()
                                    total_permissions_updated += 1
                                    self.stdout.write(f'    ~ Actualizado permiso: {module.name}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nProceso completado:'
                        f'\n  - Permisos creados: {total_permissions_created}'
                        f'\n  - Permisos actualizados: {total_permissions_updated}'
                        f'\n  - Usuarios procesados: {admin_users.count()}'
                        f'\n  - Empresas procesadas: {companies.count()}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al otorgar permisos: {str(e)}')
            )