"""
Vistas del módulo Banco de Sangre
Gestión completa de donantes, donaciones, hemocomponentes y transfusiones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Max
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal

from core.decorators import company_required
from core.utils import get_current_company
from third_parties.models import ThirdParty
from .models import (
    Donor, Donation, BloodComponent, ScreeningTest,
    CompatibilityTest, Transfusion
)


# ==================== DASHBOARD ====================

@login_required
@company_required
def index(request):
    """Dashboard principal del banco de sangre"""
    company = get_current_company(request)

    # Estadísticas generales
    total_donors = Donor.objects.filter(company=company).count()
    active_donors = Donor.objects.filter(company=company, status='active').count()

    donations_today = Donation.objects.filter(
        company=company,
        donation_date__date=timezone.now().date(),
        status='completed'
    ).count()

    donations_month = Donation.objects.filter(
        company=company,
        donation_date__month=timezone.now().month,
        donation_date__year=timezone.now().year,
        status='completed'
    ).count()

    # Inventario de componentes disponibles
    available_components = BloodComponent.objects.filter(
        company=company,
        status='available'
    ).values('blood_type').annotate(
        total=Count('id')
    ).order_by('blood_type')

    # Componentes por vencer (próximos 7 días)
    expiring_soon = BloodComponent.objects.filter(
        company=company,
        status='available',
        expiration_date__lte=timezone.now() + timedelta(days=7),
        expiration_date__gt=timezone.now()
    ).count()

    # Donaciones recientes
    recent_donations = Donation.objects.filter(
        company=company
    ).select_related('donor', 'phlebotomist').order_by('-donation_date')[:10]

    # Transfusiones recientes
    recent_transfusions = Transfusion.objects.filter(
        company=company
    ).select_related('patient', 'blood_component', 'ordering_physician').order_by('-created_at')[:10]

    # Componentes críticos (stock bajo)
    critical_stock = BloodComponent.objects.filter(
        company=company,
        status='available'
    ).values('component_type', 'blood_type').annotate(
        total=Count('id')
    ).filter(total__lt=5).order_by('total')

    context = {
        'total_donors': total_donors,
        'active_donors': active_donors,
        'donations_today': donations_today,
        'donations_month': donations_month,
        'available_components': available_components,
        'expiring_soon': expiring_soon,
        'recent_donations': recent_donations,
        'recent_transfusions': recent_transfusions,
        'critical_stock': critical_stock,
    }

    return render(request, 'blood_bank/index.html', context)


# ==================== DONANTES ====================

@login_required
@company_required
def donor_list(request):
    """Listado de donantes"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    blood_type = request.GET.get('blood_type', '')
    status = request.GET.get('status', '')

    donors = Donor.objects.filter(company=company).select_related('third_party')

    if search:
        donors = donors.filter(
            Q(donor_code__icontains=search) |
            Q(document_number__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    if blood_type:
        donors = donors.filter(blood_type=blood_type)

    if status:
        donors = donors.filter(status=status)

    donors = donors.order_by('-last_donation_date')

    paginator = Paginator(donors, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'blood_type_filter': blood_type,
        'status_filter': status,
    }

    return render(request, 'blood_bank/donor_list.html', context)


@login_required
@company_required
def donor_create(request):
    """Crear nuevo donante"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            # Generar código de donante
            last_donor = Donor.objects.filter(company=company).aggregate(
                last_code=Max('donor_code')
            )
            if last_donor['last_code']:
                last_num = int(''.join(filter(str.isdigit, last_donor['last_code'])))
                donor_code = f"DON-{last_num + 1:07d}"
            else:
                donor_code = "DON-0000001"

            # Obtener third_party si existe
            third_party_id = request.POST.get('third_party')
            third_party = None
            if third_party_id:
                third_party = get_object_or_404(ThirdParty, id=third_party_id, company=company)

            donor = Donor.objects.create(
                company=company,
                donor_code=donor_code,
                third_party=third_party,
                document_type=request.POST.get('document_type', ''),
                document_number=request.POST.get('document_number', ''),
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                birth_date=request.POST.get('birth_date') or None,
                gender=request.POST.get('gender', ''),
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                donor_type=request.POST.get('donor_type', 'voluntary'),
                blood_type=request.POST.get('blood_type'),
                rh_factor=request.POST.get('rh_factor'),
                status='active',
                created_by=request.user
            )

            messages.success(request, f'Donante {donor_code} creado exitosamente')
            return redirect('blood_bank:donor_detail', donor_id=donor.id)

        except Exception as e:
            messages.error(request, f'Error al crear donante: {str(e)}')

    # Para el formulario
    third_parties = ThirdParty.objects.filter(
        company=company,
        is_active=True
    ).order_by('first_name', 'last_name')[:100]

    context = {
        'third_parties': third_parties,
    }

    return render(request, 'blood_bank/donor_form.html', context)


@login_required
@company_required
def donor_detail(request, donor_id):
    """Detalle del donante"""
    company = get_current_company(request)
    donor = get_object_or_404(
        Donor.objects.select_related('third_party'),
        id=donor_id,
        company=company
    )

    # Historial de donaciones
    donations = donor.donations.all().order_by('-donation_date')

    # Última donación
    last_donation = donations.first()

    # Puede donar?
    can_donate = donor.can_donate()

    context = {
        'donor': donor,
        'donations': donations,
        'last_donation': last_donation,
        'can_donate': can_donate,
    }

    return render(request, 'blood_bank/donor_detail.html', context)


# ==================== DONACIONES ====================

@login_required
@company_required
def donation_list(request):
    """Listado de donaciones"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')

    donations = Donation.objects.filter(company=company).select_related(
        'donor', 'phlebotomist', 'supervising_physician'
    )

    if search:
        donations = donations.filter(
            Q(donation_number__icontains=search) |
            Q(donor__donor_code__icontains=search) |
            Q(donor__document_number__icontains=search)
        )

    if status:
        donations = donations.filter(status=status)

    if date_from:
        donations = donations.filter(donation_date__gte=date_from)

    donations = donations.order_by('-donation_date')

    paginator = Paginator(donations, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
        'date_from': date_from,
    }

    return render(request, 'blood_bank/donation_list.html', context)


@login_required
@company_required
def donation_create(request):
    """Crear nueva donación"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            donor_id = request.POST.get('donor')
            donor = get_object_or_404(Donor, id=donor_id, company=company)

            # Verificar que el donante puede donar
            if not donor.can_donate():
                messages.error(request, 'Este donante no puede donar en este momento')
                return redirect('blood_bank:donation_create')

            # Generar número de donación
            last_donation = Donation.objects.filter(company=company).aggregate(
                last_number=Max('donation_number')
            )
            if last_donation['last_number']:
                last_num = int(''.join(filter(str.isdigit, last_donation['last_number'])))
                donation_number = f"DONN-{last_num + 1:07d}"
            else:
                donation_number = "DONN-0000001"

            from payroll.models import Employee
            phlebotomist_id = request.POST.get('phlebotomist')
            phlebotomist = get_object_or_404(Employee, id=phlebotomist_id)

            supervising_physician_id = request.POST.get('supervising_physician')
            supervising_physician = None
            if supervising_physician_id:
                supervising_physician = get_object_or_404(Employee, id=supervising_physician_id)

            donation = Donation.objects.create(
                company=company,
                donation_number=donation_number,
                donor=donor,
                donation_type=request.POST.get('donation_type', 'whole_blood'),
                weight_kg=request.POST.get('weight_kg') or None,
                hemoglobin=request.POST.get('hemoglobin') or None,
                blood_pressure_systolic=request.POST.get('blood_pressure_systolic') or None,
                blood_pressure_diastolic=request.POST.get('blood_pressure_diastolic') or None,
                pulse=request.POST.get('pulse') or None,
                temperature=request.POST.get('temperature') or None,
                pre_donation_approved=request.POST.get('pre_donation_approved') == 'on',
                pre_donation_notes=request.POST.get('pre_donation_notes', ''),
                volume_ml=request.POST.get('volume_ml') or None,
                phlebotomist=phlebotomist,
                supervising_physician=supervising_physician,
                status='in_process',
                created_by=request.user
            )

            messages.success(request, f'Donación {donation_number} creada exitosamente')
            return redirect('blood_bank:donation_detail', donation_id=donation.id)

        except Exception as e:
            messages.error(request, f'Error al crear donación: {str(e)}')

    # Para el formulario
    donors = Donor.objects.filter(
        company=company,
        status='active'
    ).order_by('donor_code')

    from payroll.models import Employee
    employees = Employee.objects.filter(
        company=company,
        is_active=True
    ).order_by('third_party__first_name')

    context = {
        'donors': donors,
        'employees': employees,
    }

    return render(request, 'blood_bank/donation_form.html', context)


@login_required
@company_required
def donation_detail(request, donation_id):
    """Detalle de la donación"""
    company = get_current_company(request)
    donation = get_object_or_404(
        Donation.objects.select_related(
            'donor', 'phlebotomist', 'supervising_physician'
        ),
        id=donation_id,
        company=company
    )

    # Pruebas de cribado
    screening_tests = donation.screening_tests.all().order_by('test_type')

    # Componentes derivados
    components = donation.components.all().order_by('component_type')

    context = {
        'donation': donation,
        'screening_tests': screening_tests,
        'components': components,
    }

    return render(request, 'blood_bank/donation_detail.html', context)


# ==================== HEMOCOMPONENTES ====================

@login_required
@company_required
def component_list(request):
    """Listado de hemocomponentes"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    component_type = request.GET.get('component_type', '')
    blood_type = request.GET.get('blood_type', '')
    status = request.GET.get('status', '')

    components = BloodComponent.objects.filter(company=company).select_related('donation', 'donation__donor')

    if search:
        components = components.filter(component_code__icontains=search)

    if component_type:
        components = components.filter(component_type=component_type)

    if blood_type:
        components = components.filter(blood_type=blood_type)

    if status:
        components = components.filter(status=status)

    components = components.order_by('expiration_date')

    paginator = Paginator(components, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'component_type_filter': component_type,
        'blood_type_filter': blood_type,
        'status_filter': status,
    }

    return render(request, 'blood_bank/component_list.html', context)


@login_required
@company_required
def component_detail(request, component_id):
    """Detalle del hemocomponente"""
    company = get_current_company(request)
    component = get_object_or_404(
        BloodComponent.objects.select_related('donation', 'donation__donor'),
        id=component_id,
        company=company
    )

    # Pruebas de compatibilidad
    compatibility_tests = component.compatibility_tests.all().order_by('-test_date')

    # Transfusiones
    transfusions = component.transfusions.all().order_by('-created_at')

    context = {
        'component': component,
        'compatibility_tests': compatibility_tests,
        'transfusions': transfusions,
        'days_to_expiration': component.days_until_expiration(),
    }

    return render(request, 'blood_bank/component_detail.html', context)


# ==================== TRANSFUSIONES ====================

@login_required
@company_required
def transfusion_list(request):
    """Listado de transfusiones"""
    company = get_current_company(request)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    transfusions = Transfusion.objects.filter(company=company).select_related(
        'patient', 'blood_component', 'ordering_physician', 'administering_nurse'
    )

    if search:
        transfusions = transfusions.filter(
            Q(transfusion_number__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search)
        )

    if status:
        transfusions = transfusions.filter(status=status)

    transfusions = transfusions.order_by('-created_at')

    paginator = Paginator(transfusions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
    }

    return render(request, 'blood_bank/transfusion_list.html', context)


@login_required
@company_required
def transfusion_detail(request, transfusion_id):
    """Detalle de la transfusión"""
    company = get_current_company(request)
    transfusion = get_object_or_404(
        Transfusion.objects.select_related(
            'patient', 'blood_component', 'ordering_physician', 'administering_nurse'
        ),
        id=transfusion_id,
        company=company
    )

    context = {
        'transfusion': transfusion,
        'duration': transfusion.duration_minutes(),
    }

    return render(request, 'blood_bank/transfusion_detail.html', context)


# ==================== REPORTES ====================

@login_required
@company_required
def inventory_report(request):
    """Reporte de inventario de hemocomponentes"""
    company = get_current_company(request)

    # Inventario por tipo y grupo sanguíneo
    inventory = BloodComponent.objects.filter(
        company=company,
        status='available'
    ).values('component_type', 'blood_type').annotate(
        total_units=Count('id'),
        total_volume=Sum('volume_ml')
    ).order_by('component_type', 'blood_type')

    # Componentes por vencer
    expiring = BloodComponent.objects.filter(
        company=company,
        status='available',
        expiration_date__lte=timezone.now() + timedelta(days=7)
    ).order_by('expiration_date')

    context = {
        'inventory': inventory,
        'expiring': expiring,
    }

    return render(request, 'blood_bank/inventory_report.html', context)
