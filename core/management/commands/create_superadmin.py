"""
Comando para crear un superadministrador del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superadministrador del sistema con acceso completo a Django Admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario del superadmin',
            default='superadmin'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email del superadmin',
            default='superadmin@sistema.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña del superadmin',
            default='superadmin123'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Nombre del superadmin',
            default='Super'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Apellido del superadmin',
            default='Administrador'
        )
        parser.add_argument(
            '--document',
            type=str,
            help='Número de documento del superadmin',
            default='1000000000'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        document = options['document']

        try:
            with transaction.atomic():
                # Verificar si ya existe un superadmin
                if User.objects.filter(role='superadmin').exists():
                    existing_superadmin = User.objects.filter(role='superadmin').first()
                    self.stdout.write(
                        self.style.WARNING(
                            f'Ya existe un superadministrador: {existing_superadmin.username}'
                        )
                    )
                    return

                # Verificar si el username ya existe
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f'El usuario {username} ya existe'
                        )
                    )
                    return

                # Verificar si el documento ya existe
                if User.objects.filter(document_number=document).exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f'El documento {document} ya está registrado'
                        )
                    )
                    return

                # Crear el superadmin
                superadmin = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='superadmin',
                    document_number=document,
                    document_type='CC',
                    is_staff=True,  # Acceso a Django Admin
                    is_superuser=True,  # Permisos completos en Django Admin
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superadministrador creado exitosamente:'
                    )
                )
                self.stdout.write(f'  - Usuario: {superadmin.username}')
                self.stdout.write(f'  - Email: {superadmin.email}')
                self.stdout.write(f'  - Nombre: {superadmin.get_full_name()}')
                self.stdout.write(f'  - Rol: {superadmin.get_role_display()}')
                self.stdout.write(f'  - Django Admin: Sí')
                self.stdout.write(
                    self.style.WARNING(
                        f'  - Contraseña: {password} (¡Cámbiala inmediatamente!)'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el superadministrador: {str(e)}')
            )