"""
Modelos del sistema de nómina.
"""

# Importar todos los modelos
from .models_employee import EmployeeType, Employee
from .models_payroll import PayrollConcept, PayrollPeriod, Payroll, PayrollDetail, LaborBenefit

__all__ = [
    'EmployeeType', 'Employee',
    'PayrollConcept', 'PayrollPeriod', 'Payroll', 'PayrollDetail', 'LaborBenefit'
]