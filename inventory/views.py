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
from core.utils import get_current_company, require_company_access

from .models_product import Product, ProductCategory, UnitOfMeasure
from .models import Warehouse, StockMovement, ProductStock
from accounting.models_accounts import Account
from accounting.models_journal import JournalEntry, JournalEntryLine
from accounting.models_journal import JournalType
from decimal import Decimal


@login_required
@require_company_access
def inventory_dashboard(request):
    current_company = request.current_company

    """
    Dashboard del módulo de inventario.
    """
    # Obtener la empresa del usuario (para multi-tenancy)
    user_company = request.user.company if hasattr(request.user, 'company') else None
    
    # Base queryset con filtro de empresa
    base_filter = {'company': user_company} if user_company else {}
    
    # Estadísticas básicas
    total_products = Product.objects.filter(is_active=True, **base_filter).count()
    total_categories = ProductCategory.objects.filter(is_active=True, **base_filter).count()
    
    # Productos con stock bajo
    low_stock_products = 0
    products_with_inventory = Product.objects.filter(
        track_inventory=True,
        is_active=True,
        **base_filter
    )
    
    for product in products_with_inventory:
        if product.is_low_stock():
            low_stock_products += 1
    
    # Productos más importantes (por valor de stock)
    top_products = Product.objects.filter(is_active=True, **base_filter)[:5]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
@require_company_access
def product_list(request):
    current_company = request.current_company

    """
    Lista de productos.
    """
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    product_type = request.GET.get('type', '')
    
    # Obtener la empresa del usuario
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    products = Product.objects.filter(is_active=True, **base_filter)
    
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
    categories = ProductCategory.objects.filter(is_active=True, **base_filter)
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
@require_company_access
def new_product(request):
    current_company = request.current_company

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
            
            # Buscar cuentas contables por defecto o crear una básica
            company = Company.objects.get(id=company_id)
            
            # Intentar obtener cuentas de la categoría, sino usar cuentas por defecto
            category = ProductCategory.objects.get(id=category_id)
            
            inventory_account = None
            cost_account = None
            revenue_account = None
            
            if category.inventory_account:
                inventory_account = category.inventory_account
            if category.cost_account:
                cost_account = category.cost_account
            if category.revenue_account:
                revenue_account = category.revenue_account
            
            # Si no hay cuentas en la categoría, buscar cuentas genéricas
            if not inventory_account:
                inventory_account = Account.objects.filter(
                    company=company, 
                    is_active=True,
                    account_type='asset'
                ).first()
            
            if not cost_account:
                cost_account = Account.objects.filter(
                    company=company, 
                    is_active=True,
                    account_type='expense'
                ).first()
            
            if not revenue_account:
                revenue_account = Account.objects.filter(
                    company=company, 
                    is_active=True,
                    account_type='revenue'
                ).first()
            
            # Si aún no hay cuentas, mostrar error
            if not all([inventory_account, cost_account, revenue_account]):
                messages.error(request, 
                    'No se encontraron cuentas contables necesarias. '
                    'Configure las cuentas de inventario, costo y venta en el plan contable.'
                )
                return redirect('inventory:new_product')
            
            # Crear producto
            product = Product.objects.create(
                company=company,
                code=code,
                name=name,
                description=description,
                category=category,
                product_type=product_type,
                unit_of_measure_id=unit_of_measure_id,
                inventory_account=inventory_account,
                cost_account=cost_account,
                revenue_account=revenue_account,
                created_by=request.user
            )
            
            messages.success(request, f'Producto {product.name} creado exitosamente.')
            return redirect('inventory:product_detail', product_id=product.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    
    # Datos para el formulario
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    companies = Company.objects.filter(is_active=True)
    categories = ProductCategory.objects.filter(is_active=True, **base_filter)
    units = UnitOfMeasure.objects.filter(is_active=True, **base_filter)
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
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    categories = ProductCategory.objects.filter(is_active=True, **base_filter)
    units = UnitOfMeasure.objects.filter(is_active=True, **base_filter)
    product_types = Product.PRODUCT_TYPE_CHOICES
    
    context = {
        'product': product,
        'categories': categories,
        'units': units,
        'product_types': product_types,
    }
    
    return render(request, 'inventory/edit_product.html', context)


@login_required
@require_company_access
def stock_movement(request):
    current_company = request.current_company

    """
    Movimientos de inventario.
    """
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            product_id = request.POST.get('product')
            warehouse_id = request.POST.get('warehouse')
            movement_type = request.POST.get('movement_type')
            movement_reason = request.POST.get('movement_reason')
            quantity = float(request.POST.get('quantity', 0))
            unit_cost = float(request.POST.get('unit_cost', 0))
            reference = request.POST.get('reference', '')
            notes = request.POST.get('notes', '')
            
            # Validar datos requeridos
            if not all([product_id, warehouse_id, movement_type, movement_reason]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('inventory:stock_movement')
            
            if quantity <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero.')
                return redirect('inventory:stock_movement')
            
            # Obtener objetos
            product = Product.objects.get(id=product_id, **base_filter)
            warehouse = Warehouse.objects.get(id=warehouse_id, **base_filter)
            
            # Para salidas, verificar stock disponible
            if movement_type in ['exit', 'transfer'] and product.track_inventory:
                current_stock = product.get_current_stock(warehouse)
                if quantity > current_stock:
                    messages.error(request, f'Stock insuficiente. Stock actual: {current_stock}')
                    return redirect('inventory:stock_movement')
            
            # Crear movimiento
            movement = StockMovement.objects.create(
                company=user_company,
                product=product,
                warehouse=warehouse,
                movement_type=movement_type,
                movement_reason=movement_reason,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=reference,
                notes=notes,
                created_by=request.user
            )
            
            # Actualizar stock
            update_product_stock(movement)
            
            messages.success(request, 'Movimiento de inventario registrado exitosamente.')
            return redirect('inventory:stock_movement')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el movimiento: {str(e)}')
    
    # Obtener movimientos recientes
    recent_movements = StockMovement.objects.filter(**base_filter).order_by('-created_at')[:10]
    
    # Datos para formularios
    products = Product.objects.filter(is_active=True, track_inventory=True, **base_filter)
    warehouses = Warehouse.objects.filter(is_active=True, **base_filter)
    movement_types = StockMovement.MOVEMENT_TYPE_CHOICES
    movement_reasons = StockMovement.MOVEMENT_REASON_CHOICES
    
    context = {
        'recent_movements': recent_movements,
        'products': products,
        'warehouses': warehouses,
        'movement_types': movement_types,
        'movement_reasons': movement_reasons,
    }
    
    return render(request, 'inventory/stock_movement.html', context)


def update_product_stock(movement):
    """
    Actualiza el stock de un producto basado en un movimiento.
    """
    product = movement.product
    warehouse = movement.warehouse
    
    if not product.track_inventory:
        return
    
    # Obtener o crear registro de stock
    stock, created = ProductStock.objects.get_or_create(
        company=movement.company,
        product=product,
        warehouse=warehouse,
        defaults={
            'quantity_on_hand': 0,
            'quantity_reserved': 0,
            'quantity_available': 0,
            'average_cost': product.average_cost,
            'last_cost': movement.unit_cost,
            'total_value': 0
        }
    )
    
    # Actualizar cantidades según tipo de movimiento
    if movement.movement_type in ['entry', 'initial']:
        stock.quantity_on_hand += movement.quantity
    elif movement.movement_type in ['exit']:
        stock.quantity_on_hand -= movement.quantity
    elif movement.movement_type == 'adjustment':
        # Para ajustes, la cantidad puede ser positiva o negativa
        stock.quantity_on_hand += movement.quantity
    
    # Actualizar costos
    if movement.movement_type in ['entry', 'initial'] and movement.unit_cost > 0:
        # Calcular nuevo costo promedio
        total_value = stock.total_value + movement.total_cost
        total_quantity = stock.quantity_on_hand
        if total_quantity > 0:
            stock.average_cost = total_value / total_quantity
        stock.last_cost = movement.unit_cost
    
    # Calcular valores
    stock.quantity_available = stock.quantity_on_hand - stock.quantity_reserved
    stock.total_value = stock.quantity_on_hand * stock.average_cost
    stock.last_movement_date = movement.movement_date
    
    # Asegurar que las cantidades no sean negativas
    stock.quantity_on_hand = max(0, stock.quantity_on_hand)
    stock.quantity_available = max(0, stock.quantity_available)
    
    stock.save()
    
    # Actualizar costo promedio del producto
    product.update_average_cost()
    
    # Crear asiento contable para el movimiento
    if movement.total_cost > 0:
        create_inventory_journal_entry(movement)


def create_inventory_journal_entry(movement):
    """
    Crea un asiento contable para un movimiento de inventario.
    """
    try:
        # Obtener el tipo de comprobante para inventario
        voucher_type = JournalType.objects.filter(
            company=movement.company,
            code='CI'  # Comprobante de Inventario
        ).first()
        
        if not voucher_type:
            # Si no hay tipo CI, usar cualquier tipo activo
            voucher_type = JournalType.objects.filter(
                company=movement.company,
                is_active=True
            ).first()
        
        if not voucher_type:
            return None
        
        # Crear la entrada del diario
        journal_entry = JournalEntry.objects.create(
            company=movement.company,
            voucher_type=voucher_type,
            reference_number=f"INV-{movement.id}",
            description=f"Movimiento de inventario: {movement.get_movement_type_display()} - {movement.product.name}",
            entry_date=movement.movement_date,
            created_by=movement.created_by
        )
        
        # Definir las cuentas y montos según el tipo de movimiento
        if movement.movement_type == 'entry':
            # Entrada de inventario
            # Debe: Cuenta de Inventario
            # Haber: Cuenta de Costo (si es compra) o ajuste
            debit_account = movement.product.inventory_account
            credit_account = movement.product.cost_account
            
        elif movement.movement_type == 'exit':
            # Salida de inventario
            # Debe: Cuenta de Costo de Ventas
            # Haber: Cuenta de Inventario
            debit_account = movement.product.cost_account
            credit_account = movement.product.inventory_account
            
        elif movement.movement_type == 'adjustment':
            # Ajuste de inventario
            if movement.quantity > 0:
                # Ajuste positivo
                debit_account = movement.product.inventory_account
                credit_account = movement.product.cost_account
            else:
                # Ajuste negativo
                debit_account = movement.product.cost_account
                credit_account = movement.product.inventory_account
                
        else:
            # Para otros tipos, usar cuentas básicas
            debit_account = movement.product.inventory_account
            credit_account = movement.product.cost_account
        
        # Crear las líneas del asiento
        amount = abs(movement.total_cost)
        
        # Línea de débito
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=debit_account,
            description=f"{movement.product.code} - {movement.product.name}",
            debit_amount=amount,
            credit_amount=Decimal('0.00')
        )
        
        # Línea de crédito
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=credit_account,
            description=f"{movement.product.code} - {movement.product.name}",
            debit_amount=Decimal('0.00'),
            credit_amount=amount
        )
        
        # Asociar el asiento al movimiento
        movement.journal_entry = journal_entry
        movement.save(update_fields=['journal_entry'])
        
        return journal_entry
        
    except Exception as e:
        # Si hay error en contabilización, continuar sin asiento
        print(f"Error creating journal entry for stock movement {movement.id}: {e}")
        return None


@login_required
@require_company_access
def stock_report(request):
    current_company = request.current_company

    """
    Reporte de inventario.
    """
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    products = Product.objects.filter(is_active=True, track_inventory=True, **base_filter)
    
    context = {
        'products': products,
    }
    
    return render(request, 'inventory/stock_report.html', context)


@login_required
@require_company_access
def get_products_json(request):
    current_company = request.current_company

    """
    API para obtener productos en formato JSON.
    """
    search = request.GET.get('search', '')
    
    user_company = request.user.company if hasattr(request.user, 'company') else None
    base_filter = {'company': user_company} if user_company else {}
    
    products = Product.objects.filter(is_active=True, **base_filter)
    
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
