"""
URLs del módulo de Cardiología
"""

from django.urls import path
from . import views

app_name = 'cardiology'

urlpatterns = [
    # Dashboard
    path('', views.cardiology_dashboard, name='dashboard'),

    # Consultas Cardiológicas
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),
    path('consultations/<uuid:consultation_id>/update/', views.consultation_update, name='consultation_update'),

    # Electrocardiogramas (ECG)
    path('ecg/', views.ecg_list, name='ecg_list'),
    path('ecg/create/', views.ecg_create, name='ecg_create'),
    path('ecg/<uuid:ecg_id>/', views.ecg_detail, name='ecg_detail'),

    # Ecocardiogramas
    path('echo/', views.echo_list, name='echo_list'),
    path('echo/create/', views.echo_create, name='echo_create'),
    path('echo/<uuid:echo_id>/', views.echo_detail, name='echo_detail'),

    # Pruebas de Esfuerzo
    path('stress-test/', views.stress_test_list, name='stress_test_list'),
    path('stress-test/create/', views.stress_test_create, name='stress_test_create'),
    path('stress-test/<uuid:test_id>/', views.stress_test_detail, name='stress_test_detail'),

    # Holter
    path('holter/', views.holter_list, name='holter_list'),
    path('holter/create/', views.holter_create, name='holter_create'),
    path('holter/<uuid:holter_id>/', views.holter_detail, name='holter_detail'),

    # Evaluación de Riesgo Cardiovascular
    path('risk-assessment/', views.risk_assessment_list, name='risk_assessment_list'),
    path('risk-assessment/create/', views.risk_assessment_create, name='risk_assessment_create'),
    path('risk-assessment/<uuid:assessment_id>/', views.risk_assessment_detail, name='risk_assessment_detail'),

    # Perfil Cardiológico del Paciente
    path('patient/<uuid:patient_id>/profile/', views.patient_cardiology_profile, name='patient_profile'),
]
