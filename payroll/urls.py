"""
URLs para el módulo de nómina.
"""

from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('new-employee/', views.new_employee, name='new_employee'),
    path('liquidate/', views.liquidate_payroll, name='liquidate_payroll'),
    path('liquidate/<uuid:period_id>/', views.liquidate_payroll, name='liquidate_payroll'),
    path('certificate/', views.generate_certificate, name='certificate'),
    path('certificate/<uuid:employee_id>/', views.generate_certificate, name='certificate'),
    path('final-liquidation/', views.final_liquidation, name='final_liquidation'),
    path('final-liquidation/<uuid:employee_id>/', views.final_liquidation, name='final_liquidation'),
    path('pila/', views.generate_pila, name='pila'),
    path('reports/', views.payroll_reports, name='reports'),
]
