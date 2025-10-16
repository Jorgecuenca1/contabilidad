"""
URLs del módulo Psicología
"""

from django.urls import path
from . import views

app_name = 'psychology'

urlpatterns = [
    # Dashboard
    path('', views.psychology_dashboard, name='dashboard'),

    # Consultas
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),

    # Sesiones Terapéuticas
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/create/<uuid:consultation_id>/', views.session_create, name='session_create_from_consultation'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),

    # Planes de Tratamiento
    path('treatment-plans/', views.treatment_plan_list, name='treatment_plan_list'),
    path('treatment-plans/create/<uuid:consultation_id>/', views.treatment_plan_create, name='treatment_plan_create'),
    path('treatment-plans/<uuid:plan_id>/', views.treatment_plan_detail, name='treatment_plan_detail'),

    # Evaluaciones Psicológicas
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/create/', views.assessment_create, name='assessment_create'),
    path('assessments/create/<uuid:consultation_id>/', views.assessment_create, name='assessment_create_from_consultation'),
    path('assessments/<uuid:assessment_id>/', views.assessment_detail, name='assessment_detail'),
]
