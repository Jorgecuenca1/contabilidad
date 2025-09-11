"""
URLs del módulo de Laboratorio Clínico.
"""

from django.urls import path
from . import views

app_name = 'laboratory'

urlpatterns = [
    # Dashboard
    path('', views.laboratory_dashboard, name='dashboard'),
    
    # Órdenes de laboratorio
    path('orders/', views.lab_orders_list, name='orders_list'),
    path('orders/new/', views.new_lab_order, name='new_order'),
    path('orders/<uuid:order_id>/', views.lab_order_detail, name='order_detail'),
    
    # Resultados
    path('results/', views.lab_results_list, name='results_list'),
    path('results/<uuid:result_id>/', views.lab_result_detail, name='result_detail'),
    
    # Exámenes
    path('tests/', views.lab_tests_catalog, name='tests_catalog'),
    path('tests/<uuid:test_id>/', views.lab_test_detail, name='test_detail'),
    
    # Secciones de laboratorio
    path('sections/', views.lab_sections, name='sections'),
]