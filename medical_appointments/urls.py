"""
URLs del módulo de Citas Médicas.
"""

from django.urls import path
from . import views

app_name = 'medical_appointments'

urlpatterns = [
    # Dashboard
    path('', views.appointments_dashboard, name='dashboard'),
    
    # Citas médicas
    path('appointments/', views.appointments_list, name='list'),
    path('appointments/new/', views.new_appointment, name='new_appointment'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    
    # APIs para formulario de citas
    path('api/doctors-by-specialty/', views.get_doctors_by_specialty, name='doctors_by_specialty'),
    path('api/available-slots/', views.get_available_slots, name='available_slots'),
    
    # Horarios de médicos
    path('schedules/', views.doctor_schedules, name='schedules'),
    
    # Lista de espera
    path('waiting-list/', views.waiting_list, name='waiting_list'),
]