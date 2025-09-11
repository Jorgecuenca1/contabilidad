#!/usr/bin/env python
"""
Script para crear códigos CUPS básicos de ginecología y otros procedimientos.
"""

import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import transaction
from medical_procedures.models import CUPSCode
from decimal import Decimal


def create_basic_cups_codes():
    """Crear códigos CUPS básicos."""
    print("=== CREANDO CODIGOS CUPS BASICOS ===")
    
    # Códigos CUPS de Ginecología
    gynecology_cups = [
        {
            'cups_code': '890201',
            'short_description': 'Consulta Ginecológica Primera Vez',
            'description': 'Consulta médica especializada en ginecología para primera vez con examen físico completo',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 45,
            'base_price': Decimal('120000'),
            'professional_fee': Decimal('80000'),
            'institutional_fee': Decimal('40000'),
            'requires_pre_authorization': False,
        },
        {
            'cups_code': '890202',
            'short_description': 'Consulta Ginecológica Control',
            'description': 'Consulta médica especializada en ginecología para control y seguimiento',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 30,
            'base_price': Decimal('90000'),
            'professional_fee': Decimal('60000'),
            'institutional_fee': Decimal('30000'),
            'requires_pre_authorization': False,
        },
        {
            'cups_code': '873101',
            'short_description': 'Citología Cérvico-Uterina',
            'description': 'Toma de muestra para citología cervical (Papanicolaou) con evaluación microscópica',
            'category': 'ginecologia',
            'complexity': 'baja',
            'specialty_required': 'Ginecología',
            'estimated_duration': 15,
            'base_price': Decimal('35000'),
            'professional_fee': Decimal('20000'),
            'institutional_fee': Decimal('15000'),
            'requires_pre_authorization': False,
            'preparation_instructions': 'No estar menstruando, no haber tenido relaciones sexuales 48 horas antes',
        },
        {
            'cups_code': '876201',
            'short_description': 'Colposcopia Diagnóstica',
            'description': 'Examen colposcópico del cuello uterino para evaluación de lesiones cervicales',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 30,
            'base_price': Decimal('150000'),
            'professional_fee': Decimal('100000'),
            'institutional_fee': Decimal('50000'),
            'requires_pre_authorization': True,
        },
        {
            'cups_code': '651201',
            'short_description': 'Biopsia de Cuello Uterino',
            'description': 'Toma de biopsia del cuello uterino bajo visualización colposcópica',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 45,
            'base_price': Decimal('200000'),
            'professional_fee': Decimal('150000'),
            'institutional_fee': Decimal('50000'),
            'requires_pre_authorization': True,
            'post_procedure_care': 'Reposo relativo 24 horas, no duchas vaginales por 1 semana',
        },
        {
            'cups_code': '652301',
            'short_description': 'Legrado Uterino Diagnóstico',
            'description': 'Legrado endometrial para diagnóstico histopatológico',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 60,
            'base_price': Decimal('300000'),
            'professional_fee': Decimal('200000'),
            'institutional_fee': Decimal('100000'),
            'requires_anesthesia': True,
            'requires_pre_authorization': True,
        },
        {
            'cups_code': '653401',
            'short_description': 'Histeroscopia Diagnóstica',
            'description': 'Visualización endoscópica de la cavidad uterina con fines diagnósticos',
            'category': 'ginecologia',
            'complexity': 'alta',
            'specialty_required': 'Ginecología',
            'estimated_duration': 45,
            'base_price': Decimal('400000'),
            'professional_fee': Decimal('300000'),
            'institutional_fee': Decimal('100000'),
            'requires_anesthesia': True,
            'requires_pre_authorization': True,
        },
        {
            'cups_code': '659901',
            'short_description': 'Inserción DIU',
            'description': 'Inserción de dispositivo intrauterino anticonceptivo',
            'category': 'ginecologia',
            'complexity': 'media',
            'specialty_required': 'Ginecología',
            'estimated_duration': 30,
            'base_price': Decimal('180000'),
            'professional_fee': Decimal('120000'),
            'institutional_fee': Decimal('60000'),
            'requires_pre_authorization': False,
            'post_procedure_care': 'Control en 1 mes, vigilar signos de alarma',
        },
    ]
    
    # Códigos CUPS de Laboratorio
    laboratory_cups = [
        {
            'cups_code': '902210',
            'short_description': 'Hemograma Completo',
            'description': 'Hemograma completo con recuento diferencial de leucocitos',
            'category': 'laboratorio',
            'complexity': 'baja',
            'specialty_required': 'Laboratorio Clínico',
            'estimated_duration': 30,
            'base_price': Decimal('25000'),
            'professional_fee': Decimal('15000'),
            'institutional_fee': Decimal('10000'),
            'requires_pre_authorization': False,
        },
        {
            'cups_code': '903815',
            'short_description': 'Glicemia en Ayunas',
            'description': 'Determinación de glucosa en sangre en ayunas',
            'category': 'laboratorio',
            'complexity': 'baja',
            'specialty_required': 'Laboratorio Clínico',
            'estimated_duration': 15,
            'base_price': Decimal('12000'),
            'professional_fee': Decimal('8000'),
            'institutional_fee': Decimal('4000'),
            'requires_pre_authorization': False,
            'preparation_instructions': 'Ayuno de 8-12 horas',
        },
        {
            'cups_code': '904467',
            'short_description': 'Perfil Hormonal Femenino',
            'description': 'Determinación de hormonas FSH, LH, Estradiol, Progesterona',
            'category': 'laboratorio',
            'complexity': 'media',
            'specialty_required': 'Laboratorio Clínico',
            'estimated_duration': 60,
            'base_price': Decimal('150000'),
            'professional_fee': Decimal('100000'),
            'institutional_fee': Decimal('50000'),
            'requires_pre_authorization': True,
            'preparation_instructions': 'Tomar muestra en día específico del ciclo según indicación médica',
        },
        {
            'cups_code': '906039',
            'short_description': 'Beta HCG Cuantitativa',
            'description': 'Determinación cuantitativa de gonadotropina coriónica humana beta',
            'category': 'laboratorio',
            'complexity': 'media',
            'specialty_required': 'Laboratorio Clínico',
            'estimated_duration': 45,
            'base_price': Decimal('35000'),
            'professional_fee': Decimal('25000'),
            'institutional_fee': Decimal('10000'),
            'requires_pre_authorization': False,
        },
    ]
    
    # Códigos CUPS de Consulta General
    general_cups = [
        {
            'cups_code': '890101',
            'short_description': 'Consulta Medicina General Primera Vez',
            'description': 'Consulta médica general para primera vez con examen físico completo',
            'category': 'consulta',
            'complexity': 'baja',
            'specialty_required': 'Medicina General',
            'estimated_duration': 30,
            'base_price': Decimal('60000'),
            'professional_fee': Decimal('40000'),
            'institutional_fee': Decimal('20000'),
            'requires_pre_authorization': False,
        },
        {
            'cups_code': '890102',
            'short_description': 'Consulta Medicina General Control',
            'description': 'Consulta médica general para control y seguimiento',
            'category': 'consulta',
            'complexity': 'baja',
            'specialty_required': 'Medicina General',
            'estimated_duration': 20,
            'base_price': Decimal('45000'),
            'professional_fee': Decimal('30000'),
            'institutional_fee': Decimal('15000'),
            'requires_pre_authorization': False,
        },
    ]
    
    # Códigos CUPS de Imágenes Diagnósticas
    imaging_cups = [
        {
            'cups_code': '876301',
            'short_description': 'Ecografía Pélvica Transvaginal',
            'description': 'Ecografía transvaginal para evaluación de órganos pélvicos femeninos',
            'category': 'imagenes',
            'complexity': 'media',
            'specialty_required': 'Radiología',
            'estimated_duration': 30,
            'base_price': Decimal('120000'),
            'professional_fee': Decimal('80000'),
            'institutional_fee': Decimal('40000'),
            'requires_pre_authorization': False,
            'preparation_instructions': 'Vejiga vacía para ecografía transvaginal',
        },
        {
            'cups_code': '876302',
            'short_description': 'Ecografía Obstétrica',
            'description': 'Ecografía obstétrica para control prenatal y seguimiento fetal',
            'category': 'imagenes',
            'complexity': 'media',
            'specialty_required': 'Radiología',
            'estimated_duration': 45,
            'base_price': Decimal('150000'),
            'professional_fee': Decimal('100000'),
            'institutional_fee': Decimal('50000'),
            'requires_pre_authorization': False,
        },
    ]
    
    # Crear todos los códigos
    all_cups = gynecology_cups + laboratory_cups + general_cups + imaging_cups
    
    for cups_data in all_cups:
        cups_code, created = CUPSCode.objects.get_or_create(
            cups_code=cups_data['cups_code'],
            defaults=cups_data
        )
        if created:
            print(f"[+] CUPS creado: {cups_data['cups_code']} - {cups_data['short_description']}")
        else:
            print(f"[-] CUPS existe: {cups_data['cups_code']} - {cups_data['short_description']}")
    
    print(f"\n=== CODIGOS CUPS CONFIGURADOS ===")
    print(f"Total códigos CUPS creados: {len(all_cups)}")
    print("\nCategorías disponibles:")
    categories = CUPSCode.objects.values_list('category', flat=True).distinct()
    for category in categories:
        count = CUPSCode.objects.filter(category=category).count()
        print(f"* {category.title()}: {count} códigos")
    
    return True


if __name__ == "__main__":
    try:
        with transaction.atomic():
            create_basic_cups_codes()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()