"""
Management command to load CUPS (Clasificación Única de Procedimientos en Salud) codes
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from catalogs.models import CUPSProcedure
from decimal import Decimal
import csv


class Command(BaseCommand):
    help = 'Carga códigos CUPS desde archivo CSV o crea datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Ruta al archivo CSV con códigos CUPS',
        )
        parser.add_argument(
            '--sample',
            action='store_true',
            help='Crear datos de ejemplo en lugar de cargar desde archivo',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar todos los códigos CUPS existentes antes de cargar',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Eliminando códigos CUPS existentes...'))
            count = CUPSProcedure.objects.all().count()
            CUPSProcedure.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Eliminados {count} códigos CUPS'))

        if options['sample']:
            self.load_sample_data()
        elif options['file']:
            self.load_from_csv(options['file'])
        else:
            self.stdout.write(
                self.style.ERROR('Debe especificar --sample o --file <ruta>')
            )
            return

    def load_sample_data(self):
        """Carga datos de ejemplo de procedimientos CUPS comunes"""
        self.stdout.write('Creando datos de ejemplo de códigos CUPS...')

        sample_procedures = [
            # Consultas
            ('890201', 'CONSULTA DE PRIMERA VEZ POR MEDICINA GENERAL', 'Consulta médica general primera vez', True, Decimal('35000')),
            ('890202', 'CONSULTA DE PRIMERA VEZ POR MEDICINA ESPECIALIZADA', 'Consulta médica especializada primera vez', True, Decimal('60000')),
            ('890301', 'CONSULTA DE CONTROL O DE SEGUIMIENTO POR MEDICINA GENERAL', 'Consulta de control medicina general', True, Decimal('30000')),
            ('890302', 'CONSULTA DE CONTROL O DE SEGUIMIENTO POR MEDICINA ESPECIALIZADA', 'Consulta de control medicina especializada', True, Decimal('50000')),

            # Procedimientos de enfermería
            ('890601', 'CURACION DE HERIDAS SIMPLES', 'Curación de heridas simples', True, Decimal('15000')),
            ('890602', 'CURACION DE HERIDAS COMPLEJAS', 'Curación de heridas complejas', True, Decimal('25000')),
            ('890603', 'TOMA DE SIGNOS VITALES', 'Toma de signos vitales', True, Decimal('8000')),
            ('890604', 'APLICACION DE INYECCION INTRAMUSCULAR', 'Aplicación de inyección intramuscular', True, Decimal('10000')),
            ('890605', 'APLICACION DE INYECCION INTRAVENOSA', 'Aplicación de inyección intravenosa', True, Decimal('12000')),

            # Laboratorio clínico
            ('902210', 'CUADRO HEMATICO (HEMOGRAMA)', 'Hemograma completo', True, Decimal('15000')),
            ('902211', 'GLUCEMIA', 'Glicemia en ayunas', True, Decimal('8000')),
            ('902213', 'CREATININA', 'Creatinina sérica', True, Decimal('10000')),
            ('902215', 'COLESTEROL TOTAL', 'Colesterol total', True, Decimal('9000')),
            ('902216', 'COLESTEROL HDL', 'Colesterol HDL', True, Decimal('12000')),
            ('902217', 'COLESTEROL LDL', 'Colesterol LDL', True, Decimal('12000')),
            ('902218', 'TRIGLICERIDOS', 'Triglicéridos', True, Decimal('10000')),
            ('902250', 'PARCIAL DE ORINA', 'Uroanálisis', True, Decimal('8000')),

            # Imágenes diagnósticas
            ('870201', 'RADIOGRAFIA DE TORAX', 'Radiografía de tórax PA y lateral', True, Decimal('25000')),
            ('870202', 'RADIOGRAFIA DE ABDOMEN', 'Radiografía de abdomen simple', True, Decimal('25000')),
            ('870301', 'ECOGRAFIA OBSTETRICA', 'Ecografía obstétrica', True, Decimal('40000')),
            ('870302', 'ECOGRAFIA ABDOMINAL TOTAL', 'Ecografía abdominal total', True, Decimal('45000')),
            ('870401', 'TOMOGRAFIA AXIAL COMPUTARIZADA DE CRANEO SIN CONTRASTE', 'TAC de cráneo simple', True, Decimal('150000')),
            ('870402', 'TOMOGRAFIA AXIAL COMPUTARIZADA DE ABDOMEN SIN CONTRASTE', 'TAC de abdomen simple', True, Decimal('180000')),

            # Procedimientos quirúrgicos comunes
            ('661100', 'APENDICECTOMIA', 'Apendicectomía', True, Decimal('2500000')),
            ('741500', 'CESAREA', 'Cesárea', True, Decimal('3000000')),
            ('660100', 'COLECISTECTOMIA', 'Colecistectomía', True, Decimal('3500000')),
            ('330100', 'TRAQUEOSTOMIA', 'Traqueostomía', True, Decimal('1200000')),

            # Urgencias
            ('230101', 'ATENCION DE PARTO NORMAL', 'Atención de parto vaginal', True, Decimal('1500000')),
            ('998710', 'REANIMACION CARDIOPULMONAR BASICA', 'RCP básica', True, Decimal('100000')),
            ('998711', 'REANIMACION CARDIOPULMONAR AVANZADA', 'RCP avanzada', True, Decimal('200000')),

            # Odontología
            ('997101', 'CONSULTA ODONTOLOGICA DE PRIMERA VEZ', 'Consulta odontológica primera vez', True, Decimal('25000')),
            ('997102', 'CONSULTA ODONTOLOGICA DE CONTROL', 'Consulta odontológica de control', True, Decimal('20000')),
            ('997310', 'EXODONCIA DE DIENTE PERMANENTE', 'Extracción dental', True, Decimal('40000')),
            ('997311', 'OBTURACION DENTAL', 'Obturación (calza)', True, Decimal('35000')),
            ('997312', 'PROFILAXIS Y CONTROL DE PLACA BACTERIANA', 'Limpieza dental', True, Decimal('30000')),

            # Fisioterapia
            ('931101', 'EVALUACION Y DIAGNOSTICO POR FISIOTERAPIA', 'Evaluación fisioterapéutica', True, Decimal('35000')),
            ('931102', 'SESION DE FISIOTERAPIA', 'Sesión de fisioterapia', True, Decimal('25000')),
            ('931103', 'TERAPIA RESPIRATORIA', 'Terapia respiratoria', True, Decimal('30000')),

            # Psicología
            ('890801', 'PSICOTERAPIA INDIVIDUAL', 'Psicoterapia individual', True, Decimal('50000')),
            ('890802', 'PSICOTERAPIA DE GRUPO', 'Psicoterapia grupal', True, Decimal('30000')),

            # Vacunación
            ('993101', 'APLICACION DE VACUNA', 'Aplicación de vacuna', True, Decimal('15000')),
        ]

        created = 0
        with transaction.atomic():
            for code, name, description, is_active, standard_price in sample_procedures:
                procedure, created_flag = CUPSProcedure.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'description': description,
                        'is_active': is_active,
                        'standard_price': standard_price,
                    }
                )
                if created_flag:
                    created += 1
                    self.stdout.write(f'  Creado: {code} - {name}')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Proceso completado: {created} códigos CUPS creados')
        )

    def load_from_csv(self, file_path):
        """
        Carga códigos CUPS desde archivo CSV

        El archivo CSV debe tener las siguientes columnas:
        code, name, description, is_active, standard_price

        Ejemplo:
        890201,CONSULTA DE PRIMERA VEZ POR MEDICINA GENERAL,Consulta médica general primera vez,1,35000
        """
        self.stdout.write(f'Cargando códigos CUPS desde {file_path}...')

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created = 0
                updated = 0

                with transaction.atomic():
                    for row in reader:
                        code = row['code'].strip()
                        name = row['name'].strip()
                        description = row.get('description', '').strip()
                        is_active = row.get('is_active', '1').strip() in ['1', 'True', 'true', 'TRUE']
                        standard_price = Decimal(row.get('standard_price', '0').strip())

                        procedure, created_flag = CUPSProcedure.objects.update_or_create(
                            code=code,
                            defaults={
                                'name': name,
                                'description': description,
                                'is_active': is_active,
                                'standard_price': standard_price,
                            }
                        )

                        if created_flag:
                            created += 1
                            self.stdout.write(f'  Creado: {code} - {name}')
                        else:
                            updated += 1
                            self.stdout.write(f'  Actualizado: {code} - {name}')

                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Proceso completado: {created} códigos creados, {updated} actualizados'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Error: No se encontró el archivo {file_path}')
            )
        except KeyError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: Falta la columna {e} en el archivo CSV')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al procesar el archivo: {str(e)}')
            )
