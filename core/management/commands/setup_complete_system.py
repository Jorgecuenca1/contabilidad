"""
Comando para configurar el sistema completo con todos los datos necesarios
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime, timedelta
import random

from core.models import Company, Currency, Period, User
from accounting.models import ChartOfAccounts, JournalType, CostCenter
from third_parties.models import ThirdParty
from payroll.models import EmployeeType, Employee, PayrollConcept, PayrollPeriod
from taxes.models import TaxType
from accounts_receivable.models import Customer
from accounts_payable.models import Supplier
from treasury.models import BankAccount, Bank
from budget.models import BudgetPeriod, BudgetRubro
from public_sector.models import Budget, ContractType


class Command(BaseCommand):
    help = 'Configura el sistema completo con todos los datos necesarios'

    def handle(self, *args, **kwargs):
        self.stdout.write("=== CONFIGURANDO SISTEMA CONTABLE COMPLETO ===\n")
        
        # 1. Crear superusuario si no existe
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@contabilidad.com',
                password='admin',
                first_name='Administrador',
                last_name='Sistema',
                document_number='1234567890'
            )
            self.stdout.write(self.style.SUCCESS('✓ Superusuario admin creado'))
        else:
            admin_user = User.objects.get(username='admin')
            self.stdout.write('✓ Superusuario admin ya existe')
        
        # 2. Crear monedas
        cop, created = Currency.objects.get_or_create(
            code='COP',
            defaults={
                'name': 'Peso Colombiano',
                'symbol': '$',
                'decimal_places': 2,
                'is_active': True
            }
        )
        
        usd, created = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'symbol': 'US$',
                'decimal_places': 2,
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Monedas configuradas'))
        
        # 3. Crear empresas de ejemplo
        companies = []
        
        # Empresa privada
        empresa1, created = Company.objects.get_or_create(
            tax_id='900123456',
            defaults={
                'name': 'Soluciones Tecnológicas SAS',
                'legal_name': 'Soluciones Tecnológicas S.A.S.',
                'address': 'Calle 100 # 15-20 Oficina 501',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'phone': '(1) 7456789',
                'email': 'info@solucionestec.com',
                'website': 'www.solucionestec.com',
                'regime': 'common',
                'legal_representative': 'Juan Carlos Rodríguez',
                'legal_rep_document': '79456789',
                'fiscal_year_start': date(2025, 1, 1),
                'fiscal_year_end': date(2025, 12, 31),
                'created_by': admin_user
            }
        )
        companies.append(empresa1)
        
        # Empresa pública
        empresa2, created = Company.objects.get_or_create(
            tax_id='899999001',
            defaults={
                'name': 'Instituto Municipal de Desarrollo',
                'legal_name': 'Instituto Municipal de Desarrollo Social',
                'address': 'Carrera 7 # 32-16',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'phone': '(1) 3820000',
                'email': 'contacto@imd.gov.co',
                'website': 'www.imd.gov.co',
                'regime': 'public',
                'sector': 'public',
                'legal_representative': 'María González López',
                'legal_rep_document': '52789456',
                'fiscal_year_start': date(2025, 1, 1),
                'fiscal_year_end': date(2025, 12, 31),
                'created_by': admin_user
            }
        )
        companies.append(empresa2)
        
        # Persona natural comerciante
        empresa3, created = Company.objects.get_or_create(
            tax_id='79123456',
            defaults={
                'name': 'Carlos Andrés Pérez - Contador Público',
                'legal_name': 'Carlos Andrés Pérez Gómez',
                'address': 'Calle 45 # 23-10',
                'city': 'Medellín',
                'state': 'Antioquia',
                'phone': '(4) 4567890',
                'email': 'carlos.perez@contador.com',
                'regime': 'simplified',
                'legal_representative': 'Carlos Andrés Pérez Gómez',
                'legal_rep_document': '79123456',
                'fiscal_year_start': date(2025, 1, 1),
                'fiscal_year_end': date(2025, 12, 31),
                'created_by': admin_user
            }
        )
        companies.append(empresa3)
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(companies)} empresas creadas/verificadas'))
        
        # 4. Configurar para cada empresa
        for company in companies:
            self.stdout.write(f"\nConfigurando empresa: {company.name}")
            
            # Crear período contable
            period, created = Period.objects.get_or_create(
                company=company,
                year=2025,
                month=9,
                defaults={
                    'name': 'Septiembre 2025',
                    'start_date': date(2025, 9, 1),
                    'end_date': date(2025, 9, 30),
                    'is_active': True,
                    'created_by': admin_user
                }
            )
            
            # Crear tipos de asiento
            journal_types = [
                ('CI', 'Comprobante de Ingreso'),
                ('CE', 'Comprobante de Egreso'),
                ('CG', 'Comprobante General'),
                ('CC', 'Comprobante de Compras'),
                ('CV', 'Comprobante de Ventas'),
                ('CN', 'Comprobante de Nómina'),
                ('CB', 'Comprobante Bancario'),
                ('CA', 'Comprobante de Ajustes'),
                ('CR', 'Comprobante de Reversión'),
                ('CP', 'Comprobante de Provisiones'),
                ('CT', 'Comprobante de Traslados'),
                ('CX', 'Comprobante de Cierre'),
            ]
            
            for code, name in journal_types:
                JournalType.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear centros de costo
            cost_centers = [
                ('ADM', 'Administración'),
                ('VEN', 'Ventas'),
                ('PRO', 'Producción'),
                ('LOG', 'Logística'),
                ('TEC', 'Tecnología'),
            ]
            
            for code, name in cost_centers:
                CostCenter.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear plan de cuentas básico
            accounts = [
                ('1', 'ACTIVO', None),
                ('11', 'DISPONIBLE', '1'),
                ('1105', 'CAJA', '11'),
                ('110505', 'Caja General', '1105'),
                ('1110', 'BANCOS', '11'),
                ('111005', 'Bancos Nacionales', '1110'),
                ('13', 'DEUDORES', '1'),
                ('1305', 'CLIENTES', '13'),
                ('130505', 'Clientes Nacionales', '1305'),
                ('14', 'INVENTARIOS', '1'),
                ('1435', 'Mercancías no fabricadas', '14'),
                ('15', 'PROPIEDADES PLANTA Y EQUIPO', '1'),
                ('1524', 'Equipo de oficina', '15'),
                ('2', 'PASIVO', None),
                ('21', 'OBLIGACIONES FINANCIERAS', '2'),
                ('2105', 'Bancos nacionales', '21'),
                ('22', 'PROVEEDORES', '2'),
                ('2205', 'Nacionales', '22'),
                ('23', 'CUENTAS POR PAGAR', '2'),
                ('2365', 'Retención en la fuente', '23'),
                ('24', 'IMPUESTOS', '2'),
                ('2408', 'IVA', '24'),
                ('25', 'OBLIGACIONES LABORALES', '2'),
                ('2505', 'Salarios por pagar', '25'),
                ('3', 'PATRIMONIO', None),
                ('31', 'CAPITAL SOCIAL', '3'),
                ('3105', 'Capital suscrito y pagado', '31'),
                ('36', 'RESULTADOS DEL EJERCICIO', '3'),
                ('3605', 'Utilidad del ejercicio', '36'),
                ('4', 'INGRESOS', None),
                ('41', 'OPERACIONALES', '4'),
                ('4135', 'Comercio', '41'),
                ('5', 'GASTOS', None),
                ('51', 'OPERACIONALES DE ADMINISTRACIÓN', '5'),
                ('5105', 'Gastos de personal', '51'),
                ('52', 'OPERACIONALES DE VENTAS', '5'),
                ('5205', 'Gastos de personal', '52'),
                ('6', 'COSTOS DE VENTAS', None),
                ('61', 'COSTO DE VENTAS Y PRESTACIÓN DE SERVICIOS', '6'),
                ('6135', 'Comercio', '61'),
            ]
            
            for code, name, parent_code in accounts:
                parent = None
                if parent_code:
                    parent = ChartOfAccounts.objects.filter(
                        company=company,
                        code=parent_code
                    ).first()
                
                ChartOfAccounts.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'parent': parent,
                        'account_type': 'detail' if len(code) > 4 else 'title',
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear tipos de empleado
            employee_types = [
                ('TC', 'Tiempo Completo', True, True, True),
                ('MT', 'Medio Tiempo', True, True, True),
                ('PS', 'Prestación de Servicios', False, False, False),
                ('AP', 'Aprendiz SENA', True, False, False),
                ('PR', 'Practicante', False, False, False),
            ]
            
            for code, name, ss, pf, lb in employee_types:
                EmployeeType.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'applies_social_security': ss,
                        'applies_parafiscals': pf,
                        'applies_labor_benefits': lb,
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear empleados de ejemplo
            emp_type = EmployeeType.objects.filter(company=company, code='TC').first()
            if emp_type:
                employees = [
                    ('E001', 'Juan', 'Pérez', '79456123', 'Gerente General', 5000000),
                    ('E002', 'María', 'González', '52789456', 'Contadora', 3500000),
                    ('E003', 'Carlos', 'Rodríguez', '1032456789', 'Auxiliar Contable', 1800000),
                    ('E004', 'Ana', 'Martínez', '1019087654', 'Vendedor', 1500000),
                    ('E005', 'Luis', 'García', '80123456', 'Desarrollador', 4000000),
                ]
                
                for emp_code, fname, lname, doc, position, salary in employees:
                    Employee.objects.get_or_create(
                        company=company,
                        document_number=doc,
                        defaults={
                            'employee_type': emp_type,
                            'employee_code': emp_code,
                            'document_type': 'CC',
                            'first_name': fname,
                            'last_name': lname,
                            'birth_date': date(1990, 1, 1),
                            'gender': 'M' if fname in ['Juan', 'Carlos', 'Luis'] else 'F',
                            'marital_status': 'single',
                            'email': f'{fname.lower()}.{lname.lower()}@{company.email.split("@")[1]}',
                            'phone': '3001234567',
                            'address': 'Calle 123 # 45-67',
                            'city': company.city,
                            'state': company.state,
                            'hire_date': date(2024, 1, 1),
                            'contract_type': 'indefinite',
                            'position': position,
                            'salary_type': 'monthly',
                            'basic_salary': salary,
                            'transportation_allowance': 162000 if salary <= 2600000 else 0,
                            'eps_code': 'EPS001',
                            'eps_name': 'Sura EPS',
                            'pension_fund_code': 'PEN001',
                            'pension_fund_name': 'Protección',
                            'arl_code': 'ARL001',
                            'arl_name': 'Sura ARL',
                            'ccf_code': 'CCF001',
                            'ccf_name': 'Compensar',
                            'bank_account': '1234567890',
                            'bank_name': 'Bancolombia',
                            'account_type': 'savings',
                            'status': 'active',
                            'is_active': True,
                            'created_by': admin_user
                        }
                    )
            
            # Crear conceptos de nómina
            payroll_concepts = [
                ('001', 'Salario Básico', 'earning', 'BASICO'),
                ('002', 'Auxilio de Transporte', 'earning', 'TRANSPORTE'),
                ('003', 'Horas Extras Diurnas', 'earning', 'HED'),
                ('004', 'Horas Extras Nocturnas', 'earning', 'HEN'),
                ('005', 'Comisiones', 'earning', 'COMISION'),
                ('006', 'Bonificaciones', 'earning', 'BONIFICACION'),
                ('101', 'Salud Empleado', 'deduction', 'SALUD_EMP'),
                ('102', 'Pensión Empleado', 'deduction', 'PENSION_EMP'),
                ('103', 'Fondo Solidaridad', 'deduction', 'FSP'),
                ('104', 'Retención en la Fuente', 'deduction', 'RETEFUENTE'),
                ('105', 'Préstamos', 'deduction', 'PRESTAMO'),
                ('201', 'Salud Empleador', 'employer', 'SALUD_EMPR'),
                ('202', 'Pensión Empleador', 'employer', 'PENSION_EMPR'),
                ('203', 'ARL', 'employer', 'ARL'),
                ('204', 'SENA', 'employer', 'SENA'),
                ('205', 'ICBF', 'employer', 'ICBF'),
                ('206', 'Caja Compensación', 'employer', 'CCF'),
                ('301', 'Cesantías', 'provision', 'CESANTIAS'),
                ('302', 'Intereses Cesantías', 'provision', 'INT_CESANTIAS'),
                ('303', 'Prima', 'provision', 'PRIMA'),
                ('304', 'Vacaciones', 'provision', 'VACACIONES'),
            ]
            
            for code, name, concept_type, formula in payroll_concepts:
                PayrollConcept.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'concept_type': concept_type,
                        'formula': formula,
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear período de nómina
            PayrollPeriod.objects.get_or_create(
                company=company,
                name='Primera Quincena Septiembre 2025',
                defaults={
                    'start_date': date(2025, 9, 1),
                    'end_date': date(2025, 9, 15),
                    'payment_date': date(2025, 9, 15),
                    'status': 'open',
                    'created_by': admin_user
                }
            )
            
            # Crear tipos de impuestos
            tax_types = [
                ('IVA', 'Impuesto al Valor Agregado', 19.0, 'IVA'),
                ('RENTA', 'Impuesto de Renta', 35.0, 'RENTA'),
                ('ICA', 'Impuesto de Industria y Comercio', 1.0, 'ICA'),
                ('RETEFTE', 'Retención en la Fuente', 2.5, 'RETENCION'),
                ('RETEIVA', 'Retención de IVA', 15.0, 'RETENCION'),
                ('RETEICA', 'Retención de ICA', 0.8, 'RETENCION'),
            ]
            
            for code, name, rate, tax_type in tax_types:
                TaxType.objects.get_or_create(
                    company=company,
                    code=code,
                    defaults={
                        'name': name,
                        'rate': rate,
                        'tax_type': tax_type,
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            # Crear terceros (clientes y proveedores)
            terceros = [
                ('900111222', 'NIT', 'JURIDICA', 'Distribuidora ABC S.A.S.', True, True),
                ('900222333', 'NIT', 'JURIDICA', 'Servicios XYZ Ltda', True, True),
                ('900333444', 'NIT', 'JURIDICA', 'Tecnología Global SAS', True, True),
                ('79567890', 'CC', 'NATURAL', 'Pedro Ramírez', True, False),
                ('52345678', 'CC', 'NATURAL', 'Laura Jiménez', True, False),
                ('900444555', 'NIT', 'JURIDICA', 'Papelería Universal', False, True),
                ('900555666', 'NIT', 'JURIDICA', 'Suministros Bogotá', False, True),
                ('860001234', 'NIT', 'JURIDICA', 'Bancolombia S.A.', False, False),
            ]
            
            for doc_num, doc_type, person_type, name, is_customer, is_supplier in terceros:
                parts = name.split(' ')
                first_name = parts[0] if person_type == 'NATURAL' else name
                last_name = parts[1] if person_type == 'NATURAL' and len(parts) > 1 else ''
                
                third_party = ThirdParty.objects.get_or_create(
                    company=company,
                    document_number=doc_num,
                    defaults={
                        'person_type': person_type,
                        'document_type': doc_type,
                        'first_name': first_name,
                        'last_name': last_name,
                        'trade_name': name if person_type == 'JURIDICA' else '',
                        'is_customer': is_customer,
                        'is_supplier': is_supplier,
                        'tax_regime': 'COMUN' if person_type == 'JURIDICA' else 'SIMPLIFICADO',
                        'taxpayer_type': 'PERSONA_JURIDICA' if person_type == 'JURIDICA' else 'PERSONA_NATURAL',
                        'is_vat_responsible': True if person_type == 'JURIDICA' else False,
                        'address': f'Calle {random.randint(1, 100)} # {random.randint(1, 50)}-{random.randint(1, 99)}',
                        'city': company.city,
                        'state': company.state,
                        'phone': f'(1) {random.randint(1000000, 9999999)}',
                        'email': f'contacto@{name.lower().replace(" ", "").replace(".", "")}.com',
                        'credit_limit': Decimal(random.randint(5000000, 50000000)),
                        'payment_term_days': random.choice([15, 30, 45, 60]),
                        'created_by': admin_user
                    }
                )[0]
                
                # Crear cliente si aplica
                if is_customer:
                    Customer.objects.get_or_create(
                        company=company,
                        third_party=third_party,
                        defaults={
                            'code': f'C{doc_num[-4:]}',
                            'business_name': name,
                            'tax_id': doc_num,
                            'credit_limit': third_party.credit_limit,
                            'payment_terms': third_party.payment_term_days,
                            'is_active': True,
                            'created_by': admin_user
                        }
                    )
                
                # Crear proveedor si aplica
                if is_supplier:
                    Supplier.objects.get_or_create(
                        company=company,
                        third_party=third_party,
                        defaults={
                            'code': f'P{doc_num[-4:]}',
                            'business_name': name,
                            'tax_id': doc_num,
                            'payment_terms': third_party.payment_term_days,
                            'is_active': True,
                            'created_by': admin_user
                        }
                    )
            
            # Crear bancos y cuentas bancarias
            banks = [
                ('001', 'Bancolombia'),
                ('002', 'Banco de Bogotá'),
                ('003', 'Davivienda'),
                ('004', 'BBVA'),
            ]
            
            for bank_code, bank_name in banks:
                bank, created = Bank.objects.get_or_create(
                    code=bank_code,
                    defaults={
                        'name': bank_name,
                        'is_active': True
                    }
                )
                
                # Crear cuenta bancaria para la empresa
                if bank_code == '001':  # Solo crear una cuenta principal
                    account_code = ChartOfAccounts.objects.filter(
                        company=company,
                        code='111005'
                    ).first()
                    
                    if account_code:
                        BankAccount.objects.get_or_create(
                            company=company,
                            account_number=f'{random.randint(1000000000, 9999999999)}',
                            defaults={
                                'bank': bank,
                                'account_type': 'checking',
                                'account_name': f'Cuenta Corriente {company.name}',
                                'currency': cop,
                                'current_balance': Decimal(random.randint(10000000, 100000000)),
                                'accounting_account': account_code,
                                'status': 'active',
                                'is_cash_account': False,
                                'created_by': admin_user
                            }
                        )
            
            # Para empresa pública, crear presupuesto
            if company.sector == 'public':
                # Crear período presupuestal
                budget_period, created = BudgetPeriod.objects.get_or_create(
                    company=company,
                    year=2025,
                    defaults={
                        'name': 'Vigencia 2025',
                        'initial_budget': Decimal('5000000000'),
                        'current_budget': Decimal('5000000000'),
                        'status': 'active',
                        'approval_date': date(2024, 12, 15),
                        'approval_document': 'Acuerdo 001-2024',
                        'created_by': admin_user
                    }
                )
                
                # Crear rubros presupuestales
                rubros = [
                    ('1', 'INGRESOS', 'income', None, 2000000000),
                    ('1.1', 'Ingresos Corrientes', 'income', '1', 1500000000),
                    ('1.1.1', 'Ingresos Tributarios', 'income', '1.1', 1000000000),
                    ('1.2', 'Recursos de Capital', 'income', '1', 500000000),
                    ('2', 'GASTOS', 'expense', None, 3000000000),
                    ('2.1', 'Gastos de Funcionamiento', 'expense', '2', 2000000000),
                    ('2.1.1', 'Gastos de Personal', 'expense', '2.1', 1500000000),
                    ('2.1.2', 'Gastos Generales', 'expense', '2.1', 500000000),
                    ('2.2', 'Servicio de la Deuda', 'expense', '2', 500000000),
                    ('2.3', 'Inversión', 'expense', '2', 500000000),
                ]
                
                for code, name, rubro_type, parent_code, amount in rubros:
                    parent = None
                    if parent_code:
                        parent = BudgetRubro.objects.filter(
                            company=company,
                            code=parent_code
                        ).first()
                    
                    BudgetRubro.objects.get_or_create(
                        company=company,
                        period=budget_period,
                        code=code,
                        defaults={
                            'name': name,
                            'rubro_type': rubro_type,
                            'parent': parent,
                            'initial_appropriation': amount,
                            'current_appropriation': amount,
                            'is_active': True,
                            'created_by': admin_user
                        }
                    )
                
                # Crear tipos de contrato
                contract_types = [
                    ('PS', 'Prestación de Servicios'),
                    ('SU', 'Suministros'),
                    ('OB', 'Obra'),
                    ('CO', 'Consultoría'),
                    ('CV', 'Convenio'),
                ]
                
                for code, name in contract_types:
                    ContractType.objects.get_or_create(
                        company=company,
                        code=code,
                        defaults={
                            'name': name,
                            'is_active': True,
                            'created_by': admin_user
                        }
                    )
                
                # Crear presupuesto en el modelo antiguo también
                Budget.objects.get_or_create(
                    company=company,
                    year=2025,
                    defaults={
                        'total_budget': Decimal('5000000000'),
                        'executed_budget': Decimal('1500000000'),
                        'available_budget': Decimal('3500000000'),
                        'is_active': True,
                        'created_by': admin_user
                    }
                )
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Configuración completa para {company.name}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== SISTEMA CONFIGURADO EXITOSAMENTE ==='))
        self.stdout.write('\nAcceso al sistema:')
        self.stdout.write('URL: http://127.0.0.1:8001/')
        self.stdout.write('Usuario: admin')
        self.stdout.write('Contraseña: admin')
        self.stdout.write(f'\n{len(companies)} empresas configuradas con todos los módulos')