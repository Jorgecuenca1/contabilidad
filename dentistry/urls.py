"""
URLs del módulo Odontología
"""

from django.urls import path
from . import views

app_name = 'dentistry'

urlpatterns = [
    # Dashboard
    path('', views.dentistry_dashboard, name='dashboard'),

    # Consultas Odontológicas
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),

    # Odontogramas
    path('odontograms/', views.odontogram_list, name='odontogram_list'),
    path('odontograms/create/<uuid:patient_id>/', views.odontogram_create, name='odontogram_create'),
    path('odontograms/<uuid:odontogram_id>/', views.odontogram_detail, name='odontogram_detail'),
    path('odontograms/<uuid:odontogram_id>/update-tooth/', views.odontogram_tooth_update, name='odontogram_tooth_update'),

    # Planes de Tratamiento
    path('treatment-plans/', views.treatment_plan_list, name='treatment_plan_list'),
    path('treatment-plans/create/', views.treatment_plan_create, name='treatment_plan_create'),
    path('treatment-plans/<uuid:plan_id>/', views.treatment_plan_detail, name='treatment_plan_detail'),
    path('treatment-plans/<uuid:plan_id>/add-item/', views.treatment_plan_item_add, name='treatment_plan_item_add'),

    # Procedimientos Realizados
    path('procedure-records/', views.procedure_record_list, name='procedure_record_list'),
    path('procedure-records/create/', views.procedure_record_create, name='procedure_record_create'),
    path('procedure-records/<uuid:record_id>/', views.procedure_record_detail, name='procedure_record_detail'),

    # APIs
    path('api/patient-consultations/', views.api_patient_consultations, name='api_patient_consultations'),
    path('api/patient-odontograms/', views.api_patient_odontograms, name='api_patient_odontograms'),
]
