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
from core.models import Company


@login_required
def third_party_list(request):
    """Lista de todos los terceros de la empresa"""
    company = request.user.default_company if hasattr(request.user, 'default_company') else Company.objects.first()
    
    # Filtros
    search = request.GET.get('search', '')
    filter_type = request.GET.get('type', '')
    
    third_parties = ThirdParty.objects.filter(company=company)
    
    if search:
        third_parties = third_parties.filter(
            Q(document_number__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
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
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'filter_type': filter_type,
    }
    
    return render(request, 'third_parties/list.html', context)


@login_required
def third_party_create(request):
    """Crear nuevo tercero"""
    company = request.user.default_company if hasattr(request.user, 'default_company') else Company.objects.first()
    
    if request.method == 'POST':
        try:
            # Crear tercero
            third_party = ThirdParty.objects.create(
                company=company,
                person_type=request.POST.get('person_type'),
                document_type=request.POST.get('document_type'),
                document_number=request.POST.get('document_number'),
                first_name=request.POST.get('first_name'),
                middle_name=request.POST.get('middle_name', ''),
                last_name=request.POST.get('last_name', ''),
                second_last_name=request.POST.get('second_last_name', ''),
                trade_name=request.POST.get('trade_name', ''),
                
                # Clasificación
                is_customer=request.POST.get('is_customer') == 'on',
                is_supplier=request.POST.get('is_supplier') == 'on',
                is_employee=request.POST.get('is_employee') == 'on',
                is_shareholder=request.POST.get('is_shareholder') == 'on',
                
                # Información tributaria
                tax_regime=request.POST.get('tax_regime', 'COMUN'),
                taxpayer_type=request.POST.get('taxpayer_type', 'NO_APLICA'),
                is_vat_responsible=request.POST.get('is_vat_responsible') == 'on',
                is_withholding_agent=request.POST.get('is_withholding_agent') == 'on',
                is_self_withholding=request.POST.get('is_self_withholding') == 'on',
                is_great_contributor=request.POST.get('is_great_contributor') == 'on',
                
                # Contacto
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                phone=request.POST.get('phone', ''),
                mobile=request.POST.get('mobile', ''),
                email=request.POST.get('email', ''),
                
                # Información adicional
                economic_activity=request.POST.get('economic_activity', ''),
                ciiu_code=request.POST.get('ciiu_code', ''),
                
                # Información bancaria
                bank_name=request.POST.get('bank_name', ''),
                bank_account_type=request.POST.get('bank_account_type', ''),
                bank_account_number=request.POST.get('bank_account_number', ''),
                
                # Información comercial
                credit_limit=request.POST.get('credit_limit', 0),
                payment_term_days=request.POST.get('payment_term_days', 30),
                
                created_by=request.user
            )
            
            # Calcular dígito de verificación si es NIT
            if third_party.document_type == 'NIT':
                third_party.verification_digit = third_party.calculate_verification_digit()
                third_party.save()
            
            messages.success(request, f'Tercero {third_party.get_full_name()} creado exitosamente')
            return redirect('third_parties:detail', pk=third_party.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear tercero: {str(e)}')
    
    context = {
        'company': company,
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
        try:
            # Actualizar tercero
            third_party.person_type = request.POST.get('person_type')
            third_party.document_type = request.POST.get('document_type')
            third_party.document_number = request.POST.get('document_number')
            third_party.first_name = request.POST.get('first_name')
            third_party.middle_name = request.POST.get('middle_name', '')
            third_party.last_name = request.POST.get('last_name', '')
            third_party.second_last_name = request.POST.get('second_last_name', '')
            third_party.trade_name = request.POST.get('trade_name', '')
            
            # Clasificación
            third_party.is_customer = request.POST.get('is_customer') == 'on'
            third_party.is_supplier = request.POST.get('is_supplier') == 'on'
            third_party.is_employee = request.POST.get('is_employee') == 'on'
            third_party.is_shareholder = request.POST.get('is_shareholder') == 'on'
            
            # Información tributaria
            third_party.tax_regime = request.POST.get('tax_regime', 'COMUN')
            third_party.taxpayer_type = request.POST.get('taxpayer_type', 'NO_APLICA')
            third_party.is_vat_responsible = request.POST.get('is_vat_responsible') == 'on'
            third_party.is_withholding_agent = request.POST.get('is_withholding_agent') == 'on'
            third_party.is_self_withholding = request.POST.get('is_self_withholding') == 'on'
            third_party.is_great_contributor = request.POST.get('is_great_contributor') == 'on'
            
            # Contacto
            third_party.address = request.POST.get('address')
            third_party.city = request.POST.get('city')
            third_party.state = request.POST.get('state')
            third_party.phone = request.POST.get('phone', '')
            third_party.mobile = request.POST.get('mobile', '')
            third_party.email = request.POST.get('email', '')
            
            # Información adicional
            third_party.economic_activity = request.POST.get('economic_activity', '')
            third_party.ciiu_code = request.POST.get('ciiu_code', '')
            
            # Información bancaria
            third_party.bank_name = request.POST.get('bank_name', '')
            third_party.bank_account_type = request.POST.get('bank_account_type', '')
            third_party.bank_account_number = request.POST.get('bank_account_number', '')
            
            # Información comercial
            third_party.credit_limit = request.POST.get('credit_limit', 0)
            third_party.payment_term_days = request.POST.get('payment_term_days', 30)
            
            third_party.updated_by = request.user
            third_party.save()
            
            messages.success(request, f'Tercero {third_party.get_full_name()} actualizado exitosamente')
            return redirect('third_parties:detail', pk=third_party.pk)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar tercero: {str(e)}')
    
    context = {
        'third_party': third_party,
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
def api_search_third_parties(request):
    """API para búsqueda de terceros (usado en formularios)"""
    company = request.user.default_company if hasattr(request.user, 'default_company') else Company.objects.first()
    query = request.GET.get('q', '')
    filter_type = request.GET.get('type', '')  # customer, supplier, etc.
    
    third_parties = ThirdParty.objects.filter(company=company, is_active=True)
    
    if filter_type == 'customer':
        third_parties = third_parties.filter(is_customer=True)
    elif filter_type == 'supplier':
        third_parties = third_parties.filter(is_supplier=True)
    
    if query:
        third_parties = third_parties.filter(
            Q(document_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
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
def api_verify_nit(request):
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