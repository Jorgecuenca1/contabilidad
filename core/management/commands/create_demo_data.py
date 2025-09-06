"""
Comando para crear datos de demostración completos.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from core.models import Company, Country, Currency, FiscalYear, Period
from accounting.models_accounts import AccountType, ChartOfAccounts, Account, CostCenter
from accounts_receivable.models_customer import CustomerType, Customer
from accounts_payable.models_supplier import SupplierType, Supplier
from treasury.models_bank import Bank, BankAccount
from payroll.models_employee import EmployeeType
from taxes.models_tax_types import TaxType

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de demostración completos para el sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de demostración...')
        
        # Crear usuario admin si no existe
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@contabilidad.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Usuario admin creado'))
        
        # Crear país Colombia
        colombia, _ = Country.objects.get_or_create(
            code='CO',
            defaults={
                'name': 'Colombia',
                'tax_id_name': 'NIT',
                'currency_code': 'COP'
            }
        )
        
        # Crear moneda COP
        cop_currency, _ = Currency.objects.get_or_create(
            code='COP',
            defaults={
                'name': 'Peso Colombiano',
                'symbol': '$',
                'decimal_places': 0
            }
        )
        
        # Crear empresa demo
        company, created = Company.objects.get_or_create(
            tax_id='900123456-1',
            defaults={
                'name': 'Empresa Demo S.A.S.',
                'legal_name': 'Empresa Demostración S.A.S.',
                'country': colombia,
                'functional_currency': cop_currency,
                'regime': 'common',
                'sector': 'private',
                'fiscal_year_start': 1,
                'fiscal_year_end': 12,
                'legal_representative': 'Juan Pérez',
                'legal_rep_document': '12345678',
                'created_by': admin_user,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Empresa {company.name} creada'))
            
            # Crear año fiscal
            fiscal_year, _ = FiscalYear.objects.get_or_create(
                company=company,
                year=2025,
                defaults={
                    'start_date': '2025-01-01',
                    'end_date': '2025-12-31',
                    'status': 'open',
                    'created_by': admin_user
                }
            )
            
            # Crear períodos mensuales
            for month in range(1, 13):
                Period.objects.get_or_create(
                    fiscal_year=fiscal_year,
                    period_number=month,
                    defaults={
                        'name': f'Período {month:02d}/2025',
                        'start_date': f'2025-{month:02d}-01',
                        'end_date': f'2025-{month:02d}-28' if month == 2 else f'2025-{month:02d}-30',
                        'status': 'open'
                    }
                )
        
        # Crear tipos de cuenta
        account_types_data = [
            ('1', 'ACTIVO', 'debit', True, False),
            ('2', 'PASIVO', 'credit', True, False),
            ('3', 'PATRIMONIO', 'credit', True, False),
            ('4', 'INGRESOS', 'credit', False, True),
            ('5', 'GASTOS', 'debit', False, True),
            ('6', 'COSTOS', 'debit', False, True),
        ]
        
        for code, name, nature, is_balance_sheet, is_income_statement in account_types_data:
            AccountType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'nature': nature,
                    'is_balance_sheet': is_balance_sheet,
                    'is_income_statement': is_income_statement
                }
            )
        
        # Crear plan de cuentas
        chart, _ = ChartOfAccounts.objects.get_or_create(
            company=company,
            name='Plan Único de Cuentas - PUC',
            defaults={
                'description': 'Plan Único de Cuentas para Colombia',
                'created_by': admin_user
            }
        )
        
        # Crear cuentas principales
        accounts_data = [
            ('1105', 'CAJA', '1', 1, True),
            ('1110', 'BANCOS', '1', 1, True),
            ('1305', 'CLIENTES', '1', 1, True),
            ('1435', 'MERCANCÍAS NO FABRICADAS', '1', 1, True),
            ('1524', 'EQUIPO DE OFICINA', '1', 1, True),
            ('2205', 'PROVEEDORES', '2', 1, True),
            ('2367', 'IMPUESTOS GRAVÁMENES Y TASAS', '2', 1, True),
            ('2408', 'IVA POR PAGAR', '2', 1, True),
            ('3115', 'APORTES SOCIALES', '3', 1, True),
            ('4135', 'COMERCIO AL POR MAYOR Y AL POR MENOR', '4', 1, True),
            ('5115', 'IMPUESTOS', '5', 1, True),
            ('5195', 'DIVERSOS', '5', 1, True),
        ]
        
        for code, name, type_code, level, is_detail in accounts_data:
            account_type = AccountType.objects.get(code=type_code)
            Account.objects.get_or_create(
                chart=chart,
                code=code,
                defaults={
                    'name': name,
                    'account_type': account_type,
                    'level': level,
                    'is_detail': is_detail,
                    'is_active': True,
                    'created_by': admin_user
                }
            )
        
        # Crear centros de costo
        cost_centers_data = [
            ('ADM', 'Administración'),
            ('VEN', 'Ventas'),
            ('PRO', 'Producción'),
            ('ALM', 'Almacén'),
        ]
        
        for code, name in cost_centers_data:
            CostCenter.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'is_active': True,
                    'created_by': admin_user
                }
            )
        
        # Crear tipos de cliente
        CustomerType.objects.get_or_create(
            name='Persona Natural',
            defaults={'description': 'Cliente persona natural'}
        )
        CustomerType.objects.get_or_create(
            name='Persona Jurídica',
            defaults={'description': 'Cliente persona jurídica'}
        )
        
        # Crear clientes demo
        customer_type = CustomerType.objects.first()
        Customer.objects.get_or_create(
            company=company,
            tax_id='12345678-9',
            defaults={
                'customer_type': customer_type,
                'name': 'Cliente Demo',
                'email': 'cliente@demo.com',
                'phone': '3001234567',
                'address': 'Calle 123 #45-67',
                'city': 'Bogotá',
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        # Crear tipos de proveedor
        SupplierType.objects.get_or_create(
            name='Proveedor Nacional',
            defaults={'description': 'Proveedor nacional'}
        )
        
        # Crear proveedores demo
        supplier_type = SupplierType.objects.first()
        Supplier.objects.get_or_create(
            company=company,
            tax_id='987654321-1',
            defaults={
                'supplier_type': supplier_type,
                'name': 'Proveedor Demo S.A.S.',
                'email': 'proveedor@demo.com',
                'phone': '3009876543',
                'address': 'Carrera 456 #78-90',
                'city': 'Medellín',
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        # Crear bancos
        banks_data = [
            ('BANCOLOMBIA', 'Bancolombia S.A.'),
            ('BANCO_BOGOTA', 'Banco de Bogotá'),
            ('DAVIVIENDA', 'Banco Davivienda S.A.'),
        ]
        
        for code, name in banks_data:
            Bank.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
        
        # Crear cuenta bancaria demo
        bank = Bank.objects.first()
        bank_account_account = Account.objects.get(code='1110')
        BankAccount.objects.get_or_create(
            company=company,
            account_number='123456789',
            defaults={
                'bank': bank,
                'name': 'Cuenta Corriente Principal',
                'account_type': 'checking',
                'currency': cop_currency,
                'accounting_account': bank_account_account,
                'opening_balance': Decimal('5000000'),
                'current_balance': Decimal('5000000'),
                'status': 'active',
                'created_by': admin_user
            }
        )
        
        # Crear tipos de empleado
        employee_types_data = [
            ('Empleado Tiempo Completo', 'Empleado de tiempo completo'),
            ('Empleado Medio Tiempo', 'Empleado de medio tiempo'),
            ('Contratista', 'Contratista independiente'),
        ]
        
        for name, description in employee_types_data:
            EmployeeType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True
                }
            )
        
        # Crear tipos de impuesto
        tax_types_data = [
            ('IVA', 'Impuesto al Valor Agregado', 19.0, 'bimonthly'),
            ('Renta', 'Impuesto de Renta', 33.0, 'annual'),
            ('ICA', 'Impuesto de Industria y Comercio', 1.0, 'bimonthly'),
            ('Retención Fuente', 'Retención en la Fuente', 2.5, 'monthly'),
        ]
        
        for name, description, rate, frequency in tax_types_data:
            TaxType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'rate': Decimal(str(rate)),
                    'frequency': frequency,
                    'is_active': True
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Datos de demostración creados exitosamente:'
                '\n   • Usuario: admin / admin123'
                '\n   • Empresa: Empresa Demo S.A.S.'
                '\n   • Plan de cuentas PUC básico'
                '\n   • Centros de costo'
                '\n   • Clientes y proveedores demo'
                '\n   • Cuenta bancaria con saldo'
                '\n   • Tipos de empleado'
                '\n   • Tipos de impuesto colombianos'
                '\n\n🚀 El sistema está listo para usar!'
            )
        )
