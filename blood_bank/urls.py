"""
URLs del módulo Banco de Sangre
"""

from django.urls import path
from . import views

app_name = 'blood_bank'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Donantes
    path('donors/', views.donor_list, name='donor_list'),
    path('donors/create/', views.donor_create, name='donor_create'),
    path('donors/<uuid:donor_id>/', views.donor_detail, name='donor_detail'),

    # Donaciones
    path('donations/', views.donation_list, name='donation_list'),
    path('donations/create/', views.donation_create, name='donation_create'),
    path('donations/<uuid:donation_id>/', views.donation_detail, name='donation_detail'),

    # Hemocomponentes
    path('components/', views.component_list, name='component_list'),
    path('components/<uuid:component_id>/', views.component_detail, name='component_detail'),

    # Transfusiones
    path('transfusions/', views.transfusion_list, name='transfusion_list'),
    path('transfusions/<uuid:transfusion_id>/', views.transfusion_detail, name='transfusion_detail'),

    # Reportes
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
]
