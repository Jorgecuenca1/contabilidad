#!/usr/bin/env python
"""
Script para crear sistema completo de usuarios y permisos para todos los módulos de salud.
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import transaction
from core.models import Company, User
from core.models_modules import SystemModule, CompanyModule, UserModulePermission
from payroll.models import Employee, EmployeeType
from payroll.models_healthcare import HealthcareRole, MedicalSpecialty, LaboratorySpecialty, EmployeeHealthcareProfile


def create_complete_healthcare_system():
    """Crear sistema completo de usuarios y permisos."""
    print("=== CREANDO SISTEMA COMPLETO DE SALUD ===")
    
    # Buscar empresa de salud y admin
    healthcare_company = Company.objects.filter(category='salud').first()
    admin_user = User.objects.filter(username='admin').first()
    
    if not healthcare_company or not admin_user:
        print("[ERROR] No se encontró empresa de salud o usuario admin")
        return False
    
    print(f"Empresa de salud: {healthcare_company.name}")
    print(f"Usuario admin: {admin_user.username}")
    
    # 1. Crear módulos actualizados del sistema
    healthcare_modules = [
        {
            'code': 'medical_records',
            'name': 'Historia Clínica',
            'description': 'Gestión completa de historias clínicas - Médicos ven sus pacientes, Admin ve todo',
            'category': 'healthcare',
            'url_pattern': 'medical-records',
            'icon_class': 'bi-file-medical',
            'requires_company_category': 'salud',
        },
        {
            'code': 'medical_appointments',
            'name': 'Citas Médicas',
            'description': 'Sistema de agendamiento médico con selección de doctores por especialidad',
            'category': 'healthcare',
            'url_pattern': 'medical-appointments',
            'icon_class': 'bi-calendar-check',
            'requires_company_category': 'salud',
        },
        {
            'code': 'medical_procedures',
            'name': 'Procedimientos Médicos',
            'description': 'Gestión de procedimientos médicos con códigos CUPS',
            'category': 'healthcare',
            'url_pattern': 'medical-procedures',
            'icon_class': 'bi-clipboard2-pulse',
            'requires_company_category': 'salud',
        },
        {
            'code': 'laboratory',
            'name': 'Laboratorio Clínico',
            'description': 'Sistema de información de laboratorio (LIS) - Solo personal autorizado',
            'category': 'healthcare',
            'url_pattern': 'laboratory',
            'icon_class': 'bi-thermometer-half',
            'requires_company_category': 'salud',
        },
        {
            'code': 'gynecology',
            'name': 'Ginecología',
            'description': 'Módulo especializado en ginecología y obstetricia',
            'category': 'healthcare',
            'url_pattern': 'gynecology',
            'icon_class': 'bi-heart-pulse',
            'requires_company_category': 'salud',
        },
    ]
    
    # Crear/actualizar módulos
    for module_data in healthcare_modules:
        module, created = SystemModule.objects.update_or_create(
            code=module_data['code'],
            defaults=module_data
        )
        if created:
            print(f"[+] Módulo creado: {module_data['name']}")
        else:
            print(f"[~] Módulo actualizado: {module_data['name']}")
    
    # 2. Activar todos los módulos para la empresa de salud
    print(f"\n=== Activando módulos para {healthcare_company.name} ===")
    healthcare_modules_obj = SystemModule.objects.filter(category='healthcare')
    
    for module in healthcare_modules_obj:
        company_module, created = CompanyModule.objects.get_or_create(
            company=healthcare_company,
            module=module,
            defaults={
                'is_enabled': True,
                'enabled_by': admin_user,
            }
        )
        if created:
            print(f"[+] Módulo activado: {module.name}")
        else:
            print(f"[-] Ya activo: {module.name}")
    
    # 3. Configurar permisos para usuario admin (puede ver todo)
    print(f"\n=== Configurando permisos para Admin ===")
    all_company_modules = CompanyModule.objects.filter(company=healthcare_company)
    
    for company_module in all_company_modules:
        permission, created = UserModulePermission.objects.get_or_create(
            user=admin_user,
            company_module=company_module,
            defaults={
                'permission_level': 'admin',
                'granted_by': admin_user,
            }
        )
        if created:
            print(f"[+] Permiso admin creado: {company_module.module.name}")
        else:
            print(f"[-] Permiso admin existe: {company_module.module.name}")
    
    # 4. Crear usuarios médicos especializados
    print(f"\n=== Creando usuarios médicos especializados ===")
    
    medical_users = [
        {
            'username': 'ginecologo_jefe',
            'password': 'ginecologo123',
            'name': 'Dr. Carlos Medina Ruiz',
            'email': 'ginecologo.jefe@hospital.com',
            'role': 'MEDICO_GINECOLOGO',
            'specialty': 'GINECOLOGIA_ONCOLOGICA',
            'code': 'MED-001',
            'position': 'Jefe de Ginecología',
            'modules': ['medical_records', 'medical_appointments', 'medical_procedures', 'gynecology'],
            'permission_level': 'admin',  # Admin del módulo de ginecología
        },
        {
            'username': 'ginecologo',
            'password': 'ginecologo123',
            'name': 'Dra. Ana Patricia Gonzalez',
            'email': 'ginecologo@hospital.com',
            'role': 'MEDICO_GINECOLOGO',
            'specialty': 'GINECOLOGIA_GENERAL',
            'code': 'MED-002',
            'position': 'Ginecóloga',
            'modules': ['medical_records', 'medical_appointments', 'medical_procedures', 'gynecology'],
            'permission_level': 'edit',
        },
        {
            'username': 'medico_general',
            'password': 'medico123',
            'name': 'Dr. Roberto Martinez Silva',
            'email': 'medico.general@hospital.com',
            'role': 'MEDICO_GENERAL',
            'specialty': 'MEDICINA_GENERAL',
            'code': 'MED-003',
            'position': 'Médico General',
            'modules': ['medical_records', 'medical_appointments', 'medical_procedures'],
            'permission_level': 'edit',
        },
        {
            'username': 'laboratorista_jefe',
            'password': 'laboratorio123',
            'name': 'Dra. Maria Rodriguez Lopez',
            'email': 'laboratorista.jefe@hospital.com',
            'role': 'SUPERVISOR_LAB',
            'specialty': 'CONTROL_CALIDAD',
            'code': 'LAB-001',
            'position': 'Supervisora de Laboratorio',
            'modules': ['laboratory', 'medical_records'],  # Ve historia clínica para resultados
            'permission_level': 'admin',  # Admin del laboratorio
        },
        {
            'username': 'laboratorista',
            'password': 'laboratorio123',
            'name': 'Lic. Juan Carlos Perez',
            'email': 'laboratorista@hospital.com',
            'role': 'LABORATORISTA',
            'specialty': 'HEMATOLOGIA_LAB',
            'code': 'LAB-002',
            'position': 'Laboratorista Clínico',
            'modules': ['laboratory'],
            'permission_level': 'edit',
        },
        {
            'username': 'bacteriologo',
            'password': 'bacteriologo123',
            'name': 'Dra. Carmen Lucia Torres',
            'email': 'bacteriologo@hospital.com',
            'role': 'BACTERIOLOGO',
            'specialty': 'MICROBIOLOGIA_LAB',
            'code': 'LAB-003',
            'position': 'Bacterióloga',
            'modules': ['laboratory'],
            'permission_level': 'edit',
        },
        {
            'username': 'citologo',
            'password': 'citologo123',
            'name': 'Dra. Patricia Herrera Vega',
            'email': 'citologo@hospital.com',
            'role': 'CITOLOGO',
            'specialty': 'GINECOLOGIA_LAB',
            'code': 'LAB-004',
            'position': 'Citóloga Especialista',
            'modules': ['laboratory', 'gynecology'],  # Puede ver ginecología para citologías
            'permission_level': 'edit',
        },
    ]
    
    for user_data in medical_users:
        # Crear usuario
        user_doc_number = f"{abs(hash(user_data['username'] + '_user')) % 100000000:08d}"
        
        if User.objects.filter(username=user_data['username']).exists():
            user = User.objects.get(username=user_data['username'])
            print(f"[-] Usuario existe: {user_data['username']}")
        else:
            name_parts = user_data['name'].split()
            first_name = ' '.join(name_parts[:2]) if len(name_parts) > 2 else name_parts[0]
            last_name = ' '.join(name_parts[2:]) if len(name_parts) > 2 else name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data['email'],
                first_name=first_name,
                last_name=last_name,
                document_number=user_doc_number,
                role='contador',  # Role que permite acceso a módulos
                is_staff=False,
                is_active=True
            )
            user.companies.add(healthcare_company)
            print(f"[+] Usuario creado: {user_data['username']}")
        
        # Crear empleado
        employee_type, _ = EmployeeType.objects.get_or_create(
            company=healthcare_company,
            code='PERSONAL_MEDICO',
            defaults={'name': 'Personal Médico', 'created_by': admin_user}
        )
        
        if Employee.objects.filter(employee_code=user_data['code'], company=healthcare_company).exists():
            employee = Employee.objects.get(employee_code=user_data['code'], company=healthcare_company)
            print(f"[-] Empleado existe: {user_data['code']}")
        else:
            name_parts = user_data['name'].split()
            first_name = ' '.join(name_parts[:2]) if len(name_parts) > 2 else name_parts[0]
            last_name = ' '.join(name_parts[2:]) if len(name_parts) > 2 else name_parts[1] if len(name_parts) > 1 else ''
            
            employee = Employee.objects.create(
                company=healthcare_company,
                employee_type=employee_type,
                employee_code=user_data['code'],
                document_type='CC',
                document_number=f"{abs(hash(user_data['username'] + user_data['code'])) % 100000000:08d}",
                first_name=first_name,
                last_name=last_name,
                birth_date=date(1980, 1, 15),
                gender='F' if 'Dra.' in user_data['name'] or 'Ana' in user_data['name'] or 'Maria' in user_data['name'] or 'Carmen' in user_data['name'] or 'Patricia' in user_data['name'] else 'M',
                marital_status='married',
                email=user_data['email'],
                phone='3201234567',
                mobile='3201234567',
                address='Calle Médica #123',
                city='Bogota',
                state='Cundinamarca',
                hire_date=date.today(),
                contract_type='indefinite',
                position=user_data['position'],
                department='Área Médica',
                salary_type='fixed',
                basic_salary=12000000 if 'jefe' in user_data['username'] else 8000000,
                created_by=admin_user
            )
            print(f"[+] Empleado creado: {employee.get_full_name()}")
        
        # Crear perfil médico
        try:
            if user_data['role'] in ['LABORATORISTA', 'BACTERIOLOGO', 'CITOLOGO', 'SUPERVISOR_LAB']:
                # Perfil de laboratorio
                healthcare_role = HealthcareRole.objects.get(code=user_data['role'])
                lab_specialty = LaboratorySpecialty.objects.get(code=user_data['specialty'])
                
                profile, created = EmployeeHealthcareProfile.objects.get_or_create(
                    employee=employee,
                    defaults={
                        'healthcare_role': healthcare_role,
                        'laboratory_specialty': lab_specialty,
                        'medical_license_number': f'RM-{user_data["code"][-3:]}',
                        'assigned_department': 'Laboratorio Clínico',
                        'years_experience': 10,
                        'created_by': admin_user
                    }
                )
            else:
                # Perfil médico
                healthcare_role = HealthcareRole.objects.get(code=user_data['role'])
                medical_specialty = MedicalSpecialty.objects.get(code=user_data['specialty'])
                
                profile, created = EmployeeHealthcareProfile.objects.get_or_create(
                    employee=employee,
                    defaults={
                        'healthcare_role': healthcare_role,
                        'medical_specialty': medical_specialty,
                        'medical_license_number': f'RM-{user_data["code"][-3:]}',
                        'assigned_department': 'Área Médica',
                        'years_experience': 10,
                        'created_by': admin_user
                    }
                )
            
            if created:
                print(f"[+] Perfil médico creado para {employee.get_full_name()}")
        except Exception as e:
            print(f"[!] Error creando perfil para {employee.get_full_name()}: {e}")
        
        # Configurar permisos de módulos
        print(f"  Configurando permisos para {user.username}:")
        for module_code in user_data['modules']:
            try:
                module = SystemModule.objects.get(code=module_code)
                company_module = CompanyModule.objects.get(company=healthcare_company, module=module)
                
                permission, created = UserModulePermission.objects.get_or_create(
                    user=user,
                    company_module=company_module,
                    defaults={
                        'permission_level': user_data['permission_level'],
                        'granted_by': admin_user,
                    }
                )
                
                if created:
                    print(f"    [+] Permiso {user_data['permission_level']} para {module.name}")
                else:
                    print(f"    [-] Permiso existe para {module.name}")
            except Exception as e:
                print(f"    [!] Error configurando permiso para {module_code}: {e}")
    
    print("\n=== SISTEMA COMPLETO DE SALUD CONFIGURADO ===")
    print("USUARIOS DISPONIBLES:")
    print("* admin/admin (Administrador - Ve TODOS los módulos)")
    print("* ginecologo_jefe/ginecologo123 (Jefe Ginecología - Admin módulos ginecología)")
    print("* ginecologo/ginecologo123 (Ginecóloga - Sus pacientes)")
    print("* medico_general/medico123 (Médico General - Sus pacientes)")
    print("* laboratorista_jefe/laboratorio123 (Jefe Lab - Admin laboratorio + historia clínica)")
    print("* laboratorista/laboratorio123 (Laboratorista - Solo laboratorio)")
    print("* bacteriologo/bacteriologo123 (Bacterióloga - Solo laboratorio)")
    print("* citologo/citologo123 (Citóloga - Laboratorio + ginecología)")
    
    print("\nPERMISOS CONFIGURADOS:")
    print("• Admin: Todos los módulos (nivel admin)")
    print("• Médicos: Historia clínica (sus pacientes), citas, procedimientos")
    print("• Laboratorio: Solo personal autorizado puede acceder")
    print("• Historia Clínica: Médicos ven sus pacientes, Admin ve todo")
    
    return True


if __name__ == "__main__":
    try:
        with transaction.atomic():
            create_complete_healthcare_system()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()