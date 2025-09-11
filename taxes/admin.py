"""
Configuración del admin para los modelos de impuestos.
"""

from django.contrib import admin
from .models_tax_types import TaxType, TaxCalendar


@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    """Admin para tipos de impuesto."""
    list_display = ('code', 'name', 'category', 'rate', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(TaxCalendar)
class TaxCalendarAdmin(admin.ModelAdmin):
    """Admin para calendario tributario."""
    list_display = ('id', 'due_date')
    list_filter = ('due_date',)
    search_fields = ('id',)


# Placeholder admin for TaxDeclaration (model needs to be created)
class TaxDeclarationAdmin(admin.ModelAdmin):
    """Placeholder admin for tax declarations."""
    list_display = ('id',)
    
    class Meta:
        verbose_name = 'Declaración Tributaria'
        verbose_name_plural = 'Declaraciones Tributarias'

# We'll register this when the model exists
# admin.site.register(TaxDeclaration, TaxDeclarationAdmin)
