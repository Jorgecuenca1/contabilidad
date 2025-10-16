"""
Utilidades para generación de RIPS
Funciones para exportar archivos RIPS en formato JSON y TXT
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


def get_patient_rips_data(patient):
    """
    Extraer datos del paciente en formato RIPS
    """
    third_party = patient.third_party

    # Tipo de documento
    doc_type_map = {
        'CC': 'CC',
        'TI': 'TI',
        'CE': 'CE',
        'PA': 'PA',
        'RC': 'RC',
        'MS': 'MS',
        'AS': 'AS',
    }

    # Tipo de usuario según régimen
    regime_map = {
        'contributivo': '01',
        'subsidiado': '02',
        'vinculado': '03',
        'particular': '04',
        'especial': '05',
    }

    # Sexo
    gender_map = {
        'M': 'M',
        'F': 'F',
        'masculino': 'M',
        'femenino': 'F',
    }

    return {
        'tipoDocumentoIdentificacion': doc_type_map.get(third_party.document_type, 'CC'),
        'numDocumentoIdentificacion': third_party.document_number,
        'tipoUsuario': regime_map.get(patient.regime_type, '04'),
        'fechaNacimiento': third_party.birth_date.strftime('%Y-%m-%d') if third_party.birth_date else '',
        'codSexo': gender_map.get(third_party.gender, 'M'),
        'codPaisResidencia': '170',  # Colombia
        'codMunicipioResidencia': getattr(patient, 'birth_municipality', '05001'),  # Por defecto Medellín
        'codZonaTerritorialResidencia': '01',  # Urbana por defecto
        'incapacidad': 'NO',
        'codPaisOrigen': '170',
    }


def get_service_rips_data(invoice_item, consecutivo):
    """
    Convertir un HealthInvoiceItem en datos RIPS según su tipo
    Retorna dict con tipo de registro y datos
    """
    data = {
        'codPrestador': invoice_item.invoice.company.nit or '800037021',
        'numAutorizacion': invoice_item.authorization_number or '',
        'vrServicio': float(invoice_item.total_amount),
        'conceptoRecaudo': '05',  # Cuota moderadora
        'valorPagoModerador': float(invoice_item.moderator_fee or 0),
        'numFEVPagoModerador': '',
        'consecutivo': consecutivo,
    }

    # Extraer datos del servicio original si existe
    service = invoice_item.service_object

    if invoice_item.service_type == 'consultation':
        # RIPS Consulta (AC)
        return {
            'tipo': 'consulta',
            'data': {
                **data,
                'fechaInicioAtencion': invoice_item.service_date.strftime('%Y-%m-%d %H:%M'),
                'codConsulta': invoice_item.service_code or '890701',  # Consulta medicina general
                'modalidadGrupoServicioTecSal': '01',  # Intramural
                'grupoServicios': '01',  # Consulta externa
                'codServicio': 110,
                'finalidadTecnologiaSalud': '10',  # Diagnóstico
                'causaMotivoAtencion': '21',  # Enfermedad general
                'codDiagnosticoPrincipal': invoice_item.diagnosis_code or 'Z000',
                'codDiagnosticoRelacionado1': '',
                'codDiagnosticoRelacionado2': '',
                'codDiagnosticoRelacionado3': '',
                'tipoDiagnosticoPrincipal': '01',  # Impresión diagnóstica
                'tipoDocumentoIdentificacion': 'CC',
                'numDocumentoIdentificacion': invoice_item.invoice.created_by.username if invoice_item.invoice.created_by else '0',
            }
        }

    elif invoice_item.service_type == 'procedure':
        # RIPS Procedimiento (AP)
        return {
            'tipo': 'procedimiento',
            'data': {
                **data,
                'fechaInicioAtencion': invoice_item.service_date.strftime('%Y-%m-%d %H:%M'),
                'idMIPRES': '',
                'codProcedimiento': invoice_item.service_code or '871111',
                'viaIngresoServicioSalud': '01',  # Consulta externa
                'modalidadGrupoServicioTecSal': '01',
                'grupoServicios': '03',  # Procedimientos
                'codServicio': 300,
                'finalidadTecnologiaSalud': '02',  # Tratamiento
                'tipoDocumentoIdentificacion': 'CC',
                'numDocumentoIdentificacion': invoice_item.invoice.created_by.username if invoice_item.invoice.created_by else '0',
                'codDiagnosticoPrincipal': invoice_item.diagnosis_code or 'Z000',
                'codDiagnosticoRelacionado': '',
                'codComplicacion': '',
            }
        }

    elif invoice_item.service_type == 'medication':
        # RIPS Medicamento (AM)
        dispensing = service if service else None
        return {
            'tipo': 'medicamento',
            'data': {
                **data,
                'fechaDispensAdmon': invoice_item.service_date.strftime('%Y-%m-%d %H:%M'),
                'idMIPRES': '',
                'codDiagnosticoPrincipal': invoice_item.diagnosis_code or 'Z000',
                'codDiagnosticoRelacionado': '',
                'tipoMedicamento': '01',  # POS
                'codTecnologiaSalud': invoice_item.service_code or '19934768-18',
                'nomTecnologiaSalud': invoice_item.service_name or 'Medicamento',
                'concentracionMedicamento': 0,
                'unidadMedida': 159,
                'formaFarmaceutica': 'COLFF004',
                'unidadMinDispensa': 74,
                'cantidadMedicamento': float(invoice_item.quantity),
                'diasTratamiento': 1,
                'tipoDocumentoIdentificacion': 'CC',
                'numDocumentoIdentificacion': invoice_item.invoice.patient.document_number if invoice_item.invoice.patient else '0',
                'vrUnitMedicamento': float(invoice_item.unit_price),
            }
        }

    elif invoice_item.service_type in ['imaging', 'laboratory', 'other']:
        # RIPS Otros Servicios (AT)
        return {
            'tipo': 'otro_servicio',
            'data': {
                **data,
                'fechaSuministroTecnologia': invoice_item.service_date.strftime('%Y-%m-%d %H:%M'),
                'idMIPRES': '',
                'tipoOS': '01',  # Insumo
                'codTecnologiaSalud': invoice_item.service_code or 'SRV001',
                'nomTecnologiaSalud': invoice_item.service_name or 'Servicio',
                'cantidadOS': float(invoice_item.quantity),
                'tipoDocumentoIdentificacion': 'CC',
                'numDocumentoIdentificacion': invoice_item.invoice.patient.document_number if invoice_item.invoice.patient else '0',
                'vrUnitOS': float(invoice_item.unit_price),
            }
        }

    # Default: otro servicio
    return {
        'tipo': 'otro_servicio',
        'data': {
            **data,
            'fechaSuministroTecnologia': invoice_item.service_date.strftime('%Y-%m-%d %H:%M'),
            'idMIPRES': '',
            'tipoOS': '01',
            'codTecnologiaSalud': invoice_item.service_code or 'SRV001',
            'nomTecnologiaSalud': invoice_item.service_name or 'Servicio',
            'cantidadOS': float(invoice_item.quantity),
            'tipoDocumentoIdentificacion': 'CC',
            'numDocumentoIdentificacion': invoice_item.invoice.patient.document_number if invoice_item.invoice.patient else '0',
            'vrUnitOS': float(invoice_item.unit_price),
        }
    }


def generate_rips_json(invoice):
    """
    Generar estructura RIPS en formato JSON según normativa MinSalud
    """
    # Obtener paciente
    patient = None
    if hasattr(invoice, 'episode') and invoice.episode:
        patient = invoice.episode.patient

    if not patient:
        # Buscar paciente por third_party
        from patients.models import Patient
        if invoice.patient:
            try:
                patient = Patient.objects.get(third_party=invoice.patient)
            except Patient.DoesNotExist:
                pass

    if not patient:
        raise ValueError("No se puede generar RIPS sin datos del paciente")

    # Datos del paciente
    patient_data = get_patient_rips_data(patient)

    # Servicios por tipo
    consultas = []
    procedimientos = []
    medicamentos = []
    otros_servicios = []

    consecutivo = 1
    for item in invoice.items.all().order_by('created_at'):
        service_data = get_service_rips_data(item, consecutivo)

        if service_data['tipo'] == 'consulta':
            consultas.append(service_data['data'])
        elif service_data['tipo'] == 'procedimiento':
            procedimientos.append(service_data['data'])
        elif service_data['tipo'] == 'medicamento':
            medicamentos.append(service_data['data'])
        elif service_data['tipo'] == 'otro_servicio':
            otros_servicios.append(service_data['data'])

        consecutivo += 1

    # Estructura RIPS completa
    rips_data = {
        'numDocumentoIdObligado': invoice.company.nit or '800037021',
        'numFactura': invoice.invoice_number,
        'tipoNota': None,
        'numNota': None,
        'usuarios': [{
            **patient_data,
            'consecutivo': 1,
            'servicios': {}
        }]
    }

    # Agregar servicios solo si existen
    if consultas:
        rips_data['usuarios'][0]['servicios']['consultas'] = consultas
    if procedimientos:
        rips_data['usuarios'][0]['servicios']['procedimientos'] = procedimientos
    if medicamentos:
        rips_data['usuarios'][0]['servicios']['medicamentos'] = medicamentos
    if otros_servicios:
        rips_data['usuarios'][0]['servicios']['otrosServicios'] = otros_servicios

    return rips_data


def generate_rips_txt(invoice):
    """
    Generar archivos RIPS en formato TXT pipe-delimited (legacy)
    Retorna dict con nombre_archivo: contenido
    """
    # TODO: Implementar formato TXT pipe-delimited
    # Estructura: US|AF|AC|AP|AM|AT|AU|AH|AN
    # Por ahora retornamos estructura básica

    files = {}

    # Archivo de control (CT)
    ct_content = f"{invoice.company.nit}|{invoice.invoice_number}|{datetime.now().strftime('%Y%m%d')}\n"
    files['CT.txt'] = ct_content

    # Archivo de usuarios (US)
    us_content = ""
    # TODO: Implementar
    files['US.txt'] = us_content

    # Archivo de consultas (AC)
    ac_content = ""
    # TODO: Implementar
    files['AC.txt'] = ac_content

    return files


def save_rips_files(rips_data, invoice, format='json'):
    """
    Guardar archivos RIPS en el filesystem
    """
    # Crear directorio para RIPS si no existe
    rips_dir = os.path.join(settings.MEDIA_ROOT, 'rips', str(invoice.company.id))
    os.makedirs(rips_dir, exist_ok=True)

    # Nombre base del archivo
    base_name = f"RIPS_{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if format == 'json':
        file_path = os.path.join(rips_dir, f"{base_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rips_data, f, indent=2, ensure_ascii=False)
        return file_path

    elif format == 'txt':
        # TODO: Guardar múltiples archivos TXT
        pass

    return None


def add_service_to_episode(episode, service, service_type, user):
    """
    Helper para agregar un servicio a un episodio de atención
    """
    from rips.models import EpisodeService
    from django.contrib.contenttypes.models import ContentType

    # Obtener costo del servicio
    service_cost = 0
    if hasattr(service, 'total_amount'):
        service_cost = service.total_amount
    elif hasattr(service, 'total_cost'):
        service_cost = service.total_cost
    elif hasattr(service, 'total_stay_cost'):
        service_cost = service.total_stay_cost

    # Crear vínculo
    ct = ContentType.objects.get_for_model(service)
    episode_service = EpisodeService.objects.create(
        episode=episode,
        service_type=service_type,
        content_type=ct,
        object_id=service.pk,
        service_cost=service_cost,
        added_by=user
    )

    return episode_service
