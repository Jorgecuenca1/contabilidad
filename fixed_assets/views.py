"""
Vistas para el módulo de activos fijos.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date

from core.models import Company, Currency
from core.utils import get_current_company, require_company_access

from accounting.models_accounts import CostCenter
from .models_asset import FixedAsset, AssetCategory, DepreciationEntry
from .services import DepreciationService


@login_required
@require_company_access
def fixed_assets_dashboard(request):
    current_company = request.current_company

    """
    Dashboard del módulo de activos fijos.
    """
    # Get user's company context or default company
    company = getattr(request.user, 'company', None)
    if not company:
        company = Company.objects.filter(is_active=True).first()
    
    if not company:
        # Handle case when no company exists
        context = {
            'total_assets': 0,
            'total_categories': 0,
            'total_acquisition_cost': 0,
            'total_accumulated_depreciation': 0,
            'total_net_value': 0,
            'warranty_expiring': 0,
            'no_company': True,
        }
        return render(request, 'fixed_assets/dashboard.html', context)
    
    # Estadísticas básicas filtradas por compañía
    total_assets = FixedAsset.objects.filter(company=company, status='active').count()
    total_categories = AssetCategory.objects.filter(company=company, is_active=True).count()
    
    # Valores totales
    total_acquisition_cost = FixedAsset.objects.filter(company=company, status='active').aggregate(
        total=Sum('acquisition_cost')
    )['total'] or 0
    
    total_accumulated_depreciation = FixedAsset.objects.filter(company=company, status='active').aggregate(
        total=Sum('accumulated_depreciation')
    )['total'] or 0
    
    total_net_value = total_acquisition_cost - total_accumulated_depreciation
    
    # Activos próximos a vencer garantía
    warranty_expiring = FixedAsset.objects.filter(
        company=company,
        status='active',
        warranty_expiration__lte=timezone.now().date() + timezone.timedelta(days=30),
        warranty_expiration__gte=timezone.now().date()
    ).count()
    
    context = {
        'total_assets': total_assets,
        'total_categories': total_categories,
        'total_acquisition_cost': total_acquisition_cost,
        'total_accumulated_depreciation': total_accumulated_depreciation,
        'total_net_value': total_net_value,
        'warranty_expiring': warranty_expiring,
    }
    
    return render(request, 'fixed_assets/dashboard.html', context)


@login_required
@require_company_access
def asset_list(request):
    current_company = request.current_company

    """
    Lista de activos fijos.
    """
    # Get user's company context
    company = getattr(request.user, 'company', None)
    if not company:
        company = Company.objects.filter(is_active=True).first()
    
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    assets = FixedAsset.objects.filter(company=company)
    
    if search:
        assets = assets.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(serial_number__icontains=search)
        )
    
    if category_id:
        assets = assets.filter(category_id=category_id)
    
    if status:
        assets = assets.filter(status=status)
    
    # Paginación
    paginator = Paginator(assets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    categories = AssetCategory.objects.filter(is_active=True)
    status_choices = FixedAsset.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'status_choices': status_choices,
        'search': search,
        'selected_category': category_id,
        'selected_status': status,
    }
    
    return render(request, 'fixed_assets/asset_list.html', context)


@login_required
@require_company_access
def new_asset(request):
    current_company = request.current_company

    """
    Crear nuevo activo fijo.
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            company_id = request.POST.get('company')
            code = request.POST.get('code')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            acquisition_date = request.POST.get('acquisition_date')
            acquisition_cost = request.POST.get('acquisition_cost')
            currency_id = request.POST.get('currency')
            useful_life_years = request.POST.get('useful_life_years')
            
            # Validar datos requeridos
            if not all([company_id, code, name, category_id, acquisition_date, acquisition_cost, currency_id, useful_life_years]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('fixed_assets:new_asset')
            
            # Crear activo
            asset = FixedAsset.objects.create(
                company_id=company_id,
                code=code,
                name=name,
                description=description,
                category_id=category_id,
                acquisition_date=datetime.strptime(acquisition_date, '%Y-%m-%d').date(),
                start_depreciation_date=datetime.strptime(acquisition_date, '%Y-%m-%d').date(),
                acquisition_cost=float(acquisition_cost),
                currency_id=currency_id,
                useful_life_years=int(useful_life_years),
                created_by=request.user
            )
            
            messages.success(request, f'Activo {asset.name} creado exitosamente.')
            return redirect('fixed_assets:asset_detail', asset_id=asset.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear el activo: {str(e)}')
    
    # Datos para el formulario
    companies = Company.objects.filter(is_active=True)
    categories = AssetCategory.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    
    context = {
        'companies': companies,
        'categories': categories,
        'currencies': currencies,
        'cost_centers': cost_centers,
    }
    
    return render(request, 'fixed_assets/new_asset.html', context)


@login_required
def asset_detail(request, asset_id):
    """
    Detalle de activo fijo.
    """
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    # Calcular depreciación mensual
    monthly_depreciation = asset.calculate_monthly_depreciation()
    
    context = {
        'asset': asset,
        'monthly_depreciation': monthly_depreciation,
    }
    
    return render(request, 'fixed_assets/asset_detail.html', context)


@login_required
def edit_asset(request, asset_id):
    """
    Editar activo fijo.
    """
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos
            asset.name = request.POST.get('name', asset.name)
            asset.description = request.POST.get('description', asset.description)
            asset.category_id = request.POST.get('category', asset.category_id)
            asset.location = request.POST.get('location', asset.location)
            asset.status = request.POST.get('status', asset.status)
            
            asset.save()
            
            messages.success(request, f'Activo {asset.name} actualizado exitosamente.')
            return redirect('fixed_assets:asset_detail', asset_id=asset.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el activo: {str(e)}')
    
    # Datos para el formulario
    categories = AssetCategory.objects.filter(is_active=True)
    status_choices = FixedAsset.STATUS_CHOICES
    
    context = {
        'asset': asset,
        'categories': categories,
        'status_choices': status_choices,
    }
    
    return render(request, 'fixed_assets/edit_asset.html', context)


@login_required
@require_company_access
def depreciation_report(request):
    current_company = request.current_company

    """
    Reporte de depreciación.
    """
    assets = FixedAsset.objects.filter(status='active')
    
    # Calcular totales
    total_acquisition = assets.aggregate(total=Sum('acquisition_cost'))['total'] or 0
    total_depreciation = assets.aggregate(total=Sum('accumulated_depreciation'))['total'] or 0
    total_net_value = total_acquisition - total_depreciation
    
    context = {
        'assets': assets,
        'total_acquisition': total_acquisition,
        'total_depreciation': total_depreciation,
        'total_net_value': total_net_value,
    }
    
    return render(request, 'fixed_assets/depreciation_report.html', context)


@login_required
@require_company_access
def calculate_depreciation(request):
    current_company = request.current_company

    """
    Calcular depreciación mensual usando el servicio mejorado.
    """
    if request.method == 'POST':
        try:
            # Get user's company context
            company = getattr(request.user, 'company', None)
            if not company:
                company = Company.objects.filter(is_active=True).first()
            
            if not company:
                messages.error(request, 'No se pudo determinar la empresa.')
                return redirect('fixed_assets:depreciation_report')
            
            # Obtener fecha de cálculo
            calculation_date = request.POST.get('calculation_date')
            create_entries = request.POST.get('create_journal_entries', 'true').lower() == 'true'
            
            if not calculation_date:
                calculation_date = timezone.now().date()
            else:
                calculation_date = datetime.strptime(calculation_date, '%Y-%m-%d').date()
            
            # Usar el servicio de depreciación
            depreciation_service = DepreciationService(company)
            
            processed_entries = depreciation_service.process_period_depreciation(
                year=calculation_date.year,
                month=calculation_date.month,
                user=request.user,
                create_journal_entries=create_entries
            )
            
            if processed_entries:
                total_depreciation = sum(entry.depreciation_amount for entry in processed_entries)
                messages.success(
                    request, 
                    f'Depreciación procesada: {len(processed_entries)} activos, '
                    f'Total: ${total_depreciation:,.2f}'
                )
                if create_entries:
                    journal_entries_created = sum(1 for entry in processed_entries if entry.journal_entry)
                    messages.info(request, f'Se crearon {journal_entries_created} asientos contables.')
            else:
                messages.warning(request, 'No hay activos para depreciar en este período.')
            
        except Exception as e:
            messages.error(request, f'Error al calcular depreciación: {str(e)}')
    
    return redirect('fixed_assets:depreciation_report')


def get_assets_json(request):
    """
    API para obtener activos en formato JSON.
    """
    search = request.GET.get('search', '')
    
    assets = FixedAsset.objects.filter(status='active')
    
    if search:
        assets = assets.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    assets_data = []
    for asset in assets[:20]:  # Limitar a 20 resultados
        assets_data.append({
            'id': str(asset.id),
            'code': asset.code,
            'name': asset.name,
            'category': asset.category.name,
            'net_value': float(asset.net_book_value),
        })
    
    return JsonResponse({'assets': assets_data})


@login_required
def depreciation_schedule(request, asset_id):
    """
    Cronograma de depreciación para un activo.
    """
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    # Get user's company context
    company = getattr(request.user, 'company', None)
    if not company:
        company = Company.objects.filter(is_active=True).first()
    
    depreciation_service = DepreciationService(company)
    schedule = depreciation_service.get_depreciation_schedule(asset)
    compliance_issues = depreciation_service.validate_depreciation_compliance(asset)
    
    context = {
        'asset': asset,
        'schedule': schedule,
        'compliance_issues': compliance_issues,
    }
    
    return render(request, 'fixed_assets/depreciation_schedule.html', context)


@login_required
@require_company_access
def depreciation_entries(request):
    current_company = request.current_company

    """
    Lista de registros de depreciación.
    """
    # Get user's company context
    company = getattr(request.user, 'company', None)
    if not company:
        company = Company.objects.filter(is_active=True).first()
    
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', '')
    
    entries = DepreciationEntry.objects.filter(company=company)
    
    if year:
        entries = entries.filter(period_year=int(year))
    if month:
        entries = entries.filter(period_month=int(month))
    
    # Paginación
    paginator = Paginator(entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'selected_year': year,
        'selected_month': month,
        'years': range(2020, timezone.now().year + 2),
        'months': [(i, datetime(2023, i, 1).strftime('%B')) for i in range(1, 13)],
    }
    
    return render(request, 'fixed_assets/depreciation_entries.html', context)


@login_required
@require_company_access
def asset_categories(request):
    current_company = request.current_company

    """
    Lista de categorías de activos.
    """
    # Get user's company context
    company = getattr(request.user, 'company', None)
    if not company:
        company = Company.objects.filter(is_active=True).first()
    
    categories = AssetCategory.objects.filter(company=company, is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'fixed_assets/categories.html', context)


@login_required
@require_company_access
def new_category(request):
    current_company = request.current_company

    """
    Crear nueva categoría de activo.
    """
    if request.method == 'POST':
        try:
            # Get user's company context
            company = getattr(request.user, 'company', None)
            if not company:
                company = Company.objects.filter(is_active=True).first()
            
            code = request.POST.get('code')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            useful_life_years = request.POST.get('useful_life_years')
            depreciation_method = request.POST.get('depreciation_method')
            asset_account_id = request.POST.get('asset_account')
            depreciation_account_id = request.POST.get('depreciation_account')
            expense_account_id = request.POST.get('expense_account')
            
            # Validar datos requeridos
            if not all([code, name, useful_life_years, asset_account_id, depreciation_account_id, expense_account_id]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('fixed_assets:new_category')
            
            # Crear categoría
            category = AssetCategory.objects.create(
                company=company,
                code=code,
                name=name,
                description=description,
                useful_life_years=int(useful_life_years),
                depreciation_method=depreciation_method,
                asset_account_id=asset_account_id,
                depreciation_account_id=depreciation_account_id,
                expense_account_id=expense_account_id,
                created_by=request.user
            )
            
            messages.success(request, f'Categoría {category.name} creada exitosamente.')
            return redirect('fixed_assets:asset_categories')
            
        except Exception as e:
            messages.error(request, f'Error al crear la categoría: {str(e)}')
    
    # Get accounts for form
    from accounting.models_accounts import Account
    asset_accounts = Account.objects.filter(
        account_type='asset',
        control_type='fixed_assets',
        is_active=True
    )
    
    context = {
        'asset_accounts': asset_accounts,
    }
    
    return render(request, 'fixed_assets/new_category.html', context)
