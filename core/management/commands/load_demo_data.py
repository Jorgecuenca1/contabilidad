"""
Comando para cargar datos de demostración completos.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

from core.models import Company, Country, Currency, FiscalYear, Period
from accounting.models_accounts import AccountType, ChartOfAccounts, Account
from accounting.models_journal import JournalType, JournalEntry, JournalEntryLine
from accounts_receivable.models_customer import CustomerType, Customer
from accounts_receivable.models_invoice import Invoice, InvoiceLine
from accounts_payable.models_supplier import SupplierType, Supplier
from accounts_payable.models_bill import PurchaseInvoice, PurchaseInvoiceLine
from treasury.models_bank import Bank, BankAccount, CashAccount

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de demostración completos para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--companies',
            type=int,
            default=3,
            help='Número de empresas demo a crear'
        )

    def handle(self, *args, **options):
        self.stdout.write('Iniciando carga de datos de demostración...')
        
        # Crear datos base
        self.create_base_data()
        
        # Crear empresas demo
        companies_count = options['companies']
        for i in range(companies_count):
            self.create_demo_company(i + 1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Datos de demostración cargados exitosamente!\n'
                f'   - {companies_count} empresas creadas\n'
                f'   - Usuarios, clientes, proveedores y transacciones de ejemplo\n'
                f'   - Accede al admin con: admin/admin'
            )
        )

    def create_base_data(self):
        """Crear datos base del sistema."""
        self.stdout.write('Creando datos base...')
        
        # Países
        colombia, _ = Country.objects.get_or_create(
            code='CO',
            defaults={'name': 'Colombia'}
        )
        
        # Monedas
        cop, _ = Currency.objects.get_or_create(
            code='COP',
            defaults={'name': 'Peso Colombiano', 'symbol': '$'}
        )
        
        # Bancos
        banks_data = [
            ('001', 'Banco de Bogotá'),
            ('002', 'Banco Popular'),
            ('007', 'Bancolombia'),
            ('012', 'Banco BBVA'),
            ('013', 'Banco Davivienda'),
        ]
        
        for code, name in banks_data:
            Bank.objects.get_or_create(
                code=code,
                defaults={'name': name, 'country': colombia}
            )

    def create_demo_company(self, number):
        """Crear una empresa de demostración."""
        self.stdout.write(f'Creando empresa demo {number}...')
        
        # Datos de empresas demo
        companies_data = [
            {
                'name': 'Comercializadora ABC S.A.S.',
                'legal_name': 'COMERCIALIZADORA ABC SAS',
                'tax_id': '900123456'
            },
            {
                'name': 'Servicios Profesionales XYZ Ltda.',
                'legal_name': 'SERVICIOS PROFESIONALES XYZ LTDA',
                'tax_id': '900234567'
            },
            {
                'name': 'Manufactura Industrial DEF S.A.',
                'legal_name': 'MANUFACTURA INDUSTRIAL DEF SA',
                'tax_id': '900345678'
            }
        ]
        
        if number > len(companies_data):
            company_data = {
                'name': f'Empresa Demo {number} S.A.S.',
                'legal_name': f'EMPRESA DEMO {number} SAS',
                'tax_id': f'90{number:07d}'
            }
        else:
            company_data = companies_data[number - 1]
        
        # Crear empresa
        country = Country.objects.get(code='CO')
        currency = Currency.objects.get(code='COP')
        
        # Crear usuario admin si no existe
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@sistema.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'document_number': '12345678',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if _:
            admin_user.set_password('admin')
            admin_user.save()
        
        company, created = Company.objects.get_or_create(
            tax_id=company_data['tax_id'],
            defaults={
                'name': company_data['name'],
                'legal_name': company_data['legal_name'],
                'tax_id_dv': '1',
                'country': country,
                'functional_currency': 'COP',
                'regime': 'common',
                'sector': 'private',
                'fiscal_year_start': date(timezone.now().year, 1, 1),
                'fiscal_year_end': date(timezone.now().year, 12, 31),
                'legal_representative': 'Representante Legal',
                'legal_rep_document': '12345678',
                'address': 'Calle 123 # 45-67',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'phone': '+57 1 234 5678',
                'email': f'info@empresa{number}.com',
                'website': f'www.empresa{number}.com',
                'created_by': admin_user
            }
        )
        
        if not created:
            self.stdout.write(f'  Empresa {company.name} ya existe, saltando...')
            return
        
        # Crear plan de cuentas
        chart = ChartOfAccounts.objects.create(
            company=company,
            name='Plan Único de Cuentas - PUC Colombia',
            description='Plan de cuentas basado en el PUC colombiano',
            created_by=admin_user
        )
        
        # Crear cuentas básicas
        self.create_basic_accounts(chart)
        
        # Crear año fiscal y períodos
        self.create_fiscal_periods(company)
        
        # Crear tipos de diario
        self.create_journal_types(company)
        
        # Crear datos transaccionales
        self.create_customers(company, 5)
        self.create_suppliers(company, 3)
        self.create_bank_accounts(company, 2)
        self.create_sample_transactions(company)

    def create_basic_accounts(self, chart):
        """Crear cuentas contables básicas."""
        # Primero crear los tipos de cuenta si no existen
        account_types_data = [
            ('asset', 'Activo', 'debit', True, False),
            ('liability', 'Pasivo', 'credit', True, False),
            ('equity', 'Patrimonio', 'credit', True, False),
            ('income', 'Ingresos', 'credit', False, True),
            ('expense', 'Gastos', 'debit', False, True),
            ('cost', 'Costos', 'debit', False, True),
        ]
        
        for type_code, type_name, nature, is_balance_sheet, is_income_statement in account_types_data:
            AccountType.objects.get_or_create(
                code=type_code,
                defaults={
                    'name': type_name,
                    'nature': nature,
                    'is_balance_sheet': is_balance_sheet,
                    'is_income_statement': is_income_statement
                }
            )
        
        accounts_data = [
            # ACTIVOS
            ('1', 'ACTIVO', 'asset', False),
            ('11', 'DISPONIBLE', 'asset', False),
            ('1105', 'CAJA', 'asset', False),
            ('110505', 'Caja General', 'asset', True),
            ('1110', 'BANCOS', 'asset', False),
            ('111005', 'Bancos Nacionales', 'asset', True),
            ('13', 'DEUDORES', 'asset', False),
            ('1305', 'CLIENTES', 'asset', False),
            ('130505', 'Clientes Nacionales', 'asset', True),
            
            # PASIVOS
            ('2', 'PASIVO', 'liability', False),
            ('22', 'PROVEEDORES', 'liability', False),
            ('2205', 'PROVEEDORES NACIONALES', 'liability', False),
            ('220505', 'Proveedores Nacionales', 'liability', True),
            ('24', 'IMPUESTOS GRAVÁMENES Y TASAS', 'liability', False),
            ('2408', 'IMPUESTO SOBRE LAS VENTAS POR PAGAR', 'liability', False),
            ('240801', 'IVA Generado', 'liability', True),
            
            # PATRIMONIO
            ('3', 'PATRIMONIO', 'equity', False),
            ('31', 'CAPITAL SOCIAL', 'equity', False),
            ('3105', 'CAPITAL SUSCRITO Y PAGADO', 'equity', False),
            ('310505', 'Capital Autorizado', 'equity', True),
            
            # INGRESOS
            ('4', 'INGRESOS', 'income', False),
            ('41', 'OPERACIONALES', 'income', False),
            ('4135', 'COMERCIO AL POR MAYOR Y AL POR MENOR', 'income', False),
            ('413505', 'Venta de Mercancías', 'income', True),
            
            # GASTOS
            ('5', 'GASTOS', 'expense', False),
            ('51', 'OPERACIONALES DE ADMINISTRACIÓN', 'expense', False),
            ('5105', 'GASTOS DE PERSONAL', 'expense', False),
            ('510506', 'Sueldos', 'expense', True),
        ]
        
        admin_user = User.objects.get(username='admin')
        
        for code, name, account_type_code, is_detail in accounts_data:
            account_type = AccountType.objects.get(code=account_type_code)
            Account.objects.get_or_create(
                chart_of_accounts=chart,
                code=code,
                defaults={
                    'name': name,
                    'account_type': account_type,
                    'is_detail': is_detail,
                    'level': len(code),
                    'created_by': admin_user
                }
            )

    def create_fiscal_periods(self, company):
        """Crear año fiscal y períodos."""
        current_year = timezone.now().year
        
        fiscal_year = FiscalYear.objects.create(
            company=company,
            year=current_year,
            start_date=date(current_year, 1, 1),
            end_date=date(current_year, 12, 31),
            status='open'
        )
        
        # Crear períodos mensuales
        for month in range(1, 13):
            if month == 12:
                end_date = date(current_year, 12, 31)
            else:
                end_date = date(current_year, month + 1, 1) - timedelta(days=1)
            
            Period.objects.create(
                fiscal_year=fiscal_year,
                name=f'{current_year}-{month:02d}',
                start_date=date(current_year, month, 1),
                end_date=end_date,
                status='open'
            )

    def create_journal_types(self, company):
        """Crear tipos de diario."""
        journal_types = [
            ('VEN', 'Ventas', 'Registro de facturas de venta'),
            ('COM', 'Compras', 'Registro de facturas de compra'),
            ('REC', 'Recibos de Caja', 'Registro de pagos recibidos'),
            ('PAG', 'Pagos', 'Registro de pagos realizados'),
            ('GEN', 'General', 'Asientos contables generales'),
        ]
        
        for code, name, description in journal_types:
            JournalType.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'description': description
                }
            )

    def create_customers(self, company, count):
        """Crear clientes de ejemplo."""
        customer_type = CustomerType.objects.get_or_create(
            company=company,
            name='Cliente Regular',
            defaults={'description': 'Cliente regular del negocio'}
        )[0]
        
        customers_data = [
            ('C001', 'Juan Pérez', '12345678', 'juan@email.com'),
            ('C002', 'María García', '87654321', 'maria@email.com'),
            ('C003', 'Carlos López', '11223344', 'carlos@email.com'),
            ('C004', 'Ana Martínez', '44332211', 'ana@email.com'),
            ('C005', 'Luis Rodríguez', '55667788', 'luis@email.com'),
        ]
        
        for i in range(min(count, len(customers_data))):
            code, name, tax_id, email = customers_data[i]
            Customer.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'customer_type': customer_type,
                    'legal_name': name,
                    'tax_id': tax_id,
                    'email': email,
                    'phone': f'+57 300 {random.randint(1000000, 9999999)}',
                    'address': f'Dirección {i+1}',
                    'city': 'Bogotá'
                }
            )

    def create_suppliers(self, company, count):
        """Crear proveedores de ejemplo."""
        supplier_type = SupplierType.objects.get_or_create(
            company=company,
            name='Proveedor Regular',
            defaults={'description': 'Proveedor regular del negocio'}
        )[0]
        
        suppliers_data = [
            ('P001', 'Distribuidora XYZ S.A.S.', '900111222', 'ventas@xyz.com'),
            ('P002', 'Suministros ABC Ltda.', '900333444', 'info@abc.com'),
            ('P003', 'Comercial DEF S.A.', '900555666', 'contacto@def.com'),
        ]
        
        for i in range(min(count, len(suppliers_data))):
            code, name, tax_id, email = suppliers_data[i]
            Supplier.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'supplier_type': supplier_type,
                    'legal_name': name,
                    'tax_id': tax_id,
                    'email': email,
                    'phone': f'+57 1 {random.randint(2000000, 9999999)}',
                    'address': f'Dirección Proveedor {i+1}',
                    'city': 'Bogotá'
                }
            )

    def create_bank_accounts(self, company, count):
        """Crear cuentas bancarias de ejemplo."""
        banks = Bank.objects.all()[:count]
        
        for i, bank in enumerate(banks):
            BankAccount.objects.get_or_create(
                company=company,
                bank=bank,
                account_number=f'123456789{i}',
                defaults={
                    'account_name': f'Cuenta Corriente {i+1}',
                    'account_type': 'checking',
                    'currency': company.functional_currency,
                    'is_active': True
                }
            )
        
        # Crear cuenta de caja
        CashAccount.objects.get_or_create(
            company=company,
            name='Caja General',
            defaults={
                'description': 'Caja general de la empresa',
                'currency': company.functional_currency,
                'is_active': True
            }
        )

    def create_sample_transactions(self, company):
        """Crear transacciones de ejemplo."""
        # Obtener datos necesarios
        customers = Customer.objects.filter(company=company)
        suppliers = Supplier.objects.filter(company=company)
        
        if not customers.exists() or not suppliers.exists():
            return
        
        # Crear algunas facturas de venta
        for i in range(3):
            customer = random.choice(customers)
            invoice = Invoice.objects.create(
                company=company,
                customer=customer,
                number=f'FV-{i+1:04d}',
                date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                due_date=timezone.now().date() + timedelta(days=30),
                subtotal=Decimal(str(random.randint(100000, 500000))),
                tax_amount=Decimal('0'),
                total_amount=Decimal(str(random.randint(100000, 500000))),
                status='sent'
            )
            
            # Línea de factura
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f'Producto/Servicio {i+1}',
                quantity=Decimal('1'),
                unit_price=invoice.subtotal,
                total=invoice.subtotal
            )
        
        # Crear algunas facturas de compra
        for i in range(2):
            supplier = random.choice(suppliers)
            purchase_invoice = PurchaseInvoice.objects.create(
                company=company,
                supplier=supplier,
                number=f'FC-{i+1:04d}',
                date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                due_date=timezone.now().date() + timedelta(days=30),
                subtotal=Decimal(str(random.randint(50000, 300000))),
                tax_amount=Decimal('0'),
                total_amount=Decimal(str(random.randint(50000, 300000))),
                status='received'
            )
            
            # Línea de factura
            PurchaseInvoiceLine.objects.create(
                purchase_invoice=purchase_invoice,
                description=f'Compra {i+1}',
                quantity=Decimal('1'),
                unit_price=purchase_invoice.subtotal,
                total=purchase_invoice.subtotal
            )
