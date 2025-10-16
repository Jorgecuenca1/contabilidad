"""
Vistas del módulo de Diagnósticos CIE-10
Sistema completo de gestión de catálogo de diagnósticos médicos
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db import transaction
import csv
import io
import openpyxl
from datetime import datetime, timedelta

from .models import (
    CIE10Diagnosis, CIE10Version, CIE10Chapter, CIE10Group,
    FavoriteDiagnosis, DiagnosisImportLog
)
from core.models import Company
from core.decorators import company_required


@login_required
@company_required
def diagnostics_dashboard(request):
    """
    Dashboard principal del módulo de diagnósticos CIE-10
    Muestra estadísticas y accesos rápidos
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    # Obtener versión actual
    current_version = CIE10Version.objects.filter(is_current=True).first()

    context = {
        'current_version': current_version,
        'total_diagnoses': 0,
        'total_chapters': 0,
        'total_groups': 0,
        'active_diagnoses': 0,
        'high_cost_diagnoses': 0,
        'mandatory_notification_diagnoses': 0,
        'rare_diseases': 0,
        'most_used_diagnoses': [],
        'recent_searches': [],
        'user_favorites': [],
        'recent_imports': [],
    }

    if current_version:
        # Estadísticas generales
        context['total_diagnoses'] = CIE10Diagnosis.objects.filter(version=current_version).count()
        context['total_chapters'] = CIE10Chapter.objects.filter(version=current_version).count()
        context['total_groups'] = CIE10Group.objects.filter(version=current_version).count()
        context['active_diagnoses'] = CIE10Diagnosis.objects.filter(
            version=current_version,
            is_active=True
        ).count()

        # Diagnósticos especiales (Colombia)
        context['high_cost_diagnoses'] = CIE10Diagnosis.objects.filter(
            version=current_version,
            high_cost=True,
            is_active=True
        ).count()

        context['mandatory_notification_diagnoses'] = CIE10Diagnosis.objects.filter(
            version=current_version,
            mandatory_notification=True,
            is_active=True
        ).count()

        context['rare_diseases'] = CIE10Diagnosis.objects.filter(
            version=current_version,
            rare_disease=True,
            is_active=True
        ).count()

        # Diagnósticos más usados (top 10)
        context['most_used_diagnoses'] = CIE10Diagnosis.objects.filter(
            version=current_version,
            is_active=True,
            use_count__gt=0
        ).order_by('-use_count')[:10]

        # Favoritos del usuario
        context['user_favorites'] = FavoriteDiagnosis.objects.filter(
            company=current_company,
            user=request.user
        ).select_related('diagnosis')[:10]

    # Importaciones recientes
    context['recent_imports'] = DiagnosisImportLog.objects.filter(
        company=current_company
    ).order_by('-started_at')[:5]

    return render(request, 'diagnostics/dashboard.html', context)


@login_required
@company_required
def diagnosis_list(request):
    """
    Lista completa de diagnósticos CIE-10 con búsqueda y filtros avanzados
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    # Obtener versión actual
    current_version = CIE10Version.objects.filter(is_current=True).first()

    if not current_version:
        messages.warning(request, 'No hay una versión de CIE-10 configurada')
        return render(request, 'diagnostics/diagnosis_list.html', {'diagnoses': []})

    # Base queryset
    diagnoses = CIE10Diagnosis.objects.filter(version=current_version)

    # Filtros
    search = request.GET.get('search', '')
    chapter_id = request.GET.get('chapter', '')
    gender_filter = request.GET.get('gender', '')
    high_cost = request.GET.get('high_cost', '')
    mandatory_notification = request.GET.get('mandatory_notification', '')
    rare_disease = request.GET.get('rare_disease', '')
    show_inactive = request.GET.get('show_inactive', '')

    # Aplicar filtros
    if search:
        diagnoses = diagnoses.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(synonyms__icontains=search)
        )

    if chapter_id:
        diagnoses = diagnoses.filter(chapter_id=chapter_id)

    if gender_filter:
        diagnoses = diagnoses.filter(applicable_gender=gender_filter)

    if high_cost == 'true':
        diagnoses = diagnoses.filter(high_cost=True)

    if mandatory_notification == 'true':
        diagnoses = diagnoses.filter(mandatory_notification=True)

    if rare_disease == 'true':
        diagnoses = diagnoses.filter(rare_disease=True)

    if not show_inactive:
        diagnoses = diagnoses.filter(is_active=True)

    # Ordenamiento
    sort_by = request.GET.get('sort', 'code')
    if sort_by == 'code':
        diagnoses = diagnoses.order_by('code')
    elif sort_by == 'name':
        diagnoses = diagnoses.order_by('name')
    elif sort_by == 'most_used':
        diagnoses = diagnoses.order_by('-use_count')
    elif sort_by == 'recent':
        diagnoses = diagnoses.order_by('-updated_at')

    # Paginación
    paginator = Paginator(diagnoses, 50)  # 50 diagnósticos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Capítulos para el filtro
    chapters = CIE10Chapter.objects.filter(version=current_version).order_by('order')

    context = {
        'page_obj': page_obj,
        'current_version': current_version,
        'chapters': chapters,
        'search': search,
        'chapter_filter': chapter_id,
        'gender_filter': gender_filter,
        'high_cost_filter': high_cost,
        'mandatory_notification_filter': mandatory_notification,
        'rare_disease_filter': rare_disease,
        'show_inactive': show_inactive,
        'sort_by': sort_by,
        'total_results': paginator.count,
    }

    return render(request, 'diagnostics/diagnosis_list.html', context)


@login_required
@company_required
def diagnosis_detail(request, diagnosis_id):
    """
    Detalle completo de un diagnóstico CIE-10
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    diagnosis = get_object_or_404(CIE10Diagnosis, id=diagnosis_id)

    # Verificar si es favorito del usuario
    is_favorite = FavoriteDiagnosis.objects.filter(
        company=current_company,
        user=request.user,
        diagnosis=diagnosis
    ).exists()

    # Obtener diagnósticos relacionados (hijos)
    children_diagnoses = CIE10Diagnosis.objects.filter(
        parent=diagnosis,
        is_active=True
    ).order_by('code')

    # Diagnósticos del mismo grupo
    related_diagnoses = []
    if diagnosis.group:
        related_diagnoses = CIE10Diagnosis.objects.filter(
            group=diagnosis.group,
            is_active=True
        ).exclude(id=diagnosis.id).order_by('code')[:10]

    context = {
        'diagnosis': diagnosis,
        'is_favorite': is_favorite,
        'children_diagnoses': children_diagnoses,
        'related_diagnoses': related_diagnoses,
    }

    return render(request, 'diagnostics/diagnosis_detail.html', context)


@login_required
@company_required
def diagnosis_search_api(request):
    """
    API de búsqueda de diagnósticos para autocompletado (AJAX)
    Usado en selects de otros módulos
    """
    search = request.GET.get('q', '')

    if len(search) < 2:
        return JsonResponse({'results': []})

    current_version = CIE10Version.objects.filter(is_current=True).first()
    if not current_version:
        return JsonResponse({'results': []})

    diagnoses = CIE10Diagnosis.objects.filter(
        version=current_version,
        is_active=True
    ).filter(
        Q(code__icontains=search) |
        Q(name__icontains=search) |
        Q(synonyms__icontains=search)
    )[:20]

    results = [{
        'id': str(diagnosis.id),
        'text': f"{diagnosis.code} - {diagnosis.name}",
        'code': diagnosis.code,
        'name': diagnosis.name,
    } for diagnosis in diagnoses]

    return JsonResponse({'results': results})


@login_required
@company_required
@require_http_methods(["POST"])
def diagnosis_toggle_favorite(request, diagnosis_id):
    """
    Agregar o quitar diagnóstico de favoritos
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    diagnosis = get_object_or_404(CIE10Diagnosis, id=diagnosis_id)

    favorite = FavoriteDiagnosis.objects.filter(
        company=current_company,
        user=request.user,
        diagnosis=diagnosis
    ).first()

    if favorite:
        favorite.delete()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'message': 'Diagnóstico eliminado de favoritos'
        })
    else:
        FavoriteDiagnosis.objects.create(
            company=current_company,
            user=request.user,
            diagnosis=diagnosis
        )
        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': 'Diagnóstico agregado a favoritos'
        })


@login_required
@company_required
def favorites_list(request):
    """
    Lista de diagnósticos favoritos del usuario
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    favorites = FavoriteDiagnosis.objects.filter(
        company=current_company,
        user=request.user
    ).select_related('diagnosis').order_by('order', 'diagnosis__code')

    # Agrupar por especialidad si existe
    specialties = {}
    for fav in favorites:
        specialty = fav.specialty if fav.specialty else 'General'
        if specialty not in specialties:
            specialties[specialty] = []
        specialties[specialty].append(fav)

    context = {
        'favorites': favorites,
        'specialties': specialties,
    }

    return render(request, 'diagnostics/favorites_list.html', context)


# ============================================================================
# IMPORTADOR DE DIAGNÓSTICOS CIE-10
# ============================================================================

@login_required
@company_required
def import_form(request):
    """
    Formulario para importar catálogo CIE-10 desde CSV o Excel
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    versions = CIE10Version.objects.filter(is_active=True).order_by('-release_date')

    context = {
        'versions': versions,
    }

    return render(request, 'diagnostics/import_form.html', context)


@login_required
@company_required
@require_http_methods(["POST"])
def import_process(request):
    """
    Procesar importación de diagnósticos desde archivo
    Formatos soportados: CSV, Excel (XLSX)
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    # Validar archivo
    if 'file' not in request.FILES:
        messages.error(request, 'No se ha seleccionado ningún archivo')
        return redirect('diagnostics:import_form')

    uploaded_file = request.FILES['file']
    version_id = request.POST.get('version_id')

    # Validar versión
    if not version_id:
        messages.error(request, 'Debe seleccionar una versión de CIE-10')
        return redirect('diagnostics:import_form')

    version = get_object_or_404(CIE10Version, id=version_id)

    # Determinar tipo de archivo
    file_name = uploaded_file.name
    file_type = 'csv' if file_name.endswith('.csv') else 'xlsx'

    # Crear log de importación
    import_log = DiagnosisImportLog.objects.create(
        company=current_company,
        version=version,
        file_name=file_name,
        file_type=file_type,
        file_path=uploaded_file,
        status='processing',
        imported_by=request.user
    )

    try:
        if file_type == 'csv':
            result = process_csv_import(uploaded_file, version, import_log)
        else:
            result = process_excel_import(uploaded_file, version, import_log)

        # Actualizar log
        import_log.total_records = result['total']
        import_log.successful_imports = result['success']
        import_log.failed_imports = result['failed']
        import_log.skipped_imports = result['skipped']
        import_log.updated_records = result['updated']
        import_log.mark_completed()

        success_rate = import_log.calculate_success_rate()

        messages.success(
            request,
            f'Importación completada: {result["success"]} exitosos, '
            f'{result["failed"]} fallos, {result["skipped"]} omitidos. '
            f'Tasa de éxito: {success_rate}%'
        )

    except Exception as e:
        import_log.mark_failed(str(e))
        messages.error(request, f'Error en la importación: {str(e)}')

    return redirect('diagnostics:import_log_detail', log_id=import_log.id)


def process_csv_import(uploaded_file, version, import_log):
    """
    Procesar importación desde archivo CSV
    Formato esperado: code,name,chapter_code,group_code,gender,notes,...
    """
    result = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'updated': 0,
    }

    # Leer CSV
    file_data = uploaded_file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_data))

    for row in csv_reader:
        result['total'] += 1

        try:
            code = row.get('code', '').strip().upper()
            name = row.get('name', '').strip()

            if not code or not name:
                result['skipped'] += 1
                continue

            # Buscar o crear diagnóstico
            diagnosis, created = CIE10Diagnosis.objects.get_or_create(
                version=version,
                code=code,
                defaults={
                    'name': name,
                    'applicable_gender': row.get('gender', 'A'),
                    'notes': row.get('notes', ''),
                    'is_category': len(code.replace('.', '')) == 3,
                    'is_subcategory': len(code.replace('.', '')) > 3,
                    'level': len(code.replace('.', '')),
                }
            )

            if created:
                result['success'] += 1
            else:
                # Actualizar si ya existe
                diagnosis.name = name
                diagnosis.save()
                result['updated'] += 1

        except Exception as e:
            result['failed'] += 1
            import_log.error_log += f"Fila {result['total']}: {str(e)}\n"

    import_log.save()
    return result


def process_excel_import(uploaded_file, version, import_log):
    """
    Procesar importación desde archivo Excel
    """
    result = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'updated': 0,
    }

    # Leer Excel
    workbook = openpyxl.load_workbook(uploaded_file)
    sheet = workbook.active

    # Asumir primera fila como encabezados
    headers = [cell.value for cell in sheet[1]]

    for row in sheet.iter_rows(min_row=2, values_only=True):
        result['total'] += 1

        try:
            # Crear diccionario de la fila
            row_dict = dict(zip(headers, row))

            code = str(row_dict.get('code', '')).strip().upper()
            name = str(row_dict.get('name', '')).strip()

            if not code or not name:
                result['skipped'] += 1
                continue

            # Buscar o crear diagnóstico
            diagnosis, created = CIE10Diagnosis.objects.get_or_create(
                version=version,
                code=code,
                defaults={
                    'name': name,
                    'applicable_gender': row_dict.get('gender', 'A'),
                    'notes': row_dict.get('notes', ''),
                    'is_category': len(code.replace('.', '')) == 3,
                    'is_subcategory': len(code.replace('.', '')) > 3,
                    'level': len(code.replace('.', '')),
                }
            )

            if created:
                result['success'] += 1
            else:
                diagnosis.name = name
                diagnosis.save()
                result['updated'] += 1

        except Exception as e:
            result['failed'] += 1
            import_log.error_log += f"Fila {result['total']}: {str(e)}\n"

    import_log.save()
    return result


@login_required
@company_required
def import_logs_list(request):
    """
    Lista de logs de importaciones
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    logs = DiagnosisImportLog.objects.filter(
        company=current_company
    ).order_by('-started_at')

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'diagnostics/import_logs_list.html', context)


@login_required
@company_required
def import_log_detail(request, log_id):
    """
    Detalle de un log de importación
    """
    current_company = Company.objects.get(id=request.session.get('active_company'))

    log = get_object_or_404(
        DiagnosisImportLog,
        id=log_id,
        company=current_company
    )

    context = {
        'log': log,
        'success_rate': log.calculate_success_rate(),
    }

    return render(request, 'diagnostics/import_log_detail.html', context)


# ============================================================================
# EXPORTACIÓN
# ============================================================================

@login_required
@company_required
def export_diagnoses_csv(request):
    """
    Exportar diagnósticos a CSV
    """
    current_version = CIE10Version.objects.filter(is_current=True).first()

    if not current_version:
        messages.error(request, 'No hay versión activa de CIE-10')
        return redirect('diagnostics:diagnosis_list')

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cie10_{current_version.version_code}_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Código', 'Nombre', 'Capítulo', 'Sexo', 'Alto Costo',
        'Notificación Obligatoria', 'Enfermedad Rara', 'Activo'
    ])

    diagnoses = CIE10Diagnosis.objects.filter(
        version=current_version
    ).select_related('chapter').order_by('code')

    for diagnosis in diagnoses:
        writer.writerow([
            diagnosis.code,
            diagnosis.name,
            diagnosis.chapter.name if diagnosis.chapter else '',
            diagnosis.get_applicable_gender_display(),
            'Sí' if diagnosis.high_cost else 'No',
            'Sí' if diagnosis.mandatory_notification else 'No',
            'Sí' if diagnosis.rare_disease else 'No',
            'Sí' if diagnosis.is_active else 'No',
        ])

    return response


# ============================================================================
# GESTIÓN DE VERSIONES CIE-10
# ============================================================================

@login_required
@company_required
def versions_list(request):
    """
    Lista de versiones CIE-10 disponibles
    """
    versions = CIE10Version.objects.all().order_by('-release_date')

    context = {
        'versions': versions,
    }

    return render(request, 'diagnostics/versions_list.html', context)


@login_required
@company_required
def version_detail(request, version_id):
    """
    Detalle de una versión CIE-10
    """
    version = get_object_or_404(CIE10Version, id=version_id)

    # Estadísticas de la versión
    total_diagnoses = CIE10Diagnosis.objects.filter(version=version).count()
    total_chapters = CIE10Chapter.objects.filter(version=version).count()
    total_groups = CIE10Group.objects.filter(version=version).count()

    context = {
        'version': version,
        'total_diagnoses': total_diagnoses,
        'total_chapters': total_chapters,
        'total_groups': total_groups,
    }

    return render(request, 'diagnostics/version_detail.html', context)
