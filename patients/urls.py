"""
URLs del módulo de Pacientes
"""

from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Dashboard
    path('', views.patient_dashboard, name='dashboard'),

    # Pacientes
    path('list/', views.patient_list, name='patient_list'),
    path('create/', views.patient_create, name='patient_create'),
    path('<uuid:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<uuid:patient_id>/edit/', views.patient_edit, name='patient_edit'),

    # API
    path('api/search/', views.patient_search_api, name='patient_search_api'),
    path('api/check-duplicate/', views.check_duplicate_patient, name='check_duplicate_patient'),

    # EPS
    path('eps/', views.eps_list, name='eps_list'),
    path('eps/create/', views.eps_create, name='eps_create'),
]
