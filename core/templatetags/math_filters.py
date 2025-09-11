"""
Filtros matemáticos personalizados para templates Django
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        arg_float = float(arg)
        if arg_float == 0:
            return 0
        return float(value) / arg_float
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def sub(value, arg):
    """Resta el argumento del valor"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calcula el porcentaje del valor respecto al total"""
    try:
        total_float = float(total)
        if total_float == 0:
            return 0
        return (float(value) / total_float) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def abs_value(value):
    """Valor absoluto"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def round_number(value, decimals=0):
    """Redondea un número a los decimales especificados"""
    try:
        return round(float(value), int(decimals))
    except (ValueError, TypeError):
        return 0