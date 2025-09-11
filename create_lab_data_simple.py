#!/usr/bin/env python
"""
Script simple para crear datos de laboratorio sin simbolos Unicode.
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import transaction
from core.models import Company, User
from payroll.models import Employee, EmployeeType
from payroll.models_healthcare import (
    HealthcareRole, LaboratorySpecialty, EmployeeHealthcareProfile
)


def create_lab_system():
    """Crear sistema básico de laboratorio."""
    print("=== CREANDO SISTEMA DE LABORATORIO ===")
    
    # Roles de laboratorio
    lab_roles = [
        ('LABORATORISTA', 'Laboratorista Clinico', 'laboratorio'),
        ('BACTERIOLOGO', 'Bacteriologo', 'laboratorio'),
        ('CITOLOGO', 'Citologo', 'laboratorio'),
        ('SUPERVISOR_LAB', 'Supervisor de Laboratorio', 'laboratorio'),
    ]
    
    for code, name, category in lab_roles:
        role, created = HealthcareRole.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'category': category,
                'requires_medical_license': code != 'LABORATORISTA',
                'requires_specialty': True,
                'is_clinical_role': True,
            }
        )
        if created:
            print(f"[+] Rol creado: {name}")
        else:
            print(f"[-] Rol existe: {name}")
    
    # Especialidades de laboratorio
    lab_specialties = [
        ('HEMATOLOGIA_LAB', 'Especialista en Hematologia', 'hematology'),
        ('QUIMICA_CLINICA', 'Especialista en Quimica Clinica', 'chemistry'),
        ('MICROBIOLOGIA_LAB', 'Especialista en Microbiologia', 'microbiology'),
        ('GINECOLOGIA_LAB', 'Especialista en Laboratorio de Ginecologia', 'gynecology_lab'),
        ('CONTROL_CALIDAD', 'Especialista en Control de Calidad', 'quality_control'),
    ]
    
    for code, name, area in lab_specialties:
        specialty, created = LaboratorySpecialty.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'specialty_area': area,
                'certification_required': True,
                'requires_special_training': True,
                'training_hours_required': 120,
            }
        )
        if created:
            print(f"[+] Especialidad creada: {name}")
        else:
            print(f"[-] Especialidad existe: {name}")
    
    # Crear usuarios de laboratorio
    healthcare_company = Company.objects.filter(category='salud').first()
    admin_user = User.objects.filter(is_staff=True).first()
    
    if not healthcare_company:
        print("[ERROR] No se encontro empresa de salud")
        return False
    
    lab_users = [
        {
            'username': 'laboratorista',
            'password': 'laboratorista123',
            'name': 'Maria Rodriguez Lopez',
            'email': 'laboratorista@hospital.com',
            'role': 'LABORATORISTA',
            'specialty': 'HEMATOLOGIA_LAB',
            'code': 'LAB-001',
            'position': 'Laboratorista Clinica',
        },
        {
            'username': 'citologo',
            'password': 'citologo123', 
            'name': 'Ana Fernandez Ruiz',
            'email': 'citologo@hospital.com',
            'role': 'CITOLOGO',
            'specialty': 'GINECOLOGIA_LAB',
            'code': 'LAB-003',
            'position': 'Citologa Especialista en Ginecologia',
        },
        {
            'username': 'supervisor_lab',
            'password': 'supervisor123',
            'name': 'Roberto Gomez Herrera',
            'email': 'supervisor.lab@hospital.com',
            'role': 'SUPERVISOR_LAB', 
            'specialty': 'CONTROL_CALIDAD',
            'code': 'LAB-004',
            'position': 'Supervisor General de Laboratorio',
        },
    ]
    
    for user_data in lab_users:
        # Crear usuario
        # Generar número de documento único
        user_doc_number = f"{abs(hash(user_data['username'] + '_user')) % 100000000:08d}"
        
        if User.objects.filter(username=user_data['username']).exists():
            user = User.objects.get(username=user_data['username'])
            print(f"[-] Usuario existe: {user_data['username']}")
        else:
            name_parts = user_data['name'].split()
            user = User.objects.create_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data['email'],
                first_name=name_parts[0] + (' ' + name_parts[1] if len(name_parts) > 2 else ''),
                last_name=' '.join(name_parts[2:]) if len(name_parts) > 2 else name_parts[1],
                document_number=user_doc_number,
                is_staff=False,
                is_active=True
            )
            user.companies.add(healthcare_company)
            print(f"[+] Usuario creado: {user_data['username']}")
        
        # Crear empleado
        employee_type, _ = EmployeeType.objects.get_or_create(
            company=healthcare_company,
            code='LABORATORIO',
            defaults={'name': 'Personal de Laboratorio', 'created_by': admin_user}
        )
        
        if Employee.objects.filter(employee_code=user_data['code'], company=healthcare_company).exists():
            employee = Employee.objects.get(employee_code=user_data['code'], company=healthcare_company)
            print(f"[-] Empleado existe: {user_data['code']}")
        else:
            name_parts = user_data['name'].split()
            employee = Employee.objects.create(
                company=healthcare_company,
                employee_type=employee_type,
                employee_code=user_data['code'],
                document_type='CC',
                document_number=f"{abs(hash(user_data['username'] + user_data['code'])) % 100000000:08d}",
                first_name=name_parts[0] + (' ' + name_parts[1] if len(name_parts) > 2 else ''),
                last_name=' '.join(name_parts[2:]) if len(name_parts) > 2 else name_parts[1],
                birth_date=date(1985, 6, 15),
                gender='F' if name_parts[0] in ['Maria', 'Ana'] else 'M',
                marital_status='married',
                email=user_data['email'],
                phone='3201234567',
                mobile='3201234567',
                address='Calle Laboratorio #456',
                city='Bogota',
                state='Cundinamarca',
                hire_date=date.today(),
                contract_type='indefinite',
                position=user_data['position'],
                department='Laboratorio Clinico',
                salary_type='fixed',
                basic_salary=6500000,
                created_by=admin_user
            )
            print(f"[+] Empleado creado: {employee.get_full_name()}")
        
        # Crear perfil de salud
        healthcare_role = HealthcareRole.objects.get(code=user_data['role'])
        lab_specialty = LaboratorySpecialty.objects.get(code=user_data['specialty'])
        
        profile, created = EmployeeHealthcareProfile.objects.get_or_create(
            employee=employee,
            defaults={
                'healthcare_role': healthcare_role,
                'laboratory_specialty': lab_specialty,
                'medical_license_number': f'RM-{user_data["code"][-3:]}',
                'assigned_department': 'Laboratorio Clinico',
                'years_experience': 8,
                'created_by': admin_user
            }
        )
        if created:
            print(f"[+] Perfil de salud creado para {employee.get_full_name()}")
        else:
            print(f"[-] Perfil de salud existe para {employee.get_full_name()}")
    
    print("\n=== SISTEMA DE LABORATORIO CREADO ===")
    print("USUARIOS DISPONIBLES:")
    print("* laboratorista / laboratorista123 (Especialista en Hematologia)")
    print("* citologo / citologo123 (Especialista en Ginecologia)")
    print("* supervisor_lab / supervisor123 (Control de Calidad)")
    print("\nTodos tienen acceso a empresa de salud y perfiles especializados")
    return True


if __name__ == "__main__":
    try:
        with transaction.atomic():
            create_lab_system()
    except Exception as e:
        print(f"ERROR: {e}")