"""
URLs del módulo de Diagnósticos CIE-10
Sistema completo de gestión de catálogo de diagnósticos médicos
"""

from django.urls import path
from . import views

app_name = 'diagnostics'

urlpatterns = [
    # Dashboard
    path('', views.diagnostics_dashboard, name='dashboard'),

    # Diagnósticos - Lista y Búsqueda
    path('diagnoses/', views.diagnosis_list, name='diagnosis_list'),
    path('diagnoses/<uuid:diagnosis_id>/', views.diagnosis_detail, name='diagnosis_detail'),

    # API de búsqueda (AJAX)
    path('api/search/', views.diagnosis_search_api, name='diagnosis_search_api'),

    # Favoritos
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('diagnoses/<uuid:diagnosis_id>/toggle-favorite/', views.diagnosis_toggle_favorite, name='diagnosis_toggle_favorite'),

    # Importación
    path('import/', views.import_form, name='import_form'),
    path('import/process/', views.import_process, name='import_process'),
    path('import/logs/', views.import_logs_list, name='import_logs_list'),
    path('import/logs/<uuid:log_id>/', views.import_log_detail, name='import_log_detail'),

    # Exportación
    path('export/csv/', views.export_diagnoses_csv, name='export_diagnoses_csv'),

    # Versiones CIE-10
    path('versions/', views.versions_list, name='versions_list'),
    path('versions/<uuid:version_id>/', views.version_detail, name='version_detail'),
]
