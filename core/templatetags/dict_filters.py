"""
Filtros personalizados para diccionarios en templates de Django.
"""
from django import template

register = template.Library()


@register.filter(name='lookup')
def lookup(dictionary, key):
    """
    Permite acceder a valores de un diccionario en templates.

    Uso: {{ my_dict|lookup:'key_name' }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, None)


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Alternativa para acceder a valores de diccionario.

    Uso: {{ my_dict|get_item:'key_name' }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, [])
