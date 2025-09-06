"""
URLs para el módulo de nómina.
"""

from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('new-employee/', views.new_employee, name='new_employee'),
]
