"""
Vistas para la gestión de terceros
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import ThirdParty, ThirdPartyType, ThirdPartyContact, ThirdPartyAddress, ThirdPartyDocument
from .forms import ThirdPartyForm, ThirdPartySearchForm, ThirdPartyContactForm, ThirdPartyAddressForm
from core.models import Company
from core.utils import get_current_company, require_company_access



@login_required
@require_company_access
def third_party_list(request):
    current_company = request.current_company

    """Lista de todos los terceros de la empresa"""
    # Filtros
    search = request.GET.get('search', '')
    filter_type = request.GET.get('type', '')
    
    third_parties = ThirdParty.objects.filter(company=current_company)
    
    if search:
        third_parties = third_parties.filter(
            Q(document_number__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(nombre__icontains=search) |
            Q(primer_apellido__icontains=search) |
            Q(segundo_apellido__icontains=search) |
            Q(razon_social__icontains=search) |
            Q(trade_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if filter_type:
        if filter_type == 'customer':
            third_parties = third_parties.filter(is_customer=True)
        elif filter_type == 'supplier':
            third_parties = third_parties.filter(is_supplier=True)
        elif filter_type == 'employee':
            third_parties = third_parties.filter(is_employee=True)
    
    # Paginación
    paginator = Paginator(third_parties, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_type': filter_type,
    }
    
    return render(request, 'third_parties/list.html', context)


@login_required
@require_company_access
def third_party_create(request):
    current_company = request.current_company

    """Crear nuevo tercero"""
    if request.method == 'POST':
        form = ThirdPartyForm(request.POST)
        if form.is_valid():
            third_party = form.save(commit=False)
            third_party.company = current_company
            third_party.created_by = request.user
            third_party.save()
            
            messages.success(request, f'Tercero {third_party.get_full_name()} creado exitosamente')
            return redirect('third_parties:detail', pk=third_party.pk)
    else:
        form = ThirdPartyForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'third_parties/create.html', context)


@login_required
def third_party_detail(request, pk):
    """Ver detalle de un tercero"""
    third_party = get_object_or_404(ThirdParty, pk=pk, company__in=request.user.companies.all())
    
    # Obtener contactos adicionales
    contacts = third_party.contacts.all()
    
    # Obtener direcciones adicionales
    addresses = third_party.addresses.all()
    
    # Obtener documentos
    documents = third_party.documents.all()
    
    context = {
        'third_party': third_party,
        'contacts': contacts,
        'addresses': addresses,
        'documents': documents,
    }
    
    return render(request, 'third_parties/detail.html', context)


@login_required
def third_party_edit(request, pk):
    """Editar un tercero"""
    third_party = get_object_or_404(ThirdParty, pk=pk, company__in=request.user.companies.all())
    
    if request.method == 'POST':
        form = ThirdPartyForm(request.POST, instance=third_party)
        if form.is_valid():
            third_party = form.save(commit=False)
            third_party.updated_by = request.user
            third_party.save()
            
            messages.success(request, f'Tercero {third_party.get_full_name()} actualizado exitosamente')
            return redirect('third_parties:detail', pk=third_party.pk)
    else:
        form = ThirdPartyForm(instance=third_party)
    
    context = {
        'third_party': third_party,
        'form': form,
    }
    
    return render(request, 'third_parties/edit.html', context)


@login_required
def third_party_delete(request, pk):
    """Eliminar un tercero"""
    third_party = get_object_or_404(ThirdParty, pk=pk, company__in=request.user.companies.all())
    
    if request.method == 'POST':
        name = third_party.get_full_name()
        third_party.delete()
        messages.success(request, f'Tercero {name} eliminado exitosamente')
        return redirect('third_parties:list')
    
    context = {
        'third_party': third_party,
    }
    
    return render(request, 'third_parties/delete.html', context)


# API endpoints para búsqueda AJAX
@login_required
@require_company_access
def api_search_third_parties(request):
    current_company = request.current_company

    """API para búsqueda de terceros (usado en formularios)"""
    query = request.GET.get('q', '')
    filter_type = request.GET.get('type', '')  # customer, supplier, etc.
    
    third_parties = ThirdParty.objects.filter(company=current_company, is_active=True)
    
    if filter_type == 'customer':
        third_parties = third_parties.filter(is_customer=True)
    elif filter_type == 'supplier':
        third_parties = third_parties.filter(is_supplier=True)
    
    if query:
        third_parties = third_parties.filter(
            Q(document_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(nombre__icontains=query) |
            Q(primer_apellido__icontains=query) |
            Q(razon_social__icontains=query) |
            Q(trade_name__icontains=query)
        )[:10]
    
    results = []
    for tp in third_parties:
        results.append({
            'id': tp.id,
            'text': f"{tp.get_full_name()} - {tp.document_number}",
            'document_type': tp.document_type,
            'document_number': tp.document_number,
            'name': tp.get_full_name(),
            'email': tp.email,
            'phone': tp.phone,
            'address': tp.address,
            'city': tp.city,
            'credit_limit': float(tp.credit_limit),
            'payment_term_days': tp.payment_term_days,
        })
    
    return JsonResponse({'results': results})


@login_required
@require_company_access
def api_verify_nit(request):
    current_company = request.current_company

    """API para verificar dígito de verificación de NIT"""
    nit = request.GET.get('nit', '')
    
    if not nit:
        return JsonResponse({'valid': False, 'message': 'NIT vacío'})
    
    # Calcular dígito de verificación
    vpri = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    
    suma = 0
    for i, digit in enumerate(reversed(nit)):
        if i >= len(vpri):
            break
        if digit.isdigit():
            suma += int(digit) * vpri[i]
    
    residuo = suma % 11
    
    if residuo > 1:
        dv = str(11 - residuo)
    else:
        dv = str(residuo)
    
    return JsonResponse({
        'valid': True,
        'nit': nit,
        'dv': dv,
        'formatted': f"{nit}-{dv}"
    })