"""
Formularios para el módulo de cuentas por cobrar
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Invoice, InvoiceItem, Payment, CreditNote
from third_parties.models import ThirdParty
from core.models import Company
from accounting.models_accounts import Account


class InvoiceForm(forms.ModelForm):
    """Formulario para crear/editar facturas de venta"""
    
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_date', 'due_date', 'reference',
            'payment_terms', 'notes', 'discount_percentage',
            'tax_percentage', 'withholding_percentage'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'data-live-search': 'true'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referencia externa (opcional)',
                'maxlength': 100
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Condiciones de pago'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de la factura'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0.00'
            }),
            'tax_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '19.00'
            }),
            'withholding_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0.00'
            })
        }
        labels = {
            'customer': 'Cliente',
            'invoice_date': 'Fecha de Factura',
            'due_date': 'Fecha de Vencimiento',
            'reference': 'Referencia',
            'payment_terms': 'Términos de Pago',
            'notes': 'Observaciones',
            'discount_percentage': 'Descuento (%)',
            'tax_percentage': 'IVA (%)',
            'withholding_percentage': 'Retención (%)'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['customer'].queryset = ThirdParty.objects.filter(
                company=self.company,
                is_customer=True,
                is_active=True
            ).order_by('first_name', 'razon_social')
    
    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        
        if invoice_date and due_date:
            if due_date < invoice_date:
                raise ValidationError(
                    'La fecha de vencimiento no puede ser anterior a la fecha de factura'
                )
        
        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    """Formulario para items de factura"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'description', 'quantity', 'unit_price', 
            'discount_percentage', 'tax_percentage'
        ]
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto/servicio',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
                'min': '0.01',
                'value': '1.00'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0.00'
            }),
            'tax_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '19.00'
            })
        }
        labels = {
            'description': 'Descripción',
            'quantity': 'Cantidad',
            'unit_price': 'Precio Unitario',
            'discount_percentage': 'Desc. %',
            'tax_percentage': 'IVA %'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        if quantity and quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero')
        
        if unit_price and unit_price <= 0:
            raise ValidationError('El precio unitario debe ser mayor a cero')
        
        return cleaned_data


class PaymentForm(forms.ModelForm):
    """Formulario para pagos de clientes"""
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Efectivo'),
        ('CHECK', 'Cheque'),
        ('TRANSFER', 'Transferencia'),
        ('CREDIT_CARD', 'Tarjeta de Crédito'),
        ('DEBIT_CARD', 'Tarjeta Débito'),
        ('PSE', 'PSE'),
        ('OTHER', 'Otro')
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Payment
        fields = [
            'customer', 'payment_date', 'amount', 'payment_method',
            'reference', 'bank_account', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'data-live-search': 'true'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de referencia, cheque, etc.'
            }),
            'bank_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones del pago'
            })
        }
        labels = {
            'customer': 'Cliente',
            'payment_date': 'Fecha de Pago',
            'amount': 'Valor',
            'payment_method': 'Forma de Pago',
            'reference': 'Referencia',
            'bank_account': 'Cuenta Bancaria',
            'notes': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['customer'].queryset = ThirdParty.objects.filter(
                company=self.company,
                is_customer=True,
                is_active=True
            ).order_by('first_name', 'razon_social')
            
            # Cargar cuentas bancarias
            from treasury.models import BankAccount
            self.fields['bank_account'].queryset = BankAccount.objects.filter(
                company=self.company,
                is_active=True
            )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('El valor debe ser mayor a cero')
        return amount


class CreditNoteForm(forms.ModelForm):
    """Formulario para notas crédito"""
    
    REASON_CHOICES = [
        ('RETURN', 'Devolución de mercancía'),
        ('DISCOUNT', 'Descuento comercial'),
        ('CORRECTION', 'Corrección de factura'),
        ('DAMAGE', 'Mercancía averiada'),
        ('OTHER', 'Otro')
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CreditNote
        fields = [
            'customer', 'original_invoice', 'credit_date', 
            'reason', 'amount', 'description'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'original_invoice': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'credit_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la nota crédito',
                'required': True
            })
        }
        labels = {
            'customer': 'Cliente',
            'original_invoice': 'Factura Original',
            'credit_date': 'Fecha',
            'reason': 'Motivo',
            'amount': 'Valor',
            'description': 'Descripción'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['customer'].queryset = ThirdParty.objects.filter(
                company=self.company,
                is_customer=True,
                is_active=True
            )
            
            if customer:
                self.fields['original_invoice'].queryset = Invoice.objects.filter(
                    company=self.company,
                    customer=customer,
                    status__in=['PENDING', 'PARTIAL']
                )
            else:
                self.fields['original_invoice'].queryset = Invoice.objects.filter(
                    company=self.company
                )


class CustomerSearchForm(forms.Form):
    """Formulario de búsqueda de clientes"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por documento, nombre, email...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('active', 'Activos'),
            ('inactive', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    has_pending = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Solo con saldo pendiente'
    )


class InvoiceSearchForm(forms.Form):
    """Formulario de búsqueda de facturas"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, cliente, referencia...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('DRAFT', 'Borrador'),
            ('PENDING', 'Pendiente'),
            ('PARTIAL', 'Pagada Parcial'),
            ('PAID', 'Pagada'),
            ('CANCELLED', 'Anulada')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    customer = forms.ModelChoiceField(
        queryset=ThirdParty.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['customer'].queryset = ThirdParty.objects.filter(
                company=company,
                is_customer=True,
                is_active=True
            ).order_by('first_name', 'razon_social')


# Formset para items de factura
InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)