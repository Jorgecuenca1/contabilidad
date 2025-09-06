"""
Comando para cargar tipos de comprobantes contables colombianos.
"""

from django.core.management.base import BaseCommand
from accounting.models_journal import JournalType
from core.models import Company, User


class Command(BaseCommand):
    help = 'Carga tipos de comprobantes contables colombianos'

    def handle(self, *args, **options):
        self.stdout.write('Cargando tipos de comprobantes colombianos...')
        
        # Obtener usuario admin y empresas
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No se encontró usuario administrador'))
                return
            
            companies = Company.objects.filter(is_active=True)
            if not companies.exists():
                self.stdout.write(self.style.ERROR('No se encontraron empresas activas'))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al obtener datos base: {e}'))
            return
        
        # Tipos de comprobantes según normativa colombiana
        journal_types = [
            {
                'code': 'CI',
                'name': 'Comprobante de Ingreso',
                'description': 'Registra ingresos en efectivo, cheques, transferencias recibidas',
                'sequence_prefix': 'CI',
                'is_active': True
            },
            {
                'code': 'CE',
                'name': 'Comprobante de Egreso',
                'description': 'Registra pagos en efectivo, cheques, transferencias enviadas',
                'sequence_prefix': 'CE',
                'is_active': True
            },
            {
                'code': 'CG',
                'name': 'Comprobante General',
                'description': 'Asientos que no involucran movimiento de efectivo (ajustes, provisiones, etc.)',
                'sequence_prefix': 'CG',
                'is_active': True
            },
            {
                'code': 'CD',
                'name': 'Comprobante Diario',
                'description': 'Registro diario de operaciones rutinarias',
                'sequence_prefix': 'CD',
                'is_active': True
            },
            {
                'code': 'CF',
                'name': 'Comprobante de Facturación',
                'description': 'Registro de ventas y facturación a clientes',
                'sequence_prefix': 'CF',
                'is_active': True
            },
            {
                'code': 'CC',
                'name': 'Comprobante de Compras',
                'description': 'Registro de compras a proveedores',
                'sequence_prefix': 'CC',
                'is_active': True
            },
            {
                'code': 'CN',
                'name': 'Comprobante de Nómina',
                'description': 'Registro de nómina y prestaciones sociales',
                'sequence_prefix': 'CN',
                'is_active': True
            },
            {
                'code': 'CB',
                'name': 'Comprobante Bancario',
                'description': 'Conciliaciones bancarias y movimientos bancarios',
                'sequence_prefix': 'CB',
                'is_active': True
            },
            {
                'code': 'CA',
                'name': 'Comprobante de Ajuste',
                'description': 'Ajustes contables de fin de período',
                'sequence_prefix': 'CA',
                'is_active': True
            },
            {
                'code': 'CR',
                'name': 'Comprobante de Reversión',
                'description': 'Reversión de asientos contables',
                'sequence_prefix': 'CR',
                'is_active': True
            },
            {
                'code': 'CP',
                'name': 'Comprobante de Provisión',
                'description': 'Provisiones y estimaciones contables',
                'sequence_prefix': 'CP',
                'is_active': True
            },
            {
                'code': 'CT',
                'name': 'Comprobante de Traslado',
                'description': 'Traslados entre cuentas y reclasificaciones',
                'sequence_prefix': 'CT',
                'is_active': True
            },
            {
                'code': 'CX',
                'name': 'Comprobante de Cierre',
                'description': 'Asientos de cierre de período contable',
                'sequence_prefix': 'CX',
                'is_active': True
            },
            {
                'code': 'CO',
                'name': 'Comprobante de Apertura',
                'description': 'Asientos de apertura de nuevo período contable',
                'sequence_prefix': 'CO',
                'is_active': True
            },
            {
                'code': 'CK',
                'name': 'Comprobante de Inventario',
                'description': 'Ajustes y movimientos de inventarios',
                'sequence_prefix': 'CK',
                'is_active': True
            },
            {
                'code': 'CS',
                'name': 'Comprobante de Seguridad Social',
                'description': 'Aportes a seguridad social y parafiscales',
                'sequence_prefix': 'CS',
                'is_active': True
            },
            {
                'code': 'CV',
                'name': 'Comprobante de Ventas',
                'description': 'Registro específico de ventas por canal',
                'sequence_prefix': 'CV',
                'is_active': True
            },
            {
                'code': 'CM',
                'name': 'Comprobante Manual',
                'description': 'Asientos manuales diversos',
                'sequence_prefix': 'CM',
                'is_active': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        # Crear tipos de comprobante para cada empresa
        for company in companies:
            self.stdout.write(f'\n📋 Procesando empresa: {company.name}')
            
            for journal_type_data in journal_types:
                # Agregar company y created_by
                journal_type_data_with_company = journal_type_data.copy()
                journal_type_data_with_company['company'] = company
                journal_type_data_with_company['created_by'] = admin_user
                
                journal_type, created = JournalType.objects.get_or_create(
                    company=company,
                    code=journal_type_data['code'],
                    defaults=journal_type_data_with_company
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Creado: {journal_type.code} - {journal_type.name}')
                    )
                else:
                    # Actualizar si ya existe
                    for key, value in journal_type_data.items():
                        setattr(journal_type, key, value)
                    journal_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ↻ Actualizado: {journal_type.code} - {journal_type.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado:'
                f'\n   • {created_count} tipos de comprobante creados'
                f'\n   • {updated_count} tipos de comprobante actualizados'
                f'\n   • Total: {created_count + updated_count} tipos de comprobante disponibles'
            )
        )
        
        # Mostrar resumen de tipos
        self.stdout.write('\n📋 TIPOS DE COMPROBANTES DISPONIBLES:')
        self.stdout.write('=' * 60)
        
        for jtype in JournalType.objects.filter(is_active=True).order_by('code'):
            self.stdout.write(f'{jtype.code:3} - {jtype.name:25} | {jtype.description}')
        
        self.stdout.write('=' * 60)
        self.stdout.write('💡 Estos comprobantes cubren todas las necesidades contables colombianas')
        self.stdout.write('💡 Cada tipo genera numeración automática independiente')
