"""
URLs del módulo Imágenes Diagnósticas
"""

from django.urls import path
from . import views

app_name = 'imaging'

urlpatterns = [
    # Dashboard
    path('', views.imaging_dashboard, name='dashboard'),

    # Órdenes
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),

    # Estudios
    path('studies/', views.study_list, name='study_list'),
    path('studies/create/<uuid:order_id>/', views.study_create, name='study_create'),
    path('studies/<uuid:study_id>/', views.study_detail, name='study_detail'),

    # Informes
    path('reports/create/<uuid:study_id>/', views.report_create, name='report_create'),

    # Equipos
    path('equipment/', views.equipment_list, name='equipment_list'),

    # APIs
    path('api/equipment-by-modality/', views.api_equipment_by_modality, name='api_equipment_by_modality'),
]
