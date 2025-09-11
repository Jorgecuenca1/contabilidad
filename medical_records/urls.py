"""
URLs del módulo de Historia Clínica.
"""

from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    # Dashboard
    path('', views.medical_records_dashboard, name='dashboard'),
    
    # Historias clínicas
    path('records/', views.medical_records_list, name='list'),
    path('records/new/', views.new_medical_record, name='new_record'),
    path('records/<uuid:record_id>/', views.medical_record_detail, name='record_detail'),
    
    # Consultas
    path('consultations/', views.consultations_list, name='consultations_list'),
    path('consultations/new/', views.new_consultation, name='new_consultation'),
    path('consultations/new/<uuid:record_id>/', views.new_consultation, name='new_consultation_for_record'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),
]