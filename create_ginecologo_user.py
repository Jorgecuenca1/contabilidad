#!/usr/bin/env python
"""
Script para crear usuario ginecólogo con acceso al módulo de ginecología
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company, User
from payroll.models import Employee, EmployeeType
from payroll.models_healthcare import HealthcareRole, MedicalSpecialty, EmployeeHealthcareProfile

def create_gynecology_user():
    """Crear usuario y empleado ginecólogo"""
    
    print("=== CREANDO USUARIO GINECOLOGO ===\n")
    
    try:
        # 1. Obtener empresa del sector salud
        healthcare_company = Company.objects.filter(category='salud').first()
        if not healthcare_company:
            print("[ERROR] No se encontró empresa del sector salud")
            return False
        
        print(f"1. Usando empresa: {healthcare_company.name}")
        
        # 2. Verificar si el usuario ya existe
        if User.objects.filter(username='ginecologo').exists():
            print("2. Usuario 'ginecologo' ya existe, lo elimino y recreo")
            User.objects.filter(username='ginecologo').delete()
        
        # 3. Crear usuario ginecólogo
        ginecologo_user = User.objects.create_user(
            username='ginecologo',
            password='ginecologo123',
            email='ginecologo@hospital.com',
            first_name='Dr. Juan',
            last_name='Pérez García',
            is_staff=False,
            is_active=True
        )
        
        # Agregar acceso a la empresa
        ginecologo_user.companies.add(healthcare_company)
        
        print(f"2. Usuario creado: {ginecologo_user.username}")
        
        # 4. Crear empleado ginecólogo
        admin_user = User.objects.filter(is_staff=True).first()
        
        # Obtener o crear tipo de empleado médico
        employee_type, created = EmployeeType.objects.get_or_create(
            company=healthcare_company,
            code='MEDICO',
            defaults={
                'name': 'Médico Especialista',
                'created_by': admin_user
            }
        )
        
        # Verificar si el empleado ya existe
        if Employee.objects.filter(employee_code='GIN-001', company=healthcare_company).exists():
            print("3. Empleado ya existe, lo elimino y recreo")
            Employee.objects.filter(employee_code='GIN-001', company=healthcare_company).delete()
        
        ginecologo_employee = Employee.objects.create(
            company=healthcare_company,
            employee_type=employee_type,
            employee_code='GIN-001',
            document_type='CC',
            document_number='12345678',
            first_name='Dr. Juan',
            last_name='Pérez García',
            birth_date=date(1985, 3, 15),
            gender='M',
            marital_status='married',
            email='ginecologo@hospital.com',
            phone='3101234567',
            mobile='3101234567',
            address='Calle Hospital #123',
            city='Bogotá',
            state='Cundinamarca',
            hire_date=date.today(),
            contract_type='indefinite',
            position='Médico Ginecólogo',
            department='Ginecología y Obstetricia',
            salary_type='fixed',
            basic_salary=8500000,
            created_by=admin_user
        )
        
        print(f"3. Empleado creado: {ginecologo_employee.get_full_name()}")
        
        # 5. Crear perfil de salud
        healthcare_role = HealthcareRole.objects.filter(code='MEDICO').first()
        medical_specialty = MedicalSpecialty.objects.filter(code='GINECOLOGIA').first()
        
        if healthcare_role and medical_specialty:
            # Verificar si ya existe perfil
            if hasattr(ginecologo_employee, 'healthcare_profile'):
                print("4. Perfil de salud ya existe, lo elimino y recreo")
                ginecologo_employee.healthcare_profile.delete()
            
            healthcare_profile = EmployeeHealthcareProfile.objects.create(
                employee=ginecologo_employee,
                healthcare_role=healthcare_role,
                medical_specialty=medical_specialty,
                medical_license_number='RM-12345',
                medical_license_expiry=date(2030, 12, 31),
                assigned_department='Ginecología y Obstetricia',
                years_experience=12,
                created_by=admin_user
            )
            
            print(f"4. Perfil de salud creado: {healthcare_profile.medical_specialty.name}")
        else:
            print("[WARNING] No se pudo crear perfil de salud - faltan datos")
        
        print("\n=== USUARIO GINECOLOGO CREADO EXITOSAMENTE ===")
        print(f"Username: ginecologo")
        print(f"Password: ginecologo123")
        print(f"Empleado: {ginecologo_employee.get_full_name()}")
        print(f"Empresa: {healthcare_company.name}")
        print(f"Acceso al módulo de ginecología: [OK]")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creando usuario ginecólogo: {e}")
        return False

if __name__ == "__main__":
    create_gynecology_user()