"""
URLs del módulo Oftalmología
"""

from django.urls import path
from . import views

app_name = 'ophthalmology'

urlpatterns = [
    # Dashboard
    path('', views.ophthalmology_dashboard, name='dashboard'),

    # Consultas
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),

    # Agudeza Visual
    path('consultations/<uuid:consultation_id>/visual-acuity/', views.visual_acuity_create, name='visual_acuity_create'),

    # Refracción
    path('consultations/<uuid:consultation_id>/refraction/', views.refraction_create, name='refraction_create'),

    # Prescripciones de Lentes
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/create/', views.prescription_create, name='prescription_create'),
    path('prescriptions/create/<uuid:consultation_id>/', views.prescription_create, name='prescription_create_from_consultation'),
    path('prescriptions/<uuid:prescription_id>/', views.prescription_detail, name='prescription_detail'),
]
