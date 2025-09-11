"""
Comando para crear datos de demostración del módulo de ginecología
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from datetime import date, datetime
from decimal import Decimal

from core.models import Company, User
from third_parties.models import ThirdParty
from payroll.models import Employee, EmployeeType
from payroll.models_healthcare import (
    HealthcareRole, MedicalSpecialty, NursingSpecialty, 
    EmployeeHealthcareProfile
)
from gynecology.models import (
    Patient, GynecologyConsultationType, GynecologyProcedure,
    GynecologyAppointment
)


class Command(BaseCommand):
    help = 'Crea datos de demostración para el módulo de ginecología'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=str,
            help='ID de la empresa para crear los datos',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró la empresa con ID: {company_id}')
                )
                return
        else:
            # Usar la primera empresa de salud disponible
            company = Company.objects.filter(category='salud').first()
            if not company:
                # Usar la primera empresa disponible y convertirla a salud
                company = Company.objects.first()
                if company:
                    company.category = 'salud'
                    company.name = 'Hospital Nivel 4 Demo'
                    company.save()
                else:
                    self.stdout.write(
                        self.style.ERROR('No se encontraron empresas en el sistema')
                    )
                    return
                self.stdout.write(
                    self.style.SUCCESS(f'Empresa de salud creada: {company.name}')
                )

        # Obtener usuario admin para crear los registros
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@hospital.com',
                password='admin',
                is_staff=True,
                is_superuser=True
            )

        self.stdout.write(f'Creando datos para empresa: {company.name}')
        
        # 1. Crear roles de salud
        self.create_healthcare_roles(company, admin_user)
        
        # 2. Crear especialidades médicas
        self.create_medical_specialties(company, admin_user)
        
        # 3. Crear tipos de consulta ginecológica
        self.create_consultation_types(company, admin_user)
        
        # 4. Crear procedimientos ginecológicos
        self.create_procedures(company, admin_user)
        
        # 5. Crear empleado ginecólogo
        self.create_gynecologist_employee(company, admin_user)
        
        # 6. Crear pacientes de demostración
        self.create_sample_patients(company, admin_user)
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos de ginecología creados exitosamente!')
        )

    def create_healthcare_roles(self, company, admin_user):
        """Crear roles del sector salud"""
        roles = [
            {
                'code': 'MEDICO',
                'name': 'Médico Especialista',
                'description': 'Médico con especialización',
                'requires_license': True,
                'requires_specialty': True
            },
            {
                'code': 'MEDICO_GENERAL',
                'name': 'Médico General',
                'description': 'Médico general',
                'requires_license': True,
                'requires_specialty': False
            },
            {
                'code': 'ENFERMERA',
                'name': 'Enfermera Profesional',
                'description': 'Enfermera profesional',
                'requires_license': True,
                'requires_specialty': False
            },
            {
                'code': 'AUXILIAR_ENF',
                'name': 'Auxiliar de Enfermería',
                'description': 'Auxiliar de enfermería',
                'requires_license': False,
                'requires_specialty': False
            },
            {
                'code': 'RECEPCIONISTA',
                'name': 'Recepcionista',
                'description': 'Personal de recepción',
                'requires_license': False,
                'requires_specialty': False
            }
        ]
        
        for role_data in roles:
            role, created = HealthcareRole.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'requires_medical_license': role_data['requires_license'],
                    'requires_specialty': role_data['requires_specialty'],
                    'category': 'medico' if 'MEDICO' in role_data['code'] else 'administrativo'
                }
            )
            if created:
                self.stdout.write(f'  [OK] Rol creado: {role.name}')

    def create_medical_specialties(self, company, admin_user):
        """Crear especialidades médicas"""
        specialties = [
            {
                'code': 'GINECOLOGIA',
                'name': 'Ginecología y Obstetricia',
                'category': 'maternal_infant',
                'description': 'Especialidad en salud femenina, embarazo y parto'
            },
            {
                'code': 'MEDICINA_INTERNA',
                'name': 'Medicina Interna',
                'category': 'clinical',
                'description': 'Medicina interna y enfermedades sistémicas'
            },
            {
                'code': 'PEDIATRIA',
                'name': 'Pediatría',
                'category': 'maternal_infant',
                'description': 'Medicina pediátrica'
            },
            {
                'code': 'CARDIOLOGIA',
                'name': 'Cardiología',
                'category': 'clinical',
                'description': 'Especialidad cardiovascular'
            },
            {
                'code': 'ANESTESIA',
                'name': 'Anestesiología',
                'category': 'critical_care',
                'description': 'Anestesia y cuidados críticos'
            }
        ]
        
        for specialty_data in specialties:
            specialty, created = MedicalSpecialty.objects.get_or_create(
                code=specialty_data['code'],
                defaults={
                    'name': specialty_data['name'],
                    'category': specialty_data['category'],
                    'specialty_type': 'medica',
                    'description': specialty_data['description']
                }
            )
            if created:
                self.stdout.write(f'  [OK] Especialidad creada: {specialty.name}')

    def create_consultation_types(self, company, admin_user):
        """Crear tipos de consulta ginecológica"""
        consultation_types = [
            {
                'code': 'CONSULTA_GENERAL',
                'name': 'Consulta Ginecológica General',
                'description': 'Consulta ginecológica de rutina',
                'duration_minutes': 30,
                'base_price': Decimal('120000')
            },
            {
                'code': 'CONTROL_PRENATAL',
                'name': 'Control Prenatal',
                'description': 'Control de embarazo',
                'duration_minutes': 45,
                'base_price': Decimal('150000')
            },
            {
                'code': 'CONSULTA_PLANIFICACION',
                'name': 'Consulta de Planificación Familiar',
                'description': 'Asesoría en métodos anticonceptivos',
                'duration_minutes': 30,
                'base_price': Decimal('100000')
            },
            {
                'code': 'CITOLOGIA',
                'name': 'Citología Cervical',
                'description': 'Examen preventivo de cáncer cervical',
                'duration_minutes': 20,
                'base_price': Decimal('80000')
            },
            {
                'code': 'ECOGRAFIA_GINECOLOGICA',
                'name': 'Ecografía Ginecológica',
                'description': 'Ecografía transvaginal o abdominal',
                'duration_minutes': 30,
                'base_price': Decimal('180000')
            }
        ]
        
        for consult_data in consultation_types:
            consultation, created = GynecologyConsultationType.objects.get_or_create(
                company=company,
                code=consult_data['code'],
                defaults={
                    'name': consult_data['name'],
                    'description': consult_data['description'],
                    'duration_minutes': consult_data['duration_minutes'],
                    'base_price': consult_data['base_price'],
                    'created_by': admin_user
                }
            )
            if created:
                self.stdout.write(f'  [OK] Tipo de consulta creado: {consultation.name}')

    def create_procedures(self, company, admin_user):
        """Crear procedimientos ginecológicos"""
        procedures = [
            {
                'code': 'COLPOSCOPIA',
                'name': 'Colposcopia',
                'category': 'diagnostico',
                'description': 'Examen detallado del cuello uterino',
                'duration': 45,
                'price': Decimal('250000')
            },
            {
                'code': 'BIOPSIA_CERVICAL',
                'name': 'Biopsia Cervical',
                'category': 'diagnostico',
                'description': 'Toma de muestra para biopsia',
                'duration': 30,
                'price': Decimal('300000')
            },
            {
                'code': 'HISTEROSCOPIA',
                'name': 'Histeroscopia Diagnóstica',
                'category': 'diagnostico',
                'description': 'Visualización del interior del útero',
                'duration': 60,
                'price': Decimal('450000')
            },
            {
                'code': 'INSERCION_DIU',
                'name': 'Inserción de DIU',
                'category': 'ambulatorio',
                'description': 'Colocación de dispositivo intrauterino',
                'duration': 30,
                'price': Decimal('200000')
            },
            {
                'code': 'CRIOTERAPIA',
                'name': 'Crioterapia Cervical',
                'category': 'terapeutico',
                'description': 'Tratamiento con frío para lesiones cervicales',
                'duration': 20,
                'price': Decimal('350000')
            }
        ]
        
        for proc_data in procedures:
            procedure, created = GynecologyProcedure.objects.get_or_create(
                company=company,
                code=proc_data['code'],
                defaults={
                    'name': proc_data['name'],
                    'category': proc_data['category'],
                    'description': proc_data['description'],
                    'estimated_duration': proc_data['duration'],
                    'base_price': proc_data['price'],
                    'created_by': admin_user
                }
            )
            if created:
                self.stdout.write(f'  [OK] Procedimiento creado: {procedure.name}')

    def create_gynecologist_employee(self, company, admin_user):
        """Crear empleado ginecólogo con usuario"""
        # Obtener tipo de empleado
        employee_type, et_created = EmployeeType.objects.get_or_create(
            company=company,
            code='MEDICO',
            defaults={
                'name': 'Médico Especialista',
                'description': 'Personal médico especializado',
                'created_by': admin_user
            }
        )
        
        # Crear empleado directamente
        employee, created = Employee.objects.get_or_create(
            company=company,
            document_number='52123456',
            defaults={
                'employee_type': employee_type,
                'employee_code': 'GIN001',
                'document_type': 'CC',
                'first_name': 'Maria Alejandra',
                'last_name': 'Rodriguez Lopez',
                'birth_date': date(1985, 3, 15),
                'gender': 'F',
                'marital_status': 'single',
                'email': 'maria.rodriguez@hospital.com',
                'phone': '3201234567',
                'mobile': '3201234567',
                'address': 'Carrera 15 #85-30',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'hire_date': date(2020, 1, 15),
                'contract_type': 'indefinite',
                'position': 'Médica Ginecóloga',
                'department': 'Ginecología y Obstetricia',
                'salary_type': 'fixed',
                'basic_salary': Decimal('8000000'),
                'eps_name': 'Sanitas EPS',
                'pension_fund_name': 'Protección',
                'arl_name': 'Sura ARL',
                'created_by': admin_user
            }
        )
        
        if created:
            self.stdout.write(f'  [OK] Empleado creado: {employee.get_full_name()}')
        
        # Crear usuario para el empleado
        user, user_created = User.objects.get_or_create(
            username='ginecologo',
            defaults={
                'email': 'maria.rodriguez@hospital.com',
                'first_name': 'Maria Alejandra',
                'last_name': 'Rodriguez Lopez',
                'password': make_password('ginecologo123'),
                'is_active': True,
                'is_staff': True
            }
        )
        
        if user_created:
            self.stdout.write(f'  [OK] Usuario creado: {user.username}')
            self.stdout.write(f'     Email: {user.email}')
            self.stdout.write(f'     Contraseña: ginecologo123')
        
        # Nota: El empleado ya está creado, el usuario es independiente
        
        # Crear perfil de salud para el empleado
        healthcare_role = HealthcareRole.objects.filter(
            code='MEDICO'
        ).first()
        
        medical_specialty = MedicalSpecialty.objects.filter(
            code='GINECOLOGIA'
        ).first()
        
        if healthcare_role and medical_specialty:
            profile, profile_created = EmployeeHealthcareProfile.objects.get_or_create(
                employee=employee,
                defaults={
                    'healthcare_role': healthcare_role,
                    'medical_specialty': medical_specialty,
                    'medical_license_number': 'RM-12345',
                    'medical_license_expiry': date(2026, 12, 31),
                    'assigned_department': 'Ginecología y Obstetricia',
                    'years_experience': 10,
                    'created_by': admin_user
                }
            )
            
            if profile_created:
                self.stdout.write(f'  [OK] Perfil de salud creado para {employee.get_full_name()}')

    def create_sample_patients(self, company, admin_user):
        """Crear pacientes de demostración"""
        patients_data = [
            {
                'doc_number': '52987654',
                'name': 'Ana Maria',
                'last_name': 'Gonzalez',
                'birth_date': date(1990, 5, 20),
                'phone': '3101234567',
                'medical_record': 'HC001'
            },
            {
                'doc_number': '52876543',
                'name': 'Carmen Elena',
                'last_name': 'Martinez',
                'birth_date': date(1985, 8, 10),
                'phone': '3112345678',
                'medical_record': 'HC002'
            },
            {
                'doc_number': '52765432',
                'name': 'Luisa Fernanda',
                'last_name': 'Herrera',
                'birth_date': date(1992, 2, 28),
                'phone': '3123456789',
                'medical_record': 'HC003'
            }
        ]
        
        for patient_data in patients_data:
            # Crear tercero para la paciente
            third_party, tp_created = ThirdParty.objects.get_or_create(
                company=company,
                document_type='CC',
                document_number=patient_data['doc_number'],
                defaults={
                    'person_type': 'NATURAL',
                    'first_name': patient_data['name'],
                    'last_name': patient_data['last_name'],
                    'gender': 'F',
                    'birth_date': patient_data['birth_date'],
                    'address': f'Calle {patient_data["doc_number"][-2:]} #{patient_data["doc_number"][-4:-2]}-{patient_data["doc_number"][-2:]}',
                    'city': 'Bogotá',
                    'state': 'Cundinamarca',
                    'phone': patient_data['phone'],
                    'email': f'{patient_data["name"].lower().replace(" ", "")}.{patient_data["last_name"].lower()}@email.com',
                    'is_customer': True,  # Las pacientes son clientes
                    'created_by': admin_user
                }
            )
            
            # Crear paciente
            patient, p_created = Patient.objects.get_or_create(
                company=company,
                medical_record_number=patient_data['medical_record'],
                defaults={
                    'third_party': third_party,
                    'blood_type': 'O+',
                    'insurance_type': 'eps',
                    'eps_name': 'Sanitas EPS',
                    'insurance_number': f'EPS{patient_data["doc_number"]}',
                    'emergency_contact_name': 'Contacto de Emergencia',
                    'emergency_contact_phone': '3001111111',
                    'emergency_contact_relationship': 'Familiar',
                    'pregnancies': 1,
                    'births': 1,
                    'abortions': 0,
                    'cesarean_sections': 0,
                    'created_by': admin_user
                }
            )
            
            if p_created:
                self.stdout.write(f'  [OK] Paciente creada: {patient.get_full_name()}')