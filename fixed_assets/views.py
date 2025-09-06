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
from accounting.models_accounts import CostCenter
from .models_asset import FixedAsset, AssetCategory


@login_required
def fixed_assets_dashboard(request):
    """
    Dashboard del módulo de activos fijos.
    """
    # Estadísticas básicas
    total_assets = FixedAsset.objects.filter(status='active').count()
    total_categories = AssetCategory.objects.filter(is_active=True).count()
    
    # Valores totales
    total_acquisition_cost = FixedAsset.objects.filter(status='active').aggregate(
        total=Sum('acquisition_cost')
    )['total'] or 0
    
    total_accumulated_depreciation = FixedAsset.objects.filter(status='active').aggregate(
        total=Sum('accumulated_depreciation')
    )['total'] or 0
    
    total_net_value = total_acquisition_cost - total_accumulated_depreciation
    
    # Activos próximos a vencer garantía
    warranty_expiring = FixedAsset.objects.filter(
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
def asset_list(request):
    """
    Lista de activos fijos.
    """
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    assets = FixedAsset.objects.all()
    
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
def new_asset(request):
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
def depreciation_report(request):
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
def calculate_depreciation(request):
    """
    Calcular depreciación mensual.
    """
    if request.method == 'POST':
        try:
            # Obtener fecha de cálculo
            calculation_date = request.POST.get('calculation_date')
            if not calculation_date:
                calculation_date = timezone.now().date()
            else:
                calculation_date = datetime.strptime(calculation_date, '%Y-%m-%d').date()
            
            # Obtener activos activos
            assets = FixedAsset.objects.filter(status='active')
            
            calculated_count = 0
            for asset in assets:
                # Calcular depreciación mensual
                monthly_depreciation = asset.calculate_monthly_depreciation()
                
                if monthly_depreciation > 0:
                    # Actualizar depreciación acumulada
                    asset.accumulated_depreciation += monthly_depreciation
                    asset.net_book_value = asset.acquisition_cost - asset.accumulated_depreciation
                    asset.save()
                    calculated_count += 1
            
            messages.success(request, f'Depreciación calculada para {calculated_count} activos.')
            
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
