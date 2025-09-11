"""
Vistas del módulo core.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from datetime import datetime, date

from .models import Company, User, Country
from accounting.models_accounts import Account
from accounts_receivable.models_customer import Customer
from accounts_payable.models_supplier import Supplier


def dashboard(request):
    """
    Dashboard principal del sistema.
    """
    if not request.user.is_authenticated:
        return render(request, 'core/login.html')
    
    # Estadísticas básicas
    context = {
        'user': request.user,
        'active_company': request.user.companies.first() if hasattr(request.user, 'companies') and request.user.companies.exists() else None,
        'total_companies': Company.objects.count(),
        'total_users': User.objects.count(),
        'total_accounts': Account.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_suppliers': Supplier.objects.count(),
        'message': 'Bienvenido al sistema de contabilidad multiempresa!'
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def company_selector(request):
    """
    Selector de empresa para usuarios multiempresa.
    """
    # Filter companies that are active through the relationship
    companies = Company.objects.filter(
        id__in=request.user.companies.values_list('id', flat=True),
        is_active=True
    )
    return JsonResponse({
        'companies': [
            {
                'id': str(company.id),
                'name': company.name,
                'tax_id': company.tax_id
            }
            for company in companies
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