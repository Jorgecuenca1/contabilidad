"""
Validadores personalizados para el sistema contable colombiano
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


def validate_nit(value):
    """
    Validar formato y dígito de verificación de NIT colombiano
    """
    if not value:
        return
    
    # Limpiar el NIT (remover espacios y guiones)
    nit_clean = str(value).strip().replace('-', '').replace(' ', '')
    
    # Validar que solo contenga números
    if not nit_clean.isdigit():
        raise ValidationError(
            _('El NIT debe contener solo números'),
            code='invalid_nit_format'
        )
    
    # Validar longitud
    if len(nit_clean) < 8 or len(nit_clean) > 15:
        raise ValidationError(
            _('El NIT debe tener entre 8 y 15 dígitos'),
            code='invalid_nit_length'
        )


def validate_nit_with_dv(nit, dv):
    """
    Validar NIT con su dígito de verificación
    """
    if not nit or not dv:
        return
    
    calculated_dv = calculate_nit_verification_digit(nit)
    
    if str(dv) != calculated_dv:
        raise ValidationError(
            _('El dígito de verificación es incorrecto. Debería ser: %(dv)s') % {
                'dv': calculated_dv
            },
            code='invalid_verification_digit'
        )


def calculate_nit_verification_digit(nit):
    """
    Calcular el dígito de verificación para un NIT colombiano
    """
    if not nit:
        return '0'
    
    # Limpiar el NIT
    nit_clean = str(nit).replace('-', '').replace(' ', '').strip()
    
    # Factores de multiplicación
    factors = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    
    # Calcular suma
    sum_total = 0
    nit_reversed = nit_clean[::-1]  # Invertir string
    
    for i, digit in enumerate(nit_reversed):
        if i < len(factors):
            sum_total += int(digit) * factors[i]
    
    # Calcular resto
    remainder = sum_total % 11
    
    # Calcular dígito de verificación
    if remainder > 1:
        return str(11 - remainder)
    else:
        return str(remainder)


def validate_cedula(value):
    """
    Validar formato de cédula de ciudadanía colombiana
    """
    if not value:
        return
    
    cedula = str(value).strip()
    
    # Debe ser numérica
    if not cedula.isdigit():
        raise ValidationError(
            _('La cédula debe contener solo números'),
            code='invalid_cedula_format'
        )
    
    # Longitud entre 6 and 12 dígitos
    if len(cedula) < 6 or len(cedula) > 12:
        raise ValidationError(
            _('La cédula debe tener entre 6 y 12 dígitos'),
            code='invalid_cedula_length'
        )


def validate_phone_colombia(value):
    """
    Validar formato de teléfono colombiano
    """
    if not value:
        return
    
    phone = str(value).strip()
    
    # Remover caracteres especiales
    phone_clean = re.sub(r'[^\d]', '', phone)
    
    # Teléfono fijo: 7 dígitos (sin indicativo) o 10 dígitos (con indicativo)
    # Celular: 10 dígitos
    if len(phone_clean) not in [7, 10]:
        raise ValidationError(
            _('El teléfono debe tener 7 dígitos (fijo) o 10 dígitos (celular con indicativo)'),
            code='invalid_phone_format'
        )
    
    # Si tiene 10 dígitos, debe comenzar con 3 (celular) o códigos de área válidos
    if len(phone_clean) == 10:
        valid_prefixes = ['1', '2', '3', '4', '5', '6', '7', '8']  # Códigos de área principales
        if phone_clean[0] not in valid_prefixes:
            raise ValidationError(
                _('Número de teléfono con formato inválido'),
                code='invalid_phone_prefix'
            )


def validate_ciiu_code(value):
    """
    Validar código CIIU (Clasificación Industrial Internacional Uniforme)
    """
    if not value:
        return
    
    ciiu = str(value).strip()
    
    # Debe ser de exactamente 4 dígitos
    if not ciiu.isdigit() or len(ciiu) != 4:
        raise ValidationError(
            _('El código CIIU debe tener exactamente 4 dígitos numéricos'),
            code='invalid_ciiu_format'
        )


def validate_bank_account(value):
    """
    Validar formato de cuenta bancaria colombiana
    """
    if not value:
        return
    
    account = str(value).strip().replace('-', '').replace(' ', '')
    
    # Debe ser numérica
    if not account.isdigit():
        raise ValidationError(
            _('La cuenta bancaria debe contener solo números'),
            code='invalid_bank_account_format'
        )
    
    # Longitud entre 8 y 20 dígitos
    if len(account) < 8 or len(account) > 20:
        raise ValidationError(
            _('La cuenta bancaria debe tener entre 8 y 20 dígitos'),
            code='invalid_bank_account_length'
        )


def validate_positive_decimal(value):
    """
    Validar que un valor decimal sea positivo
    """
    if value is not None and value < 0:
        raise ValidationError(
            _('Este valor debe ser positivo'),
            code='negative_value'
        )


def validate_percentage(value):
    """
    Validar que un valor esté en rango de porcentaje (0-100)
    """
    if value is not None:
        if value < 0 or value > 100:
            raise ValidationError(
                _('El porcentaje debe estar entre 0 and 100'),
                code='invalid_percentage'
            )


def validate_accounting_period_dates(start_date, end_date):
    """
    Validar fechas de período contable
    """
    if start_date and end_date:
        if end_date <= start_date:
            raise ValidationError(
                _('La fecha de fin debe ser posterior a la fecha de inicio'),
                code='invalid_date_range'
            )
        
        # Un período no debería ser mayor a un año
        days_diff = (end_date - start_date).days
        if days_diff > 366:  # Considerando años bisiestos
            raise ValidationError(
                _('Un período contable no debería exceder un año'),
                code='period_too_long'
            )


def validate_invoice_number_format(value):
    """
    Validar formato de número de factura colombiano
    Formato típico: PREFIJO-NUMERO (ej: FAC-001, SETP-0001)
    """
    if not value:
        return
    
    invoice_number = str(value).strip()
    
    # Patrón: Letras opcionales seguidas de guión y números
    pattern = r'^[A-Z]{0,10}-?\d{1,10}$'
    
    if not re.match(pattern, invoice_number):
        raise ValidationError(
            _('Formato de factura inválido. Use formato: PREFIJO-NUMERO'),
            code='invalid_invoice_format'
        )


def validate_double_entry_balance(debit_total, credit_total):
    """
    Validar que el asiento contable esté balanceado (partida doble)
    """
    if abs(debit_total - credit_total) > Decimal('0.01'):
        raise ValidationError(
            _('El asiento contable debe estar balanceado. Débitos: %(debit)s, Créditos: %(credit)s') % {
                'debit': debit_total,
                'credit': credit_total
            },
            code='unbalanced_entry'
        )


def validate_chart_account_code(value, parent_code=None):
    """
    Validar código de cuenta del plan contable colombiano (PUC)
    """
    if not value:
        return
    
    code = str(value).strip()
    
    # Debe ser numérico
    if not code.isdigit():
        raise ValidationError(
            _('El código de cuenta debe ser numérico'),
            code='invalid_account_code_format'
        )
    
    # Longitud entre 1 y 10 dígitos
    if len(code) < 1 or len(code) > 10:
        raise ValidationError(
            _('El código de cuenta debe tener entre 1 y 10 dígitos'),
            code='invalid_account_code_length'
        )
    
    # Si tiene cuenta padre, el código debe comenzar con el código del padre
    if parent_code and not code.startswith(parent_code):
        raise ValidationError(
            _('El código debe comenzar con el código de la cuenta padre: %(parent)s') % {
                'parent': parent_code
            },
            code='invalid_account_hierarchy'
        )


def validate_minimum_salary(value):
    """
    Validar que el salario sea al menos el mínimo legal vigente
    Salario mínimo 2024: $1,300,000 COP
    """
    if value is None:
        return
    
    minimum_salary = Decimal('1300000')  # Actualizar según año vigente
    
    if value < minimum_salary:
        raise ValidationError(
            _('El salario no puede ser menor al mínimo legal: $%(minimum)s') % {
                'minimum': f'{minimum_salary:,.0f}'
            },
            code='below_minimum_salary'
        )


def validate_working_days(value):
    """
    Validar días trabajados en el mes
    """
    if value is not None:
        if value < 0 or value > 31:
            raise ValidationError(
                _('Los días trabajados deben estar entre 0 y 31'),
                code='invalid_working_days'
            )


def validate_overtime_hours(value):
    """
    Validar horas extra según legislación colombiana
    Máximo 2 horas diarias, 12 semanales, 48 mensuales
    """
    if value is not None:
        if value < 0:
            raise ValidationError(
                _('Las horas extra no pueden ser negativas'),
                code='negative_overtime'
            )
        
        if value > 48:
            raise ValidationError(
                _('Las horas extra no pueden exceder 48 por período mensual'),
                code='excessive_overtime'
            )


def validate_tax_rate(value):
    """
    Validar tarifas de impuestos colombianos
    """
    if value is not None:
        # IVA válido: 0%, 5%, 19%
        valid_vat_rates = [Decimal('0'), Decimal('5'), Decimal('19')]
        
        if value not in valid_vat_rates:
            raise ValidationError(
                _('Tarifa de IVA inválida. Valores válidos: 0%, 5%, 19%'),
                code='invalid_vat_rate'
            )


def validate_withholding_rate(value):
    """
    Validar tarifas de retención en la fuente
    """
    if value is not None:
        if value < 0 or value > 35:  # Rango típico de retenciones
            raise ValidationError(
                _('La tarifa de retención debe estar entre 0% y 35%'),
                code='invalid_withholding_rate'
            )


def validate_colombian_currency_amount(value):
    """
    Validar montos en pesos colombianos
    """
    if value is not None:
        # Mínimo 1 peso
        if value < Decimal('1'):
            raise ValidationError(
                _('El monto mínimo es $1 peso'),
                code='amount_too_small'
            )
        
        # Máximo razonable (evitar overflow)
        max_amount = Decimal('999999999999.99')
        if value > max_amount:
            raise ValidationError(
                _('El monto excede el límite permitido'),
                code='amount_too_large'
            )