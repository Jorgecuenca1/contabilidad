"""
Comando para cargar datos iniciales del sistema.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, datetime
from decimal import Decimal

from core.models import Country, Currency, User, Company
from core.models_extended import FiscalYear, Period
from accounting.models_accounts import AccountType, ChartOfAccounts, Account


class Command(BaseCommand):
    help = 'Carga datos iniciales del sistema de contabilidad'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos iniciales...')
        
        with transaction.atomic():
            self.create_countries()
            self.create_currencies()
            self.create_account_types()
            self.create_sample_company()
            
        self.stdout.write(
            self.style.SUCCESS('Datos iniciales cargados exitosamente')
        )

    def create_countries(self):
        """Crear países iniciales."""
        countries_data = [
            {
                'code': 'COL',
                'name': 'Colombia',
                'currency_code': 'COP',
                'currency_symbol': '$',
                'tax_id_regex': r'^\d{9,10}$',
                'tax_configuration': {
                    'iva_rate': 19,  # IVA estándar 2025
                    'iva_reduced': 5,  # IVA reducido
                    'retefuente_rates': {
                        'honorarios': 10,  # Profesionales independientes
                        'servicios': 4,  # Servicios gravados
                        'compras': 2.5,  # Compras gravadas
                        'arrendamientos': 3.5,  # Arrendamientos
                        'rendimientos_financieros': 7,  # Rendimientos financieros
                        'otros_ingresos_tributarios': 2.5
                    },
                    'retencion_ica_rates': {
                        'general': 0.414,  # Promedio nacional
                        'bogota': 0.414,
                        'medellin': 0.7,
                        'cali': 1.0
                    },
                    'social_security_2025': {
                        'salud_empleado': 4.0,
                        'pension_empleado': 4.0,
                        'salud_empleador': 8.5,
                        'pension_empleador': 12.0,
                        'arl_clase_1': 0.348,
                        'arl_clase_2': 0.435,
                        'arl_clase_3': 0.783,
                        'arl_clase_4': 1.740,
                        'arl_clase_5': 3.219,
                        'sena': 2.0,
                        'icbf': 3.0,
                        'ccf': 4.0
                    }
                }
            },
            {
                'code': 'PER',
                'name': 'Perú',
                'currency_code': 'PEN',
                'currency_symbol': 'S/',
                'tax_id_regex': r'^\d{11}$',
                'tax_configuration': {
                    'igv_rate': 18
                }
            },
            {
                'code': 'ECU',
                'name': 'Ecuador',
                'currency_code': 'USD',
                'currency_symbol': '$',
                'tax_id_regex': r'^\d{10,13}$',
                'tax_configuration': {
                    'iva_rate': 12
                }
            }
        ]
        
        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                code=country_data['code'],
                defaults=country_data
            )
            if created:
                self.stdout.write(f'  País creado: {country.name}')

    def create_currencies(self):
        """Crear monedas iniciales."""
        currencies_data = [
            {'code': 'COP', 'name': 'Peso Colombiano', 'symbol': '$', 'decimal_places': 2},
            {'code': 'USD', 'name': 'Dólar Estadounidense', 'symbol': '$', 'decimal_places': 2},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'decimal_places': 2},
            {'code': 'PEN', 'name': 'Sol Peruano', 'symbol': 'S/', 'decimal_places': 2},
        ]
        
        for currency_data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults=currency_data
            )
            if created:
                self.stdout.write(f'  Moneda creada: {currency.name}')

    def create_account_types(self):
        """Crear tipos de cuenta contable."""
        account_types_data = [
            {'code': '1', 'name': 'Activo', 'type': 'asset', 'nature': 'debit', 'is_balance_sheet': True, 'is_income_statement': False},
            {'code': '2', 'name': 'Pasivo', 'type': 'liability', 'nature': 'credit', 'is_balance_sheet': True, 'is_income_statement': False},
            {'code': '3', 'name': 'Patrimonio', 'type': 'equity', 'nature': 'credit', 'is_balance_sheet': True, 'is_income_statement': False},
            {'code': '4', 'name': 'Ingresos', 'type': 'income', 'nature': 'credit', 'is_balance_sheet': False, 'is_income_statement': True},
            {'code': '5', 'name': 'Gastos', 'type': 'expense', 'nature': 'debit', 'is_balance_sheet': False, 'is_income_statement': True},
            {'code': '6', 'name': 'Costos', 'type': 'cost', 'nature': 'debit', 'is_balance_sheet': False, 'is_income_statement': True},
        ]
        
        for account_type_data in account_types_data:
            account_type, created = AccountType.objects.get_or_create(
                code=account_type_data['code'],
                defaults=account_type_data
            )
            if created:
                self.stdout.write(f'  Tipo de cuenta creado: {account_type.name}')

    def create_sample_company(self):
        """Crear empresa de ejemplo."""
        # Obtener país y usuario admin
        colombia = Country.objects.get(code='COL')
        admin_user = User.objects.get(username='admin')
        
        # Crear empresa
        company, created = Company.objects.get_or_create(
            tax_id='900123456',
            defaults={
                'name': 'Empresa Demo S.A.S.',
                'legal_name': 'Empresa Demostración Contabilidad S.A.S.',
                'tax_id_dv': '7',
                'country': colombia,
                'address': 'Calle 123 # 45-67',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'postal_code': '110111',
                'phone': '+57 1 234 5678',
                'email': 'info@empresademo.com',
                'website': 'https://www.empresademo.com',
                'regime': 'common',
                'sector': 'private',
                'functional_currency': 'COP',
                'fiscal_year_start': date(2025, 1, 1),
                'fiscal_year_end': date(2025, 12, 31),
                'legal_representative': 'Juan Pérez García',
                'legal_rep_document': '12345678',
                'created_by': admin_user,
                'settings': {
                    'auto_numbering': True,
                    'require_cost_center': False,
                    'decimal_places': 2
                }
            }
        )
        
        if created:
            self.stdout.write(f'  Empresa creada: {company.name}')
            
            # Crear año fiscal
            fiscal_year, fy_created = FiscalYear.objects.get_or_create(
                company=company,
                year=2025,
                defaults={
                    'start_date': date(2025, 1, 1),
                    'end_date': date(2025, 12, 31),
                    'status': 'open'
                }
            )
            
            if fy_created:
                self.stdout.write(f'    Año fiscal creado: {fiscal_year.year}')
                
                # Crear períodos mensuales
                for month in range(1, 13):
                    if month == 12:
                        start_date = date(2025, month, 1)
                        end_date = date(2025, month, 31)
                    else:
                        start_date = date(2025, month, 1)
                        # Calcular último día del mes
                        if month in [1, 3, 5, 7, 8, 10, 12]:
                            end_date = date(2025, month, 31)
                        elif month in [4, 6, 9, 11]:
                            end_date = date(2025, month, 30)
                        else:  # febrero
                            end_date = date(2025, month, 28)
                    
                    period, p_created = Period.objects.get_or_create(
                        fiscal_year=fiscal_year,
                        month=month,
                        defaults={
                            'start_date': start_date,
                            'end_date': end_date,
                            'status': 'open'
                        }
                    )
                    
                    if p_created:
                        self.stdout.write(f'      Período creado: {period.fiscal_year.year}/{period.month:02d}')
            
            # Crear plan de cuentas
            chart, chart_created = ChartOfAccounts.objects.get_or_create(
                company=company,
                defaults={
                    'name': 'Plan Único de Cuentas - PUC Colombia',
                    'description': 'Plan de cuentas basado en el PUC colombiano',
                    'account_code_length': 6,
                    'cost_center_required': False,
                    'project_required': False,
                    'created_by': admin_user
                }
            )
            
            if chart_created:
                self.stdout.write(f'    Plan de cuentas creado: {chart.name}')
                self.create_sample_accounts(chart, admin_user)

    def create_sample_accounts(self, chart, user):
        """Crear cuentas de ejemplo."""
        # Obtener tipos de cuenta
        asset_type = AccountType.objects.get(code='1')
        liability_type = AccountType.objects.get(code='2')
        equity_type = AccountType.objects.get(code='3')
        income_type = AccountType.objects.get(code='4')
        expense_type = AccountType.objects.get(code='5')
        
        # Cuentas principales
        accounts_data = [
            # ACTIVOS
            {'code': '1', 'name': 'ACTIVO', 'account_type': asset_type, 'is_detail': False, 'level': 1},
            {'code': '11', 'name': 'ACTIVO CORRIENTE', 'account_type': asset_type, 'is_detail': False, 'level': 2, 'parent_code': '1'},
            {'code': '1105', 'name': 'CAJA', 'account_type': asset_type, 'is_detail': False, 'level': 3, 'parent_code': '11', 'control_type': 'cash'},
            {'code': '110505', 'name': 'Caja General', 'account_type': asset_type, 'is_detail': True, 'level': 4, 'parent_code': '1105'},
            {'code': '1110', 'name': 'BANCOS', 'account_type': asset_type, 'is_detail': False, 'level': 3, 'parent_code': '11', 'control_type': 'bank'},
            {'code': '111005', 'name': 'Banco de Bogotá - Cuenta Corriente', 'account_type': asset_type, 'is_detail': True, 'level': 4, 'parent_code': '1110'},
            {'code': '1305', 'name': 'CLIENTES', 'account_type': asset_type, 'is_detail': False, 'level': 3, 'parent_code': '13', 'control_type': 'receivables'},
            {'code': '130505', 'name': 'Clientes Nacionales', 'account_type': asset_type, 'is_detail': True, 'level': 4, 'parent_code': '1305', 'requires_third_party': True},
            
            # PASIVOS
            {'code': '2', 'name': 'PASIVO', 'account_type': liability_type, 'is_detail': False, 'level': 1},
            {'code': '21', 'name': 'PASIVO CORRIENTE', 'account_type': liability_type, 'is_detail': False, 'level': 2, 'parent_code': '2'},
            {'code': '2205', 'name': 'PROVEEDORES', 'account_type': liability_type, 'is_detail': False, 'level': 3, 'parent_code': '21', 'control_type': 'payables'},
            {'code': '220505', 'name': 'Proveedores Nacionales', 'account_type': liability_type, 'is_detail': True, 'level': 4, 'parent_code': '2205', 'requires_third_party': True},
            {'code': '2408', 'name': 'IMPUESTO A LAS VENTAS POR PAGAR', 'account_type': liability_type, 'is_detail': False, 'level': 3, 'parent_code': '24', 'control_type': 'tax'},
            {'code': '240805', 'name': 'IVA por Pagar', 'account_type': liability_type, 'is_detail': True, 'level': 4, 'parent_code': '2408'},
            
            # PATRIMONIO
            {'code': '3', 'name': 'PATRIMONIO', 'account_type': equity_type, 'is_detail': False, 'level': 1},
            {'code': '31', 'name': 'CAPITAL SOCIAL', 'account_type': equity_type, 'is_detail': False, 'level': 2, 'parent_code': '3'},
            {'code': '3115', 'name': 'APORTES SOCIALES', 'account_type': equity_type, 'is_detail': False, 'level': 3, 'parent_code': '31'},
            {'code': '311505', 'name': 'Capital Suscrito y Pagado', 'account_type': equity_type, 'is_detail': True, 'level': 4, 'parent_code': '3115'},
            
            # INGRESOS
            {'code': '4', 'name': 'INGRESOS', 'account_type': income_type, 'is_detail': False, 'level': 1},
            {'code': '41', 'name': 'INGRESOS OPERACIONALES', 'account_type': income_type, 'is_detail': False, 'level': 2, 'parent_code': '4'},
            {'code': '4135', 'name': 'COMERCIO AL POR MAYOR Y AL POR MENOR', 'account_type': income_type, 'is_detail': False, 'level': 3, 'parent_code': '41'},
            {'code': '413505', 'name': 'Ventas de Mercancías', 'account_type': income_type, 'is_detail': True, 'level': 4, 'parent_code': '4135'},
            
            # GASTOS
            {'code': '5', 'name': 'GASTOS', 'account_type': expense_type, 'is_detail': False, 'level': 1},
            {'code': '51', 'name': 'GASTOS OPERACIONALES DE ADMINISTRACIÓN', 'account_type': expense_type, 'is_detail': False, 'level': 2, 'parent_code': '5'},
            {'code': '5105', 'name': 'GASTOS DE PERSONAL', 'account_type': expense_type, 'is_detail': False, 'level': 3, 'parent_code': '51'},
            {'code': '510506', 'name': 'Sueldos', 'account_type': expense_type, 'is_detail': True, 'level': 4, 'parent_code': '5105'},
        ]
        
        # Crear cuentas con jerarquía
        created_accounts = {}
        
        for account_data in accounts_data:
            parent = None
            if 'parent_code' in account_data:
                parent = created_accounts.get(account_data['parent_code'])
            
            account_data_clean = account_data.copy()
            account_data_clean.pop('parent_code', None)
            
            account, created = Account.objects.get_or_create(
                chart_of_accounts=chart,
                code=account_data['code'],
                defaults={
                    **account_data_clean,
                    'parent': parent,
                    'created_by': user
                }
            )
            
            created_accounts[account_data['code']] = account
            
            if created:
                self.stdout.write(f'      Cuenta creada: {account.code} - {account.name}')




