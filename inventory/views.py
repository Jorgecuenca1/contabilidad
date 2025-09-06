"""
Vistas para el módulo de inventario.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator

from core.models import Company
from .models_product import Product, ProductCategory, UnitOfMeasure


@login_required
def inventory_dashboard(request):
    """
    Dashboard del módulo de inventario.
    """
    # Estadísticas básicas
    total_products = Product.objects.filter(is_active=True).count()
    total_categories = ProductCategory.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        track_inventory=True,
        is_active=True
    ).count()  # Aquí se implementaría la lógica de stock bajo
    
    # Productos más vendidos (placeholder)
    top_products = Product.objects.filter(is_active=True)[:5]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
def product_list(request):
    """
    Lista de productos.
    """
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    product_type = request.GET.get('type', '')
    
    products = Product.objects.filter(is_active=True)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if product_type:
        products = products.filter(product_type=product_type)
    
    # Paginación
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    categories = ProductCategory.objects.filter(is_active=True)
    product_types = Product.PRODUCT_TYPE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'product_types': product_types,
        'search': search,
        'selected_category': category_id,
        'selected_type': product_type,
    }
    
    return render(request, 'inventory/product_list.html', context)


@login_required
def new_product(request):
    """
    Crear nuevo producto.
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            company_id = request.POST.get('company')
            code = request.POST.get('code')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            product_type = request.POST.get('product_type')
            unit_of_measure_id = request.POST.get('unit_of_measure')
            
            # Validar datos requeridos
            if not all([company_id, code, name, category_id, unit_of_measure_id]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('inventory:new_product')
            
            # Crear producto
            product = Product.objects.create(
                company_id=company_id,
                code=code,
                name=name,
                description=description,
                category_id=category_id,
                product_type=product_type,
                unit_of_measure_id=unit_of_measure_id,
                created_by=request.user
            )
            
            messages.success(request, f'Producto {product.name} creado exitosamente.')
            return redirect('inventory:product_detail', product_id=product.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    
    # Datos para el formulario
    companies = Company.objects.filter(is_active=True)
    categories = ProductCategory.objects.filter(is_active=True)
    units = UnitOfMeasure.objects.filter(is_active=True)
    product_types = Product.PRODUCT_TYPE_CHOICES
    
    context = {
        'companies': companies,
        'categories': categories,
        'units': units,
        'product_types': product_types,
    }
    
    return render(request, 'inventory/new_product.html', context)


@login_required
def product_detail(request, product_id):
    """
    Detalle de producto.
    """
    product = get_object_or_404(Product, id=product_id)
    
    context = {
        'product': product,
    }
    
    return render(request, 'inventory/product_detail.html', context)


@login_required
def edit_product(request, product_id):
    """
    Editar producto.
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos
            product.name = request.POST.get('name', product.name)
            product.description = request.POST.get('description', product.description)
            product.category_id = request.POST.get('category', product.category_id)
            product.product_type = request.POST.get('product_type', product.product_type)
            product.unit_of_measure_id = request.POST.get('unit_of_measure', product.unit_of_measure_id)
            
            product.save()
            
            messages.success(request, f'Producto {product.name} actualizado exitosamente.')
            return redirect('inventory:product_detail', product_id=product.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el producto: {str(e)}')
    
    # Datos para el formulario
    categories = ProductCategory.objects.filter(is_active=True)
    units = UnitOfMeasure.objects.filter(is_active=True)
    product_types = Product.PRODUCT_TYPE_CHOICES
    
    context = {
        'product': product,
        'categories': categories,
        'units': units,
        'product_types': product_types,
    }
    
    return render(request, 'inventory/edit_product.html', context)


@login_required
def stock_movement(request):
    """
    Movimientos de inventario.
    """
    context = {}
    return render(request, 'inventory/stock_movement.html', context)


@login_required
def stock_report(request):
    """
    Reporte de inventario.
    """
    products = Product.objects.filter(is_active=True, track_inventory=True)
    
    context = {
        'products': products,
    }
    
    return render(request, 'inventory/stock_report.html', context)


def get_products_json(request):
    """
    API para obtener productos en formato JSON.
    """
    search = request.GET.get('search', '')
    
    products = Product.objects.filter(is_active=True)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    products_data = []
    for product in products[:20]:  # Limitar a 20 resultados
        products_data.append({
            'id': str(product.id),
            'code': product.code,
            'name': product.name,
            'price': float(product.sale_price),
            'unit': product.unit_of_measure.symbol,
        })
    
    return JsonResponse({'products': products_data})
