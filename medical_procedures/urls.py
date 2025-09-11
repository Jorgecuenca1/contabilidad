"""
URLs del módulo de Procedimientos Médicos.
"""

from django.urls import path
from . import views

app_name = 'medical_procedures'

urlpatterns = [
    # Dashboard
    path('', views.procedures_dashboard, name='dashboard'),
    
    # Procedimientos médicos
    path('procedures/', views.procedures_list, name='list'),
    path('procedures/new/', views.new_procedure, name='new_procedure'),
    path('procedures/<uuid:procedure_id>/', views.procedure_detail, name='procedure_detail'),
    
    # Catálogo CUPS
    path('cups/', views.cups_catalog, name='cups_catalog'),
    path('cups/<uuid:cups_id>/', views.cups_detail, name='cups_detail'),
    
    # Plantillas
    path('templates/', views.procedure_templates, name='templates'),
    
    # APIs
    path('api/cups-by-category/', views.get_cups_by_category, name='cups_by_category'),
]