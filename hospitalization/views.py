"""
Vistas del módulo Hospitalización
Gestión completa de camas, ingresos, egresos y estancias
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, F, Max
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal

from core.decorators import company_required
from core.utils import get_current_company
from core.models import User
from patients.models import Patient
from .models import (
    Ward, Bed, Admission, AdmissionTransfer,
    MedicalEvolution, MedicalOrder, AdmissionServiceItem
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def hospitalization_dashboard(request):
    """Dashboard principal de hospitalización"""
    company = get_current_company(request)

    # Estadísticas generales
    total_beds = Bed.objects.filter(company=company, is_active=True).count()
    available_beds = Bed.objects.filter(company=company, status='available', is_active=True).count()
    occupied_beds = Bed.objects.filter(company=company, status='occupied', is_active=True).count()
    maintenance_beds = Bed.objects.filter(company=company, status='maintenance', is_active=True).count()

    # Tasa de ocupación
    occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

    # Admisiones activas
    active_admissions = Admission.objects.filter(
        company=company,
        status='active'
    ).select_related('patient__third_party', 'bed__ward', 'attending_physician').order_by('-admission_date')

    total_active_admissions = active_admissions.count()

    # Admisiones por pabellón
    admissions_by_ward = Admission.objects.filter(
        company=company,
        status='active'
    ).values('bed__ward__name').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    # Pacientes con estancia prolongada (más de 15 días)
    long_stay_patients = active_admissions.filter(
        admission_date__lte=timezone.now() - timedelta(days=15)
    )[:10]

    # Admisiones recientes (últimos 10)
    recent_admissions = Admission.objects.filter(
        company=company
    ).select_related('patient__third_party', 'bed__ward', 'attending_physician').order_by('-admission_date')[:10]

    # Egresos del día
    today = timezone.now().date()
    today_discharges = Admission.objects.filter(
        company=company,
        discharge_date__date=today
    ).count()

    # Órdenes médicas pendientes
    pending_orders = MedicalOrder.objects.filter(
        company=company,
        status='pending'
    ).count()

    # Estadísticas por tipo de admisión
    admissions_by_type = Admission.objects.filter(
        company=company,
        admission_date__gte=timezone.now() - timedelta(days=30)
    ).values('admission_type').annotate(
        total=Count('id')
    )

    # Promedio de estancia
    discharged_last_month = Admission.objects.filter(
        company=company,
        status='discharged',
        discharge_date__gte=timezone.now() - timedelta(days=30)
    )

    avg_stay_days = 0
    if discharged_last_month.exists():
        total_days = sum([adm.get_stay_duration() for adm in discharged_last_month])
        avg_stay_days = total_days / discharged_last_month.count()

    context = {
        'total_beds': total_beds,
        'available_beds': available_beds,
        'occupied_beds': occupied_beds,
        'maintenance_beds': maintenance_beds,
        'occupancy_rate': round(occupancy_rate, 1),
        'total_active_admissions': total_active_admissions,
        'active_admissions': active_admissions[:15],
        'admissions_by_ward': admissions_by_ward,
        'long_stay_patients': long_stay_patients,
        'recent_admissions': recent_admissions,
        'today_discharges': today_discharges,
        'pending_orders': pending_orders,
        'admissions_by_type': admissions_by_type,
        'avg_stay_days': round(avg_stay_days, 1),
    }

    return render(request, 'hospitalization/dashboard.html', context)


# ==================== GESTIÓN DE PABELLONES ====================

@login_required
@company_required
def ward_list(request):
    """Listado de pabellones"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    ward_type = request.GET.get('ward_type', '')
    status = request.GET.get('status', 'active')

    wards = Ward.objects.filter(company=company)

    if search:
        wards = wards.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(building__icontains=search)
        )

    if ward_type:
        wards = wards.filter(ward_type=ward_type)

    if status == 'active':
        wards = wards.filter(is_active=True)
    elif status == 'inactive':
        wards = wards.filter(is_active=False)

    wards = wards.order_by('floor', 'name')

    # Agregar estadísticas de cada pabellón
    for ward in wards:
        ward.available_beds = ward.get_available_beds_count()
        ward.occupied_beds = ward.get_occupied_beds_count()
        ward.occupancy_rate = ward.get_occupancy_rate()

    paginator = Paginator(wards, 20)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'search': search,
        'ward_type': ward_type,
        'status': status,
    }

    return render(request, 'hospitalization/ward_list.html', context)


@login_required
@company_required
def ward_detail(request, ward_id):
    """Detalle del pabellón"""
    company = get_current_company(request)
    ward = get_object_or_404(Ward, id=ward_id, company=company)

    # Camas del pabellón
    beds = ward.beds.filter(is_active=True).order_by('room_number', 'bed_number')

    # Admisiones activas en el pabellón
    active_admissions = Admission.objects.filter(
        company=company,
        bed__ward=ward,
        status='active'
    ).select_related('patient__third_party', 'bed', 'attending_physician')

    context = {
        'ward': ward,
        'beds': beds,
        'active_admissions': active_admissions,
        'available_beds': ward.get_available_beds_count(),
        'occupied_beds': ward.get_occupied_beds_count(),
        'occupancy_rate': ward.get_occupancy_rate(),
    }

    return render(request, 'hospitalization/ward_detail.html', context)


# ==================== GESTIÓN DE CAMAS ====================

@login_required
@company_required
def bed_list(request):
    """Listado de camas"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    ward_id = request.GET.get('ward', '')
    status = request.GET.get('status', '')
    bed_type = request.GET.get('bed_type', '')

    beds = Bed.objects.filter(company=company).select_related('ward')

    if search:
        beds = beds.filter(
            Q(code__icontains=search) |
            Q(room_number__icontains=search) |
            Q(ward__name__icontains=search)
        )

    if ward_id:
        beds = beds.filter(ward_id=ward_id)

    if status:
        beds = beds.filter(status=status)

    if bed_type:
        beds = beds.filter(bed_type=bed_type)

    beds = beds.filter(is_active=True).order_by('ward__floor', 'ward__name', 'room_number', 'bed_number')

    # Para cada cama, obtener admisión actual si existe
    for bed in beds:
        if bed.status == 'occupied':
            bed.current_admission = bed.get_current_admission()

    paginator = Paginator(beds, 50)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # Lista de pabellones para filtro
    wards = Ward.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'wards': wards,
        'search': search,
        'ward_filter': ward_id,
        'status_filter': status,
        'bed_type_filter': bed_type,
    }

    return render(request, 'hospitalization/bed_list.html', context)


@login_required
@company_required
def bed_detail(request, bed_id):
    """Detalle de la cama"""
    company = get_current_company(request)
    bed = get_object_or_404(Bed, id=bed_id, company=company)

    # Admisión actual
    current_admission = bed.get_current_admission() if bed.status == 'occupied' else None

    # Historial de admisiones de la cama
    admissions_history = bed.admissions.all().select_related(
        'patient__third_party', 'attending_physician'
    ).order_by('-admission_date')[:20]

    context = {
        'bed': bed,
        'current_admission': current_admission,
        'admissions_history': admissions_history,
    }

    return render(request, 'hospitalization/bed_detail.html', context)


# ==================== GESTIÓN DE ADMISIONES ====================

@login_required
@company_required
def admission_list(request):
    """Listado de admisiones"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', 'active')
    ward_id = request.GET.get('ward', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    admissions = Admission.objects.filter(company=company).select_related(
        'patient__third_party', 'bed__ward', 'attending_physician'
    )

    if search:
        admissions = admissions.filter(
            Q(admission_number__icontains=search) |
            Q(patient__third_party__name__icontains=search) |
            Q(patient__third_party__identification_number__icontains=search) |
            Q(patient__medical_record_number__icontains=search)
        )

    if status:
        admissions = admissions.filter(status=status)

    if ward_id:
        admissions = admissions.filter(bed__ward_id=ward_id)

    if date_from:
        admissions = admissions.filter(admission_date__gte=date_from)

    if date_to:
        admissions = admissions.filter(admission_date__lte=date_to)

    admissions = admissions.order_by('-admission_date')

    # Calcular días de estancia para cada admisión
    for admission in admissions:
        admission.stay_days = admission.get_stay_duration()

    paginator = Paginator(admissions, 20)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # Lista de pabellones para filtro
    wards = Ward.objects.filter(company=company, is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'wards': wards,
        'search': search,
        'status_filter': status,
        'ward_filter': ward_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'hospitalization/admission_list.html', context)


@login_required
@company_required
def admission_detail(request, admission_id):
    """Detalle de la admisión"""
    company = get_current_company(request)
    admission = get_object_or_404(
        Admission.objects.select_related(
            'patient__third_party', 'bed__ward', 'attending_physician', 'created_by'
        ),
        id=admission_id,
        company=company
    )

    # Evoluciones médicas
    evolutions = admission.evolutions.all().select_related('created_by').order_by('-evolution_date')[:10]

    # Órdenes médicas
    orders = admission.orders.all().select_related('ordered_by', 'executed_by').order_by('-order_date')

    # Traslados
    transfers = admission.transfers.all().select_related(
        'from_bed__ward', 'to_bed__ward', 'authorized_by', 'executed_by'
    ).order_by('-transfer_date')

    # Servicios facturados
    service_items = admission.service_items.all().select_related('created_by').order_by('-service_date')

    # Calcular costos
    stay_days = admission.get_stay_duration()
    bed_cost = admission.bed.daily_rate * (stay_days if stay_days > 0 else 1)
    services_total = sum([item.get_total() for item in service_items])
    total_cost = bed_cost + services_total

    context = {
        'admission': admission,
        'evolutions': evolutions,
        'orders': orders,
        'transfers': transfers,
        'service_items': service_items,
        'stay_days': stay_days,
        'stay_hours': admission.get_stay_hours(),
        'bed_cost': bed_cost,
        'services_total': services_total,
        'total_cost': total_cost,
    }

    return render(request, 'hospitalization/admission_detail.html', context)


@login_required
@company_required
def admission_create(request):
    """Crear nueva admisión"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            patient_id = request.POST.get('patient')
            bed_id = request.POST.get('bed')
            admission_type = request.POST.get('admission_type')
            admission_diagnosis = request.POST.get('admission_diagnosis')
            admission_reason = request.POST.get('admission_reason')
            attending_physician_id = request.POST.get('attending_physician')

            # Validaciones
            patient = get_object_or_404(Patient, id=patient_id, company=company)
            bed = get_object_or_404(Bed, id=bed_id, company=company)
            attending_physician = get_object_or_404(User, id=attending_physician_id)

            # Verificar que la cama esté disponible
            if not bed.is_available():
                messages.error(request, 'La cama seleccionada no está disponible')
                return redirect('hospitalization:admission_create')

            # Generar número de admisión
            last_admission = Admission.objects.filter(company=company).aggregate(
                last_number=Max('admission_number')
            )
            if last_admission['last_number']:
                # Extraer número y sumar 1
                last_num = int(''.join(filter(str.isdigit, last_admission['last_number'])))
                admission_number = f"ADM-{last_num + 1:07d}"
            else:
                admission_number = "ADM-0000001"

            # Crear admisión
            admission = Admission.objects.create(
                company=company,
                admission_number=admission_number,
                patient=patient,
                bed=bed,
                admission_type=admission_type,
                admission_diagnosis=admission_diagnosis,
                admission_reason=admission_reason,
                attending_physician=attending_physician,
                status='active',
                created_by=request.user
            )

            # Cambiar estado de la cama a ocupada
            bed.status = 'occupied'
            bed.save()

            messages.success(request, f'Admisión {admission_number} creada exitosamente')
            return redirect('hospitalization:admission_detail', admission_id=admission.id)

        except Exception as e:
            messages.error(request, f'Error al crear la admisión: {str(e)}')
            return redirect('hospitalization:admission_create')

    # GET - Mostrar formulario
    # Camas disponibles
    available_beds = Bed.objects.filter(
        company=company,
        status='available',
        is_active=True
    ).select_related('ward').order_by('ward__name', 'room_number', 'bed_number')

    # Pacientes
    patients = Patient.objects.filter(
        company=company,
        is_active=True
    ).select_related('third_party').order_by('third_party__name')

    # Médicos
    physicians = User.objects.filter(companies=company, is_active=True).order_by('first_name', 'last_name')

    context = {
        'available_beds': available_beds,
        'patients': patients,
        'physicians': physicians,
    }

    return render(request, 'hospitalization/admission_form.html', context)


@login_required
@company_required
def admission_discharge(request, admission_id):
    """Dar de alta a un paciente"""
    company = get_current_company(request)
    admission = get_object_or_404(Admission, id=admission_id, company=company)

    if not admission.can_discharge():
        messages.error(request, 'Esta admisión no puede ser egresada')
        return redirect('hospitalization:admission_detail', admission_id=admission.id)

    if request.method == 'POST':
        try:
            discharge_type = request.POST.get('discharge_type')
            discharge_diagnosis = request.POST.get('discharge_diagnosis')
            discharge_summary = request.POST.get('discharge_summary')
            discharge_recommendations = request.POST.get('discharge_recommendations')
            requires_followup = request.POST.get('requires_followup') == 'on'
            followup_date = request.POST.get('followup_date') or None
            followup_observations = request.POST.get('followup_observations', '')

            # Actualizar admisión
            admission.status = 'discharged'
            admission.discharge_date = timezone.now()
            admission.discharge_type = discharge_type
            admission.discharge_diagnosis = discharge_diagnosis
            admission.discharge_summary = discharge_summary
            admission.discharge_recommendations = discharge_recommendations
            admission.requires_followup = requires_followup
            admission.followup_date = followup_date
            admission.followup_observations = followup_observations

            # Calcular costo total
            admission.total_stay_cost = admission.calculate_stay_cost()
            admission.save()

            # Liberar la cama
            bed = admission.bed
            bed.status = 'cleaning'  # La cama pasa a limpieza
            bed.save()

            messages.success(request, f'Egreso registrado exitosamente. Paciente dado de alta.')
            return redirect('hospitalization:admission_detail', admission_id=admission.id)

        except Exception as e:
            messages.error(request, f'Error al registrar el egreso: {str(e)}')

    context = {
        'admission': admission,
        'stay_days': admission.get_stay_duration(),
        'estimated_cost': admission.calculate_stay_cost(),
    }

    return render(request, 'hospitalization/admission_discharge_form.html', context)


# ==================== EVOLUCIONES MÉDICAS ====================

@login_required
@company_required
def evolution_create(request, admission_id):
    """Crear evolución médica"""
    company = get_current_company(request)
    admission = get_object_or_404(Admission, id=admission_id, company=company)

    if request.method == 'POST':
        try:
            evolution = MedicalEvolution.objects.create(
                company=company,
                admission=admission,
                evolution_type=request.POST.get('evolution_type'),
                temperature=request.POST.get('temperature') or None,
                heart_rate=request.POST.get('heart_rate') or None,
                respiratory_rate=request.POST.get('respiratory_rate') or None,
                blood_pressure_sys=request.POST.get('blood_pressure_sys') or None,
                blood_pressure_dia=request.POST.get('blood_pressure_dia') or None,
                oxygen_saturation=request.POST.get('oxygen_saturation') or None,
                subjective=request.POST.get('subjective'),
                objective=request.POST.get('objective'),
                assessment=request.POST.get('assessment'),
                plan=request.POST.get('plan'),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )

            messages.success(request, 'Evolución médica registrada exitosamente')
            return redirect('hospitalization:admission_detail', admission_id=admission.id)

        except Exception as e:
            messages.error(request, f'Error al crear la evolución: {str(e)}')

    context = {
        'admission': admission,
    }

    return render(request, 'hospitalization/evolution_form.html', context)


# ==================== ÓRDENES MÉDICAS ====================

@login_required
@company_required
def order_create(request, admission_id):
    """Crear orden médica"""
    company = get_current_company(request)
    admission = get_object_or_404(Admission, id=admission_id, company=company)

    if request.method == 'POST':
        try:
            order = MedicalOrder.objects.create(
                company=company,
                admission=admission,
                order_type=request.POST.get('order_type'),
                priority=request.POST.get('priority'),
                description=request.POST.get('description'),
                dosage=request.POST.get('dosage', ''),
                frequency=request.POST.get('frequency', ''),
                duration=request.POST.get('duration', ''),
                observations=request.POST.get('observations', ''),
                ordered_by=request.user
            )

            messages.success(request, 'Orden médica creada exitosamente')
            return redirect('hospitalization:admission_detail', admission_id=admission.id)

        except Exception as e:
            messages.error(request, f'Error al crear la orden: {str(e)}')

    context = {
        'admission': admission,
    }

    return render(request, 'hospitalization/order_form.html', context)


@login_required
@company_required
def order_execute(request, order_id):
    """Ejecutar orden médica"""
    company = get_current_company(request)
    order = get_object_or_404(MedicalOrder, id=order_id, company=company)

    if request.method == 'POST':
        try:
            order.status = 'completed'
            order.execution_date = timezone.now()
            order.execution_notes = request.POST.get('execution_notes', '')
            order.executed_by = request.user
            order.save()

            messages.success(request, 'Orden ejecutada exitosamente')
            return redirect('hospitalization:admission_detail', admission_id=order.admission.id)

        except Exception as e:
            messages.error(request, f'Error al ejecutar la orden: {str(e)}')
            return redirect('hospitalization:admission_detail', admission_id=order.admission.id)

    return redirect('hospitalization:admission_detail', admission_id=order.admission.id)


# ==================== REPORTES ====================

@login_required
@company_required
def occupancy_report(request):
    """Reporte de ocupación hospitalaria"""
    company = get_current_company(request)

    # Estadísticas por pabellón
    wards_stats = []
    wards = Ward.objects.filter(company=company, is_active=True).order_by('name')

    for ward in wards:
        total_beds = ward.beds.filter(is_active=True).count()
        available = ward.get_available_beds_count()
        occupied = ward.get_occupied_beds_count()
        occupancy_rate = ward.get_occupancy_rate()

        wards_stats.append({
            'ward': ward,
            'total_beds': total_beds,
            'available': available,
            'occupied': occupied,
            'occupancy_rate': occupancy_rate,
        })

    # Estadísticas generales
    total_beds = sum([w['total_beds'] for w in wards_stats])
    total_occupied = sum([w['occupied'] for w in wards_stats])
    overall_occupancy = (total_occupied / total_beds * 100) if total_beds > 0 else 0

    context = {
        'wards_stats': wards_stats,
        'total_beds': total_beds,
        'total_occupied': total_occupied,
        'overall_occupancy': round(overall_occupancy, 1),
    }

    return render(request, 'hospitalization/occupancy_report.html', context)


# ==================== APIs ====================

@login_required
@company_required
def api_available_beds(request):
    """API: Obtener camas disponibles por pabellón"""
    company = get_current_company(request)
    ward_id = request.GET.get('ward_id')

    if ward_id:
        beds = Bed.objects.filter(
            company=company,
            ward_id=ward_id,
            status='available',
            is_active=True
        ).values('id', 'code', 'room_number', 'bed_number', 'bed_type')
    else:
        beds = Bed.objects.filter(
            company=company,
            status='available',
            is_active=True
        ).values('id', 'code', 'room_number', 'bed_number', 'bed_type', 'ward__name')

    return JsonResponse(list(beds), safe=False)


@login_required
@company_required
def api_bed_status(request, bed_id):
    """API: Estado de una cama"""
    company = get_current_company(request)
    bed = get_object_or_404(Bed, id=bed_id, company=company)

    data = {
        'id': str(bed.id),
        'code': bed.code,
        'status': bed.status,
        'is_available': bed.is_available(),
        'room_number': bed.room_number,
        'bed_number': bed.bed_number,
        'ward': bed.ward.name,
    }

    if bed.status == 'occupied':
        admission = bed.get_current_admission()
        if admission:
            data['admission'] = {
                'number': admission.admission_number,
                'patient': admission.patient.third_party.get_full_name(),
                'admission_date': admission.admission_date.isoformat(),
                'stay_days': admission.get_stay_duration(),
            }

    return JsonResponse(data)
