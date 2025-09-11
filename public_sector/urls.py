"""
URLs para el módulo de sector público.
"""

from django.urls import path
from . import views

app_name = 'public_sector'

urlpatterns = [
    path('', views.public_sector_dashboard, name='dashboard'),
    path('chip-report/', views.generate_chip_report, name='chip_report'),
]

