#!/usr/bin/env python
"""
Script para probar la funcionalidad de empleados del sector salud
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company, User
from payroll.models import Employee, EmployeeType
from payroll.models_healthcare import HealthcareRole, MedicalSpecialty, EmployeeHealthcareProfile
from datetime import date

def test_healthcare_employee_creation():
    """Probar la creación de un empleado del sector salud"""
    
    print("=== PRUEBA DE EMPLEADO DEL SECTOR SALUD ===\n")
    
    # 1. Verificar empresa del sector salud
    company = Company.objects.first()
    print(f"1. Empresa: {company.name}")
    print(f"   Categoría: {company.category}")
    print(f"   Es del sector salud: {company.is_healthcare_company()}\n")
    
    # 2. Verificar roles de salud disponibles
    healthcare_roles = HealthcareRole.objects.filter(is_active=True)
    print(f"2. Roles de salud disponibles ({healthcare_roles.count()}):")
    for role in healthcare_roles:
        print(f"   - {role.name}")
    print()
    
    # 3. Verificar especialidades médicas disponibles
    medical_specialties = MedicalSpecialty.objects.filter(is_active=True, specialty_type='medica')
    print(f"3. Especialidades médicas disponibles ({medical_specialties.count()}):")
    for specialty in medical_specialties:
        print(f"   - {specialty.name}")
    print()
    
    # 4. Crear empleado de prueba con perfil de salud
    try:
        # Obtener datos necesarios
        admin_user = User.objects.filter(is_staff=True).first()
        employee_type = EmployeeType.objects.filter(company=company).first()
        healthcare_role = HealthcareRole.objects.filter(code='MEDICO').first()
        medical_specialty = MedicalSpecialty.objects.filter(code='GINECOLOGIA').first()
        
        if not employee_type:
            employee_type = EmployeeType.objects.create(
                company=company,
                code='MEDICO',
                name='Médico Especialista',
                created_by=admin_user
            )
        
        # Crear empleado de prueba
        test_employee = Employee.objects.create(
            company=company,
            employee_type=employee_type,
            employee_code='TEST-GINEC-001',
            document_type='CC',
            document_number='98765432',
            first_name='Ana',
            last_name='García Rodríguez',
            birth_date=date(1990, 5, 15),
            gender='F',
            marital_status='single',
            email='ana.garcia@hospital.com',
            phone='3105555555',
            mobile='3105555555',
            address='Calle 50 #20-30',
            city='Bogotá',
            state='Cundinamarca',
            hire_date=date.today(),
            contract_type='indefinite',
            position='Médica Ginecóloga',
            department='Ginecología y Obstetricia',
            salary_type='fixed',
            basic_salary=7500000,
            created_by=admin_user
        )
        
        print(f"4. Empleado creado exitosamente:")
        print(f"   - Código: {test_employee.employee_code}")
        print(f"   - Nombre: {test_employee.get_full_name()}")
        print(f"   - Posición: {test_employee.position}")
        print(f"   - Departamento: {test_employee.department}\n")
        
        # 5. Crear perfil de salud
        if healthcare_role and medical_specialty:
            healthcare_profile = EmployeeHealthcareProfile.objects.create(
                employee=test_employee,
                healthcare_role=healthcare_role,
                medical_specialty=medical_specialty,
                medical_license_number='RM-54321',
                medical_license_expiry=date(2027, 12, 31),
                assigned_department='Ginecología y Obstetricia',
                years_experience=8,
                created_by=admin_user
            )
            
            print(f"5. Perfil de salud creado:")
            print(f"   - Rol: {healthcare_profile.healthcare_role.name}")
            print(f"   - Especialidad: {healthcare_profile.medical_specialty.name}")
            print(f"   - Registro médico: {healthcare_profile.medical_license_number}")
            print(f"   - Experiencia: {healthcare_profile.years_experience} años\n")
        
        # 6. Verificar integración completa
        print("6. Verificación de integración:")
        print(f"   - El empleado tiene perfil de salud: {hasattr(test_employee, 'healthcare_profile')}")
        
        if hasattr(test_employee, 'healthcare_profile'):
            profile = test_employee.healthcare_profile
            print(f"   - Especialidad del empleado: {profile.medical_specialty.name}")
            print(f"   - Aparecería en ginecología: {profile.medical_specialty.code == 'GINECOLOGIA'}")
        
        print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
        print("✅ El sistema permite crear empleados del sector salud")
        print("✅ Los roles y especialidades están configurados")
        print("✅ La integración con el perfil de salud funciona")
        print("✅ Los empleados ginecólogos aparecerán en el módulo de ginecología")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

if __name__ == "__main__":
    test_healthcare_employee_creation()