"""
Tests for payroll app functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, datetime

from core.models import Company
from .models import EmployeeType, Employee, PayrollConcept, PayrollPeriod, Payroll, PayrollDetail
from .views import calculate_concept_amount, calculate_income_tax_retention


class PayrollModelsTest(TestCase):
    """Test payroll models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            tax_id='900123456-7',
            created_by=self.user
        )
        
        self.employee_type = EmployeeType.objects.create(
            company=self.company,
            code='EMP',
            name='Empleado',
            applies_social_security=True,
            applies_parafiscals=True,
            applies_labor_benefits=True,
            created_by=self.user
        )
        
        self.employee = Employee.objects.create(
            company=self.company,
            employee_type=self.employee_type,
            employee_code='EMP001',
            document_type='CC',
            document_number='12345678',
            first_name='Juan',
            last_name='Pérez García',
            birth_date=date(1990, 1, 15),
            gender='M',
            marital_status='single',
            address='Calle 123 #45-67',
            city='Bogotá',
            state='Cundinamarca',
            hire_date=date.today(),
            contract_type='indefinite',
            position='Desarrollador',
            salary_type='fixed',
            basic_salary=Decimal('2500000'),
            eps_name='SURA EPS',
            pension_fund_name='Porvenir',
            arl_name='SURA ARL',
            ccf_name='Compensar',
            created_by=self.user
        )

    def test_employee_creation(self):
        """Test employee model creation."""
        self.assertEqual(self.employee.get_full_name(), 'Juan Pérez García')
        self.assertTrue(self.employee.is_active)
        self.assertEqual(str(self.employee), 'EMP001 - Juan Pérez García')
    
    def test_employee_age_calculation(self):
        """Test employee age calculation."""
        age = self.employee.get_current_age()
        expected_age = date.today().year - 1990
        # Adjust for birthday not yet reached this year
        if (date.today().month, date.today().day) < (1, 15):
            expected_age -= 1
        self.assertEqual(age, expected_age)


class PayrollViewsTest(TestCase):
    """Test payroll views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.company = Company.objects.create(
            name='Test Company',
            tax_id='900123456-7',
            created_by=self.user
        )
    
    def test_payroll_dashboard_view(self):
        """Test payroll dashboard view."""
        response = self.client.get(reverse('payroll:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Módulo de Nómina')
    
    def test_new_employee_view(self):
        """Test new employee view."""
        response = self.client.get(reverse('payroll:new_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nuevo Empleado')
    
    def test_liquidate_payroll_view(self):
        """Test liquidate payroll view."""
        response = self.client.get(reverse('payroll:liquidate_payroll'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Liquidar Nómina')
    
    def test_generate_certificate_view(self):
        """Test generate certificate view."""
        response = self.client.get(reverse('payroll:certificate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Certificado de Ingresos')
    
    def test_generate_pila_view(self):
        """Test generate PILA view."""
        response = self.client.get(reverse('payroll:pila'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILA')
    
    def test_payroll_reports_view(self):
        """Test payroll reports view."""
        response = self.client.get(reverse('payroll:reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reportes de Nómina')
