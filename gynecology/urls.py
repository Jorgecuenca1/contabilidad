"""
URLs del módulo de Ginecología.
"""

from django.urls import path
from . import views

app_name = 'gynecology'

urlpatterns = [
    # Dashboard
    path('', views.gynecology_dashboard, name='dashboard'),
    
    # Pacientes
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.new_patient, name='new_patient'),
    path('patients/<uuid:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # Citas
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.new_appointment, name='new_appointment'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    
    # Procedimientos
    path('procedures/', views.procedures_list, name='procedures_list'),
    path('procedures/new/', views.new_procedure, name='new_procedure'),
    path('procedures/<uuid:procedure_id>/', views.procedure_detail, name='procedure_detail'),
]