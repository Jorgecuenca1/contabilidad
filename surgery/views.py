from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from core.decorators import company_required
from .models import (
    OperatingRoom, SurgicalProcedure, Surgery,
    AnesthesiaNote, SurgicalSupply, PostOperativeNote
)
from third_parties.models import ThirdParty
from payroll.models import Employee


# ==================== DASHBOARD ====================

@login_required
@company_required
def surgery_dashboard(request):
    """Dashboard principal del módulo de cirugías"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    # Estadísticas generales
    total_surgeries = Surgery.objects.filter(company=current_company).count()
    today = date.today()
    surgeries_today = Surgery.objects.filter(
        company=current_company,
        scheduled_date=today
    ).count()

    # Cirugías por estado
    surgeries_scheduled = Surgery.objects.filter(
        company=current_company,
        status='scheduled'
    ).count()

    surgeries_in_progress = Surgery.objects.filter(
        company=current_company,
        status='in_progress'
    ).count()

    # Quirófanos disponibles
    available_rooms = OperatingRoom.objects.filter(
        company=current_company,
        status='available'
    ).count()

    # Cirugías programadas hoy
    today_surgeries = Surgery.objects.filter(
        company=current_company,
        scheduled_date=today
    ).select_related('patient', 'operating_room', 'surgical_procedure', 'surgeon').order_by('scheduled_time')[:10]

    # Cirugías próximas (próximos 7 días)
    next_week = today + timedelta(days=7)
    upcoming_surgeries = Surgery.objects.filter(
        company=current_company,
        scheduled_date__gte=today,
        scheduled_date__lte=next_week,
        status__in=['scheduled', 'confirmed']
    ).select_related('patient', 'surgical_procedure', 'surgeon').order_by('scheduled_date', 'scheduled_time')[:10]

    # Estado de quirófanos
    operating_rooms = OperatingRoom.objects.filter(
        company=current_company,
        is_active=True
    ).order_by('room_number')

    # Cirujanos disponibles
    surgeons = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='cirujano') |
        Q(position__icontains='surgeon')
    )[:10]

    # Anestesiólogos disponibles
    anesthesiologists = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='anestesiólogo') |
        Q(position__icontains='anestesiologo') |
        Q(position__icontains='anesthesiologist')
    )[:10]

    context = {
        'total_surgeries': total_surgeries,
        'surgeries_today': surgeries_today,
        'surgeries_scheduled': surgeries_scheduled,
        'surgeries_in_progress': surgeries_in_progress,
        'available_rooms': available_rooms,
        'today_surgeries': today_surgeries,
        'upcoming_surgeries': upcoming_surgeries,
        'operating_rooms': operating_rooms,
        'surgeons': surgeons,
        'anesthesiologists': anesthesiologists,
    }

    return render(request, 'surgery/dashboard.html', context)


# ==================== OPERATING ROOM VIEWS ====================

@login_required
@company_required
def operating_room_list(request):
    """Lista de quirófanos"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    rooms = OperatingRoom.objects.filter(
        company=current_company
    ).order_by('room_number')

    # Filtros
    status_filter = request.GET.get('status', '')
    room_type_filter = request.GET.get('room_type', '')

    if status_filter:
        rooms = rooms.filter(status=status_filter)

    if room_type_filter:
        rooms = rooms.filter(room_type=room_type_filter)

    # Paginación
    paginator = Paginator(rooms, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'room_type_filter': room_type_filter,
    }

    return render(request, 'surgery/operating_room_list.html', context)


@login_required
@company_required
def operating_room_create(request):
    """Crear quirófano"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    if request.method == 'POST':
        try:
            from core.models import Company
            company_obj = Company.objects.get(id=current_company)

            room = OperatingRoom(
                company=company_obj,
                room_number=request.POST.get('room_number'),
                room_name=request.POST.get('room_name'),
                room_type=request.POST.get('room_type'),
                floor=request.POST.get('floor'),
                building=request.POST.get('building', ''),
                status=request.POST.get('status', 'available'),
                has_laminar_flow=request.POST.get('has_laminar_flow') == 'on',
                capacity=int(request.POST.get('capacity', 1)),
                equipment_description=request.POST.get('equipment_description', ''),
                notes=request.POST.get('notes', ''),
                is_active=True,
                created_by=request.user
            )
            room.save()

            messages.success(request, f'Quirófano {room.room_number} creado exitosamente')
            return redirect('surgery:operating_room_detail', room_id=room.id)

        except Exception as e:
            messages.error(request, f'Error al crear quirófano: {str(e)}')

    return render(request, 'surgery/operating_room_form.html', {})


@login_required
@company_required
def operating_room_detail(request, room_id):
    """Detalle de quirófano"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    room = get_object_or_404(OperatingRoom, id=room_id, company=current_company)

    # Cirugías programadas en este quirófano
    today = date.today()
    next_week = today + timedelta(days=7)

    scheduled_surgeries = Surgery.objects.filter(
        company=current_company,
        operating_room=room,
        scheduled_date__gte=today,
        scheduled_date__lte=next_week
    ).select_related('patient', 'surgical_procedure', 'surgeon').order_by('scheduled_date', 'scheduled_time')

    context = {
        'room': room,
        'scheduled_surgeries': scheduled_surgeries,
    }

    return render(request, 'surgery/operating_room_detail.html', context)


@login_required
@company_required
def operating_room_update(request, room_id):
    """Actualizar quirófano"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    room = get_object_or_404(OperatingRoom, id=room_id, company=current_company)

    if request.method == 'POST':
        try:
            room.room_number = request.POST.get('room_number')
            room.room_name = request.POST.get('room_name')
            room.room_type = request.POST.get('room_type')
            room.floor = request.POST.get('floor')
            room.building = request.POST.get('building', '')
            room.status = request.POST.get('status')
            room.has_laminar_flow = request.POST.get('has_laminar_flow') == 'on'
            room.capacity = int(request.POST.get('capacity', 1))
            room.equipment_description = request.POST.get('equipment_description', '')
            room.notes = request.POST.get('notes', '')
            room.save()

            messages.success(request, f'Quirófano {room.room_number} actualizado exitosamente')
            return redirect('surgery:operating_room_detail', room_id=room.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar quirófano: {str(e)}')

    context = {
        'room': room,
    }

    return render(request, 'surgery/operating_room_form.html', context)


# ==================== SURGICAL PROCEDURE VIEWS ====================

@login_required
@company_required
def surgical_procedure_list(request):
    """Lista de procedimientos quirúrgicos"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    procedures = SurgicalProcedure.objects.filter(
        company=current_company
    ).order_by('name')

    # Filtros
    specialty_filter = request.GET.get('specialty', '')
    complexity_filter = request.GET.get('complexity', '')
    search = request.GET.get('search', '')

    if specialty_filter:
        procedures = procedures.filter(specialty=specialty_filter)

    if complexity_filter:
        procedures = procedures.filter(complexity=complexity_filter)

    if search:
        procedures = procedures.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )

    # Paginación
    paginator = Paginator(procedures, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'specialty_filter': specialty_filter,
        'complexity_filter': complexity_filter,
        'search': search,
    }

    return render(request, 'surgery/surgical_procedure_list.html', context)


@login_required
@company_required
def surgical_procedure_create(request):
    """Crear procedimiento quirúrgico"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    if request.method == 'POST':
        try:
            from core.models import Company
            company_obj = Company.objects.get(id=current_company)

            procedure = SurgicalProcedure(
                company=company_obj,
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                specialty=request.POST.get('specialty'),
                complexity=request.POST.get('complexity'),
                estimated_duration_minutes=int(request.POST.get('estimated_duration_minutes', 60)),
                requires_icu=request.POST.get('requires_icu') == 'on',
                requires_blood_bank=request.POST.get('requires_blood_bank') == 'on',
                anesthesia_type_recommended=request.POST.get('anesthesia_type_recommended', ''),
                pre_operative_requirements=request.POST.get('pre_operative_requirements', ''),
                post_operative_care=request.POST.get('post_operative_care', ''),
                contraindications=request.POST.get('contraindications', ''),
                is_active=True,
                created_by=request.user
            )
            procedure.save()

            messages.success(request, f'Procedimiento {procedure.name} creado exitosamente')
            return redirect('surgery:surgical_procedure_detail', procedure_id=procedure.id)

        except Exception as e:
            messages.error(request, f'Error al crear procedimiento: {str(e)}')

    return render(request, 'surgery/surgical_procedure_form.html', {})


@login_required
@company_required
def surgical_procedure_detail(request, procedure_id):
    """Detalle de procedimiento quirúrgico"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    procedure = get_object_or_404(SurgicalProcedure, id=procedure_id, company=current_company)

    # Cirugías programadas con este procedimiento
    upcoming_surgeries = Surgery.objects.filter(
        company=current_company,
        surgical_procedure=procedure,
        scheduled_date__gte=date.today()
    ).select_related('patient', 'surgeon').order_by('scheduled_date', 'scheduled_time')[:10]

    # Estadísticas
    total_surgeries = Surgery.objects.filter(
        company=current_company,
        surgical_procedure=procedure
    ).count()

    completed_surgeries = Surgery.objects.filter(
        company=current_company,
        surgical_procedure=procedure,
        status='completed'
    ).count()

    context = {
        'procedure': procedure,
        'upcoming_surgeries': upcoming_surgeries,
        'total_surgeries': total_surgeries,
        'completed_surgeries': completed_surgeries,
    }

    return render(request, 'surgery/surgical_procedure_detail.html', context)


@login_required
@company_required
def surgical_procedure_update(request, procedure_id):
    """Actualizar procedimiento quirúrgico"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    procedure = get_object_or_404(SurgicalProcedure, id=procedure_id, company=current_company)

    if request.method == 'POST':
        try:
            procedure.code = request.POST.get('code')
            procedure.name = request.POST.get('name')
            procedure.description = request.POST.get('description', '')
            procedure.specialty = request.POST.get('specialty')
            procedure.complexity = request.POST.get('complexity')
            procedure.estimated_duration_minutes = int(request.POST.get('estimated_duration_minutes', 60))
            procedure.requires_icu = request.POST.get('requires_icu') == 'on'
            procedure.requires_blood_bank = request.POST.get('requires_blood_bank') == 'on'
            procedure.anesthesia_type_recommended = request.POST.get('anesthesia_type_recommended', '')
            procedure.pre_operative_requirements = request.POST.get('pre_operative_requirements', '')
            procedure.post_operative_care = request.POST.get('post_operative_care', '')
            procedure.contraindications = request.POST.get('contraindications', '')
            procedure.save()

            messages.success(request, f'Procedimiento {procedure.name} actualizado exitosamente')
            return redirect('surgery:surgical_procedure_detail', procedure_id=procedure.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar procedimiento: {str(e)}')

    context = {
        'procedure': procedure,
    }

    return render(request, 'surgery/surgical_procedure_form.html', context)


# ==================== SURGERY VIEWS ====================

@login_required
@company_required
def surgery_list(request):
    """Lista de cirugías"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgeries = Surgery.objects.filter(
        company=current_company
    ).select_related('patient', 'surgical_procedure', 'operating_room', 'surgeon').order_by('-scheduled_date', '-scheduled_time')

    # Filtros
    status_filter = request.GET.get('status', '')
    urgency_filter = request.GET.get('urgency', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    if status_filter:
        surgeries = surgeries.filter(status=status_filter)

    if urgency_filter:
        surgeries = surgeries.filter(urgency=urgency_filter)

    if date_from:
        surgeries = surgeries.filter(scheduled_date__gte=date_from)

    if date_to:
        surgeries = surgeries.filter(scheduled_date__lte=date_to)

    if search:
        surgeries = surgeries.filter(
            Q(surgery_number__icontains=search) |
            Q(patient__nombre__icontains=search) |
            Q(surgical_procedure__name__icontains=search)
        )

    # Paginación
    paginator = Paginator(surgeries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'urgency_filter': urgency_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }

    return render(request, 'surgery/surgery_list.html', context)


@login_required
@company_required
def surgery_create(request):
    """Crear cirugía"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    if request.method == 'POST':
        try:
            from core.models import Company
            company_obj = Company.objects.get(id=current_company)

            # Obtener objetos relacionados
            patient = ThirdParty.objects.get(id=request.POST.get('patient_id'), company=current_company)
            operating_room = OperatingRoom.objects.get(id=request.POST.get('operating_room_id'), company=current_company)
            surgical_procedure = SurgicalProcedure.objects.get(id=request.POST.get('surgical_procedure_id'), company=current_company)
            surgeon = Employee.objects.get(id=request.POST.get('surgeon_id'), company=current_company)
            anesthesiologist = Employee.objects.get(id=request.POST.get('anesthesiologist_id'), company=current_company)

            # Asistente y enfermeras son opcionales
            assistant_surgeon_id = request.POST.get('assistant_surgeon_id')
            assistant_surgeon = Employee.objects.get(id=assistant_surgeon_id, company=current_company) if assistant_surgeon_id else None

            scrub_nurse_id = request.POST.get('scrub_nurse_id')
            scrub_nurse = Employee.objects.get(id=scrub_nurse_id, company=current_company) if scrub_nurse_id else None

            circulating_nurse_id = request.POST.get('circulating_nurse_id')
            circulating_nurse = Employee.objects.get(id=circulating_nurse_id, company=current_company) if circulating_nurse_id else None

            # Generar número de cirugía
            last_surgery = Surgery.objects.filter(company=current_company).order_by('-surgery_number').first()
            if last_surgery and last_surgery.surgery_number:
                try:
                    last_number = int(last_surgery.surgery_number.split('-')[-1])
                    surgery_number = f"CIR-{last_number + 1:06d}"
                except:
                    surgery_number = f"CIR-{Surgery.objects.filter(company=current_company).count() + 1:06d}"
            else:
                surgery_number = "CIR-000001"

            surgery = Surgery(
                company=company_obj,
                surgery_number=surgery_number,
                patient=patient,
                scheduled_date=request.POST.get('scheduled_date'),
                scheduled_time=request.POST.get('scheduled_time'),
                operating_room=operating_room,
                surgical_procedure=surgical_procedure,
                surgeon=surgeon,
                assistant_surgeon=assistant_surgeon,
                anesthesiologist=anesthesiologist,
                scrub_nurse=scrub_nurse,
                circulating_nurse=circulating_nurse,
                urgency=request.POST.get('urgency'),
                status='scheduled',
                pre_operative_diagnosis=request.POST.get('pre_operative_diagnosis'),
                pre_operative_diagnosis_code=request.POST.get('pre_operative_diagnosis_code', ''),
                special_considerations=request.POST.get('special_considerations', ''),
                patient_consent_signed=request.POST.get('patient_consent_signed') == 'on',
                fasting_verified=request.POST.get('fasting_verified') == 'on',
                allergies=request.POST.get('allergies', ''),
                created_by=request.user
            )
            surgery.save()

            messages.success(request, f'Cirugía {surgery.surgery_number} programada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al crear cirugía: {str(e)}')

    # Obtener datos para el formulario
    patients = ThirdParty.objects.filter(
        company=current_company,
        is_customer=True,
        is_active=True
    ).order_by('nombre')

    operating_rooms = OperatingRoom.objects.filter(
        company=current_company,
        is_active=True,
        status='available'
    ).order_by('room_number')

    surgical_procedures = SurgicalProcedure.objects.filter(
        company=current_company,
        is_active=True
    ).order_by('name')

    surgeons = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='cirujano') |
        Q(position__icontains='surgeon')
    ).order_by('first_name', 'last_name')

    anesthesiologists = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='anestesiólogo') |
        Q(position__icontains='anestesiologo') |
        Q(position__icontains='anesthesiologist')
    ).order_by('first_name', 'last_name')

    nurses = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='enfermer') |
        Q(position__icontains='nurse')
    ).order_by('first_name', 'last_name')

    context = {
        'patients': patients,
        'operating_rooms': operating_rooms,
        'surgical_procedures': surgical_procedures,
        'surgeons': surgeons,
        'anesthesiologists': anesthesiologists,
        'nurses': nurses,
    }

    return render(request, 'surgery/surgery_form.html', context)


@login_required
@company_required
def surgery_detail(request, surgery_id):
    """Detalle de cirugía"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)

    # Obtener información relacionada
    try:
        anesthesia_note = AnesthesiaNote.objects.get(surgery=surgery)
    except AnesthesiaNote.DoesNotExist:
        anesthesia_note = None

    try:
        postop_note = PostOperativeNote.objects.get(surgery=surgery)
    except PostOperativeNote.DoesNotExist:
        postop_note = None

    surgical_supplies = SurgicalSupply.objects.filter(surgery=surgery).order_by('created_at')

    context = {
        'surgery': surgery,
        'anesthesia_note': anesthesia_note,
        'postop_note': postop_note,
        'surgical_supplies': surgical_supplies,
    }

    return render(request, 'surgery/surgery_detail.html', context)


@login_required
@company_required
def surgery_update(request, surgery_id):
    """Actualizar cirugía"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)

    if request.method == 'POST':
        try:
            # Actualizar campos editables
            surgery.scheduled_date = request.POST.get('scheduled_date')
            surgery.scheduled_time = request.POST.get('scheduled_time')
            surgery.status = request.POST.get('status')

            # Actualizar quirófano si cambió
            operating_room_id = request.POST.get('operating_room_id')
            if operating_room_id:
                surgery.operating_room = OperatingRoom.objects.get(id=operating_room_id, company=current_company)

            # Actualizar cirujano si cambió
            surgeon_id = request.POST.get('surgeon_id')
            if surgeon_id:
                surgery.surgeon = Employee.objects.get(id=surgeon_id, company=current_company)

            # Actualizar anestesiólogo si cambió
            anesthesiologist_id = request.POST.get('anesthesiologist_id')
            if anesthesiologist_id:
                surgery.anesthesiologist = Employee.objects.get(id=anesthesiologist_id, company=current_company)

            # Actualizar otros campos
            surgery.special_considerations = request.POST.get('special_considerations', '')
            surgery.patient_consent_signed = request.POST.get('patient_consent_signed') == 'on'
            surgery.fasting_verified = request.POST.get('fasting_verified') == 'on'

            # Si está completando información transoperatoria
            if request.POST.get('actual_start_time'):
                actual_start = request.POST.get('actual_start_time')
                surgery.actual_start_time = datetime.strptime(actual_start, '%Y-%m-%dT%H:%M')

            if request.POST.get('actual_end_time'):
                actual_end = request.POST.get('actual_end_time')
                surgery.actual_end_time = datetime.strptime(actual_end, '%Y-%m-%dT%H:%M')

            surgery.post_operative_diagnosis = request.POST.get('post_operative_diagnosis', '')
            surgery.post_operative_diagnosis_code = request.POST.get('post_operative_diagnosis_code', '')
            surgery.surgical_findings = request.POST.get('surgical_findings', '')
            surgery.surgical_technique = request.POST.get('surgical_technique', '')
            surgery.complications = request.POST.get('complications', '')

            if request.POST.get('estimated_blood_loss'):
                surgery.estimated_blood_loss = int(request.POST.get('estimated_blood_loss'))

            surgery.save()

            messages.success(request, f'Cirugía {surgery.surgery_number} actualizada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar cirugía: {str(e)}')

    # Obtener datos para el formulario
    operating_rooms = OperatingRoom.objects.filter(
        company=current_company,
        is_active=True
    ).order_by('room_number')

    surgeons = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='cirujano') |
        Q(position__icontains='surgeon')
    ).order_by('first_name', 'last_name')

    anesthesiologists = Employee.objects.filter(
        company=current_company,
        is_active=True
    ).filter(
        Q(position__icontains='anestesiólogo') |
        Q(position__icontains='anestesiologo') |
        Q(position__icontains='anesthesiologist')
    ).order_by('first_name', 'last_name')

    context = {
        'surgery': surgery,
        'operating_rooms': operating_rooms,
        'surgeons': surgeons,
        'anesthesiologists': anesthesiologists,
    }

    return render(request, 'surgery/surgery_form.html', context)


# ==================== ANESTHESIA NOTE VIEWS ====================

@login_required
@company_required
def anesthesia_note_create(request, surgery_id):
    """Crear nota de anestesia"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)

    # Verificar si ya existe nota de anestesia
    if hasattr(surgery, 'anesthesia_note'):
        messages.warning(request, 'Esta cirugía ya tiene una nota de anestesia')
        return redirect('surgery:anesthesia_note_detail', surgery_id=surgery.id)

    if request.method == 'POST':
        try:
            anesthesia_note = AnesthesiaNote(
                surgery=surgery,
                company=surgery.company,
                asa_classification=request.POST.get('asa_classification'),
                anesthesia_type=request.POST.get('anesthesia_type'),
                fasting_hours=int(request.POST.get('fasting_hours', 0)),
                # Signos vitales pre-operatorios
                pre_blood_pressure_systolic=int(request.POST.get('pre_blood_pressure_systolic', 0)),
                pre_blood_pressure_diastolic=int(request.POST.get('pre_blood_pressure_diastolic', 0)),
                pre_heart_rate=int(request.POST.get('pre_heart_rate', 0)),
                pre_respiratory_rate=int(request.POST.get('pre_respiratory_rate', 0)),
                pre_oxygen_saturation=int(request.POST.get('pre_oxygen_saturation', 0)),
                pre_temperature=Decimal(request.POST.get('pre_temperature', 0)),
                # Monitoreo intraoperatorio
                intra_blood_pressure_min_systolic=int(request.POST.get('intra_blood_pressure_min_systolic', 0)) if request.POST.get('intra_blood_pressure_min_systolic') else None,
                intra_blood_pressure_max_systolic=int(request.POST.get('intra_blood_pressure_max_systolic', 0)) if request.POST.get('intra_blood_pressure_max_systolic') else None,
                intra_blood_pressure_min_diastolic=int(request.POST.get('intra_blood_pressure_min_diastolic', 0)) if request.POST.get('intra_blood_pressure_min_diastolic') else None,
                intra_blood_pressure_max_diastolic=int(request.POST.get('intra_blood_pressure_max_diastolic', 0)) if request.POST.get('intra_blood_pressure_max_diastolic') else None,
                intra_heart_rate_min=int(request.POST.get('intra_heart_rate_min', 0)) if request.POST.get('intra_heart_rate_min') else None,
                intra_heart_rate_max=int(request.POST.get('intra_heart_rate_max', 0)) if request.POST.get('intra_heart_rate_max') else None,
                intra_oxygen_saturation_min=int(request.POST.get('intra_oxygen_saturation_min', 0)) if request.POST.get('intra_oxygen_saturation_min') else None,
                # Medicamentos y líquidos
                medications_administered=request.POST.get('medications_administered', ''),
                fluids_administered=request.POST.get('fluids_administered', ''),
                # Tiempos
                emergence_time=int(request.POST.get('emergence_time', 0)) if request.POST.get('emergence_time') else None,
                extubation_time=int(request.POST.get('extubation_time', 0)) if request.POST.get('extubation_time') else None,
                recovery_room_time=int(request.POST.get('recovery_room_time', 0)) if request.POST.get('recovery_room_time') else None,
                # Complicaciones
                complications=request.POST.get('complications', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )
            anesthesia_note.save()

            messages.success(request, 'Nota de anestesia creada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al crear nota de anestesia: {str(e)}')

    context = {
        'surgery': surgery,
    }

    return render(request, 'surgery/anesthesia_note_form.html', context)


@login_required
@company_required
def anesthesia_note_detail(request, surgery_id):
    """Detalle de nota de anestesia"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)
    anesthesia_note = get_object_or_404(AnesthesiaNote, surgery=surgery)

    context = {
        'surgery': surgery,
        'anesthesia_note': anesthesia_note,
    }

    return render(request, 'surgery/anesthesia_note_detail.html', context)


@login_required
@company_required
def anesthesia_note_update(request, surgery_id):
    """Actualizar nota de anestesia"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)
    anesthesia_note = get_object_or_404(AnesthesiaNote, surgery=surgery)

    if request.method == 'POST':
        try:
            anesthesia_note.asa_classification = request.POST.get('asa_classification')
            anesthesia_note.anesthesia_type = request.POST.get('anesthesia_type')
            anesthesia_note.fasting_hours = int(request.POST.get('fasting_hours', 0))
            # Actualizar campos...
            anesthesia_note.medications_administered = request.POST.get('medications_administered', '')
            anesthesia_note.fluids_administered = request.POST.get('fluids_administered', '')
            anesthesia_note.complications = request.POST.get('complications', '')
            anesthesia_note.observations = request.POST.get('observations', '')
            anesthesia_note.save()

            messages.success(request, 'Nota de anestesia actualizada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar nota de anestesia: {str(e)}')

    context = {
        'surgery': surgery,
        'anesthesia_note': anesthesia_note,
    }

    return render(request, 'surgery/anesthesia_note_form.html', context)


# ==================== SURGICAL SUPPLY VIEWS ====================

@login_required
@company_required
def surgical_supply_add(request, surgery_id):
    """Agregar insumo quirúrgico"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)

    if request.method == 'POST':
        try:
            supply = SurgicalSupply(
                surgery=surgery,
                company=surgery.company,
                supply_type=request.POST.get('supply_type'),
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                lot_number=request.POST.get('lot_number'),
                serial_number=request.POST.get('serial_number', ''),
                expiration_date=request.POST.get('expiration_date') if request.POST.get('expiration_date') else None,
                manufacturer=request.POST.get('manufacturer', ''),
                quantity=Decimal(request.POST.get('quantity', 1)),
                unit=request.POST.get('unit', 'unidad'),
                unit_cost=Decimal(request.POST.get('unit_cost', 0)) if request.POST.get('unit_cost') else None,
                used_by=request.POST.get('used_by', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )
            supply.save()

            messages.success(request, 'Insumo quirúrgico registrado exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al registrar insumo: {str(e)}')

    context = {
        'surgery': surgery,
    }

    return render(request, 'surgery/surgical_supply_form.html', context)


@login_required
@company_required
def surgical_supply_list(request, surgery_id):
    """Lista de insumos de una cirugía"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)
    supplies = SurgicalSupply.objects.filter(surgery=surgery).order_by('created_at')

    # Calcular total
    total_cost = sum(supply.total_cost for supply in supplies if supply.total_cost)

    context = {
        'surgery': surgery,
        'supplies': supplies,
        'total_cost': total_cost,
    }

    return render(request, 'surgery/surgical_supply_list.html', context)


# ==================== POST-OPERATIVE NOTE VIEWS ====================

@login_required
@company_required
def postop_note_create(request, surgery_id):
    """Crear nota post-operatoria"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)

    # Verificar si ya existe nota post-operatoria
    if hasattr(surgery, 'postoperative_note'):
        messages.warning(request, 'Esta cirugía ya tiene una nota post-operatoria')
        return redirect('surgery:postop_note_detail', surgery_id=surgery.id)

    if request.method == 'POST':
        try:
            postop_note = PostOperativeNote(
                surgery=surgery,
                company=surgery.company,
                patient_condition=request.POST.get('patient_condition'),
                consciousness_level=request.POST.get('consciousness_level'),
                # Signos vitales post-operatorios
                blood_pressure_systolic=int(request.POST.get('blood_pressure_systolic', 0)),
                blood_pressure_diastolic=int(request.POST.get('blood_pressure_diastolic', 0)),
                heart_rate=int(request.POST.get('heart_rate', 0)),
                respiratory_rate=int(request.POST.get('respiratory_rate', 0)),
                oxygen_saturation=int(request.POST.get('oxygen_saturation', 0)),
                temperature=Decimal(request.POST.get('temperature', 0)),
                # Manejo del dolor
                pain_scale=int(request.POST.get('pain_scale', 0)),
                analgesic_plan=request.POST.get('analgesic_plan', ''),
                # Drenajes y dispositivos
                drains_in_place=request.POST.get('drains_in_place', ''),
                catheters_in_place=request.POST.get('catheters_in_place', ''),
                # Órdenes post-operatorias
                diet_orders=request.POST.get('diet_orders', ''),
                activity_orders=request.POST.get('activity_orders', ''),
                medication_orders=request.POST.get('medication_orders', ''),
                laboratory_orders=request.POST.get('laboratory_orders', ''),
                imaging_orders=request.POST.get('imaging_orders', ''),
                # Seguimiento
                next_evaluation_time=request.POST.get('next_evaluation_time'),
                warnings=request.POST.get('warnings', ''),
                special_care=request.POST.get('special_care', ''),
                observations=request.POST.get('observations', ''),
                created_by=request.user
            )
            postop_note.save()

            messages.success(request, 'Nota post-operatoria creada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al crear nota post-operatoria: {str(e)}')

    context = {
        'surgery': surgery,
    }

    return render(request, 'surgery/postop_note_form.html', context)


@login_required
@company_required
def postop_note_detail(request, surgery_id):
    """Detalle de nota post-operatoria"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)
    postop_note = get_object_or_404(PostOperativeNote, surgery=surgery)

    context = {
        'surgery': surgery,
        'postop_note': postop_note,
    }

    return render(request, 'surgery/postop_note_detail.html', context)


@login_required
@company_required
def postop_note_update(request, surgery_id):
    """Actualizar nota post-operatoria"""
    current_company = request.session.get('active_company')

    if not current_company:
        messages.error(request, 'No hay empresa activa seleccionada')
        return redirect('core:dashboard')

    surgery = get_object_or_404(Surgery, id=surgery_id, company=current_company)
    postop_note = get_object_or_404(PostOperativeNote, surgery=surgery)

    if request.method == 'POST':
        try:
            postop_note.patient_condition = request.POST.get('patient_condition')
            postop_note.consciousness_level = request.POST.get('consciousness_level')
            postop_note.pain_scale = int(request.POST.get('pain_scale', 0))
            postop_note.analgesic_plan = request.POST.get('analgesic_plan', '')
            postop_note.diet_orders = request.POST.get('diet_orders', '')
            postop_note.activity_orders = request.POST.get('activity_orders', '')
            postop_note.medication_orders = request.POST.get('medication_orders', '')
            postop_note.warnings = request.POST.get('warnings', '')
            postop_note.observations = request.POST.get('observations', '')
            postop_note.save()

            messages.success(request, 'Nota post-operatoria actualizada exitosamente')
            return redirect('surgery:surgery_detail', surgery_id=surgery.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar nota post-operatoria: {str(e)}')

    context = {
        'surgery': surgery,
        'postop_note': postop_note,
    }

    return render(request, 'surgery/postop_note_form.html', context)
