"""
Formularios para el módulo de contabilidad
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models_accounts import Account, ChartOfAccounts, AccountType, CostCenter
from .models_journal import JournalEntry, JournalEntryLine, JournalType
from core.models import Company, Period, Currency


class JournalEntryForm(forms.ModelForm):
    """Formulario para crear asientos contables"""
    
    class Meta:
        model = JournalEntry
        fields = [
            'company', 'journal_type', 'date', 'reference', 
            'description', 'period', 'currency'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'journal_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de referencia (ej: FAC-001)',
                'maxlength': 50
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción de la transacción',
                'required': True
            }),
            'period': forms.Select(attrs={
                'class': 'form-select'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'company': 'Empresa',
            'journal_type': 'Tipo de Comprobante',
            'date': 'Fecha',
            'reference': 'Referencia',
            'description': 'Descripción',
            'period': 'Período',
            'currency': 'Moneda'
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar opciones según el usuario
        if self.user:
            self.fields['company'].queryset = Company.objects.filter(
                is_active=True
            )
            
        # Configurar valores iniciales
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        self.fields['journal_type'].queryset = JournalType.objects.filter(is_active=True)
        
        # Establecer moneda por defecto (COP)
        cop_currency = Currency.objects.filter(code='COP').first()
        if cop_currency:
            self.fields['currency'].initial = cop_currency.pk
    
    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get('company')
        date = cleaned_data.get('date')
        
        # Validar período activo
        if company and date:
            period = Period.objects.filter(
                fiscal_year__company=company,
                start_date__lte=date,
                end_date__gte=date,
                status='open'
            ).first()
            
            if not period:
                raise ValidationError(
                    'No hay un período contable activo para la fecha seleccionada'
                )
            cleaned_data['period'] = period
        
        return cleaned_data


class JournalEntryLineForm(forms.ModelForm):
    """Formulario para líneas de asiento contable"""
    
    class Meta:
        model = JournalEntryLine
        fields = [
            'account', 'description', 'debit', 'credit', 
            'cost_center', 'third_party_id'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select account-select',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Concepto del movimiento'
            }),
            'debit': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-select'
            }),
            'third_party_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID del tercero (opcional)'
            })
        }
        labels = {
            'account': 'Cuenta',
            'description': 'Descripción',
            'debit': 'Débito',
            'credit': 'Crédito',
            'cost_center': 'Centro de Costo',
            'third_party_id': 'ID Tercero'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            # Filtrar cuentas por empresa y solo cuentas de detalle
            self.fields['account'].queryset = Account.objects.filter(
                company=self.company,
                is_detail=True,
                is_active=True
            ).select_related('account_type')
            
            # Filtrar centros de costo
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.company,
                is_active=True
            )
            
    
    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit', 0)
        credit = cleaned_data.get('credit', 0)
        
        # Validar que solo uno de los campos tenga valor
        if debit and credit:
            raise ValidationError(
                'Una línea no puede tener valores tanto en débito como en crédito'
            )
        
        if not debit and not credit:
            raise ValidationError(
                'Debe especificar un valor en débito o crédito'
            )
        
        return cleaned_data


class AccountForm(forms.ModelForm):
    """Formulario para crear/editar cuentas contables"""
    
    class Meta:
        model = Account
        fields = [
            'code', 'name', 'account_type', 'parent', 'description',
            'is_detail', 'requires_third_party', 'requires_cost_center',
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de cuenta (ej: 1105)',
                'maxlength': 20
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la cuenta',
                'required': True
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la cuenta'
            }),
            'is_detail': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requires_third_party': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requires_cost_center': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'code': 'Código',
            'name': 'Nombre',
            'account_type': 'Tipo de Cuenta',
            'parent': 'Cuenta Padre',
            'description': 'Descripción',
            'is_detail': 'Es Cuenta de Detalle',
            'requires_third_party': 'Requiere Tercero',
            'requires_cost_center': 'Requiere Centro de Costo',
            'is_active': 'Activa'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['account_type'].queryset = AccountType.objects.filter(
                is_active=True
            )
            self.fields['parent'].queryset = Account.objects.filter(
                company=self.company,
                is_detail=False,
                is_active=True
            )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            raise ValidationError('El código es obligatorio')
        
        # Validar que el código solo contenga números
        if not code.isdigit():
            raise ValidationError('El código debe contener solo números')
        
        # Validar unicidad por empresa
        if self.company:
            existing = Account.objects.filter(
                company=self.company,
                code=code
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Ya existe una cuenta con el código {code}')
        
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        is_detail = cleaned_data.get('is_detail')
        code = cleaned_data.get('code')
        
        # Validar jerarquía de cuentas
        if parent and code:
            if not code.startswith(parent.code):
                raise ValidationError(
                    f'El código debe comenzar con {parent.code} (código de la cuenta padre)'
                )
        
        # Si es cuenta de detalle, debe tener padre
        if is_detail and not parent:
            raise ValidationError(
                'Las cuentas de detalle deben tener una cuenta padre'
            )
        
        return cleaned_data


class CostCenterForm(forms.ModelForm):
    """Formulario para crear/editar centros de costo"""
    
    class Meta:
        model = CostCenter
        fields = ['code', 'name', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código del centro de costo',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del centro de costo',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del centro de costo'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        
        if self.company:
            existing = CostCenter.objects.filter(
                company=self.company,
                code=code
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Ya existe un centro de costo con el código {code}')
        
        return code


class JournalTypeForm(forms.ModelForm):
    """Formulario para tipos de comprobante"""
    
    class Meta:
        model = JournalType
        fields = ['code', 'name', 'description', 'sequence_prefix', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código (ej: CI)',
                'maxlength': 5,
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del comprobante',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del tipo de comprobante'
            }),
            'sequence_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prefijo para numeración',
                'maxlength': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        
        # Validar que sea uno de los códigos colombianos válidos
        valid_codes = [
            'CI', 'CE', 'CG', 'CC', 'CN', 'CB', 'CA', 'CR', 
            'CP', 'CT', 'CX', 'CO', 'CK', 'CS', 'CV', 'CM'
        ]
        
        if code not in valid_codes:
            raise ValidationError(
                f'Código inválido. Debe ser uno de: {", ".join(valid_codes)}'
            )
        
        return code