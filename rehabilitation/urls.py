"""
URLs del módulo Rehabilitación
"""

from django.urls import path
from . import views

app_name = 'rehabilitation'

urlpatterns = [
    # Dashboard
    path('', views.rehabilitation_dashboard, name='dashboard'),

    # Consultas
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/<uuid:consultation_id>/', views.consultation_detail, name='consultation_detail'),

    # Evaluación Física
    path('consultations/<uuid:consultation_id>/assessment/', views.physical_assessment_create, name='physical_assessment_create'),

    # Planes de Rehabilitación
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/<uuid:consultation_id>/', views.plan_create, name='plan_create'),
    path('plans/<uuid:plan_id>/', views.plan_detail, name='plan_detail'),

    # Sesiones de Rehabilitación
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/<uuid:plan_id>/', views.session_create, name='session_create'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),

    # Ejercicios
    path('plans/<uuid:plan_id>/exercises/', views.exercise_list, name='exercise_list'),
    path('plans/<uuid:plan_id>/exercises/create/', views.exercise_create, name='exercise_create'),

    # Mediciones de Progreso
    path('plans/<uuid:plan_id>/progress/create/', views.progress_measurement_create, name='progress_measurement_create'),
]
