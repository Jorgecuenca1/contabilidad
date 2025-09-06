"""
Comando para cargar datos faltantes después de las migraciones.
"""

from django.core.management.base import BaseCommand
from decimal import Decimal

from payroll.models_employee import EmployeeType
from taxes.models_tax_types import TaxType


class Command(BaseCommand):
    help = 'Carga datos faltantes para tipos de empleado e impuestos'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos faltantes...')
        
        # Crear tipos de empleado
        employee_types_data = [
            ('Empleado Tiempo Completo', 'Empleado de tiempo completo'),
            ('Empleado Medio Tiempo', 'Empleado de medio tiempo'),
            ('Contratista', 'Contratista independiente'),
            ('Aprendiz SENA', 'Aprendiz del SENA'),
            ('Practicante', 'Estudiante en práctica'),
        ]
        
        for name, description in employee_types_data:
            employee_type, created = EmployeeType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Tipo de empleado creado: {name}')
        
        # Crear tipos de impuesto
        tax_types_data = [
            ('IVA', 'Impuesto al Valor Agregado', 19.0, 'bimonthly'),
            ('Renta', 'Impuesto de Renta', 33.0, 'annual'),
            ('ICA', 'Impuesto de Industria y Comercio', 1.0, 'bimonthly'),
            ('Retención Fuente', 'Retención en la Fuente', 2.5, 'monthly'),
            ('Retención IVA', 'Retención de IVA', 15.0, 'monthly'),
            ('Retención ICA', 'Retención de ICA', 1.0, 'monthly'),
        ]
        
        for name, description, rate, frequency in tax_types_data:
            tax_type, created = TaxType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'rate': Decimal(str(rate)),
                    'frequency': frequency,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Tipo de impuesto creado: {name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Datos faltantes cargados exitosamente!'
            )
        )




