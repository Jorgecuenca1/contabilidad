"""
Vistas del módulo Autorizaciones EPS
Gestión completa de solicitudes, aprobaciones y contrarreferencias
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import os

from core.decorators import company_required, module_permission_required
from core.utils import get_current_company
from core.models import User
from patients.models import Patient, EPS
from payroll.models import Employee
from third_parties.models import ThirdParty
from .models import (
    AuthorizationRequest, CounterReferral, AuthorizationAttachment, AuthorizationUsage
)


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations')
def index(request):
    """Dashboard principal del módulo de autorizaciones."""
    company_id = request.session.get('active_company')
    today = timezone.now().date()

    # Estadísticas básicas
    pending_count = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status__in=['draft', 'submitted', 'under_review']
    ).count()

    approved_count = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status__in=['approved', 'partial_approved']
    ).count()

    denied_count = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status='denied'
    ).count()

    # Autorizaciones próximas a vencer (7 días)
    expiring_soon = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status='approved',
        expiration_date__gte=today,
        expiration_date__lte=today + timedelta(days=7)
    ).count()

    # Últimas solicitudes
    recent_requests = AuthorizationRequest.objects.filter(
        company_id=company_id
    ).select_related(
        'patient', 'eps', 'requesting_physician', 'created_by'
    ).order_by('-request_date')[:10]

    # Estadísticas por EPS con tasa de aprobación
    eps_stats = []
    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)

    for eps in eps_list:
        total = AuthorizationRequest.objects.filter(
            company_id=company_id,
            eps=eps
        ).count()

        if total > 0:
            approved = AuthorizationRequest.objects.filter(
                company_id=company_id,
                eps=eps,
                status__in=['approved', 'partial_approved']
            ).count()

            denied = AuthorizationRequest.objects.filter(
                company_id=company_id,
                eps=eps,
                status='denied'
            ).count()

            approval_rate = (approved / total * 100) if total > 0 else 0

            eps_stats.append({
                'eps': eps,
                'total': total,
                'approved': approved,
                'denied': denied,
                'approval_rate': round(approval_rate, 1)
            })

    # Tiempo promedio de respuesta (en días)
    avg_response_time = AuthorizationRequest.objects.filter(
        company_id=company_id,
        response_date__isnull=False,
        submission_date__isnull=False
    ).extra(
        select={'response_days': 'julianday(response_date) - julianday(submission_date)'}
    ).values('response_days')

    if avg_response_time:
        total_days = sum(float(item['response_days']) for item in avg_response_time if item['response_days'])
        avg_days = total_days / len(avg_response_time) if len(avg_response_time) > 0 else 0
    else:
        avg_days = 0

    # Contrarreferencias pendientes
    pending_counter_referrals = CounterReferral.objects.filter(
        company_id=company_id,
        status='pending'
    ).count()

    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'denied_count': denied_count,
        'expiring_soon': expiring_soon,
        'recent_requests': recent_requests,
        'eps_stats': eps_stats,
        'avg_response_days': round(avg_days, 1),
        'pending_counter_referrals': pending_counter_referrals,
    }

    return render(request, 'authorizations/index.html', context)


# =============================================================================
# SOLICITUDES DE AUTORIZACIÓN
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations')
def authorization_list(request):
    """Lista de solicitudes de autorización con filtros."""
    company_id = request.session.get('active_company')

    authorizations = AuthorizationRequest.objects.filter(
        company_id=company_id
    ).select_related('patient', 'eps', 'requesting_physician', 'created_by')

    # Filtros
    status = request.GET.get('status')
    eps_id = request.GET.get('eps')
    physician_id = request.GET.get('physician')
    priority = request.GET.get('priority')
    service_type = request.GET.get('service_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        authorizations = authorizations.filter(status=status)

    if eps_id:
        authorizations = authorizations.filter(eps_id=eps_id)

    if physician_id:
        authorizations = authorizations.filter(requesting_physician_id=physician_id)

    if priority:
        authorizations = authorizations.filter(priority=priority)

    if service_type:
        authorizations = authorizations.filter(service_type=service_type)

    if date_from:
        authorizations = authorizations.filter(request_date__date__gte=date_from)

    if date_to:
        authorizations = authorizations.filter(request_date__date__lte=date_to)

    if search:
        authorizations = authorizations.filter(
            Q(authorization_number__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(diagnosis_description__icontains=search) |
            Q(service_description__icontains=search)
        )

    # Paginación
    paginator = Paginator(authorizations.order_by('-request_date'), 15)
    page = request.GET.get('page')
    authorizations = paginator.get_page(page)

    # Para filtros
    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)
    physicians = Employee.objects.filter(company_id=company_id, is_active=True)

    context = {
        'authorizations': authorizations,
        'status_choices': AuthorizationRequest.STATUS_CHOICES,
        'priority_choices': AuthorizationRequest.PRIORITY_CHOICES,
        'service_type_choices': AuthorizationRequest.SERVICE_TYPE_CHOICES,
        'eps_list': eps_list,
        'physicians': physicians,
        'filters': {
            'status': status,
            'eps': eps_id,
            'physician': physician_id,
            'priority': priority,
            'service_type': service_type,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'authorizations/authorization_list.html', context)


@login_required
@company_required
@module_permission_required('authorizations')
def authorization_detail(request, pk):
    """Detalle completo de una autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest.objects.select_related(
            'patient', 'eps', 'requesting_physician', 'created_by', 'updated_by'
        ),
        id=pk,
        company_id=company_id
    )

    # Documentos adjuntos
    attachments = AuthorizationAttachment.objects.filter(
        authorization_request=authorization
    ).select_related('created_by').order_by('-created_at')

    # Historial de uso
    usage_history = AuthorizationUsage.objects.filter(
        authorization_request=authorization
    ).select_related('created_by').order_by('-usage_date')

    # Contrarreferencias
    counter_referrals = CounterReferral.objects.filter(
        authorization_request=authorization
    ).select_related('referring_physician').order_by('-creation_date')

    # Calcular cantidad usada y disponible
    total_used = sum(u.quantity_used for u in usage_history)
    available_quantity = (authorization.approved_quantity or 0) - total_used

    context = {
        'authorization': authorization,
        'attachments': attachments,
        'usage_history': usage_history,
        'counter_referrals': counter_referrals,
        'total_used': total_used,
        'available_quantity': available_quantity,
    }

    return render(request, 'authorizations/authorization_detail.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_create(request):
    """Crear nueva solicitud de autorización."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            authorization = AuthorizationRequest()
            authorization.company_id = company_id

            # Generar número de autorización (formato: AUTH-YYYY-NNNN)
            year = timezone.now().year
            last_auth = AuthorizationRequest.objects.filter(
                company_id=company_id,
                authorization_number__startswith=f'AUTH-{year}'
            ).aggregate(last_number=Max('authorization_number'))

            if last_auth['last_number']:
                try:
                    last_num = int(last_auth['last_number'].split('-')[-1])
                    authorization.authorization_number = f"AUTH-{year}-{last_num + 1:04d}"
                except (ValueError, IndexError):
                    authorization.authorization_number = f"AUTH-{year}-0001"
            else:
                authorization.authorization_number = f"AUTH-{year}-0001"

            # Datos básicos
            authorization.eps_id = request.POST.get('eps')
            authorization.patient_id = request.POST.get('patient')
            authorization.requesting_physician_id = request.POST.get('requesting_physician')

            # Detalles de la solicitud
            authorization.service_type = request.POST.get('service_type')
            authorization.cups_code = request.POST.get('cups_code', '')
            authorization.service_description = request.POST.get('service_description')
            authorization.quantity = int(request.POST.get('quantity', 1))

            # Diagnóstico
            authorization.diagnosis_code = request.POST.get('diagnosis_code')
            authorization.diagnosis_description = request.POST.get('diagnosis_description')

            # Justificación médica
            authorization.medical_justification = request.POST.get('medical_justification')
            authorization.clinical_history_summary = request.POST.get('clinical_history_summary', '')

            # Prioridad
            authorization.priority = request.POST.get('priority', 'normal')

            authorization.created_by = request.user
            authorization.save()

            messages.success(request, f'Autorización {authorization.authorization_number} creada exitosamente.')
            return redirect('authorizations:authorization_detail', pk=authorization.id)

        except Exception as e:
            messages.error(request, f'Error al crear la autorización: {str(e)}')

    # Obtener datos para el formulario
    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)
    physicians = Employee.objects.filter(company_id=company_id, is_active=True)

    context = {
        'patients': patients,
        'eps_list': eps_list,
        'physicians': physicians,
        'service_type_choices': AuthorizationRequest.SERVICE_TYPE_CHOICES,
        'priority_choices': AuthorizationRequest.PRIORITY_CHOICES,
    }

    return render(request, 'authorizations/authorization_form.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_update(request, pk):
    """Editar autorización (solo si está en borrador o enviada)."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=pk,
        company_id=company_id
    )

    # Solo se puede editar si está en draft o submitted
    if authorization.status not in ['draft', 'submitted']:
        messages.error(request, 'No se puede editar una autorización en estado ' + authorization.get_status_display())
        return redirect('authorizations:authorization_detail', pk=pk)

    if request.method == 'POST':
        try:
            # Datos básicos
            authorization.eps_id = request.POST.get('eps')
            authorization.patient_id = request.POST.get('patient')
            authorization.requesting_physician_id = request.POST.get('requesting_physician')

            # Detalles de la solicitud
            authorization.service_type = request.POST.get('service_type')
            authorization.cups_code = request.POST.get('cups_code', '')
            authorization.service_description = request.POST.get('service_description')
            authorization.quantity = int(request.POST.get('quantity', 1))

            # Diagnóstico
            authorization.diagnosis_code = request.POST.get('diagnosis_code')
            authorization.diagnosis_description = request.POST.get('diagnosis_description')

            # Justificación médica
            authorization.medical_justification = request.POST.get('medical_justification')
            authorization.clinical_history_summary = request.POST.get('clinical_history_summary', '')

            # Prioridad
            authorization.priority = request.POST.get('priority', 'normal')

            authorization.updated_by = request.user
            authorization.save()

            messages.success(request, 'Autorización actualizada exitosamente.')
            return redirect('authorizations:authorization_detail', pk=authorization.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar la autorización: {str(e)}')

    # Obtener datos para el formulario
    from patients.models import Patient
    patients = Patient.objects.filter(
        company_id=company_id,
        is_active=True
    ).select_related('third_party').order_by('third_party__first_name', 'third_party__last_name')

    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)
    physicians = Employee.objects.filter(company_id=company_id, is_active=True)

    context = {
        'authorization': authorization,
        'patients': patients,
        'eps_list': eps_list,
        'physicians': physicians,
        'service_type_choices': AuthorizationRequest.SERVICE_TYPE_CHOICES,
        'priority_choices': AuthorizationRequest.PRIORITY_CHOICES,
    }

    return render(request, 'authorizations/authorization_form.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_approve(request, pk):
    """Aprobar una autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            eps_auth_number = request.POST.get('eps_authorization_number')
            approved_qty = int(request.POST.get('approved_quantity'))
            expiration_days = int(request.POST.get('expiration_days', 30))
            response_notes = request.POST.get('eps_response', '')

            if not eps_auth_number:
                messages.error(request, 'Debe ingresar el número de autorización de la EPS.')
                return redirect('authorizations:authorization_detail', pk=pk)

            # Usar método del modelo
            authorization.approve(eps_auth_number, approved_qty, expiration_days, request.user)

            # Guardar notas de respuesta
            if response_notes:
                authorization.eps_response = response_notes
                authorization.save()

            messages.success(request, f'Autorización {authorization.authorization_number} aprobada exitosamente.')
            return redirect('authorizations:authorization_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al aprobar la autorización: {str(e)}')
            return redirect('authorizations:authorization_detail', pk=pk)

    return redirect('authorizations:authorization_detail', pk=pk)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_deny(request, pk):
    """Negar una autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            denial_reason = request.POST.get('denial_reason')

            if not denial_reason:
                messages.error(request, 'Debe ingresar la razón de la negación.')
                return redirect('authorizations:authorization_detail', pk=pk)

            # Usar método del modelo
            authorization.deny(denial_reason, request.user)

            messages.success(request, f'Autorización {authorization.authorization_number} negada.')
            return redirect('authorizations:authorization_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al negar la autorización: {str(e)}')
            return redirect('authorizations:authorization_detail', pk=pk)

    return redirect('authorizations:authorization_detail', pk=pk)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_cancel(request, pk):
    """Cancelar una autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            authorization.status = 'cancelled'
            authorization.updated_by = request.user
            authorization.save()

            messages.success(request, f'Autorización {authorization.authorization_number} cancelada.')
            return redirect('authorizations:authorization_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al cancelar la autorización: {str(e)}')

    return redirect('authorizations:authorization_detail', pk=pk)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def authorization_submit(request, pk):
    """Enviar autorización (draft → submitted)."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            if authorization.status != 'draft':
                messages.error(request, 'Solo se pueden enviar autorizaciones en estado borrador.')
                return redirect('authorizations:authorization_detail', pk=pk)

            authorization.status = 'submitted'
            authorization.submission_date = timezone.now()
            authorization.updated_by = request.user
            authorization.save()

            messages.success(request, f'Autorización {authorization.authorization_number} enviada a la EPS.')
            return redirect('authorizations:authorization_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al enviar la autorización: {str(e)}')

    return redirect('authorizations:authorization_detail', pk=pk)


# =============================================================================
# CONTRARREFERENCIAS
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations')
def counter_referral_list(request):
    """Lista de contrarreferencias con filtros."""
    company_id = request.session.get('active_company')

    counter_referrals = CounterReferral.objects.filter(
        company_id=company_id
    ).select_related('patient', 'eps', 'authorization_request', 'referring_physician')

    # Filtros
    status = request.GET.get('status')
    eps_id = request.GET.get('eps')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        counter_referrals = counter_referrals.filter(status=status)

    if eps_id:
        counter_referrals = counter_referrals.filter(eps_id=eps_id)

    if date_from:
        counter_referrals = counter_referrals.filter(service_date__gte=date_from)

    if date_to:
        counter_referrals = counter_referrals.filter(service_date__lte=date_to)

    if search:
        counter_referrals = counter_referrals.filter(
            Q(counter_referral_number__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(final_diagnosis__icontains=search)
        )

    # Paginación
    paginator = Paginator(counter_referrals.order_by('-creation_date'), 15)
    page = request.GET.get('page')
    counter_referrals = paginator.get_page(page)

    # Para filtros
    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)

    context = {
        'counter_referrals': counter_referrals,
        'status_choices': CounterReferral.STATUS_CHOICES,
        'eps_list': eps_list,
        'filters': {
            'status': status,
            'eps': eps_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }

    return render(request, 'authorizations/counter_referral_list.html', context)


@login_required
@company_required
@module_permission_required('authorizations')
def counter_referral_detail(request, pk):
    """Detalle completo de una contrarreferencia."""
    company_id = request.session.get('active_company')

    counter_referral = get_object_or_404(
        CounterReferral.objects.select_related(
            'patient', 'eps', 'authorization_request', 'referring_physician', 'created_by'
        ),
        id=pk,
        company_id=company_id
    )

    # Documentos adjuntos
    attachments = AuthorizationAttachment.objects.filter(
        counter_referral=counter_referral
    ).select_related('created_by').order_by('-created_at')

    context = {
        'counter_referral': counter_referral,
        'attachments': attachments,
    }

    return render(request, 'authorizations/counter_referral_detail.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def counter_referral_create(request):
    """Crear nueva contrarreferencia."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            counter_referral = CounterReferral()
            counter_referral.company_id = company_id

            # Generar número de contrarreferencia (formato: CR-YYYY-NNNN)
            year = timezone.now().year
            last_cr = CounterReferral.objects.filter(
                company_id=company_id,
                counter_referral_number__startswith=f'CR-{year}'
            ).aggregate(last_number=Max('counter_referral_number'))

            if last_cr['last_number']:
                try:
                    last_num = int(last_cr['last_number'].split('-')[-1])
                    counter_referral.counter_referral_number = f"CR-{year}-{last_num + 1:04d}"
                except (ValueError, IndexError):
                    counter_referral.counter_referral_number = f"CR-{year}-0001"
            else:
                counter_referral.counter_referral_number = f"CR-{year}-0001"

            # Relación con autorización
            counter_referral.authorization_request_id = request.POST.get('authorization_request')

            # Obtener datos de la autorización
            auth_request = AuthorizationRequest.objects.get(id=counter_referral.authorization_request_id)
            counter_referral.eps = auth_request.eps
            counter_referral.patient = auth_request.patient

            # Médico que envía
            counter_referral.referring_physician_id = request.POST.get('referring_physician')

            # Detalles de la atención
            counter_referral.service_date = request.POST.get('service_date')
            counter_referral.services_provided = request.POST.get('services_provided')

            # Resultados y evolución
            counter_referral.treatment_results = request.POST.get('treatment_results')
            counter_referral.patient_evolution = request.POST.get('patient_evolution', '')
            counter_referral.final_diagnosis = request.POST.get('final_diagnosis')

            # Recomendaciones
            counter_referral.recommendations = request.POST.get('recommendations')
            counter_referral.requires_followup = request.POST.get('requires_followup') == 'on'

            if counter_referral.requires_followup:
                counter_referral.followup_instructions = request.POST.get('followup_instructions', '')

            counter_referral.created_by = request.user
            counter_referral.save()

            messages.success(request, f'Contrarreferencia {counter_referral.counter_referral_number} creada exitosamente.')
            return redirect('authorizations:counter_referral_detail', pk=counter_referral.id)

        except Exception as e:
            messages.error(request, f'Error al crear la contrarreferencia: {str(e)}')

    # Obtener autorizaciones aprobadas
    approved_authorizations = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status__in=['approved', 'partial_approved']
    ).select_related('patient', 'eps').order_by('-request_date')

    physicians = Employee.objects.filter(company_id=company_id, is_active=True)

    context = {
        'approved_authorizations': approved_authorizations,
        'physicians': physicians,
    }

    return render(request, 'authorizations/counter_referral_form.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def counter_referral_update(request, pk):
    """Editar contrarreferencia."""
    company_id = request.session.get('active_company')

    counter_referral = get_object_or_404(
        CounterReferral,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            # Médico que envía
            counter_referral.referring_physician_id = request.POST.get('referring_physician')

            # Detalles de la atención
            counter_referral.service_date = request.POST.get('service_date')
            counter_referral.services_provided = request.POST.get('services_provided')

            # Resultados y evolución
            counter_referral.treatment_results = request.POST.get('treatment_results')
            counter_referral.patient_evolution = request.POST.get('patient_evolution', '')
            counter_referral.final_diagnosis = request.POST.get('final_diagnosis')

            # Recomendaciones
            counter_referral.recommendations = request.POST.get('recommendations')
            counter_referral.requires_followup = request.POST.get('requires_followup') == 'on'

            if counter_referral.requires_followup:
                counter_referral.followup_instructions = request.POST.get('followup_instructions', '')

            counter_referral.save()

            messages.success(request, 'Contrarreferencia actualizada exitosamente.')
            return redirect('authorizations:counter_referral_detail', pk=counter_referral.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar la contrarreferencia: {str(e)}')

    physicians = Employee.objects.filter(company_id=company_id, is_active=True)

    context = {
        'counter_referral': counter_referral,
        'physicians': physicians,
    }

    return render(request, 'authorizations/counter_referral_form.html', context)


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def counter_referral_send(request, pk):
    """Marcar contrarreferencia como enviada."""
    company_id = request.session.get('active_company')

    counter_referral = get_object_or_404(
        CounterReferral,
        id=pk,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            counter_referral.mark_as_sent()
            messages.success(request, f'Contrarreferencia {counter_referral.counter_referral_number} marcada como enviada.')

        except Exception as e:
            messages.error(request, f'Error al enviar la contrarreferencia: {str(e)}')

    return redirect('authorizations:counter_referral_detail', pk=pk)


# =============================================================================
# DOCUMENTOS ADJUNTOS
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def attachment_upload(request, type, object_id):
    """Subir documento adjunto a autorización o contrarreferencia."""
    company_id = request.session.get('active_company')

    if request.method == 'POST':
        try:
            attachment = AuthorizationAttachment()

            # Asignar a autorización o contrarreferencia
            if type == 'authorization':
                authorization = get_object_or_404(
                    AuthorizationRequest,
                    id=object_id,
                    company_id=company_id
                )
                attachment.authorization_request = authorization
            elif type == 'counter_referral':
                counter_referral = get_object_or_404(
                    CounterReferral,
                    id=object_id,
                    company_id=company_id
                )
                attachment.counter_referral = counter_referral
            else:
                messages.error(request, 'Tipo de objeto inválido.')
                return redirect('authorizations:index')

            attachment.title = request.POST.get('title')
            attachment.description = request.POST.get('description', '')
            attachment.document_type = request.POST.get('document_type')
            attachment.file = request.FILES.get('file')
            attachment.created_by = request.user
            attachment.save()

            messages.success(request, 'Documento adjuntado exitosamente.')

            if type == 'authorization':
                return redirect('authorizations:authorization_detail', pk=object_id)
            else:
                return redirect('authorizations:counter_referral_detail', pk=object_id)

        except Exception as e:
            messages.error(request, f'Error al subir el documento: {str(e)}')

    # Redirigir según el tipo
    if type == 'authorization':
        return redirect('authorizations:authorization_detail', pk=object_id)
    else:
        return redirect('authorizations:counter_referral_detail', pk=object_id)


@login_required
@company_required
@module_permission_required('authorizations')
def attachment_download(request, pk):
    """Descargar documento adjunto."""
    company_id = request.session.get('active_company')

    # Verificar acceso al documento
    attachment = get_object_or_404(AuthorizationAttachment, id=pk)

    # Verificar que pertenece a la empresa
    if attachment.authorization_request:
        if attachment.authorization_request.company_id != company_id:
            raise Http404("Documento no encontrado")
    elif attachment.counter_referral:
        if attachment.counter_referral.company_id != company_id:
            raise Http404("Documento no encontrado")

    # Servir archivo
    if attachment.file and os.path.exists(attachment.file.path):
        return FileResponse(
            open(attachment.file.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(attachment.file.name)
        )
    else:
        raise Http404("Archivo no encontrado")


@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def attachment_delete(request, pk):
    """Eliminar documento adjunto."""
    company_id = request.session.get('active_company')

    attachment = get_object_or_404(AuthorizationAttachment, id=pk)

    # Verificar que pertenece a la empresa
    if attachment.authorization_request:
        if attachment.authorization_request.company_id != company_id:
            raise Http404("Documento no encontrado")
        redirect_url = 'authorizations:authorization_detail'
        redirect_pk = attachment.authorization_request.id
    elif attachment.counter_referral:
        if attachment.counter_referral.company_id != company_id:
            raise Http404("Documento no encontrado")
        redirect_url = 'authorizations:counter_referral_detail'
        redirect_pk = attachment.counter_referral.id
    else:
        raise Http404("Documento no encontrado")

    if request.method == 'POST':
        try:
            # Eliminar archivo físico
            if attachment.file and os.path.exists(attachment.file.path):
                os.remove(attachment.file.path)

            attachment.delete()
            messages.success(request, 'Documento eliminado exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al eliminar el documento: {str(e)}')

    return redirect(redirect_url, pk=redirect_pk)


# =============================================================================
# REGISTRO DE USO
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations', 'edit')
def usage_create(request, authorization_id):
    """Registrar uso de autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=authorization_id,
        company_id=company_id
    )

    if request.method == 'POST':
        try:
            # Validar que la autorización esté aprobada
            if authorization.status not in ['approved', 'partial_approved']:
                messages.error(request, 'Solo se puede registrar uso en autorizaciones aprobadas.')
                return redirect('authorizations:authorization_detail', pk=authorization_id)

            # Validar cantidad disponible
            usage_history = AuthorizationUsage.objects.filter(authorization_request=authorization)
            total_used = sum(u.quantity_used for u in usage_history)
            available = (authorization.approved_quantity or 0) - total_used

            quantity_used = int(request.POST.get('quantity_used', 1))

            if quantity_used > available:
                messages.error(request, f'Cantidad solicitada ({quantity_used}) excede la cantidad disponible ({available}).')
                return redirect('authorizations:authorization_detail', pk=authorization_id)

            # Crear registro de uso
            usage = AuthorizationUsage()
            usage.authorization_request = authorization
            usage.usage_date = request.POST.get('usage_date') or timezone.now()
            usage.quantity_used = quantity_used
            usage.notes = request.POST.get('notes', '')
            usage.created_by = request.user
            usage.save()

            messages.success(request, 'Uso registrado exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al registrar el uso: {str(e)}')

    return redirect('authorizations:authorization_detail', pk=authorization_id)


@login_required
@company_required
@module_permission_required('authorizations')
def usage_list(request, authorization_id):
    """Ver historial de uso de una autorización."""
    company_id = request.session.get('active_company')

    authorization = get_object_or_404(
        AuthorizationRequest,
        id=authorization_id,
        company_id=company_id
    )

    usage_history = AuthorizationUsage.objects.filter(
        authorization_request=authorization
    ).select_related('created_by').order_by('-usage_date')

    total_used = sum(u.quantity_used for u in usage_history)
    available = (authorization.approved_quantity or 0) - total_used

    context = {
        'authorization': authorization,
        'usage_history': usage_history,
        'total_used': total_used,
        'available': available,
    }

    return render(request, 'authorizations/usage_list.html', context)


# =============================================================================
# REPORTES
# =============================================================================

@login_required
@company_required
@module_permission_required('authorizations')
def reports(request):
    """Reportes y estadísticas del módulo."""
    company_id = request.session.get('active_company')

    # Rango de fechas
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Autorizaciones por EPS
    auth_by_eps = AuthorizationRequest.objects.filter(
        company_id=company_id,
        request_date__date__gte=date_from,
        request_date__date__lte=date_to
    ).values('eps__name').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status__in=['approved', 'partial_approved'])),
        denied=Count('id', filter=Q(status='denied'))
    ).order_by('-total')

    # Autorizaciones por estado
    auth_by_status = AuthorizationRequest.objects.filter(
        company_id=company_id,
        request_date__date__gte=date_from,
        request_date__date__lte=date_to
    ).values('status').annotate(total=Count('id')).order_by('-total')

    # Autorizaciones por mes
    auth_by_month = AuthorizationRequest.objects.filter(
        company_id=company_id,
        request_date__date__gte=date_from,
        request_date__date__lte=date_to
    ).annotate(
        month=TruncMonth('request_date')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    # Tiempo promedio de respuesta por EPS
    avg_response_by_eps = []
    eps_list = EPS.objects.filter(company_id=company_id, is_active=True)

    for eps in eps_list:
        auth_with_response = AuthorizationRequest.objects.filter(
            company_id=company_id,
            eps=eps,
            response_date__isnull=False,
            submission_date__isnull=False,
            request_date__date__gte=date_from,
            request_date__date__lte=date_to
        ).extra(
            select={'response_days': 'julianday(response_date) - julianday(submission_date)'}
        ).values('response_days')

        if auth_with_response:
            total_days = sum(float(item['response_days']) for item in auth_with_response if item['response_days'])
            avg_days = total_days / len(auth_with_response) if len(auth_with_response) > 0 else 0

            avg_response_by_eps.append({
                'eps': eps.name,
                'avg_days': round(avg_days, 1),
                'count': len(auth_with_response)
            })

    # Autorizaciones próximas a vencer
    expiring_authorizations = AuthorizationRequest.objects.filter(
        company_id=company_id,
        status='approved',
        expiration_date__gte=timezone.now().date(),
        expiration_date__lte=timezone.now().date() + timedelta(days=15)
    ).select_related('patient', 'eps').order_by('expiration_date')

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'auth_by_eps': auth_by_eps,
        'auth_by_status': auth_by_status,
        'auth_by_month': auth_by_month,
        'avg_response_by_eps': avg_response_by_eps,
        'expiring_authorizations': expiring_authorizations,
    }

    return render(request, 'authorizations/reports.html', context)


# =============================================================================
# API / AJAX ENDPOINTS
# =============================================================================

@login_required
@company_required
def api_patient_info(request, patient_id):
    """API para obtener información del paciente (AJAX)."""
    company_id = request.session.get('active_company')

    try:
        from patients.models import Patient
        patient = Patient.objects.select_related('third_party').get(
            id=patient_id,
            company_id=company_id
        )

        data = {
            'id': str(patient.id),
            'full_name': patient.get_full_name(),
            'document_number': patient.document_number,
            'phone': patient.phone1 or '',
            'email': patient.email or '',
            'address': patient.address or '',
            'city': patient.city or '',
        }

        return JsonResponse(data)
    except ThirdParty.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)


@login_required
@company_required
def api_authorization_info(request, authorization_id):
    """API para obtener información de autorización (AJAX)."""
    company_id = request.session.get('active_company')

    try:
        authorization = AuthorizationRequest.objects.select_related(
            'patient', 'eps', 'requesting_physician'
        ).get(
            id=authorization_id,
            company_id=company_id
        )

        # Calcular uso
        usage_history = AuthorizationUsage.objects.filter(authorization_request=authorization)
        total_used = sum(u.quantity_used for u in usage_history)
        available = (authorization.approved_quantity or 0) - total_used

        data = {
            'id': str(authorization.id),
            'authorization_number': authorization.authorization_number,
            'patient_name': authorization.patient.get_full_name(),
            'eps_name': authorization.eps.name,
            'service_description': authorization.service_description,
            'diagnosis': authorization.diagnosis_description,
            'status': authorization.get_status_display(),
            'approved_quantity': authorization.approved_quantity or 0,
            'total_used': total_used,
            'available': available,
            'expiration_date': authorization.expiration_date.isoformat() if authorization.expiration_date else None,
        }

        return JsonResponse(data)
    except AuthorizationRequest.DoesNotExist:
        return JsonResponse({'error': 'Autorización no encontrada'}, status=404)
