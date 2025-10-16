"""
Vistas del módulo RIPS
Gestión de Episodios de Atención y Generación de RIPS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import json
import os

from core.decorators import company_required
from core.utils import get_current_company
from .models import AttentionEpisode, EpisodeService, RIPSFile, RIPSTransaction
from .utils import add_service_to_episode
from billing_health.models import HealthInvoice
from patients.models import Patient


# ==================== DASHBOARD ====================

@login_required
@company_required
def dashboard(request):
    """Dashboard principal del módulo RIPS"""
    company = get_current_company(request)

    # Estadísticas de episodios
    total_episodes = AttentionEpisode.objects.filter(company=company).count()
    active_episodes = AttentionEpisode.objects.filter(company=company, status='active').count()
    closed_episodes = AttentionEpisode.objects.filter(company=company, status='closed').count()
    billed_episodes = AttentionEpisode.objects.filter(company=company, status='billed').count()

    # Episodios activos
    episodes_active = AttentionEpisode.objects.filter(
        company=company,
        status='active'
    ).select_related('patient', 'payer').order_by('-admission_date')[:10]

    # Episodios cerrados pendientes de facturar
    episodes_pending = AttentionEpisode.objects.filter(
        company=company,
        status='closed',
        is_billed=False
    ).select_related('patient', 'payer').order_by('-discharge_date')[:10]

    # Archivos RIPS recientes
    rips_files = RIPSFile.objects.filter(company=company).order_by('-created_at')[:5]

    context = {
        'total_episodes': total_episodes,
        'active_episodes': active_episodes,
        'closed_episodes': closed_episodes,
        'billed_episodes': billed_episodes,
        'episodes_active': episodes_active,
        'episodes_pending': episodes_pending,
        'rips_files': rips_files,
    }

    return render(request, 'rips/dashboard.html', context)


# ==================== EPISODIOS DE ATENCIÓN ====================

@login_required
@company_required
def episode_list(request):
    """Lista de episodios de atención"""
    company = get_current_company(request)

    # Filtros
    status = request.GET.get('status', '')
    episode_type = request.GET.get('episode_type', '')
    search = request.GET.get('search', '')

    episodes = AttentionEpisode.objects.filter(company=company)

    if status:
        episodes = episodes.filter(status=status)

    if episode_type:
        episodes = episodes.filter(episode_type=episode_type)

    if search:
        episodes = episodes.filter(
            Q(episode_number__icontains=search) |
            Q(patient__third_party__first_name__icontains=search) |
            Q(patient__third_party__last_name__icontains=search) |
            Q(patient__third_party__document_number__icontains=search)
        )

    episodes = episodes.select_related(
        'patient', 'patient__third_party', 'payer', 'created_by'
    ).order_by('-admission_date')

    # Paginación
    paginator = Paginator(episodes, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status': status,
        'episode_type': episode_type,
        'search': search,
        'total_results': paginator.count,
    }

    return render(request, 'rips/episode_list.html', context)


@login_required
@company_required
def episode_create(request):
    """Crear nuevo episodio de atención"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            from third_parties.models import ThirdParty

            # Datos básicos
            patient_id = request.POST.get('patient_id')
            payer_id = request.POST.get('payer_id')
            episode_type = request.POST.get('episode_type')
            admission_diagnosis = request.POST.get('admission_diagnosis', '')
            authorization_number = request.POST.get('authorization_number', '')

            # Validaciones
            if not patient_id or not payer_id:
                messages.error(request, 'Paciente y pagador son obligatorios')
                return redirect('rips:episode_create')

            patient = get_object_or_404(Patient, pk=patient_id, company=company)
            payer = get_object_or_404(ThirdParty, pk=payer_id, company=company)

            # Generar número de episodio
            last_episode = AttentionEpisode.objects.filter(company=company).order_by('-created_at').first()
            if last_episode:
                try:
                    last_num = int(last_episode.episode_number.split('-')[-1])
                    episode_number = f"EP-{timezone.now().year}-{last_num + 1:06d}"
                except:
                    episode_number = f"EP-{timezone.now().year}-000001"
            else:
                episode_number = f"EP-{timezone.now().year}-000001"

            # Crear episodio
            episode = AttentionEpisode.objects.create(
                company=company,
                episode_number=episode_number,
                episode_type=episode_type,
                status='active',
                patient=patient,
                payer=payer,
                admission_date=timezone.now(),
                admission_diagnosis=admission_diagnosis,
                authorization_number=authorization_number,
                created_by=request.user
            )

            messages.success(request, f'Episodio {episode_number} creado exitosamente')
            return redirect('rips:episode_detail', episode_id=episode.id)

        except Exception as e:
            messages.error(request, f'Error al crear episodio: {str(e)}')
            return redirect('rips:episode_create')

    # GET - Mostrar formulario
    from third_parties.models import ThirdParty

    patients = Patient.objects.filter(
        company=company,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name')[:100]

    payers = ThirdParty.objects.filter(
        company=company,
        is_payer=True,
        is_active=True
    ).order_by('name')

    context = {
        'patients': patients,
        'payers': payers,
    }

    return render(request, 'rips/episode_form.html', context)


@login_required
@company_required
def episode_detail(request, episode_id):
    """Detalle de episodio de atención"""
    company = get_current_company(request)
    episode = get_object_or_404(
        AttentionEpisode,
        id=episode_id,
        company=company
    )

    # Servicios del episodio
    services = episode.services.all().select_related('content_type').order_by('added_at')

    context = {
        'episode': episode,
        'services': services,
        'total_services': services.count(),
    }

    return render(request, 'rips/episode_detail.html', context)


@login_required
@company_required
def episode_close(request, episode_id):
    """Cerrar episodio de atención"""
    company = get_current_company(request)
    episode = get_object_or_404(
        AttentionEpisode,
        id=episode_id,
        company=company
    )

    if episode.status != 'active':
        messages.warning(request, 'Solo se pueden cerrar episodios activos')
        return redirect('rips:episode_detail', episode_id=episode.id)

    if request.method == 'POST':
        discharge_diagnosis = request.POST.get('discharge_diagnosis', '')

        episode.discharge_diagnosis = discharge_diagnosis
        episode.close_episode(request.user)

        messages.success(request, f'Episodio {episode.episode_number} cerrado exitosamente')
        return redirect('rips:episode_detail', episode_id=episode.id)

    context = {
        'episode': episode,
    }

    return render(request, 'rips/episode_close.html', context)


@login_required
@company_required
def episode_generate_invoice(request, episode_id):
    """Generar factura desde episodio"""
    company = get_current_company(request)
    episode = get_object_or_404(
        AttentionEpisode,
        id=episode_id,
        company=company
    )

    if episode.is_billed:
        messages.warning(request, 'Este episodio ya ha sido facturado')
        return redirect('rips:episode_detail', episode_id=episode.id)

    if episode.status != 'closed':
        messages.error(request, 'Solo se pueden facturar episodios cerrados')
        return redirect('rips:episode_detail', episode_id=episode.id)

    try:
        invoice = episode.generate_invoice(request.user)
        messages.success(request, f'Factura {invoice.invoice_number} generada exitosamente')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    except Exception as e:
        messages.error(request, f'Error al generar factura: {str(e)}')
        return redirect('rips:episode_detail', episode_id=episode.id)


# ==================== ARCHIVOS RIPS ====================

@login_required
@company_required
def rips_list(request):
    """Lista de archivos RIPS generados"""
    company = get_current_company(request)

    # Filtros
    status = request.GET.get('status', '')

    rips_files = RIPSFile.objects.filter(company=company)

    if status:
        rips_files = rips_files.filter(status=status)

    rips_files = rips_files.order_by('-created_at')

    # Paginación
    paginator = Paginator(rips_files, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status': status,
    }

    return render(request, 'rips/rips_list.html', context)


@login_required
@company_required
def rips_generate(request):
    """Generar archivo RIPS desde factura"""
    company = get_current_company(request)

    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice_id')
            file_format = request.POST.get('format', 'json')

            invoice = get_object_or_404(HealthInvoice, pk=invoice_id, company=company)

            # Generar RIPS
            result = invoice.generate_rips(format=file_format)

            messages.success(request, f'RIPS generado exitosamente para factura {invoice.invoice_number}')
            return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            messages.error(request, f'Error al generar RIPS: {str(e)}')
            return redirect('rips:rips_generate')

    # GET - Mostrar formulario
    invoices = HealthInvoice.objects.filter(
        company=company,
        status__in=['issued', 'sent', 'paid'],
        rips_generated=False
    ).select_related('patient', 'payer').order_by('-invoice_date')[:50]

    context = {
        'invoices': invoices,
    }

    return render(request, 'rips/rips_generate.html', context)


@login_required
@company_required
def rips_download(request, invoice_id):
    """Descargar archivo RIPS"""
    company = get_current_company(request)
    invoice = get_object_or_404(HealthInvoice, pk=invoice_id, company=company)

    if not invoice.rips_generated or not invoice.rips_file_path:
        messages.error(request, 'No hay archivo RIPS generado para esta factura')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    # Verificar que el archivo existe
    if not os.path.exists(invoice.rips_file_path):
        messages.error(request, 'El archivo RIPS no se encuentra en el servidor')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)

    # Descargar archivo
    try:
        response = FileResponse(open(invoice.rips_file_path, 'rb'))
        response['Content-Type'] = 'application/json'
        response['Content-Disposition'] = f'attachment; filename="RIPS_{invoice.invoice_number}.json"'
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar archivo: {str(e)}')
        return redirect('billing_health:invoice_detail', invoice_id=invoice.id)


# ==================== API ENDPOINTS ====================

@login_required
def api_search_patients(request):
    """API para buscar pacientes (autocomplete)"""
    company = get_current_company(request)
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    patients = Patient.objects.filter(
        company=company,
        is_active=True
    ).select_related('third_party').filter(
        Q(third_party__first_name__icontains=query) |
        Q(third_party__last_name__icontains=query) |
        Q(third_party__document_number__icontains=query) |
        Q(medical_record_number__icontains=query)
    )[:20]

    results = [
        {
            'id': str(p.id),
            'name': f"{p.third_party.first_name} {p.third_party.last_name}",
            'document': p.third_party.document_number,
            'medical_record': p.medical_record_number,
            'text': f"{p.third_party.first_name} {p.third_party.last_name} - {p.third_party.document_number}"
        }
        for p in patients
    ]

    return JsonResponse({'results': results})
