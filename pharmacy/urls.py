"""
URLs del módulo Farmacia
"""

from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Dashboard
    path('', views.pharmacy_dashboard, name='dashboard'),

    # Medicamentos
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/create/', views.medicine_create, name='medicine_create'),
    path('medicines/<uuid:medicine_id>/', views.medicine_detail, name='medicine_detail'),

    # Lotes
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),

    # Dispensación
    path('dispensing/', views.dispensing_list, name='dispensing_list'),
    path('dispensing/create/', views.dispensing_create, name='dispensing_create'),
    path('dispensing/<uuid:dispensing_id>/', views.dispensing_detail, name='dispensing_detail'),
    path('dispensing/<uuid:dispensing_id>/add-item/', views.dispensing_add_item, name='dispensing_add_item'),
    path('dispensing/<uuid:dispensing_id>/deliver/', views.dispensing_deliver, name='dispensing_deliver'),

    # Inventario
    path('inventory/report/', views.inventory_report, name='inventory_report'),

    # Alertas
    path('alerts/', views.alerts_list, name='alerts_list'),

    # API
    path('api/search-medicines/', views.api_search_medicines, name='api_search_medicines'),
]
