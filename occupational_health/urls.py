"""
URLs del módulo Salud Ocupacional
"""

from django.urls import path
from . import views

app_name = 'occupational_health'

urlpatterns = [
    # Dashboard
    path('', views.occupational_health_dashboard, name='dashboard'),

    # Exámenes Ocupacionales
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<uuid:exam_id>/', views.exam_detail, name='exam_detail'),
    path('exams/<uuid:exam_id>/update-status/', views.exam_update_status, name='exam_update_status'),

    # Exámenes de Laboratorio
    path('exams/<uuid:exam_id>/lab-test/create/', views.lab_test_create, name='lab_test_create'),
    path('lab-tests/<uuid:test_id>/', views.lab_test_detail, name='lab_test_detail'),

    # Aptitud Laboral
    path('aptitudes/', views.aptitude_list, name='aptitude_list'),
    path('exams/<uuid:exam_id>/aptitude/create/', views.aptitude_create, name='aptitude_create'),
    path('aptitudes/<uuid:aptitude_id>/', views.aptitude_detail, name='aptitude_detail'),

    # Riesgos Ocupacionales
    path('risks/', views.risk_list, name='risk_list'),
    path('exams/<uuid:exam_id>/risk/create/', views.risk_create, name='risk_create'),

    # Recomendaciones de Salud
    path('recommendations/', views.recommendation_list, name='recommendation_list'),
    path('exams/<uuid:exam_id>/recommendation/create/', views.recommendation_create, name='recommendation_create'),

    # Reportes Empresariales
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<uuid:report_id>/update-status/', views.report_update_status, name='report_update_status'),
]
