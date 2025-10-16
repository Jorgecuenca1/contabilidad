"""
URLs del módulo Hospitalización
"""

from django.urls import path
from . import views

app_name = 'hospitalization'

urlpatterns = [
    # Dashboard
    path('', views.hospitalization_dashboard, name='dashboard'),

    # Pabellones
    path('wards/', views.ward_list, name='ward_list'),
    path('wards/<uuid:ward_id>/', views.ward_detail, name='ward_detail'),

    # Camas
    path('beds/', views.bed_list, name='bed_list'),
    path('beds/<uuid:bed_id>/', views.bed_detail, name='bed_detail'),

    # Admisiones
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/create/', views.admission_create, name='admission_create'),
    path('admissions/<uuid:admission_id>/', views.admission_detail, name='admission_detail'),
    path('admissions/<uuid:admission_id>/discharge/', views.admission_discharge, name='admission_discharge'),

    # Evoluciones médicas
    path('admissions/<uuid:admission_id>/evolution/create/', views.evolution_create, name='evolution_create'),

    # Órdenes médicas
    path('admissions/<uuid:admission_id>/order/create/', views.order_create, name='order_create'),
    path('orders/<uuid:order_id>/execute/', views.order_execute, name='order_execute'),

    # Reportes
    path('reports/occupancy/', views.occupancy_report, name='occupancy_report'),

    # APIs
    path('api/available-beds/', views.api_available_beds, name='api_available_beds'),
    path('api/bed-status/<uuid:bed_id>/', views.api_bed_status, name='api_bed_status'),
]
