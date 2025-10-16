"""
Management command para cargar módulos de salud en el sistema
"""

from django.core.management.base import BaseCommand
from core.models_modules import SystemModule


class Command(BaseCommand):
    help = 'Carga los módulos de salud en el sistema'

    def handle(self, *args, **options):
        self.stdout.write('Cargando módulos de salud...')

        # Módulos de salud a crear
        health_modules = [
            {
                'code': 'patients',
                'name': 'Gestión de Pacientes',
                'description': 'Gestión maestro de pacientes con datos demográficos, EPS, consentimientos y búsqueda avanzada',
                'category': 'healthcare',
                'url_pattern': 'patients',
                'icon_class': 'bi-people-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'diagnostics',
                'name': 'Diagnósticos CIE-10',
                'description': 'Catálogo completo de diagnósticos médicos CIE-10 con importador y búsqueda',
                'category': 'healthcare',
                'url_pattern': 'diagnostics',
                'icon_class': 'bi-clipboard2-pulse',
                'requires_company_category': 'salud',
            },
            {
                'code': 'catalogs',
                'name': 'Catálogos CUPS/CUMS',
                'description': 'Catálogos centralizados de procedimientos (CUPS) y medicamentos (CUMS)',
                'category': 'healthcare',
                'url_pattern': 'catalogs',
                'icon_class': 'bi-book',
                'requires_company_category': 'salud',
            },
            {
                'code': 'rips',
                'name': 'Generador RIPS',
                'description': 'Generación automática de archivos RIPS según normativa colombiana (Res. 3374/2000)',
                'category': 'healthcare',
                'url_pattern': 'rips',
                'icon_class': 'bi-file-earmark-medical',
                'requires_company_category': 'salud',
            },
            {
                'code': 'emergency',
                'name': 'Urgencias',
                'description': 'Módulo de urgencias médicas con triage y admisión',
                'category': 'healthcare',
                'url_pattern': 'emergency',
                'icon_class': 'bi-heart-pulse-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'hospitalization',
                'name': 'Hospitalización',
                'description': 'Gestión de camas, ingresos, egresos y control de estancias',
                'category': 'healthcare',
                'url_pattern': 'hospitalization',
                'icon_class': 'bi-hospital',
                'requires_company_category': 'salud',
            },
            {
                'code': 'surgery',
                'name': 'Cirugías y Quirófano',
                'description': 'Programación quirúrgica, control de salas, notas de anestesia y trazabilidad',
                'category': 'healthcare',
                'url_pattern': 'surgery',
                'icon_class': 'bi-scissors',
                'requires_company_category': 'salud',
            },
            {
                'code': 'blood_bank',
                'name': 'Banco de Sangre',
                'description': 'Gestión de donantes, cribado, compatibilidad e inventario de hemocomponentes',
                'category': 'healthcare',
                'url_pattern': 'blood-bank',
                'icon_class': 'bi-droplet-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'occupational_health',
                'name': 'Salud Ocupacional',
                'description': 'Exámenes de ingreso, periódicos, retiro, aptitud laboral y reportes empresariales',
                'category': 'healthcare',
                'url_pattern': 'occupational-health',
                'icon_class': 'bi-briefcase-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'imaging',
                'name': 'Imágenes Diagnósticas',
                'description': 'Radiología, TAC, ecografías, resonancias e integración DICOM',
                'category': 'healthcare',
                'url_pattern': 'imaging',
                'icon_class': 'bi-camera-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'ophthalmology',
                'name': 'Oftalmología',
                'description': 'Consulta oftalmológica especializada, agudeza visual y refracción',
                'category': 'healthcare',
                'url_pattern': 'ophthalmology',
                'icon_class': 'bi-eye-fill',
                'requires_company_category': 'salud',
            },
            {
                'code': 'dentistry',
                'name': 'Odontología',
                'description': 'Odontograma, piezas dentales y tratamientos odontológicos',
                'category': 'healthcare',
                'url_pattern': 'dentistry',
                'icon_class': 'bi-emoji-smile',
                'requires_company_category': 'salud',
            },
            {
                'code': 'psychology',
                'name': 'Psicología',
                'description': 'Consulta psicológica, sesiones terapéuticas y seguimiento',
                'category': 'healthcare',
                'url_pattern': 'psychology',
                'icon_class': 'bi-chat-heart',
                'requires_company_category': 'salud',
            },
            {
                'code': 'rehabilitation',
                'name': 'Rehabilitación',
                'description': 'Fisioterapia, sesiones de rehabilitación y planes de tratamiento',
                'category': 'healthcare',
                'url_pattern': 'rehabilitation',
                'icon_class': 'bi-activity',
                'requires_company_category': 'salud',
            },
            {
                'code': 'authorizations',
                'name': 'Autorizaciones EPS',
                'description': 'Gestión de solicitudes, aprobaciones y contrarreferencias con aseguradoras',
                'category': 'healthcare',
                'url_pattern': 'authorizations',
                'icon_class': 'bi-check-circle',
                'requires_company_category': 'salud',
            },
            {
                'code': 'pharmacy',
                'name': 'Farmacia',
                'description': 'Inventario de medicamentos, dispensación y control de lotes y vencimientos',
                'category': 'healthcare',
                'url_pattern': 'pharmacy',
                'icon_class': 'bi-capsule',
                'requires_company_category': 'salud',
            },
            {
                'code': 'billing_health',
                'name': 'Facturación Salud',
                'description': 'Facturación de servicios de salud vinculada a RIPS',
                'category': 'healthcare',
                'url_pattern': 'billing-health',
                'icon_class': 'bi-receipt',
                'requires_company_category': 'salud',
            },
            {
                'code': 'health_reports',
                'name': 'Reportes Clínicos',
                'description': 'Productividad médica, morbilidad CIE-10, tiempos de espera e indicadores',
                'category': 'healthcare',
                'url_pattern': 'health-reports',
                'icon_class': 'bi-graph-up',
                'requires_company_category': 'salud',
            },
            {
                'code': 'telemedicine',
                'name': 'Telemedicina',
                'description': 'Consultas virtuales y atención domiciliaria con firma digital',
                'category': 'healthcare',
                'url_pattern': 'telemedicine',
                'icon_class': 'bi-laptop',
                'requires_company_category': 'salud',
            },
            # Módulos de salud existentes
            {
                'code': 'gynecology',
                'name': 'Ginecología',
                'description': 'Historia clínica ginecológica especializada y controles prenatales',
                'category': 'healthcare',
                'url_pattern': 'gynecology',
                'icon_class': 'bi-gender-female',
                'requires_company_category': 'salud',
            },
            {
                'code': 'laboratory',
                'name': 'Laboratorio Clínico',
                'description': 'Órdenes de laboratorio, procesamiento de muestras y resultados',
                'category': 'healthcare',
                'url_pattern': 'laboratory',
                'icon_class': 'bi-flask',
                'requires_company_category': 'salud',
            },
            {
                'code': 'medical_records',
                'name': 'Historias Clínicas',
                'description': 'Historia clínica electrónica completa con diagnósticos y prescripciones',
                'category': 'healthcare',
                'url_pattern': 'medical-records',
                'icon_class': 'bi-file-medical',
                'requires_company_category': 'salud',
            },
            {
                'code': 'medical_appointments',
                'name': 'Citas Médicas',
                'description': 'Agenda médica, agendamiento y control de asistencia',
                'category': 'healthcare',
                'url_pattern': 'medical-appointments',
                'icon_class': 'bi-calendar-check',
                'requires_company_category': 'salud',
            },
            {
                'code': 'medical_procedures',
                'name': 'Procedimientos Médicos',
                'description': 'Catálogo de procedimientos con tarifas y autorización de servicios',
                'category': 'healthcare',
                'url_pattern': 'medical-procedures',
                'icon_class': 'bi-bandaid',
                'requires_company_category': 'salud',
            },
        ]

        created_count = 0
        updated_count = 0

        for module_data in health_modules:
            module, created = SystemModule.objects.update_or_create(
                code=module_data['code'],
                defaults={
                    'name': module_data['name'],
                    'description': module_data['description'],
                    'category': module_data['category'],
                    'url_pattern': module_data['url_pattern'],
                    'icon_class': module_data['icon_class'],
                    'requires_company_category': module_data.get('requires_company_category', ''),
                    'is_available': True,
                    'is_core_module': False,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] Creado: {module.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  [*] Actualizado: {module.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n[OK] Proceso completado:'))
        self.stdout.write(self.style.SUCCESS(f'  - Modulos creados: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  - Modulos actualizados: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  - Total: {created_count + updated_count}'))
