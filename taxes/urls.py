"""
URLs para el módulo de impuestos.
"""

from django.urls import path
from . import views

app_name = 'taxes'

urlpatterns = [
    path('', views.taxes_dashboard, name='dashboard'),
    path('new-declaration/', views.new_tax_declaration, name='new_tax_declaration'),
]
