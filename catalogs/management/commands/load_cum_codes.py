"""
Management command to load CUM (Clasificación Única de Medicamentos) codes
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from catalogs.models import CUMSMedication
from decimal import Decimal
import csv


class Command(BaseCommand):
    help = 'Carga códigos CUM desde archivo CSV o crea datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Ruta al archivo CSV con códigos CUM',
        )
        parser.add_argument(
            '--sample',
            action='store_true',
            help='Crear datos de ejemplo en lugar de cargar desde archivo',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar todos los códigos CUM existentes antes de cargar',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Eliminando códigos CUM existentes...'))
            count = CUMSMedication.objects.all().count()
            CUMSMedication.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Eliminados {count} códigos CUM'))

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
        """Carga datos de ejemplo de medicamentos CUM comunes"""
        self.stdout.write('Creando datos de ejemplo de códigos CUM...')

        sample_medications = [
            # Analgésicos y antiinflamatorios
            ('19840247', 'ACETAMINOFEN', 'TABLETA', '500 MG', 'ACETAMINOFEN 500 MG TABLETA', 'ORAL', True, Decimal('200')),
            ('19840248', 'IBUPROFENO', 'TABLETA', '400 MG', 'IBUPROFENO 400 MG TABLETA', 'ORAL', True, Decimal('300')),
            ('19840249', 'NAPROXENO', 'TABLETA', '250 MG', 'NAPROXENO 250 MG TABLETA', 'ORAL', True, Decimal('350')),
            ('19840250', 'DICLOFENACO', 'TABLETA', '50 MG', 'DICLOFENACO 50 MG TABLETA', 'ORAL', True, Decimal('400')),
            ('19840251', 'DIPIRONA', 'TABLETA', '500 MG', 'DIPIRONA 500 MG TABLETA', 'ORAL', True, Decimal('250')),

            # Antibióticos
            ('19840301', 'AMOXICILINA', 'CAPSULA', '500 MG', 'AMOXICILINA 500 MG CAPSULA', 'ORAL', True, Decimal('500')),
            ('19840302', 'AMOXICILINA + ACIDO CLAVULANICO', 'TABLETA', '875/125 MG', 'AMOXICILINA + ACIDO CLAVULANICO 875/125 MG TABLETA', 'ORAL', True, Decimal('1200')),
            ('19840303', 'AZITROMICINA', 'TABLETA', '500 MG', 'AZITROMICINA 500 MG TABLETA', 'ORAL', True, Decimal('1500')),
            ('19840304', 'CIPROFLOXACINA', 'TABLETA', '500 MG', 'CIPROFLOXACINA 500 MG TABLETA', 'ORAL', True, Decimal('800')),
            ('19840305', 'CEFALEXINA', 'CAPSULA', '500 MG', 'CEFALEXINA 500 MG CAPSULA', 'ORAL', True, Decimal('600')),
            ('19840306', 'CLINDAMICINA', 'CAPSULA', '300 MG', 'CLINDAMICINA 300 MG CAPSULA', 'ORAL', True, Decimal('900')),

            # Antihipertensivos
            ('19840401', 'LOSARTAN', 'TABLETA', '50 MG', 'LOSARTAN 50 MG TABLETA', 'ORAL', True, Decimal('450')),
            ('19840402', 'ENALAPRIL', 'TABLETA', '10 MG', 'ENALAPRIL 10 MG TABLETA', 'ORAL', True, Decimal('350')),
            ('19840403', 'AMLODIPINO', 'TABLETA', '5 MG', 'AMLODIPINO 5 MG TABLETA', 'ORAL', True, Decimal('400')),
            ('19840404', 'HIDROCLOROTIAZIDA', 'TABLETA', '25 MG', 'HIDROCLOROTIAZIDA 25 MG TABLETA', 'ORAL', True, Decimal('250')),
            ('19840405', 'METOPROLOL', 'TABLETA', '50 MG', 'METOPROLOL 50 MG TABLETA', 'ORAL', True, Decimal('600')),

            # Antidiabéticos
            ('19840501', 'METFORMINA', 'TABLETA', '850 MG', 'METFORMINA 850 MG TABLETA', 'ORAL', True, Decimal('300')),
            ('19840502', 'GLIBENCLAMIDA', 'TABLETA', '5 MG', 'GLIBENCLAMIDA 5 MG TABLETA', 'ORAL', True, Decimal('250')),
            ('19840503', 'INSULINA NPH', 'SUSPENSION INYECTABLE', '100 UI/ML', 'INSULINA NPH 100 UI/ML FRASCO 10 ML', 'PARENTERAL', True, Decimal('35000')),
            ('19840504', 'INSULINA CRISTALINA', 'SOLUCION INYECTABLE', '100 UI/ML', 'INSULINA CRISTALINA 100 UI/ML FRASCO 10 ML', 'PARENTERAL', True, Decimal('38000')),

            # Antiulcerosos
            ('19840601', 'OMEPRAZOL', 'CAPSULA', '20 MG', 'OMEPRAZOL 20 MG CAPSULA', 'ORAL', True, Decimal('400')),
            ('19840602', 'RANITIDINA', 'TABLETA', '150 MG', 'RANITIDINA 150 MG TABLETA', 'ORAL', True, Decimal('300')),
            ('19840603', 'ESOMEPRAZOL', 'CAPSULA', '40 MG', 'ESOMEPRAZOL 40 MG CAPSULA', 'ORAL', True, Decimal('1200')),

            # Antihistamínicos
            ('19840701', 'LORATADINA', 'TABLETA', '10 MG', 'LORATADINA 10 MG TABLETA', 'ORAL', True, Decimal('250')),
            ('19840702', 'CETIRIZINA', 'TABLETA', '10 MG', 'CETIRIZINA 10 MG TABLETA', 'ORAL', True, Decimal('300')),
            ('19840703', 'DIFENHIDRAMINA', 'TABLETA', '25 MG', 'DIFENHIDRAMINA 25 MG TABLETA', 'ORAL', True, Decimal('200')),

            # Corticoides
            ('19840801', 'PREDNISOLONA', 'TABLETA', '5 MG', 'PREDNISOLONA 5 MG TABLETA', 'ORAL', True, Decimal('350')),
            ('19840802', 'DEXAMETASONA', 'TABLETA', '0.5 MG', 'DEXAMETASONA 0.5 MG TABLETA', 'ORAL', True, Decimal('250')),
            ('19840803', 'HIDROCORTISONA', 'CREMA', '1%', 'HIDROCORTISONA 1% CREMA TUBO 30 G', 'TOPICA', True, Decimal('8000')),

            # Vitaminas y suplementos
            ('19840901', 'ACIDO FOLICO', 'TABLETA', '1 MG', 'ACIDO FOLICO 1 MG TABLETA', 'ORAL', True, Decimal('150')),
            ('19840902', 'COMPLEJO B', 'TABLETA', '', 'COMPLEJO B TABLETA', 'ORAL', True, Decimal('200')),
            ('19840903', 'SULFATO FERROSO', 'TABLETA', '300 MG', 'SULFATO FERROSO 300 MG TABLETA', 'ORAL', True, Decimal('180')),
            ('19840904', 'VITAMINA C', 'TABLETA', '500 MG', 'VITAMINA C 500 MG TABLETA', 'ORAL', True, Decimal('200')),

            # Anticoagulantes
            ('19841001', 'WARFARINA', 'TABLETA', '5 MG', 'WARFARINA 5 MG TABLETA', 'ORAL', True, Decimal('450')),
            ('19841002', 'ENOXAPARINA', 'JERINGA PRELLENADA', '40 MG/0.4 ML', 'ENOXAPARINA 40 MG/0.4 ML JERINGA PRELLENADA', 'PARENTERAL', True, Decimal('25000')),
            ('19841003', 'ACIDO ACETILSALICILICO', 'TABLETA', '100 MG', 'ACIDO ACETILSALICILICO (ASA) 100 MG TABLETA', 'ORAL', True, Decimal('150')),

            # Anticonvulsivantes
            ('19841101', 'ACIDO VALPROICO', 'TABLETA', '500 MG', 'ACIDO VALPROICO 500 MG TABLETA', 'ORAL', True, Decimal('800')),
            ('19841102', 'CARBAMAZEPINA', 'TABLETA', '200 MG', 'CARBAMAZEPINA 200 MG TABLETA', 'ORAL', True, Decimal('400')),
            ('19841103', 'FENITOINA', 'TABLETA', '100 MG', 'FENITOINA 100 MG TABLETA', 'ORAL', True, Decimal('350')),

            # Broncodilatadores
            ('19841201', 'SALBUTAMOL', 'INHALADOR', '100 MCG', 'SALBUTAMOL 100 MCG/DOSIS INHALADOR', 'INHALATORIA', True, Decimal('15000')),
            ('19841202', 'SALBUTAMOL', 'SOLUCION PARA NEBULIZAR', '5 MG/ML', 'SALBUTAMOL 5 MG/ML SOLUCION PARA NEBULIZAR', 'INHALATORIA', True, Decimal('12000')),
            ('19841203', 'IPRATROPIO', 'SOLUCION PARA NEBULIZAR', '0.25 MG/ML', 'IPRATROPIO 0.25 MG/ML SOLUCION PARA NEBULIZAR', 'INHALATORIA', True, Decimal('18000')),

            # Soluciones parenterales
            ('19841301', 'SOLUCION SALINA 0.9%', 'SOLUCION INYECTABLE', '500 ML', 'CLORURO DE SODIO 0.9% BOLSA 500 ML', 'PARENTERAL', True, Decimal('3500')),
            ('19841302', 'LACTATO DE RINGER', 'SOLUCION INYECTABLE', '500 ML', 'LACTATO DE RINGER BOLSA 500 ML', 'PARENTERAL', True, Decimal('3800')),
            ('19841303', 'DEXTROSA 5%', 'SOLUCION INYECTABLE', '500 ML', 'DEXTROSA 5% BOLSA 500 ML', 'PARENTERAL', True, Decimal('3500')),

            # Antiparasitarios
            ('19841401', 'ALBENDAZOL', 'TABLETA', '400 MG', 'ALBENDAZOL 400 MG TABLETA', 'ORAL', True, Decimal('500')),
            ('19841402', 'METRONIDAZOL', 'TABLETA', '500 MG', 'METRONIDAZOL 500 MG TABLETA', 'ORAL', True, Decimal('300')),

            # Antieméticos
            ('19841501', 'METOCLOPRAMIDA', 'TABLETA', '10 MG', 'METOCLOPRAMIDA 10 MG TABLETA', 'ORAL', True, Decimal('200')),
            ('19841502', 'ONDANSETRON', 'TABLETA', '8 MG', 'ONDANSETRON 8 MG TABLETA', 'ORAL', True, Decimal('1500')),
        ]

        created = 0
        with transaction.atomic():
            for code, active_ingredient, pharmaceutical_form, concentration, description, route, is_active, standard_price in sample_medications:
                medication, created_flag = CUMSMedication.objects.get_or_create(
                    code=code,
                    defaults={
                        'active_ingredient': active_ingredient,
                        'pharmaceutical_form': pharmaceutical_form,
                        'concentration': concentration,
                        'description': description,
                        'route_of_administration': route,
                        'is_active': is_active,
                        'standard_price': standard_price,
                    }
                )
                if created_flag:
                    created += 1
                    self.stdout.write(f'  Creado: {code} - {description}')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Proceso completado: {created} códigos CUM creados')
        )

    def load_from_csv(self, file_path):
        """
        Carga códigos CUM desde archivo CSV

        El archivo CSV debe tener las siguientes columnas:
        code, active_ingredient, pharmaceutical_form, concentration, description, route_of_administration, is_active, standard_price

        Ejemplo:
        19840247,ACETAMINOFEN,TABLETA,500 MG,ACETAMINOFEN 500 MG TABLETA,ORAL,1,200
        """
        self.stdout.write(f'Cargando códigos CUM desde {file_path}...')

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created = 0
                updated = 0

                with transaction.atomic():
                    for row in reader:
                        code = row['code'].strip()
                        active_ingredient = row['active_ingredient'].strip()
                        pharmaceutical_form = row.get('pharmaceutical_form', '').strip()
                        concentration = row.get('concentration', '').strip()
                        description = row.get('description', '').strip()
                        route = row.get('route_of_administration', 'ORAL').strip()
                        is_active = row.get('is_active', '1').strip() in ['1', 'True', 'true', 'TRUE']
                        standard_price = Decimal(row.get('standard_price', '0').strip())

                        medication, created_flag = CUMSMedication.objects.update_or_create(
                            code=code,
                            defaults={
                                'active_ingredient': active_ingredient,
                                'pharmaceutical_form': pharmaceutical_form,
                                'concentration': concentration,
                                'description': description,
                                'route_of_administration': route,
                                'is_active': is_active,
                                'standard_price': standard_price,
                            }
                        )

                        if created_flag:
                            created += 1
                            self.stdout.write(f'  Creado: {code} - {description}')
                        else:
                            updated += 1
                            self.stdout.write(f'  Actualizado: {code} - {description}')

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
