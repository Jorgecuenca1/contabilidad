"""
Modelos específicos para el sector salud en el sistema de nómina.
"""

from django.db import models
import uuid
from core.models import Company, User


class CompanyCategory(models.Model):
    """
    Categorías de empresa (salud, educación, manufactura, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuraciones específicas por categoría
    requires_specialties = models.BooleanField(default=False, help_text="Requiere especialidades profesionales")
    has_patients = models.BooleanField(default=False, help_text="Maneja pacientes/clientes especiales")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_company_categories'
        verbose_name = 'Categoría de Empresa'
        verbose_name_plural = 'Categorías de Empresa'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class HealthcareRole(models.Model):
    """
    Roles específicos del sector salud.
    """
    CATEGORY_CHOICES = [
        ('medico', 'Médicos'),
        ('enfermeria', 'Enfermería'),
        ('laboratorio', 'Personal de Laboratorio'),
        ('tecnico', 'Técnicos Especializados'),
        ('administrativo', 'Personal Administrativo'),
        ('servicios', 'Servicios Generales'),
        ('apoyo', 'Personal de Apoyo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Configuraciones específicas
    requires_medical_license = models.BooleanField(default=False)
    requires_specialty = models.BooleanField(default=False)
    is_clinical_role = models.BooleanField(default=False, help_text="Rol clínico con contacto directo con pacientes")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_healthcare_roles'
        verbose_name = 'Rol de Salud'
        verbose_name_plural = 'Roles de Salud'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name}"


class MedicalSpecialty(models.Model):
    """
    Especialidades médicas y de enfermería.
    """
    SPECIALTY_TYPE_CHOICES = [
        ('medica', 'Especialidad Médica'),
        ('enfermeria', 'Especialidad de Enfermería'),
        ('tecnica', 'Especialidad Técnica'),
    ]
    
    CATEGORY_CHOICES = [
        ('clinica', 'Especialidades Clínicas'),
        ('quirurgica', 'Especialidades Quirúrgicas'),
        ('materno_infantil', 'Materno-Infantiles'),
        ('apoyo_diagnostico', 'Apoyo Diagnóstico'),
        ('laboratorio', 'Especialidades de Laboratorio'),
        ('cuidados_criticos', 'Cuidados Críticos'),
        ('salud_mental', 'Salud Mental'),
        ('medicina_preventiva', 'Medicina Preventiva'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    specialty_type = models.CharField(max_length=20, choices=SPECIALTY_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Departamento al que pertenece
    department = models.CharField(max_length=100, blank=True)
    
    # Configuraciones
    requires_subspecialty = models.BooleanField(default=False)
    years_of_training = models.IntegerField(default=0, help_text="Años de formación especializada")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_medical_specialties'
        verbose_name = 'Especialidad Médica'
        verbose_name_plural = 'Especialidades Médicas'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name}"


class NursingSpecialty(models.Model):
    """
    Especialidades específicas de enfermería.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Configuraciones específicas de enfermería
    certification_required = models.BooleanField(default=False)
    continuing_education_hours = models.IntegerField(default=0, help_text="Horas de educación continua requeridas anualmente")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_nursing_specialties'
        verbose_name = 'Especialidad de Enfermería'
        verbose_name_plural = 'Especialidades de Enfermería'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}"


class EmployeeHealthcareProfile(models.Model):
    """
    Perfil específico de salud para empleados del sector sanitario.
    Extiende la información del Employee con datos específicos del sector salud.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='healthcare_profile')
    
    # Rol en salud
    healthcare_role = models.ForeignKey(HealthcareRole, on_delete=models.PROTECT, null=True, blank=True)
    
    # Especialidades
    medical_specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.PROTECT, null=True, blank=True)
    nursing_specialty = models.ForeignKey(NursingSpecialty, on_delete=models.PROTECT, null=True, blank=True)
    laboratory_specialty = models.ForeignKey('LaboratorySpecialty', on_delete=models.PROTECT, null=True, blank=True)
    subspecialty = models.CharField(max_length=200, blank=True, help_text="Subespecialidad adicional")
    
    # Licencias y certificaciones
    medical_license_number = models.CharField(max_length=50, blank=True, help_text="Número de registro médico")
    medical_license_expiry = models.DateField(null=True, blank=True)
    nursing_license_number = models.CharField(max_length=50, blank=True, help_text="Número de tarjeta profesional de enfermería")
    nursing_license_expiry = models.DateField(null=True, blank=True)
    
    # Certificaciones adicionales
    certifications = models.JSONField(default=list, help_text="Lista de certificaciones adicionales")
    
    # Departamento específico
    assigned_department = models.CharField(max_length=100, blank=True, help_text="Departamento específico asignado")
    shift_schedule = models.CharField(max_length=50, blank=True, help_text="Horario de turno")
    
    # Experiencia
    years_experience = models.IntegerField(default=0, help_text="Años de experiencia en el área")
    
    # Estado de la licencia
    license_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'payroll_employee_healthcare_profiles'
        verbose_name = 'Perfil de Salud del Empleado'
        verbose_name_plural = 'Perfiles de Salud de Empleados'
    
    def __str__(self):
        return f"Perfil de salud - {self.employee.get_full_name()}"
    
    def get_primary_specialty(self):
        """Retorna la especialidad principal del empleado."""
        if self.medical_specialty:
            return self.medical_specialty.name
        elif self.nursing_specialty:
            return self.nursing_specialty.name
        elif self.laboratory_specialty:
            return self.laboratory_specialty.name
        elif self.healthcare_role:
            return self.healthcare_role.name
        return "Sin especialidad"
    
    def is_licensed_professional(self):
        """Verifica si es un profesional con licencia activa."""
        if self.medical_license_number and self.license_active:
            return True
        if self.nursing_license_number and self.license_active:
            return True
        return False


class LaboratorySpecialty(models.Model):
    """
    Especialidades específicas de laboratorio clínico.
    """
    SPECIALTY_AREAS = [
        ('hematology', 'Hematología'),
        ('chemistry', 'Química Clínica'),
        ('microbiology', 'Microbiología'),
        ('pathology', 'Patología'),
        ('molecular', 'Diagnóstico Molecular'),
        ('blood_bank', 'Banco de Sangre'),
        ('immunology', 'Inmunología'),
        ('cytology', 'Citología'),
        ('toxicology', 'Toxicología'),
        ('parasitology', 'Parasitología'),
        ('mycology', 'Micología'),
        ('virology', 'Virología'),
        ('gynecology_lab', 'Laboratorio de Ginecología'),
        ('emergency_lab', 'Laboratorio de Urgencias'),
        ('quality_control', 'Control de Calidad'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    specialty_area = models.CharField(max_length=20, choices=SPECIALTY_AREAS)
    description = models.TextField(blank=True)
    
    # Configuraciones específicas de laboratorio
    certification_required = models.BooleanField(default=False)
    requires_special_training = models.BooleanField(default=False)
    training_hours_required = models.IntegerField(default=0, help_text="Horas de capacitación requeridas")
    
    # Equipos y tecnologías asociadas
    associated_equipment = models.JSONField(default=list, help_text="Lista de equipos específicos")
    required_certifications = models.JSONField(default=list, help_text="Certificaciones requeridas")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_laboratory_specialties'
        verbose_name = 'Especialidad de Laboratorio'
        verbose_name_plural = 'Especialidades de Laboratorio'
        ordering = ['specialty_area', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_specialty_area_display()})"