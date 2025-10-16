"""
URLs del módulo Reportes Clínicos
"""

from django.urls import path
from . import views

app_name = 'health_reports'

urlpatterns = [
    path('', views.index, name='index'),
]
