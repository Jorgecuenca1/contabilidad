"""
Comando para cargar conceptos de nómina básicos según normativa colombiana.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from payroll.models import PayrollConcept, EmployeeType
from core.models import Company, User


class Command(BaseCommand):
    help = 'Cargar conceptos de nómina básicos para Colombia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company_id',
            type=int,
            help='ID de la empresa (opcional, carga para todas si no se especifica)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        
        if company_id:
            companies = Company.objects.filter(id=company_id)
        else:
            companies = Company.objects.filter(is_active=True)

        if not companies.exists():
            self.stdout.write(
                self.style.ERROR('No se encontraron empresas válidas')
            )
            return

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No se encontró usuario administrador')
            )
            return

        concepts_data = [
            # DEVENGOS
            {
                'code': 'SALARY',
                'name': 'Salario Básico',
                'description': 'Salario básico mensual del empleado',
                'concept_type': 'earning',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },
            {
                'code': 'TRANSPORT',
                'name': 'Auxilio de Transporte',
                'description': 'Auxilio de transporte para empleados que ganen hasta 2 SMMLV',
                'concept_type': 'earning',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 162000,  # Valor 2025
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': True,
                'affects_income_tax': False,
            },
            {
                'code': 'OVERTIME_ORD',
                'name': 'Horas Extras Diurnas',
                'description': 'Horas extras diurnas (25% recargo)',
                'concept_type': 'earning',
                'calculation_type': 'percentage',
                'percentage': 25,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },
            {
                'code': 'OVERTIME_NIGHT',
                'name': 'Horas Extras Nocturnas',
                'description': 'Horas extras nocturnas (75% recargo)',
                'concept_type': 'earning',
                'calculation_type': 'percentage',
                'percentage': 75,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },
            {
                'code': 'SUNDAY_WORK',
                'name': 'Trabajo Dominical',
                'description': 'Trabajo en domingo (75% recargo)',
                'concept_type': 'earning',
                'calculation_type': 'percentage',
                'percentage': 75,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },
            {
                'code': 'COMMISSIONS',
                'name': 'Comisiones',
                'description': 'Comisiones variables por ventas',
                'concept_type': 'earning',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },
            {
                'code': 'BONUS',
                'name': 'Bonificaciones',
                'description': 'Bonificaciones extraordinarias',
                'concept_type': 'earning',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 0,
                'affects_social_security': True,
                'affects_parafiscals': True,
                'affects_labor_benefits': True,
                'affects_income_tax': True,
            },

            # DEDUCCIONES - Seguridad Social Empleado
            {
                'code': 'EPS_EMP',
                'name': 'Aporte Salud Empleado',
                'description': 'Descuento EPS empleado (4%)',
                'concept_type': 'deduction',
                'calculation_type': 'percentage',
                'percentage': 4,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'PENSION_EMP',
                'name': 'Aporte Pensión Empleado',
                'description': 'Descuento pensión empleado (4%)',
                'concept_type': 'deduction',
                'calculation_type': 'percentage',
                'percentage': 4,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'SOLIDARITY_FUND',
                'name': 'Fondo de Solidaridad Pensional',
                'description': 'Fondo solidaridad pensional (1% para salarios >4 SMMLV)',
                'concept_type': 'deduction',
                'calculation_type': 'percentage',
                'percentage': 1,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'RETENTION',
                'name': 'Retención en la Fuente',
                'description': 'Retención en la fuente por salarios',
                'concept_type': 'deduction',
                'calculation_type': 'formula',
                'percentage': 0,
                'fixed_value': 0,
                'formula': 'Según tabla DIAN',
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'LOAN',
                'name': 'Préstamos',
                'description': 'Descuentos por préstamos a empleados',
                'concept_type': 'deduction',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'GARNISHMENT',
                'name': 'Embargos',
                'description': 'Embargos judiciales',
                'concept_type': 'deduction',
                'calculation_type': 'fixed',
                'percentage': 0,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },

            # APORTES PATRONALES
            {
                'code': 'EPS_EMP_PATRON',
                'name': 'Aporte Salud Empleador',
                'description': 'Aporte EPS empleador (8.5%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 8.5,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'PENSION_PATRON',
                'name': 'Aporte Pensión Empleador',
                'description': 'Aporte pensión empleador (12%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 12,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'ARL',
                'name': 'Aporte ARL',
                'description': 'Aporte riesgos laborales (0.522% - 6.96%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 0.522,  # Clase I por defecto
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'SENA',
                'name': 'Aporte SENA',
                'description': 'Aporte SENA (2%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 2,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'ICBF',
                'name': 'Aporte ICBF',
                'description': 'Aporte ICBF (3%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 3,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'CCF',
                'name': 'Aporte Caja de Compensación',
                'description': 'Aporte CCF (4%)',
                'concept_type': 'employer_contribution',
                'calculation_type': 'percentage',
                'percentage': 4,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },

            # PROVISIONES
            {
                'code': 'SEVERANCE',
                'name': 'Provisión Cesantías',
                'description': 'Provisión cesantías (8.33%)',
                'concept_type': 'provision',
                'calculation_type': 'percentage',
                'percentage': 8.33,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'SEVERANCE_INT',
                'name': 'Provisión Intereses Cesantías',
                'description': 'Provisión intereses cesantías (12% anual)',
                'concept_type': 'provision',
                'calculation_type': 'percentage',
                'percentage': 1,  # 12% / 12 meses
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'BONUS_PROV',
                'name': 'Provisión Prima de Servicios',
                'description': 'Provisión prima de servicios (8.33%)',
                'concept_type': 'provision',
                'calculation_type': 'percentage',
                'percentage': 8.33,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
            {
                'code': 'VACATION_PROV',
                'name': 'Provisión Vacaciones',
                'description': 'Provisión vacaciones (4.17%)',
                'concept_type': 'provision',
                'calculation_type': 'percentage',
                'percentage': 4.17,
                'fixed_value': 0,
                'affects_social_security': False,
                'affects_parafiscals': False,
                'affects_labor_benefits': False,
                'affects_income_tax': False,
            },
        ]

        employee_types_data = [
            {
                'code': 'EMP',
                'name': 'Empleado',
                'description': 'Empleado con contrato laboral',
                'applies_social_security': True,
                'applies_parafiscals': True,
                'applies_labor_benefits': True,
            },
            {
                'code': 'CNT',
                'name': 'Contratista',
                'description': 'Contratista por prestación de servicios',
                'applies_social_security': False,
                'applies_parafiscals': False,
                'applies_labor_benefits': False,
            },
            {
                'code': 'APR',
                'name': 'Aprendiz',
                'description': 'Aprendiz SENA',
                'applies_social_security': True,
                'applies_parafiscals': False,
                'applies_labor_benefits': False,
            },
            {
                'code': 'INT',
                'name': 'Salario Integral',
                'description': 'Empleado con salario integral',
                'applies_social_security': True,
                'applies_parafiscals': False,
                'applies_labor_benefits': True,
            },
        ]

        for company in companies:
            self.stdout.write(f'Procesando empresa: {company.name}')
            
            with transaction.atomic():
                # Crear tipos de empleado
                for emp_type_data in employee_types_data:
                    emp_type, created = EmployeeType.objects.get_or_create(
                        company=company,
                        code=emp_type_data['code'],
                        defaults={
                            'name': emp_type_data['name'],
                            'description': emp_type_data['description'],
                            'applies_social_security': emp_type_data['applies_social_security'],
                            'applies_parafiscals': emp_type_data['applies_parafiscals'],
                            'applies_labor_benefits': emp_type_data['applies_labor_benefits'],
                            'created_by': admin_user,
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Tipo empleado: {emp_type.name}')
                        )

                # Crear conceptos de nómina
                for concept_data in concepts_data:
                    concept, created = PayrollConcept.objects.get_or_create(
                        company=company,
                        code=concept_data['code'],
                        defaults={
                            'name': concept_data['name'],
                            'description': concept_data['description'],
                            'concept_type': concept_data['concept_type'],
                            'calculation_type': concept_data['calculation_type'],
                            'percentage': concept_data['percentage'],
                            'fixed_value': concept_data['fixed_value'],
                            'formula': concept_data.get('formula', ''),
                            'affects_social_security': concept_data['affects_social_security'],
                            'affects_parafiscals': concept_data['affects_parafiscals'],
                            'affects_labor_benefits': concept_data['affects_labor_benefits'],
                            'affects_income_tax': concept_data['affects_income_tax'],
                            'created_by': admin_user,
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Concepto: {concept.name}')
                        )

        self.stdout.write(
            self.style.SUCCESS(f'Conceptos de nómina cargados exitosamente para {companies.count()} empresa(s)')
        )