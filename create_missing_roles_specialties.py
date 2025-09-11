#!/usr/bin/env python
"""
Script para crear roles y especialidades médicas faltantes.
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import transaction
from payroll.models_healthcare import HealthcareRole, MedicalSpecialty, NursingSpecialty, LaboratorySpecialty


def create_missing_roles_specialties():
    """Crear roles y especialidades médicas faltantes."""
    print("=== CREANDO ROLES Y ESPECIALIDADES FALTANTES ===")
    
    # Roles médicos adicionales
    additional_medical_roles = [
        ('MEDICO_GENERAL', 'Médico General', 'medicina'),
        ('MEDICO_GINECOLOGO', 'Médico Ginecólogo', 'ginecologia'),
        ('MEDICO_ESPECIALISTA', 'Médico Especialista', 'especialidad'),
        ('JEFE_SERVICIO', 'Jefe de Servicio Médico', 'administracion'),
    ]
    
    for code, name, category in additional_medical_roles:
        role, created = HealthcareRole.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'category': category,
                'requires_medical_license': True,
                'requires_specialty': True,
                'is_clinical_role': True,
            }
        )
        if created:
            print(f"[+] Rol creado: {name}")
        else:
            print(f"[-] Rol existe: {name}")
    
    # Especialidades médicas adicionales
    additional_medical_specialties = [
        ('MEDICINA_GENERAL', 'Medicina General', 'medica', 'clinica', 'Medicina general y familiar'),
        ('GINECOLOGIA_GENERAL', 'Ginecología General', 'medica', 'materno_infantil', 'Ginecología y obstetricia general'),
        ('GINECOLOGIA_ONCOLOGICA', 'Ginecología Oncológica', 'medica', 'materno_infantil', 'Ginecología oncológica especializada'),
        ('OBSTETRICIA', 'Obstetricia', 'medica', 'materno_infantil', 'Especialidad en obstetricia'),
        ('MEDICINA_INTERNA', 'Medicina Interna', 'medica', 'clinica', 'Medicina interna para adultos'),
        ('PEDIATRIA', 'Pediatría', 'medica', 'materno_infantil', 'Medicina pediátrica'),
        ('CIRUGIA_GENERAL', 'Cirugía General', 'medica', 'quirurgica', 'Cirugía general'),
        ('ANESTESIOLOGIA', 'Anestesiología', 'medica', 'quirurgica', 'Anestesia y reanimación'),
        ('RADIOLOGIA', 'Radiología', 'medica', 'apoyo_diagnostico', 'Imágenes diagnósticas'),
        ('PATOLOGIA', 'Patología', 'medica', 'apoyo_diagnostico', 'Anatomía patológica'),
        ('URGENCIAS', 'Medicina de Urgencias', 'medica', 'cuidados_criticos', 'Medicina de emergencias'),
        ('CARDIOLOGIA', 'Cardiología', 'medica', 'clinica', 'Especialidad cardiovascular'),
    ]
    
    for code, name, specialty_type, category, description in additional_medical_specialties:
        specialty, created = MedicalSpecialty.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'specialty_type': specialty_type,
                'category': category,
                'description': description,
                'years_of_training': 4,
            }
        )
        if created:
            print(f"[+] Especialidad médica creada: {name}")
        else:
            print(f"[-] Especialidad médica existe: {name}")
    
    print("\n=== ROLES Y ESPECIALIDADES CONFIGURADOS ===")
    print(f"Total roles: {HealthcareRole.objects.count()}")
    print(f"Total especialidades médicas: {MedicalSpecialty.objects.count()}")
    print(f"Total especialidades de laboratorio: {LaboratorySpecialty.objects.count()}")
    
    return True


if __name__ == "__main__":
    try:
        with transaction.atomic():
            create_missing_roles_specialties()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()