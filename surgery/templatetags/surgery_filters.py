from django import template

register = template.Library()

@register.filter
def full_name(employee):
    """Retorna el nombre completo del empleado"""
    if employee:
        return f"{employee.first_name} {employee.last_name}".strip()
    return ""
