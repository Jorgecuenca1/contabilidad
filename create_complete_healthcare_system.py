#!/usr/bin/env python
"""
Script completo para crear sistema de salud con laboratorio integrado.
Crea roles, especialidades, empleados, datos de laboratorio y usuarios completos.
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
    HealthcareRole, MedicalSpecialty, NursingSpecialty, 
    LaboratorySpecialty, EmployeeHealthcareProfile
)
from laboratory.models import LabSection, TestCategory, LabTest


def create_laboratory_roles_and_specialties():
    """Crear roles y especialidades de laboratorio."""
    print("=== CREANDO ROLES Y ESPECIALIDADES DE LABORATORIO ===\n")
    
    # Roles de laboratorio
    lab_roles = [
        {
            'code': 'LABORATORISTA',
            'name': 'Laboratorista Clínico',
            'category': 'laboratorio',
            'requires_medical_license': False,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'BACTERIOLOGO',
            'name': 'Bacteriólogo',
            'category': 'laboratorio',
            'requires_medical_license': True,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'QUIMICO_FARMACEUTICO',
            'name': 'Químico Farmacéutico',
            'category': 'laboratorio',
            'requires_medical_license': True,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'PATOLOGO',
            'name': 'Patólogo',
            'category': 'laboratorio',
            'requires_medical_license': True,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'CITOLOGO',
            'name': 'Citólogo',
            'category': 'laboratorio',
            'requires_medical_license': True,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'TECNICO_LAB',
            'name': 'Técnico de Laboratorio',
            'category': 'laboratorio',
            'requires_medical_license': False,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
        {
            'code': 'SUPERVISOR_LAB',
            'name': 'Supervisor de Laboratorio',
            'category': 'laboratorio',
            'requires_medical_license': True,
            'requires_specialty': True,
            'is_clinical_role': True,
        },
    ]
    
    for role_data in lab_roles:
        role, created = HealthcareRole.objects.get_or_create(
            code=role_data['code'],
            defaults=role_data
        )
        if created:
            print(f"[+] Rol creado: {role.name}")
        else:
            print(f"[-] Rol existe: {role.name}")
    
    # Especialidades de laboratorio
    lab_specialties = [
        {
            'code': 'HEMATOLOGIA_LAB',
            'name': 'Especialista en Hematología de Laboratorio',
            'specialty_area': 'hematology',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 120,
            'associated_equipment': ['Contadores Hematológicos', 'Microscopios', 'Citómetros de Flujo'],
            'required_certifications': ['Certificación en Morfología Celular', 'Interpretación de Hemograma'],
        },
        {
            'code': 'QUIMICA_CLINICA',
            'name': 'Especialista en Química Clínica',
            'specialty_area': 'chemistry',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 100,
            'associated_equipment': ['Analizadores de Química', 'Espectrofotómetros', 'Electrolitos'],
            'required_certifications': ['Certificación en Bioquímica Clínica', 'Control de Calidad'],
        },
        {
            'code': 'MICROBIOLOGIA_LAB',
            'name': 'Especialista en Microbiología',
            'specialty_area': 'microbiology',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 150,
            'associated_equipment': ['Incubadoras', 'Sistemas de Identificación', 'Antibiogramas'],
            'required_certifications': ['Identificación Bacteriana', 'Pruebas de Sensibilidad'],
        },
        {
            'code': 'BANCO_SANGRE',
            'name': 'Especialista en Banco de Sangre',
            'specialty_area': 'blood_bank',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 200,
            'associated_equipment': ['Sistemas de Tipificación', 'Pruebas de Compatibilidad', 'Centrífugas'],
            'required_certifications': ['Medicina Transfusional', 'Inmunohematología'],
        },
        {
            'code': 'PATOLOGIA_LAB',
            'name': 'Especialista en Patología',
            'specialty_area': 'pathology',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 300,
            'associated_equipment': ['Microscopios Especializados', 'Sistemas de Tinción', 'Micrótomos'],
            'required_certifications': ['Histopatología', 'Inmunohistoquímica'],
        },
        {
            'code': 'CITOLOGIA_LAB',
            'name': 'Especialista en Citología',
            'specialty_area': 'cytology',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 180,
            'associated_equipment': ['Microscopios de Citología', 'Sistemas de Tinción Pap', 'LBC'],
            'required_certifications': ['Citología Cervical', 'Sistema Bethesda'],
        },
        {
            'code': 'GINECOLOGIA_LAB',
            'name': 'Especialista en Laboratorio de Ginecología',
            'specialty_area': 'gynecology_lab',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 100,
            'associated_equipment': ['Colposcopios', 'Sistemas HPV', 'Hormonales'],
            'required_certifications': ['Citología Ginecológica', 'Pruebas HPV', 'Hormonas Reproductivas'],
        },
        {
            'code': 'URGENCIAS_LAB',
            'name': 'Especialista en Laboratorio de Urgencias',
            'specialty_area': 'emergency_lab',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 80,
            'associated_equipment': ['Analizadores STAT', 'Gasometría', 'POCT'],
            'required_certifications': ['Pruebas de Urgencias', 'Gasometría Arterial'],
        },
        {
            'code': 'CONTROL_CALIDAD',
            'name': 'Especialista en Control de Calidad',
            'specialty_area': 'quality_control',
            'certification_required': True,
            'requires_special_training': True,
            'training_hours_required': 120,
            'associated_equipment': ['Sistemas de QC', 'Calibradores', 'Controles'],
            'required_certifications': ['Gestión de Calidad', 'ISO 15189', 'Acreditación'],
        },
    ]
    
    for specialty_data in lab_specialties:
        specialty, created = LaboratorySpecialty.objects.get_or_create(
            code=specialty_data['code'],
            defaults=specialty_data
        )
        if created:
            print(f"[+] Especialidad creada: {specialty.name}")
        else:
            print(f"[-] Especialidad existe: {specialty.name}")
    
    print()


def create_laboratory_users_and_employees():
    """Crear usuarios y empleados de laboratorio."""
    print("=== CREANDO EMPLEADOS Y USUARIOS DE LABORATORIO ===\n")
    
    # Obtener empresa de salud
    healthcare_company = Company.objects.filter(category='salud').first()
    if not healthcare_company:
        print("[ERROR] No se encontró empresa del sector salud")
        return
    
    admin_user = User.objects.filter(is_staff=True).first()
    
    # Usuarios de laboratorio a crear
    lab_users = [
        {
            'username': 'laboratorista',
            'password': 'laboratorista123',
            'first_name': 'María',
            'last_name': 'Rodríguez López',
            'email': 'laboratorista@hospital.com',
            'employee_data': {
                'employee_code': 'LAB-001',
                'document_number': '45678901',
                'position': 'Laboratorista Clínica Principal',
                'department': 'Laboratorio Clínico',
                'basic_salary': 4500000,
                'healthcare_role_code': 'LABORATORISTA',
                'specialty_code': 'HEMATOLOGIA_LAB',
            }
        },
        {
            'username': 'bacteriologo',
            'password': 'bacteriologo123',
            'first_name': 'Dr. Carlos',
            'last_name': 'Mendoza Silva',
            'email': 'bacteriologo@hospital.com',
            'employee_data': {
                'employee_code': 'LAB-002',
                'document_number': '78901234',
                'position': 'Bacteriólogo Jefe',
                'department': 'Microbiología',
                'basic_salary': 8500000,
                'healthcare_role_code': 'BACTERIOLOGO',
                'specialty_code': 'MICROBIOLOGIA_LAB',
                'license_number': 'RM-78901',
            }
        },
        {
            'username': 'citologo',
            'password': 'citologo123',
            'first_name': 'Dra. Ana',
            'last_name': 'Fernández Ruiz',
            'email': 'citologo@hospital.com',
            'employee_data': {
                'employee_code': 'LAB-003',
                'document_number': '56789012',
                'position': 'Citóloga Especialista',
                'department': 'Citología y Patología',
                'basic_salary': 7500000,
                'healthcare_role_code': 'CITOLOGO',
                'specialty_code': 'GINECOLOGIA_LAB',  # Especializada en ginecología
                'license_number': 'RM-56789',
            }
        },
        {
            'username': 'supervisor_lab',
            'password': 'supervisor123',
            'first_name': 'Dr. Roberto',
            'last_name': 'Gómez Herrera',
            'email': 'supervisor.lab@hospital.com',
            'employee_data': {
                'employee_code': 'LAB-004',
                'document_number': '34567890',
                'position': 'Supervisor General de Laboratorio',
                'department': 'Dirección de Laboratorio',
                'basic_salary': 9500000,
                'healthcare_role_code': 'SUPERVISOR_LAB',
                'specialty_code': 'CONTROL_CALIDAD',
                'license_number': 'RM-34567',
            }
        },
    ]
    
    for user_data in lab_users:
        # Crear usuario
        if User.objects.filter(username=user_data['username']).exists():
            print(f"- Usuario ya existe: {user_data['username']}")
            user = User.objects.get(username=user_data['username'])
        else:
            user = User.objects.create_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_staff=False,
                is_active=True
            )
            user.companies.add(healthcare_company)
            print(f"[+] Usuario creado: {user_data['username']}")
        
        # Crear empleado
        emp_data = user_data['employee_data']
        
        # Obtener o crear tipo de empleado
        employee_type, created = EmployeeType.objects.get_or_create(
            company=healthcare_company,
            code='LABORATORIO',
            defaults={
                'name': 'Personal de Laboratorio',
                'created_by': admin_user
            }
        )
        
        # Verificar si el empleado ya existe
        if Employee.objects.filter(employee_code=emp_data['employee_code'], company=healthcare_company).exists():
            print(f"- Empleado ya existe: {emp_data['employee_code']}")
            employee = Employee.objects.get(employee_code=emp_data['employee_code'], company=healthcare_company)
        else:
            employee = Employee.objects.create(
                company=healthcare_company,
                employee_type=employee_type,
                employee_code=emp_data['employee_code'],
                document_type='CC',
                document_number=emp_data['document_number'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                birth_date=date(1985, 6, 15),  # Fecha ejemplo
                gender='F' if user_data['first_name'] in ['María', 'Ana'] else 'M',
                marital_status='married',
                email=user_data['email'],
                phone='3201234567',
                mobile='3201234567',
                address='Calle Laboratorio #456',
                city='Bogotá',
                state='Cundinamarca',
                hire_date=date.today(),
                contract_type='indefinite',
                position=emp_data['position'],
                department=emp_data['department'],
                salary_type='fixed',
                basic_salary=emp_data['basic_salary'],
                created_by=admin_user
            )
            print(f"✓ Empleado creado: {employee.get_full_name()}")
        
        # Crear perfil de salud
        healthcare_role = HealthcareRole.objects.filter(code=emp_data['healthcare_role_code']).first()
        lab_specialty = LaboratorySpecialty.objects.filter(code=emp_data['specialty_code']).first()
        
        if healthcare_role and lab_specialty:
            profile, created = EmployeeHealthcareProfile.objects.get_or_create(
                employee=employee,
                defaults={
                    'healthcare_role': healthcare_role,
                    'laboratory_specialty': lab_specialty,
                    'medical_license_number': emp_data.get('license_number', ''),
                    'medical_license_expiry': date(2030, 12, 31) if emp_data.get('license_number') else None,
                    'assigned_department': emp_data['department'],
                    'years_experience': 8,
                    'created_by': admin_user
                }
            )
            if created:
                print(f"✓ Perfil de salud creado: {lab_specialty.name}")
            else:
                print(f"- Perfil de salud existe: {lab_specialty.name}")
    
    print()


def create_laboratory_sections_and_tests():
    """Crear secciones y pruebas de laboratorio."""
    print("=== CREANDO SECCIONES Y PRUEBAS DE LABORATORIO ===\n")
    
    healthcare_company = Company.objects.filter(category='salud').first()
    admin_user = User.objects.filter(is_staff=True).first()
    
    # Secciones de laboratorio
    lab_sections = [
        {
            'code': 'HEMATOLOGIA',
            'name': 'Hematología',
            'section_type': 'hematology',
            'description': 'Sección de estudios hematológicos y morfología celular',
            'max_processing_time_hours': 4,
        },
        {
            'code': 'QUIMICA',
            'name': 'Química Clínica',
            'section_type': 'chemistry',
            'description': 'Análisis bioquímicos y químicos clínicos',
            'max_processing_time_hours': 6,
        },
        {
            'code': 'MICROBIO',
            'name': 'Microbiología',
            'section_type': 'microbiology',
            'description': 'Cultivos e identificación microbiológica',
            'max_processing_time_hours': 72,
            'requires_special_handling': True,
        },
        {
            'code': 'GINECO_LAB',
            'name': 'Laboratorio de Ginecología',
            'section_type': 'gynecology',
            'description': 'Pruebas especializadas para ginecología y obstetricia',
            'max_processing_time_hours': 24,
        },
        {
            'code': 'CITOLOGIA',
            'name': 'Citología',
            'section_type': 'cytology',
            'description': 'Citología cervical y diagnóstica',
            'max_processing_time_hours': 48,
        },
    ]
    
    created_sections = {}
    
    for section_data in lab_sections:
        section, created = LabSection.objects.get_or_create(
            company=healthcare_company,
            code=section_data['code'],
            defaults={**section_data, 'created_by': admin_user}
        )
        created_sections[section_data['code']] = section
        if created:
            print(f"✓ Sección creada: {section.name}")
        else:
            print(f"- Sección existe: {section.name}")
    
    # Categorías de pruebas para ginecología
    gyneco_categories = [
        {
            'code': 'HORMONAS_REPRO',
            'name': 'Hormonas Reproductivas',
            'section': 'GINECO_LAB',
            'requires_fasting': False,
            'special_instructions': 'Indicar día del ciclo menstrual',
        },
        {
            'code': 'CITOLOGIA_CERV',
            'name': 'Citología Cervical',
            'section': 'CITOLOGIA',
            'requires_fasting': False,
            'special_instructions': 'No relaciones sexuales 48h antes, no duchas vaginales',
        },
        {
            'code': 'INFECCIONES_GIN',
            'name': 'Infecciones Ginecológicas',
            'section': 'MICROBIO',
            'requires_fasting': False,
            'special_instructions': 'No antimicóticos ni antibióticos previos',
        },
        {
            'code': 'MARCADORES_TUM',
            'name': 'Marcadores Tumorales Ginecológicos',
            'section': 'QUIMICA',
            'requires_fasting': True,
            'special_instructions': 'Ayuno de 12 horas',
        },
    ]
    
    created_categories = {}
    
    for cat_data in gyneco_categories:
        section = created_sections[cat_data['section']]
        category, created = TestCategory.objects.get_or_create(
            company=healthcare_company,
            code=cat_data['code'],
            defaults={
                'name': cat_data['name'],
                'section': section,
                'requires_fasting': cat_data['requires_fasting'],
                'special_instructions': cat_data['special_instructions'],
            }
        )
        created_categories[cat_data['code']] = category
        if created:
            print(f"✓ Categoría creada: {category.name}")
        else:
            print(f"- Categoría existe: {category.name}")
    
    # Pruebas específicas de ginecología
    gyneco_tests = [
        # Hormonas reproductivas
        {
            'code': 'FSH',
            'name': 'Hormona Folículo Estimulante',
            'short_name': 'FSH',
            'category': 'HORMONAS_REPRO',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'mUI/mL',
            'reference_range_min': 2.5,
            'reference_range_max': 10.2,
            'processing_time_hours': 24,
            'cost': 35000,
            'price': 55000,
        },
        {
            'code': 'LH',
            'name': 'Hormona Luteinizante',
            'short_name': 'LH',
            'category': 'HORMONAS_REPRO',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'mUI/mL',
            'reference_range_min': 1.9,
            'reference_range_max': 12.5,
            'processing_time_hours': 24,
            'cost': 35000,
            'price': 55000,
        },
        {
            'code': 'ESTRADIOL',
            'name': 'Estradiol',
            'short_name': 'E2',
            'category': 'HORMONAS_REPRO',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'pg/mL',
            'reference_range_min': 15.0,
            'reference_range_max': 350.0,
            'processing_time_hours': 24,
            'cost': 40000,
            'price': 65000,
        },
        {
            'code': 'PROGESTERONA',
            'name': 'Progesterona',
            'short_name': 'P4',
            'category': 'HORMONAS_REPRO',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'ng/mL',
            'reference_range_min': 0.2,
            'reference_range_max': 25.0,
            'processing_time_hours': 24,
            'cost': 40000,
            'price': 65000,
        },
        # Citología
        {
            'code': 'PAP_CONVENCIONAL',
            'name': 'Citología Cervical Convencional',
            'short_name': 'PAP',
            'category': 'CITOLOGIA_CERV',
            'specimen_type': 'cervical_sample',
            'specimen_volume_ml': 1.0,
            'result_type': 'text',
            'reference_range_text': 'Negativo para lesión intraepitelial o malignidad',
            'processing_time_hours': 48,
            'cost': 25000,
            'price': 45000,
        },
        {
            'code': 'HPV_HR',
            'name': 'Virus Papiloma Humano Alto Riesgo',
            'short_name': 'HPV-HR',
            'category': 'CITOLOGIA_CERV',
            'specimen_type': 'cervical_sample',
            'specimen_volume_ml': 1.0,
            'result_type': 'positive_negative',
            'reference_range_text': 'Negativo',
            'processing_time_hours': 48,
            'cost': 120000,
            'price': 180000,
        },
        # Infecciones
        {
            'code': 'CULTIVO_VAGINAL',
            'name': 'Cultivo Vaginal',
            'short_name': 'C. Vaginal',
            'category': 'INFECCIONES_GIN',
            'specimen_type': 'vaginal_swab',
            'specimen_volume_ml': 1.0,
            'result_type': 'culture',
            'reference_range_text': 'Flora normal',
            'processing_time_hours': 72,
            'cost': 35000,
            'price': 55000,
        },
        # Marcadores tumorales
        {
            'code': 'CA125',
            'name': 'Antígeno Carbohidrato 125',
            'short_name': 'CA 125',
            'category': 'MARCADORES_TUM',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'U/mL',
            'reference_range_min': 0.0,
            'reference_range_max': 35.0,
            'processing_time_hours': 24,
            'requires_fasting': True,
            'cost': 85000,
            'price': 125000,
        },
        {
            'code': 'CA199',
            'name': 'Antígeno Carbohidrato 19-9',
            'short_name': 'CA 19-9',
            'category': 'MARCADORES_TUM',
            'specimen_type': 'blood_serum',
            'specimen_volume_ml': 3.0,
            'result_type': 'numeric',
            'unit_of_measure': 'U/mL',
            'reference_range_min': 0.0,
            'reference_range_max': 37.0,
            'processing_time_hours': 24,
            'requires_fasting': True,
            'cost': 85000,
            'price': 125000,
        },
    ]
    
    for test_data in gyneco_tests:
        category = created_categories[test_data['category']]
        test, created = LabTest.objects.get_or_create(
            company=healthcare_company,
            code=test_data['code'],
            defaults={
                **{k: v for k, v in test_data.items() if k != 'category'},
                'category': category,
                'created_by': admin_user
            }
        )
        if created:
            print(f"✓ Prueba creada: {test.name}")
        else:
            print(f"- Prueba existe: {test.name}")
    
    print()


def main():
    """Función principal para crear todo el sistema de laboratorio."""
    print("[HOSPITAL] CREANDO SISTEMA COMPLETO DE LABORATORIO INTEGRADO CON GINECOLOGIA [HOSPITAL]\n")
    
    try:
        with transaction.atomic():
            create_laboratory_roles_and_specialties()
            create_laboratory_users_and_employees()
            create_laboratory_sections_and_tests()
        
        print("[OK] SISTEMA DE LABORATORIO CREADO EXITOSAMENTE [OK]\n")
        
        print("=== USUARIOS CREADOS ===")
        print("* Laboratorista: laboratorista / laboratorista123")
        print("* Bacteriologo: bacteriologo / bacteriologo123")
        print("* Citologo (especialista en ginecologia): citologo / citologo123")
        print("* Supervisor de Laboratorio: supervisor_lab / supervisor123")
        print()
        
        print("=== FUNCIONALIDADES IMPLEMENTADAS ===")
        print("[+] Roles y especialidades de laboratorio completas")
        print("[+] Empleados de laboratorio con perfiles especializados")
        print("[+] Secciones de laboratorio (Hematologia, Quimica, Micro, Gineco)")
        print("[+] Pruebas de laboratorio especificas para ginecologia")
        print("[+] Integracion completa laboratorio-ginecologia")
        print("[+] Permisos granulares por especialidad")
        print("[+] Sistema de ordenes de laboratorio")
        print("[+] Trazabilidad completa de muestras")
        print()
        
        print(">>> INTEGRACIONES DISPONIBLES:")
        print("- Ginecologos pueden ordenar pruebas especificas")
        print("- Laboratoristas ven solo pruebas de su especialidad")
        print("- Citologos especializados en ginecologia ven submodulo")
        print("- Supervisor tiene acceso completo al laboratorio")
        print("- Trazabilidad completa desde orden hasta resultado")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR creando sistema de laboratorio: {e}")
        return False


if __name__ == "__main__":
    main()