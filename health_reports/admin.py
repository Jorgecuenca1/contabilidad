"""
Admin del módulo Reportes Clínicos
"""

from django.contrib import admin
from .models import Health_reportsModule


@admin.register(Health_reportsModule)
class Health_reportsModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
