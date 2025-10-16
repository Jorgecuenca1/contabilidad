"""
URLs del módulo Urgencias
Sistema de urgencias médicas con triage, admisión y atención
"""

from django.urls import path
from . import views

app_name = 'emergency'

urlpatterns = [
    # Dashboard
    path('', views.emergency_dashboard, name='dashboard'),

    # Triage
    path('triage/', views.triage_list, name='triage_list'),
    path('triage/create/', views.triage_create, name='triage_create'),
    path('triage/<uuid:triage_id>/', views.triage_detail, name='triage_detail'),
    path('triage/<uuid:triage_id>/update/', views.triage_update, name='triage_update'),

    # Admisiones
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/create/', views.admission_create, name='admission_create'),
    path('admissions/<uuid:admission_id>/', views.admission_detail, name='admission_detail'),
    path('admissions/<uuid:admission_id>/update-status/', views.admission_update_status, name='admission_update_status'),

    # Signos Vitales
    path('admissions/<uuid:admission_id>/vital-signs/', views.vital_signs_list, name='vital_signs_list'),
    path('admissions/<uuid:admission_id>/vital-signs/create/', views.vital_signs_create, name='vital_signs_create'),
    path('admissions/<uuid:admission_id>/vital-signs/chart/', views.vital_signs_chart, name='vital_signs_chart'),

    # Atención
    path('admissions/<uuid:admission_id>/attention/create/', views.attention_create, name='attention_create'),
    path('attention/<uuid:attention_id>/', views.attention_detail, name='attention_detail'),
    path('attention/<uuid:attention_id>/update/', views.attention_update, name='attention_update'),

    # Procedimientos
    path('attention/<uuid:attention_id>/procedures/', views.procedure_list, name='procedure_list'),
    path('attention/<uuid:attention_id>/procedures/create/', views.procedure_create, name='procedure_create'),

    # Alta
    path('admissions/<uuid:admission_id>/discharge/create/', views.discharge_create, name='discharge_create'),
    path('discharge/<uuid:discharge_id>/', views.discharge_detail, name='discharge_detail'),

    # API/AJAX
    path('api/triage/<uuid:triage_id>/', views.get_triage_info, name='get_triage_info'),
]
