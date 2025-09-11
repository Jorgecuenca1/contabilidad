"""
Formularios para gestión de terceros
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import ThirdParty, ThirdPartyType, ThirdPartyContact, ThirdPartyAddress


class ThirdPartyForm(forms.ModelForm):
    """Formulario principal para terceros con campos dinámicos"""
    
    class Meta:
        model = ThirdParty
        fields = [
            # Básicos
            'person_type', 'document_type', 'document_number', 'verification_digit',
            
            # Personas naturales
            'nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            
            # Personas jurídicas
            'razon_social', 'trade_name',
            
            # Clasificación
            'is_customer', 'is_supplier', 'is_shareholder', 'is_bank', 'is_government',
            
            # Tributario
            'tax_regime', 'taxpayer_type', 'is_vat_responsible', 'is_ica_agent', 
            'is_withholding_agent', 'is_self_withholding', 'is_great_contributor',
            'great_contributor_resolution',
            
            # Geográfico y contacto
            'address', 'neighborhood', 'city', 'state', 'country', 'postal_code',
            'phone', 'mobile', 'fax', 'email', 'website',
            
            # Adicionales para jurídicas
            'economic_activity', 'ciiu_code', 'legal_representative', 'legal_rep_document',
            
            # Bancario
            'bank_name', 'bank_account_type', 'bank_account_number',
            
            # Comercial
            'credit_limit', 'payment_term_days', 'discount_percentage',
            
            # Contacto adicional
            'contact_person', 'contact_position', 'contact_phone', 'contact_email',
            
            # Estado
            'is_active', 'rating', 'notes'
        ]
        
        widgets = {
            'person_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'togglePersonFields(this.value)'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'handleDocumentType(this.value)'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de documento',
                'onblur': 'calculateDV()'
            }),
            'verification_digit': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'size': '1'
            }),
            
            # Personas naturales
            'nombre': forms.TextInput(attrs={
                'class': 'form-control natural-field',
                'placeholder': 'Primer nombre'
            }),
            'segundo_nombre': forms.TextInput(attrs={
                'class': 'form-control natural-field',
                'placeholder': 'Segundo nombre (opcional)'
            }),
            'primer_apellido': forms.TextInput(attrs={
                'class': 'form-control natural-field',
                'placeholder': 'Primer apellido'
            }),
            'segundo_apellido': forms.TextInput(attrs={
                'class': 'form-control natural-field',
                'placeholder': 'Segundo apellido (opcional)'
            }),
            
            # Personas jurídicas
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control juridica-field',
                'placeholder': 'Razón social completa'
            }),
            'trade_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre comercial'
            }),
            
            # Clasificación (checkboxes)
            'is_customer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_supplier': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_shareholder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bank': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_government': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Tributario
            'tax_regime': forms.Select(attrs={'class': 'form-select'}),
            'taxpayer_type': forms.Select(attrs={'class': 'form-select'}),
            'is_vat_responsible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_ica_agent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_withholding_agent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_self_withholding': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_great_contributor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'great_contributor_resolution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resolución de gran contribuyente'
            }),
            
            # Geográfico
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'neighborhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barrio'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'Colombia'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código postal'
            }),
            
            # Contacto
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono fijo'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono móvil'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sitio web'
            }),
            
            # Adicionales para jurídicas
            'economic_activity': forms.TextInput(attrs={
                'class': 'form-control juridica-field',
                'placeholder': 'Actividad económica principal'
            }),
            'ciiu_code': forms.TextInput(attrs={
                'class': 'form-control juridica-field',
                'placeholder': 'Código CIIU'
            }),
            'legal_representative': forms.TextInput(attrs={
                'class': 'form-control juridica-field',
                'placeholder': 'Nombre del representante legal'
            }),
            'legal_rep_document': forms.TextInput(attrs={
                'class': 'form-control juridica-field',
                'placeholder': 'Documento del representante legal'
            }),
            
            # Bancario
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del banco'
            }),
            'bank_account_type': forms.Select(attrs={'class': 'form-select'}),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cuenta'
            }),
            
            # Comercial
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'payment_term_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '30'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            
            # Contacto adicional
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona de contacto'
            }),
            'contact_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de contacto'
            }),
            
            # Estado
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones generales'
            }),
        }
        
        labels = {
            'person_type': 'Tipo de Persona',
            'document_type': 'Tipo de Documento',
            'document_number': 'Número de Documento',
            'verification_digit': 'DV',
            'nombre': 'Primer Nombre',
            'segundo_nombre': 'Segundo Nombre',
            'primer_apellido': 'Primer Apellido',
            'segundo_apellido': 'Segundo Apellido',
            'razon_social': 'Razón Social',
            'trade_name': 'Nombre Comercial',
            'is_customer': 'Es Cliente',
            'is_supplier': 'Es Proveedor',
            'is_shareholder': 'Es Accionista',
            'is_bank': 'Es Banco',
            'is_government': 'Es Entidad Gubernamental',
            'address': 'Dirección',
            'city': 'Ciudad',
            'state': 'Departamento',
            'country': 'País',
            'credit_limit': 'Cupo de Crédito',
            'payment_term_days': 'Días de Pago',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default values for optional fields
        self.fields['tax_regime'].required = False
        self.fields['taxpayer_type'].required = False
        self.fields['credit_limit'].required = False
        self.fields['payment_term_days'].required = False
        self.fields['discount_percentage'].required = False
        
        # Set initial values if not provided
        if not self.instance.pk:
            self.fields['credit_limit'].initial = 0
            self.fields['payment_term_days'].initial = 30
            self.fields['discount_percentage'].initial = 0
            self.fields['tax_regime'].initial = 'COMUN'
            self.fields['taxpayer_type'].initial = 'NO_APLICA'
        
        # Hacer campos obligatorios según el tipo de persona
        if self.instance and self.instance.pk:
            if self.instance.person_type == 'NATURAL':
                self.fields['nombre'].required = True
                self.fields['primer_apellido'].required = True
                self.fields['razon_social'].required = False
            elif self.instance.person_type == 'JURIDICA':
                self.fields['razon_social'].required = True
                self.fields['nombre'].required = False
                self.fields['primer_apellido'].required = False
    
    def clean_document_number(self):
        """Validar número de documento según el tipo"""
        document_number = self.cleaned_data.get('document_number', '').strip()
        document_type = self.data.get('document_type', '')
        
        if not document_number:
            raise ValidationError('El número de documento es obligatorio')
        
        # Validar formato según tipo de documento
        if document_type == 'NIT':
            # NIT debe ser numérico
            if not document_number.replace('-', '').isdigit():
                raise ValidationError('El NIT debe contener solo números')
            
            # Remover guiones para validación
            nit_clean = document_number.replace('-', '')
            
            # Validar longitud (entre 8 y 15 dígitos)
            if len(nit_clean) < 8 or len(nit_clean) > 15:
                raise ValidationError('El NIT debe tener entre 8 y 15 dígitos')
            
            # Validar dígito de verificación si está incluido
            if '-' in document_number:
                parts = document_number.split('-')
                if len(parts) == 2:
                    nit_base = parts[0]
                    dv_provided = parts[1]
                    dv_calculated = self._calculate_nit_dv(nit_base)
                    
                    if dv_provided != dv_calculated:
                        raise ValidationError(
                            f'Dígito de verificación incorrecto. Debería ser: {dv_calculated}'
                        )
        
        elif document_type == 'CC':
            # Cédula debe ser numérica
            if not document_number.isdigit():
                raise ValidationError('La cédula debe contener solo números')
            
            # Validar longitud (entre 6 y 12 dígitos)
            if len(document_number) < 6 or len(document_number) > 12:
                raise ValidationError('La cédula debe tener entre 6 y 12 dígitos')
        
        elif document_type == 'CE':
            # Cédula extranjería puede ser alfanumérica
            if len(document_number) < 6 or len(document_number) > 12:
                raise ValidationError('La cédula de extranjería debe tener entre 6 y 12 caracteres')
        
        return document_number
    
    def clean_email(self):
        """Validar email si se proporciona"""
        email = self.cleaned_data.get('email', '').strip()
        
        if email and '@' not in email:
            raise ValidationError('Ingrese un email válido')
        
        return email
    
    def clean_ciiu_code(self):
        """Validar código CIIU"""
        ciiu_code = self.cleaned_data.get('ciiu_code', '').strip()
        
        if ciiu_code:
            # El código CIIU debe ser numérico y de 4 dígitos
            if not ciiu_code.isdigit():
                raise ValidationError('El código CIIU debe ser numérico')
            
            if len(ciiu_code) != 4:
                raise ValidationError('El código CIIU debe tener exactamente 4 dígitos')
        
        return ciiu_code
    
    def clean(self):
        cleaned_data = super().clean()
        person_type = cleaned_data.get('person_type')
        
        # Validaciones específicas por tipo de persona
        if person_type == 'NATURAL':
            if not cleaned_data.get('nombre'):
                self.add_error('nombre', 'El primer nombre es obligatorio para personas naturales')
            if not cleaned_data.get('primer_apellido'):
                self.add_error('primer_apellido', 'El primer apellido es obligatorio para personas naturales')
        
        elif person_type == 'JURIDICA':
            if not cleaned_data.get('razon_social'):
                self.add_error('razon_social', 'La razón social es obligatoria para personas jurídicas')
            
            # Para personas jurídicas, validar campos adicionales
            if not cleaned_data.get('economic_activity'):
                self.add_error('economic_activity', 'La actividad económica es obligatoria para personas jurídicas')
        
        # Validar documento único por empresa
        document_type = cleaned_data.get('document_type')
        document_number = cleaned_data.get('document_number')
        
        if document_type and document_number:
            query = ThirdParty.objects.filter(
                document_type=document_type,
                document_number=document_number
            )
            
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise ValidationError(
                    f'Ya existe un tercero con {document_type} {document_number}'
                )
        
        # Validar que al menos un tipo esté marcado
        types_checked = any([
            cleaned_data.get('is_customer'),
            cleaned_data.get('is_supplier'),
            cleaned_data.get('is_shareholder'),
            cleaned_data.get('is_bank'),
            cleaned_data.get('is_government')
        ])
        
        if not types_checked:
            raise ValidationError(
                'Debe marcar al menos un tipo (Cliente, Proveedor, Accionista, etc.)'
            )
        
        return cleaned_data
    
    def _calculate_nit_dv(self, nit):
        """Calcular dígito de verificación para NIT"""
        vpri = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        
        suma = 0
        for i, digit in enumerate(reversed(nit)):
            if i >= len(vpri):
                break
            suma += int(digit) * vpri[i]
        
        residuo = suma % 11
        
        if residuo > 1:
            return str(11 - residuo)
        else:
            return str(residuo)


class ThirdPartyContactForm(forms.ModelForm):
    """Formulario para contactos adicionales"""
    
    class Meta:
        model = ThirdPartyContact
        fields = ['name', 'position', 'department', 'phone', 'mobile', 'email', 'is_primary', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ThirdPartyAddressForm(forms.ModelForm):
    """Formulario para direcciones adicionales"""
    
    class Meta:
        model = ThirdPartyAddress
        fields = [
            'address_type', 'name', 'address', 'neighborhood', 'city', 
            'state', 'country', 'postal_code', 'phone', 'is_primary'
        ]
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'Colombia'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ThirdPartySearchForm(forms.Form):
    """Formulario de búsqueda de terceros"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por documento, nombre, email...'
        })
    )
    
    person_type = forms.ChoiceField(
        choices=[('', 'Todos')] + ThirdParty.PERSON_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_customer = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_supplier = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )