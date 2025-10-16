"""
Vistas del módulo de Pacientes
Sistema completo de gestión de pacientes para IPS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
import json

from core.decorators import company_required
from core.utils import get_current_company
from .models import Patient, EPS, PatientInsuranceHistory, PatientDocument
from third_parties.models import ThirdParty


@login_required
@company_required
def patient_dashboard(request):
    """Dashboard principal del módulo de pacientes"""
    company = get_current_company(request)

    # Estadísticas
    total_patients = Patient.objects.filter(company=company, is_active=True).count()
    new_patients_month = Patient.objects.filter(
        company=company,
        registration_date__year=timezone.now().year,
        registration_date__month=timezone.now().month
    ).count()

    # Pacientes por régimen
    patients_by_regime = Patient.objects.filter(
        company=company,
        is_active=True
    ).values('regime_type').annotate(count=Count('id')).order_by('-count')

    # Pacientes por EPS (Top 10)
    patients_by_eps = Patient.objects.filter(
        company=company,
        is_active=True,
        eps__isnull=False
    ).values('eps__name').annotate(count=Count('id')).order_by('-count')[:10]

    # Pacientes recientes
    recent_patients = Patient.objects.filter(
        company=company
    ).select_related('third_party', 'eps').order_by('-created_at')[:10]

    # Pacientes con última visita (más activos)
    active_patients = Patient.objects.filter(
        company=company,
        is_active=True,
        last_visit_date__isnull=False
    ).select_related('third_party').order_by('-last_visit_date')[:10]

    context = {
        'total_patients': total_patients,
        'new_patients_month': new_patients_month,
        'patients_by_regime': patients_by_regime,
        'patients_by_eps': patients_by_eps,
        'recent_patients': recent_patients,
        'active_patients': active_patients,
    }

    return render(request, 'patients/dashboard.html', context)


@login_required
@company_required
def patient_list(request):
    """Lista de pacientes con búsqueda avanzada y filtros"""
    company = get_current_company(request)

    # Filtros
    search = request.GET.get('search', '')
    eps_filter = request.GET.get('eps', '')
    regime_filter = request.GET.get('regime', '')
    blood_type_filter = request.GET.get('blood_type', '')
    age_range = request.GET.get('age_range', '')
    gender_filter = request.GET.get('gender', '')
    active_only = request.GET.get('active', 'true') == 'true'

    patients = Patient.objects.filter(company=company).select_related('third_party', 'eps')

    if active_only:
        patients = patients.filter(is_active=True, is_deceased=False)

    # Búsqueda general
    if search:
        patients = patients.filter(
            Q(medical_record_number__icontains=search) |
            Q(third_party__first_name__icontains=search) |
            Q(third_party__last_name__icontains=search) |
            Q(third_party__second_last_name__icontains=search) |
            Q(third_party__document_number__icontains=search) |
            Q(third_party__phone__icontains=search) |
            Q(third_party__email__icontains=search) |
            Q(insurance_number__icontains=search)
        )

    # Filtros específicos
    if eps_filter:
        patients = patients.filter(eps_id=eps_filter)

    if regime_filter:
        patients = patients.filter(regime_type=regime_filter)

    if blood_type_filter:
        patients = patients.filter(blood_type=blood_type_filter)

    if gender_filter:
        patients = patients.filter(third_party__gender=gender_filter)

    # Filtro por rango de edad
    if age_range:
        today = date.today()
        if age_range == '0-1':
            start_date = today.replace(year=today.year - 1)
            patients = patients.filter(third_party__birth_date__gte=start_date)
        elif age_range == '1-12':
            start_date = today.replace(year=today.year - 12)
            end_date = today.replace(year=today.year - 1)
            patients = patients.filter(third_party__birth_date__range=[start_date, end_date])
        elif age_range == '13-17':
            start_date = today.replace(year=today.year - 17)
            end_date = today.replace(year=today.year - 13)
            patients = patients.filter(third_party__birth_date__range=[start_date, end_date])
        elif age_range == '18-59':
            start_date = today.replace(year=today.year - 59)
            end_date = today.replace(year=today.year - 18)
            patients = patients.filter(third_party__birth_date__range=[start_date, end_date])
        elif age_range == '60+':
            end_date = today.replace(year=today.year - 60)
            patients = patients.filter(third_party__birth_date__lte=end_date)

    # Ordenamiento
    sort = request.GET.get('sort', '-last_visit_date')
    patients = patients.order_by(sort, '-created_at')

    # Paginación
    paginator = Paginator(patients, 25)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # Para los filtros
    eps_list = EPS.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'eps_list': eps_list,
        'search': search,
        'eps_filter': eps_filter,
        'regime_filter': regime_filter,
        'blood_type_filter': blood_type_filter,
        'age_range': age_range,
        'gender_filter': gender_filter,
        'active_only': active_only,
        'sort': sort,
        'total_results': paginator.count,
    }

    return render(request, 'patients/patient_list.html', context)


@login_required
@company_required
def patient_detail(request, patient_id):
    """Detalle completo del paciente"""
    company = get_current_company(request)
    patient = get_object_or_404(
        Patient.objects.select_related('third_party', 'eps'),
        pk=patient_id,
        company=company
    )

    # Historial de aseguramiento
    insurance_history = patient.insurance_history.select_related('eps').order_by('-start_date')[:10]

    # Documentos del paciente
    documents = patient.documents.filter(is_active=True).order_by('-uploaded_at')[:20]

    # Últimas atenciones (si existen relaciones con otros módulos)
    # latest_appointments = patient.appointments.all()[:5]

    context = {
        'patient': patient,
        'insurance_history': insurance_history,
        'documents': documents,
        'age': patient.get_age(),
        'age_string': patient.get_age_string(),
        'is_minor': patient.is_minor(),
    }

    return render(request, 'patients/patient_detail.html', context)


@login_required
@company_required
def patient_create(request):
    """Crear nuevo paciente"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Validar que no exista el documento
            document_number = request.POST['document_number']
            existing_patient = Patient.objects.filter(
                company=company,
                third_party__document_number=document_number
            ).first()

            if existing_patient:
                messages.error(request, f'Ya existe un paciente con documento {document_number}')
                return redirect('patients:patient_detail', patient_id=existing_patient.id)

            # Crear o buscar tercero
            third_party, created = ThirdParty.objects.get_or_create(
                company=company,
                document_type=request.POST['document_type'],
                document_number=document_number,
                defaults={
                    'first_name': request.POST['first_name'],
                    'second_name': request.POST.get('second_name', ''),
                    'last_name': request.POST['last_name'],
                    'second_last_name': request.POST.get('second_last_name', ''),
                    'gender': request.POST['gender'],
                    'birth_date': request.POST.get('birth_date') or None,
                    'phone': request.POST.get('phone', ''),
                    'mobile': request.POST.get('mobile', ''),
                    'email': request.POST.get('email', ''),
                    'address': request.POST.get('address', ''),
                    'city': request.POST.get('city', ''),
                    'department': request.POST.get('department', ''),
                    'is_patient': True,
                    'created_by': request.user,
                }
            )

            if not created:
                # Actualizar datos si el tercero ya existía
                third_party.is_patient = True
                third_party.first_name = request.POST['first_name']
                third_party.second_name = request.POST.get('second_name', '')
                third_party.last_name = request.POST['last_name']
                third_party.second_last_name = request.POST.get('second_last_name', '')
                third_party.gender = request.POST['gender']
                if request.POST.get('birth_date'):
                    third_party.birth_date = request.POST['birth_date']
                third_party.save()

            # Generar número de historia clínica automático
            last_patient = Patient.objects.filter(company=company).aggregate(
                last_number=Max('medical_record_number')
            )

            if last_patient['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_patient['last_number'])))
                    medical_record_number = f"HC-{last_num + 1:07d}"
                except:
                    medical_record_number = f"HC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            else:
                medical_record_number = "HC-0000001"

            # Crear paciente
            patient = Patient.objects.create(
                company=company,
                third_party=third_party,
                medical_record_number=medical_record_number,
                regime_type=request.POST.get('regime_type', 'contributivo'),
                eps_id=request.POST.get('eps_id') or None,
                insurance_number=request.POST.get('insurance_number', ''),
                blood_type=request.POST.get('blood_type', ''),
                marital_status=request.POST.get('marital_status', ''),
                education_level=request.POST.get('education_level', ''),
                occupation=request.POST.get('occupation', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                emergency_contact_relationship=request.POST.get('emergency_contact_relationship', ''),
                created_by=request.user,
            )

            messages.success(request, f'Paciente creado exitosamente. HC: {medical_record_number}')
            return redirect('patients:patient_detail', patient_id=patient.id)

        except Exception as e:
            messages.error(request, f'Error al crear paciente: {str(e)}')
            return redirect('patients:patient_create')

    # GET - Mostrar formulario
    eps_list = EPS.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'eps_list': eps_list,
        'document_types': ThirdParty.DOCUMENT_TYPE_CHOICES,
        'gender_choices': ThirdParty.GENDER_CHOICES,
        'blood_types': Patient.BLOOD_TYPE_CHOICES,
        'regime_choices': Patient.REGIME_TYPE_CHOICES,
        'marital_status_choices': Patient.MARITAL_STATUS_CHOICES,
        'education_choices': Patient.EDUCATION_LEVEL_CHOICES,
    }

    return render(request, 'patients/patient_form.html', context)


@login_required
@company_required
def patient_edit(request, patient_id):
    """Editar datos del paciente"""
    company = get_current_company(request)
    patient = get_object_or_404(Patient, pk=patient_id, company=company)

    if request.method == 'POST':
        try:
            # Actualizar tercero
            third_party = patient.third_party
            third_party.first_name = request.POST['first_name']
            third_party.second_name = request.POST.get('second_name', '')
            third_party.last_name = request.POST['last_name']
            third_party.second_last_name = request.POST.get('second_last_name', '')
            third_party.gender = request.POST['gender']
            if request.POST.get('birth_date'):
                third_party.birth_date = request.POST['birth_date']
            third_party.phone = request.POST.get('phone', '')
            third_party.mobile = request.POST.get('mobile', '')
            third_party.email = request.POST.get('email', '')
            third_party.address = request.POST.get('address', '')
            third_party.city = request.POST.get('city', '')
            third_party.department = request.POST.get('department', '')
            third_party.save()

            # Actualizar paciente
            patient.regime_type = request.POST.get('regime_type', 'contributivo')
            patient.eps_id = request.POST.get('eps_id') or None
            patient.insurance_number = request.POST.get('insurance_number', '')
            patient.blood_type = request.POST.get('blood_type', '')
            patient.marital_status = request.POST.get('marital_status', '')
            patient.education_level = request.POST.get('education_level', '')
            patient.occupation = request.POST.get('occupation', '')
            patient.emergency_contact_name = request.POST.get('emergency_contact_name', '')
            patient.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
            patient.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '')
            patient.allergies = request.POST.get('allergies', '')
            patient.chronic_diseases = request.POST.get('chronic_diseases', '')
            patient.notes = request.POST.get('notes', '')
            patient.updated_by = request.user
            patient.save()

            messages.success(request, 'Paciente actualizado exitosamente')
            return redirect('patients:patient_detail', patient_id=patient.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar paciente: {str(e)}')

    eps_list = EPS.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'patient': patient,
        'eps_list': eps_list,
        'document_types': ThirdParty.DOCUMENT_TYPE_CHOICES,
        'gender_choices': ThirdParty.GENDER_CHOICES,
        'blood_types': Patient.BLOOD_TYPE_CHOICES,
        'regime_choices': Patient.REGIME_TYPE_CHOICES,
        'marital_status_choices': Patient.MARITAL_STATUS_CHOICES,
        'education_choices': Patient.EDUCATION_LEVEL_CHOICES,
        'edit_mode': True,
    }

    return render(request, 'patients/patient_form.html', context)


# ====================
# EPS
# ====================

@login_required
@company_required
def eps_list(request):
    """Lista de EPS"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    regime_filter = request.GET.get('regime', '')

    eps_list = EPS.objects.filter(company=company)

    if search:
        eps_list = eps_list.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(nit__icontains=search)
        )

    if regime_filter:
        eps_list = eps_list.filter(regime=regime_filter)

    eps_list = eps_list.annotate(
        patient_count=Count('patients', filter=Q(patients__is_active=True))
    ).order_by('name')

    paginator = Paginator(eps_list, 25)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'search': search,
        'regime_filter': regime_filter,
    }

    return render(request, 'patients/eps_list.html', context)


@login_required
@company_required
def eps_create(request):
    """Crear nueva EPS"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            EPS.objects.create(
                company=company,
                code=request.POST['code'],
                nit=request.POST['nit'],
                name=request.POST['name'],
                regime=request.POST['regime'],
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                created_by=request.user,
            )

            messages.success(request, 'EPS creada exitosamente')
            return redirect('patients:eps_list')

        except Exception as e:
            messages.error(request, f'Error al crear EPS: {str(e)}')

    context = {
        'regime_choices': EPS.REGIME_CHOICES,
    }

    return render(request, 'patients/eps_form.html', context)


# ====================
# API / AJAX
# ====================

@login_required
def patient_search_api(request):
    """API de búsqueda de pacientes para autocompletado"""
    company = get_current_company(request)
    search = request.GET.get('q', '')

    if len(search) < 2:
        return JsonResponse({'results': []})

    patients = Patient.objects.filter(
        company=company,
        is_active=True,
        is_deceased=False
    ).filter(
        Q(medical_record_number__icontains=search) |
        Q(third_party__first_name__icontains=search) |
        Q(third_party__last_name__icontains=search) |
        Q(third_party__document_number__icontains=search)
    ).select_related('third_party', 'eps')[:20]

    results = [{
        'id': str(patient.id),
        'text': f"{patient.get_full_name()} - HC: {patient.medical_record_number}",
        'medical_record_number': patient.medical_record_number,
        'document_number': patient.third_party.document_number,
        'document_type': patient.third_party.get_document_type_display(),
        'age': patient.get_age_string(),
        'gender': patient.third_party.get_gender_display(),
        'eps': patient.eps.name if patient.eps else 'Sin EPS',
        'phone': patient.third_party.mobile or patient.third_party.phone,
    } for patient in patients]

    return JsonResponse({'results': results})


@login_required
def check_duplicate_patient(request):
    """Verificar si existe un paciente con el mismo documento"""
    company = get_current_company(request)
    document_number = request.GET.get('document_number', '')

    if not document_number:
        return JsonResponse({'exists': False})

    patient = Patient.objects.filter(
        company=company,
        third_party__document_number=document_number
    ).select_related('third_party').first()

    if patient:
        return JsonResponse({
            'exists': True,
            'patient': {
                'id': str(patient.id),
                'name': patient.get_full_name(),
                'medical_record_number': patient.medical_record_number,
                'age': patient.get_age_string(),
            }
        })

    return JsonResponse({'exists': False})
