"""
Vistas del módulo core.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from datetime import datetime, date

from .models import Company, User, Country
from .models_modules import SystemModule, CompanyModule, UserModulePermission
from accounting.models_accounts import Account
from accounts_receivable.models_customer import Customer
from accounts_payable.models_supplier import Supplier


def dashboard(request):
    """
    Dashboard principal del sistema.
    """
    if not request.user.is_authenticated:
        return render(request, 'core/login.html')
    
    # Verificar si hay empresa seleccionada en sesión
    active_company_id = request.session.get('active_company')
    active_company = None
    
    if active_company_id:
        try:
            active_company = Company.objects.get(id=active_company_id, is_active=True)
            # Verificar que el usuario aún tenga acceso a esta empresa
            if not request.user.can_access_company(active_company):
                # Limpiar sesión y redirigir a selector
                if 'active_company' in request.session:
                    del request.session['active_company']
                return redirect('core:company_selector')
        except Company.DoesNotExist:
            # Empresa no existe, limpiar sesión y redirigir
            if 'active_company' in request.session:
                del request.session['active_company']
            return redirect('core:company_selector')
    else:
        # No hay empresa en sesión, redirigir a selector
        return redirect('core:company_selector')
    
    # Obtener módulos disponibles y activos para la empresa
    available_modules = []
    active_modules = []
    active_modules_by_category = {}
    
    if active_company:
        # Módulos del sistema disponibles para esta empresa
        all_modules = SystemModule.objects.filter(is_available=True)
        available_modules = [m for m in all_modules if m.can_be_activated_for_company(active_company)]
        
        # Módulos actualmente activados
        active_modules = CompanyModule.objects.filter(
            company=active_company,
            is_enabled=True
        ).select_related('module')
        
        # Organizar módulos activos por categoría
        for company_module in active_modules:
            module = company_module.module
            category_display = {
                'finance': 'Módulos Financieros',
                'operations': 'Módulos Operacionales', 
                'healthcare': 'Módulos de Salud',
                'education': 'Módulos Educativos',
                'manufacturing': 'Módulos de Manufactura'
            }.get(module.category, module.category.title())
            
            if category_display not in active_modules_by_category:
                active_modules_by_category[category_display] = []
            
            active_modules_by_category[category_display].append({
                'module': module,
                'is_active': True,
                'can_access': True
            })
    
    # Verificar si puede cambiar de empresa (simplificado - si tiene acceso a más de una empresa)
    accessible_companies_count = request.user.get_accessible_companies().count()
    can_switch_company = accessible_companies_count > 1
    
    # Estadísticas básicas
    context = {
        'user': request.user,
        'active_company': active_company,
        'can_switch_company': can_switch_company,
        'can_select_company': can_switch_company,  # Para compatibilidad con template
        'current_company': active_company,  # Para compatibilidad con template
        'user_companies': request.user.get_accessible_companies(),  # Para el selector
        'user_role': request.user.role,  # Para mostrar rol en template
        'total_companies': Company.objects.count(),
        'total_users': User.objects.count(),
        'total_accounts': Account.objects.filter(custom_company=active_company).count() if active_company else 0,
        'total_customers': Customer.objects.filter(company=active_company).count() if active_company else 0,
        'total_suppliers': Supplier.objects.filter(company=active_company).count() if active_company else 0,
        'available_modules': available_modules,
        'active_modules': active_modules,
        'active_modules_by_category': active_modules_by_category,
        'is_healthcare_company': active_company.is_healthcare_company() if active_company else False,
        'is_public_company': active_company.sector == 'public' if active_company else False,
        'is_admin': request.user.role in ['superadmin', 'admin'],
        'accessible_companies_count': accessible_companies_count,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def select_company(request):
    """
    Seleccionar empresa activa para el usuario.
    """
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        
        if company_id:
            # Verificar que el usuario tenga acceso a esta empresa
            accessible_companies = request.user.get_accessible_companies()
            selected_company = accessible_companies.filter(id=company_id).first()
            
            if selected_company:
                # Guardar en la sesión
                request.session['selected_company_id'] = str(company_id)
                messages.success(request, f'Empresa seleccionada: {selected_company.name}')
                return JsonResponse({'success': True, 'company_name': selected_company.name})
            else:
                messages.error(request, 'No tiene acceso a esta empresa.')
                return JsonResponse({'success': False, 'error': 'Sin acceso a la empresa'})
        else:
            messages.error(request, 'Empresa no válida.')
            return JsonResponse({'success': False, 'error': 'Empresa no válida'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def company_selector_api(request):
    """
    API para obtener las empresas accesibles del usuario.
    """
    accessible_companies = request.user.get_accessible_companies()
    return JsonResponse({
        'companies': [
            {
                'id': str(company.id),
                'name': company.name,
                'tax_id': company.tax_id
            }
            for company in accessible_companies
        ]
    })


@login_required
def company_list(request):
    """
    Lista de empresas.
    """
    search = request.GET.get('search', '')
    regime = request.GET.get('regime', '')
    sector = request.GET.get('sector', '')
    
    companies = Company.objects.all()
    
    if search:
        companies = companies.filter(
            Q(name__icontains=search) |
            Q(legal_name__icontains=search) |
            Q(tax_id__icontains=search)
        )
    
    if regime:
        companies = companies.filter(regime=regime)
    
    if sector:
        companies = companies.filter(sector=sector)
    
    # Paginación
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    regime_choices = Company.REGIME_CHOICES
    sector_choices = Company.SECTOR_CHOICES
    
    context = {
        'page_obj': page_obj,
        'regime_choices': regime_choices,
        'sector_choices': sector_choices,
        'search': search,
        'selected_regime': regime,
        'selected_sector': sector,
    }
    
    return render(request, 'core/company_list.html', context)


@login_required
def new_company(request):
    """
    Crear nueva empresa.
    """
    # Solo superadmin puede crear empresas
    if request.user.role != 'superadmin':
        messages.error(request, 'No tienes permisos para crear nuevas empresas.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.POST.get('name')
            legal_name = request.POST.get('legal_name')
            tax_id = request.POST.get('tax_id')
            tax_id_dv = request.POST.get('tax_id_dv', '')
            country_id = request.POST.get('country')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            email = request.POST.get('email')
            regime = request.POST.get('regime')
            sector = request.POST.get('sector')
            fiscal_year_start = request.POST.get('fiscal_year_start')
            fiscal_year_end = request.POST.get('fiscal_year_end')
            legal_representative = request.POST.get('legal_representative')
            legal_rep_document = request.POST.get('legal_rep_document')
            
            # Validar datos requeridos
            if not all([name, legal_name, tax_id, country_id, address, city, state, email, regime, fiscal_year_start, fiscal_year_end, legal_representative, legal_rep_document]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('core:new_company')
            
            # Crear empresa
            company = Company.objects.create(
                name=name,
                legal_name=legal_name,
                tax_id=tax_id,
                tax_id_dv=tax_id_dv,
                country_id=country_id,
                address=address,
                city=city,
                state=state,
                postal_code=request.POST.get('postal_code', ''),
                phone=request.POST.get('phone', ''),
                email=email,
                website=request.POST.get('website', ''),
                regime=regime,
                sector=sector,
                functional_currency=request.POST.get('functional_currency', 'COP'),
                fiscal_year_start=datetime.strptime(fiscal_year_start, '%Y-%m-%d').date(),
                fiscal_year_end=datetime.strptime(fiscal_year_end, '%Y-%m-%d').date(),
                legal_representative=legal_representative,
                legal_rep_document=legal_rep_document,
                created_by=request.user
            )
            
            messages.success(request, f'Empresa {company.name} creada exitosamente.')
            return redirect('core:company_detail', company_id=company.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la empresa: {str(e)}')
    
    # Datos para el formulario
    countries = Country.objects.all()  # Country model doesn't have is_active field
    regime_choices = Company.REGIME_CHOICES
    sector_choices = Company.SECTOR_CHOICES
    
    context = {
        'countries': countries,
        'regime_choices': regime_choices,
        'sector_choices': sector_choices,
    }
    
    return render(request, 'core/new_company.html', context)


@login_required
def company_detail(request, company_id):
    """
    Detalle de empresa.
    """
    company = get_object_or_404(Company, id=company_id)
    
    # Estadísticas de la empresa
    stats = {
        'total_users': company.users.count(),
        'total_customers': company.customers.count(),
        'total_suppliers': company.suppliers.count(),
        'total_accounts': company.accounts.count(),
    }
    
    context = {
        'company': company,
        'stats': stats,
    }
    
    return render(request, 'core/company_detail.html', context)


@login_required
def edit_company(request, company_id):
    """
    Editar empresa.
    """
    company = get_object_or_404(Company, id=company_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos
            company.name = request.POST.get('name', company.name)
            company.legal_name = request.POST.get('legal_name', company.legal_name)
            company.address = request.POST.get('address', company.address)
            company.city = request.POST.get('city', company.city)
            company.state = request.POST.get('state', company.state)
            company.postal_code = request.POST.get('postal_code', company.postal_code)
            company.phone = request.POST.get('phone', company.phone)
            company.email = request.POST.get('email', company.email)
            company.website = request.POST.get('website', company.website)
            company.regime = request.POST.get('regime', company.regime)
            company.sector = request.POST.get('sector', company.sector)
            company.legal_representative = request.POST.get('legal_representative', company.legal_representative)
            company.legal_rep_document = request.POST.get('legal_rep_document', company.legal_rep_document)
            
            # Actualizar fechas fiscales si se proporcionan
            fiscal_year_start = request.POST.get('fiscal_year_start')
            fiscal_year_end = request.POST.get('fiscal_year_end')
            if fiscal_year_start:
                company.fiscal_year_start = datetime.strptime(fiscal_year_start, '%Y-%m-%d').date()
            if fiscal_year_end:
                company.fiscal_year_end = datetime.strptime(fiscal_year_end, '%Y-%m-%d').date()
            
            company.save()
            
            messages.success(request, f'Empresa {company.name} actualizada exitosamente.')
            return redirect('core:company_detail', company_id=company.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la empresa: {str(e)}')
    
    # Datos para el formulario
    countries = Country.objects.all()  # Country model doesn't have is_active field
    regime_choices = Company.REGIME_CHOICES
    sector_choices = Company.SECTOR_CHOICES
    
    context = {
        'company': company,
        'countries': countries,
        'regime_choices': regime_choices,
        'sector_choices': sector_choices,
    }
    
    return render(request, 'core/edit_company.html', context)


@login_required
def user_profile(request):
    """Vista para el perfil del usuario."""
    context = {
        'user': request.user,
    }
    return render(request, 'registration/profile.html', context)


def custom_logout(request):
    """Vista personalizada de logout."""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('/accounts/login/')


@login_required
def manage_modules(request):
    """Gestionar módulos de la empresa."""
    active_company = request.user.companies.first()
    if not active_company:
        messages.error(request, 'Debe seleccionar una empresa primero.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        module_id = request.POST.get('module_id')
        
        if action == 'activate':
            try:
                module = SystemModule.objects.get(id=module_id)
                if module.can_be_activated_for_company(active_company):
                    company_module, created = CompanyModule.objects.get_or_create(
                        company=active_company,
                        module=module,
                        defaults={'enabled_by': request.user, 'is_enabled': True}
                    )
                    
                    if not created:
                        company_module.is_enabled = True
                        company_module.save()
                    
                    messages.success(request, f'Módulo {module.name} activado exitosamente.')
                else:
                    messages.error(request, f'El módulo {module.name} no está disponible para esta empresa.')
            except SystemModule.DoesNotExist:
                messages.error(request, 'Módulo no encontrado.')
        
        elif action == 'deactivate':
            try:
                company_module = CompanyModule.objects.get(
                    company=active_company,
                    module_id=module_id
                )
                if not company_module.module.is_core_module:
                    company_module.is_enabled = False
                    company_module.save()
                    messages.success(request, f'Módulo {company_module.module.name} desactivado exitosamente.')
                else:
                    messages.error(request, 'No se puede desactivar un módulo core.')
            except CompanyModule.DoesNotExist:
                messages.error(request, 'Módulo no encontrado.')
        
        return redirect('core:manage_modules')
    
    # Obtener módulos disponibles y activos
    all_modules = SystemModule.objects.filter(is_available=True).order_by('category', 'name')
    available_modules = [m for m in all_modules if m.can_be_activated_for_company(active_company)]
    
    active_modules = CompanyModule.objects.filter(
        company=active_company,
        is_enabled=True
    ).select_related('module')
    
    active_module_ids = {cm.module.id for cm in active_modules}
    
    context = {
        'active_company': active_company,
        'available_modules': available_modules,
        'active_modules': active_modules,
        'active_module_ids': active_module_ids,
    }
    
    return render(request, 'core/manage_modules.html', context)