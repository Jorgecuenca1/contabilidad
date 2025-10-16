"""
URLs del módulo RIPS
"""

from django.urls import path
from . import views

app_name = 'rips'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Episodios de atención
    path('episodios/', views.episode_list, name='episode_list'),
    path('episodios/crear/', views.episode_create, name='episode_create'),
    path('episodios/<uuid:episode_id>/', views.episode_detail, name='episode_detail'),
    path('episodios/<uuid:episode_id>/cerrar/', views.episode_close, name='episode_close'),
    path('episodios/<uuid:episode_id>/facturar/', views.episode_generate_invoice, name='episode_generate_invoice'),

    # Archivos RIPS
    path('archivos/', views.rips_list, name='rips_list'),
    path('generar/', views.rips_generate, name='rips_generate'),
    path('descargar/<uuid:invoice_id>/', views.rips_download, name='rips_download'),

    # API
    path('api/buscar-pacientes/', views.api_search_patients, name='api_search_patients'),
]
