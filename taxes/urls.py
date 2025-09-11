"""
URLs para el módulo de impuestos.
"""

from django.urls import path
from . import views

app_name = 'taxes'

urlpatterns = [
    path('', views.taxes_dashboard, name='dashboard'),
    path('new-declaration/', views.new_tax_declaration, name='new_tax_declaration'),
    path('iva-declaration/', views.iva_declaration, name='iva_declaration'),
    path('retention-declaration/', views.retention_declaration, name='retention_declaration'),
    path('ica-declaration/', views.ica_declaration, name='ica_declaration'),
    path('retention-certificates/', views.retention_certificates, name='retention_certificates'),
    path('magnetic-media/', views.magnetic_media, name='magnetic_media'),
    path('tax-calendar/', views.tax_calendar, name='tax_calendar'),
    path('iva-report/', views.iva_report, name='iva_report'),
    path('renta-declaration/', views.renta_declaration, name='renta_declaration'),
]
