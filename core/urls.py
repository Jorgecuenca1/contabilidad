"""
URLs del módulo core.
"""

from django.urls import path
from . import views
from .views_company_selector import (
    company_selector, select_company, company_modules_config, 
    toggle_company_module, switch_company
)

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.user_profile, name='profile'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/new/', views.new_company, name='new_company'),
    path('companies/<uuid:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<uuid:company_id>/edit/', views.edit_company, name='edit_company'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Sistema selector de empresas
    path('company-selector/', company_selector, name='company_selector'),
    path('select-company/', select_company, name='select_company'),
    path('switch-company/', switch_company, name='switch_company'),
    
    # Configuración de módulos
    path('companies/<uuid:company_id>/modules/', company_modules_config, name='company_modules_config'),
    path('ajax/toggle-module/', toggle_company_module, name='toggle_company_module'),
    
    # APIs
    path('api/companies/', views.company_selector_api, name='company_selector_api'),
    path('modules/', views.manage_modules, name='manage_modules'),
]

