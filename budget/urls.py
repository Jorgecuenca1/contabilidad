from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    # Dashboard
    path('', views.budget_dashboard, name='dashboard'),
    path('dashboard/', views.budget_dashboard, name='budget_dashboard'),
    
    # CDP - Certificado de Disponibilidad Presupuestal
    path('cdp/create/', views.cdp_create, name='cdp_create'),
    path('cdp/<int:pk>/', views.cdp_detail, name='cdp_detail'),
    
    # RP - Registro Presupuestal
    path('rp/create/', views.rp_create, name='rp_create'),
    path('rp/<int:pk>/', views.rp_detail, name='rp_detail'),
    
    # Obligaciones
    path('obligation/create/', views.obligation_create, name='obligation_create'),
    path('obligation/<int:pk>/', views.obligation_detail, name='obligation_detail'),
    
    # PAC - Plan Anual de Caja
    path('pac/', views.pac_management, name='pac_management'),
    
    # Reportes
    path('execution-report/', views.budget_execution_report, name='execution_report'),
    
    # Modificaciones Presupuestales
    path('modifications/', views.budget_modifications, name='modifications'),
    
    # API endpoints
    path('api/cdp/<int:cdp_id>/details/', views.api_cdp_details, name='api_cdp_details'),
    path('api/rubro/<int:rubro_id>/availability/', views.api_rubro_availability, name='api_rubro_availability'),
]