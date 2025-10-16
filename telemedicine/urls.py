"""
URLs del módulo Telemedicina
Consultas virtuales, atención domiciliaria y firma digital
"""

from django.urls import path
from . import views

app_name = 'telemedicine'

urlpatterns = [
    # Dashboard
    path('', views.telemedicine_dashboard, name='dashboard'),

    # Citas de Telemedicina
    path('appointments/', views.appointments_list, name='appointments_list'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<uuid:appointment_id>/update-status/', views.appointment_update_status, name='appointment_update_status'),

    # Consultas Virtuales
    path('virtual-consultations/', views.virtual_consultations_list, name='virtual_consultations_list'),
    path('virtual-consultations/create/', views.virtual_consultation_create, name='virtual_consultation_create'),
    path('virtual-consultations/<uuid:consultation_id>/', views.virtual_consultation_detail, name='virtual_consultation_detail'),

    # Atención Domiciliaria
    path('home-care-visits/', views.home_care_visits_list, name='home_care_visits_list'),
    path('home-care-visits/create/', views.home_care_visit_create, name='home_care_visit_create'),
    path('home-care-visits/<uuid:visit_id>/', views.home_care_visit_detail, name='home_care_visit_detail'),

    # Documentos Médicos
    path('documents/', views.medical_documents_list, name='medical_documents_list'),
    path('documents/create/', views.medical_document_create, name='medical_document_create'),
    path('documents/<uuid:document_id>/', views.medical_document_detail, name='medical_document_detail'),
    path('documents/<uuid:document_id>/sign/', views.medical_document_sign, name='medical_document_sign'),

    # Estadísticas
    path('statistics/', views.telemedicine_statistics, name='statistics'),

    # API/AJAX
    path('api/patient/<uuid:patient_id>/', views.get_patient_info, name='get_patient_info'),
]
