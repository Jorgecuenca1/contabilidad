"""
URLs del módulo core.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.user_profile, name='profile'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/new/', views.new_company, name='new_company'),
    path('companies/<uuid:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<uuid:company_id>/edit/', views.edit_company, name='edit_company'),
    path('select-company/', views.select_company, name='select_company'),
    path('api/companies/', views.company_selector_api, name='company_selector_api'),
    path('logout/', views.custom_logout, name='logout'),
]

