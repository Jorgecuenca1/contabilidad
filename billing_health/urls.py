"""
URLs del módulo Facturación Salud
Sistema de facturación de servicios de salud con integración RIPS
"""

from django.urls import path
from . import views

app_name = 'billing_health'

urlpatterns = [
    # Dashboard
    path('', views.billing_dashboard, name='dashboard'),

    # Facturas
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<uuid:invoice_id>/', views.invoice_detail, name='invoice_detail'),

    # Items de factura
    path('invoices/<uuid:invoice_id>/items/add/', views.invoice_add_item, name='invoice_add_item'),
    path('invoices/<uuid:invoice_id>/items/<uuid:item_id>/delete/', views.invoice_delete_item, name='invoice_delete_item'),

    # Acciones de factura
    path('invoices/<uuid:invoice_id>/approve/', views.invoice_approve, name='invoice_approve'),

    # Pagos
    path('invoices/<uuid:invoice_id>/payments/add/', views.invoice_add_payment, name='invoice_add_payment'),

    # Glosas
    path('invoices/<uuid:invoice_id>/glosas/add/', views.invoice_add_glosa, name='invoice_add_glosa'),
    path('glosas/<uuid:glosa_id>/respond/', views.glosa_respond, name='glosa_respond'),

    # RIPS
    path('invoices/<uuid:invoice_id>/generate-rips/', views.generate_rips, name='generate_rips'),

    # Tarifarios
    path('tariffs/', views.tariff_list, name='tariff_list'),
    path('tariffs/create/', views.tariff_create, name='tariff_create'),

    # API endpoints
    path('api/patients/search/', views.api_search_patients, name='api_search_patients'),
    path('api/services/search/', views.api_search_services, name='api_search_services'),
    path('api/patient/unbilled-services/', views.api_get_patient_unbilled_services, name='api_patient_unbilled_services'),
]
