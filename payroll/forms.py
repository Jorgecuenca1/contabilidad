"""
Formularios para el módulo de nómina
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Employee, PayrollPeriod, Payroll, PayrollItem, SocialSecurityRate
from third_parties.models import ThirdParty
from core.models import Company
import re


class EmployeeForm(forms.ModelForm):
    """Formulario para crear/editar empleados"""
    
    class Meta:
        model = Employee
        fields = [
            'third_party', 'employee_number', 'position', 'department',
            'hire_date', 'contract_type', 'salary_type', 'basic_salary',
            'transportation_allowance', 'eps', 'pension_fund', 'arl',
            'compensation_fund', 'is_active', 'termination_date'
        ]
        widgets = {
            'third_party': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'data-live-search': 'true'
            }),
            'employee_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número único del empleado',
                'required': True
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo o posición',
                'required': True
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento o área'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'contract_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'salary_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'required': True
            }),
            'transportation_allowance': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'eps': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EPS del empleado'
            }),
            'pension_fund': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fondo de pensiones'
            }),
            'arl': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ARL - Riesgos laborales'
            }),
            'compensation_fund': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Caja de compensación'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'termination_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'third_party': 'Tercero',
            'employee_number': 'Número de Empleado',
            'position': 'Cargo',
            'department': 'Departamento',
            'hire_date': 'Fecha de Ingreso',
            'contract_type': 'Tipo de Contrato',
            'salary_type': 'Tipo de Salario',
            'basic_salary': 'Salario Básico',
            'transportation_allowance': 'Auxilio de Transporte',
            'eps': 'EPS',
            'pension_fund': 'Fondo de Pensiones',
            'arl': 'ARL',
            'compensation_fund': 'Caja de Compensación',
            'is_active': 'Activo',
            'termination_date': 'Fecha de Terminación'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            # Filtrar solo terceros marcados como empleados
            self.fields['third_party'].queryset = ThirdParty.objects.filter(
                company=self.company,
                is_employee=True,
                is_active=True
            ).order_by('first_name', 'razon_social')
    
    def clean_employee_number(self):
        """Validar que el número de empleado sea único por empresa"""
        employee_number = self.cleaned_data.get('employee_number')
        
        if self.company:
            existing = Employee.objects.filter(
                company=self.company,
                employee_number=employee_number
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Ya existe un empleado con el número {employee_number}')
        
        return employee_number
    
    def clean_basic_salary(self):
        """Validar salario básico"""
        basic_salary = self.cleaned_data.get('basic_salary')
        
        if basic_salary <= 0:
            raise ValidationError('El salario básico debe ser mayor a cero')
        
        # Validar salario mínimo (2024: $1,300,000)
        salario_minimo = Decimal('1300000')
        if basic_salary < salario_minimo:
            raise ValidationError(f'El salario no puede ser menor al mínimo legal: ${salario_minimo:,.0f}')
        
        return basic_salary
    
    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        termination_date = cleaned_data.get('termination_date')
        is_active = cleaned_data.get('is_active')
        
        # Si el empleado está inactivo, debe tener fecha de terminación
        if not is_active and not termination_date:
            self.add_error('termination_date', 
                'Los empleados inactivos deben tener fecha de terminación')
        
        # La fecha de terminación debe ser posterior a la de ingreso
        if hire_date and termination_date and termination_date <= hire_date:
            self.add_error('termination_date', 
                'La fecha de terminación debe ser posterior a la fecha de ingreso')
        
        return cleaned_data


class PayrollPeriodForm(forms.ModelForm):
    """Formulario para períodos de nómina"""
    
    class Meta:
        model = PayrollPeriod
        fields = [
            'period_type', 'year', 'month', 'period_number',
            'start_date', 'end_date', 'payment_date', 'description'
        ]
        widgets = {
            'period_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2030',
                'required': True
            }),
            'month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12'
            }),
            'period_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '24'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del período'
            })
        }
        labels = {
            'period_type': 'Tipo de Período',
            'year': 'Año',
            'month': 'Mes',
            'period_number': 'Número de Período',
            'start_date': 'Fecha Inicio',
            'end_date': 'Fecha Fin',
            'payment_date': 'Fecha de Pago',
            'description': 'Descripción'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        payment_date = cleaned_data.get('payment_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
        
        if payment_date and end_date:
            if payment_date < end_date:
                raise ValidationError('La fecha de pago debe ser igual o posterior a la fecha de fin del período')
        
        return cleaned_data


class PayrollForm(forms.ModelForm):
    """Formulario para nómina de empleado"""
    
    class Meta:
        model = Payroll
        fields = [
            'employee', 'payroll_period', 'worked_days', 'overtime_hours',
            'overtime_percentage', 'bonuses', 'commissions', 'other_income',
            'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'data-live-search': 'true'
            }),
            'payroll_period': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'worked_days': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '0',
                'max': '31',
                'value': '30'
            }),
            'overtime_hours': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.5',
                'min': '0',
                'value': '0'
            }),
            'overtime_percentage': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '25.00'
            }),
            'bonuses': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'commissions': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'other_income': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de la nómina'
            })
        }
        labels = {
            'employee': 'Empleado',
            'payroll_period': 'Período de Nómina',
            'worked_days': 'Días Trabajados',
            'overtime_hours': 'Horas Extra',
            'overtime_percentage': 'Porcentaje Horas Extra (%)',
            'bonuses': 'Bonificaciones',
            'commissions': 'Comisiones',
            'other_income': 'Otros Ingresos',
            'notes': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['employee'].queryset = Employee.objects.filter(
                company=self.company,
                is_active=True
            ).select_related('third_party').order_by(
                'third_party__first_name', 'third_party__razon_social'
            )
            
            self.fields['payroll_period'].queryset = PayrollPeriod.objects.filter(
                company=self.company,
                status='OPEN'
            ).order_by('-start_date')
    
    def clean_worked_days(self):
        """Validar días trabajados"""
        worked_days = self.cleaned_data.get('worked_days')
        
        if worked_days < 0:
            raise ValidationError('Los días trabajados no pueden ser negativos')
        
        if worked_days > 31:
            raise ValidationError('Los días trabajados no pueden exceder 31')
        
        return worked_days
    
    def clean_overtime_hours(self):
        """Validar horas extra"""
        overtime_hours = self.cleaned_data.get('overtime_hours')
        
        if overtime_hours < 0:
            raise ValidationError('Las horas extra no pueden ser negativas')
        
        # Máximo de horas extra según ley colombiana
        if overtime_hours > 48:
            raise ValidationError('Las horas extra no pueden exceder 48 por período')
        
        return overtime_hours


class SocialSecurityRateForm(forms.ModelForm):
    """Formulario para tarifas de seguridad social"""
    
    class Meta:
        model = SocialSecurityRate
        fields = [
            'concept', 'employee_rate', 'employer_rate', 'min_salary_base',
            'max_salary_base', 'effective_from', 'effective_to', 'is_active'
        ]
        widgets = {
            'concept': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'employee_rate': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.001',
                'min': '0',
                'max': '100',
                'placeholder': '0.000'
            }),
            'employer_rate': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'step': '0.001',
                'min': '0',
                'max': '100',
                'placeholder': '0.000'
            }),
            'min_salary_base': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'max_salary_base': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'concept': 'Concepto',
            'employee_rate': 'Tarifa Empleado (%)',
            'employer_rate': 'Tarifa Empleador (%)',
            'min_salary_base': 'Base Salarial Mínima',
            'max_salary_base': 'Base Salarial Máxima',
            'effective_from': 'Vigente Desde',
            'effective_to': 'Vigente Hasta',
            'is_active': 'Activo'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        effective_from = cleaned_data.get('effective_from')
        effective_to = cleaned_data.get('effective_to')
        min_salary_base = cleaned_data.get('min_salary_base')
        max_salary_base = cleaned_data.get('max_salary_base')
        
        if effective_from and effective_to:
            if effective_to <= effective_from:
                raise ValidationError('La fecha final debe ser posterior a la fecha inicial')
        
        if min_salary_base and max_salary_base:
            if max_salary_base <= min_salary_base:
                raise ValidationError('La base salarial máxima debe ser mayor a la mínima')
        
        return cleaned_data


class PayrollSearchForm(forms.Form):
    """Formulario de búsqueda de nóminas"""
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    period = forms.ModelChoiceField(
        queryset=PayrollPeriod.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('DRAFT', 'Borrador'),
            ('CALCULATED', 'Calculada'),
            ('APPROVED', 'Aprobada'),
            ('PAID', 'Pagada')
        ],
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
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company,
                is_active=True
            ).select_related('third_party').order_by(
                'third_party__first_name', 'third_party__razon_social'
            )
            
            self.fields['period'].queryset = PayrollPeriod.objects.filter(
                company=company
            ).order_by('-start_date')


# Formset para items de nómina
PayrollItemFormSet = forms.inlineformset_factory(
    Payroll,
    PayrollItem,
    fields=['concept', 'amount', 'is_deduction'],
    extra=0,
    can_delete=True,
    widgets={
        'concept': forms.Select(attrs={'class': 'form-select'}),
        'amount': forms.NumberInput(attrs={
            'class': 'form-control text-end',
            'step': '0.01'
        }),
        'is_deduction': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    }
)