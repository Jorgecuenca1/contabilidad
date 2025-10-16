"""
URLs del módulo Autorizaciones EPS
Rutas para gestión de autorizaciones, contrarreferencias y adjuntos
"""

from django.urls import path
from . import views

app_name = 'authorizations'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Authorization Requests
    path('requests/', views.authorization_list, name='authorization_list'),
    path('requests/create/', views.authorization_create, name='authorization_create'),
    path('requests/<uuid:pk>/', views.authorization_detail, name='authorization_detail'),
    path('requests/<uuid:pk>/update/', views.authorization_update, name='authorization_update'),
    path('requests/<uuid:pk>/approve/', views.authorization_approve, name='authorization_approve'),
    path('requests/<uuid:pk>/deny/', views.authorization_deny, name='authorization_deny'),
    path('requests/<uuid:pk>/cancel/', views.authorization_cancel, name='authorization_cancel'),
    path('requests/<uuid:pk>/submit/', views.authorization_submit, name='authorization_submit'),

    # Counter-Referrals
    path('counter-referrals/', views.counter_referral_list, name='counter_referral_list'),
    path('counter-referrals/create/', views.counter_referral_create, name='counter_referral_create'),
    path('counter-referrals/<uuid:pk>/', views.counter_referral_detail, name='counter_referral_detail'),
    path('counter-referrals/<uuid:pk>/update/', views.counter_referral_update, name='counter_referral_update'),
    path('counter-referrals/<uuid:pk>/send/', views.counter_referral_send, name='counter_referral_send'),

    # Attachments
    path('attachments/upload/<str:type>/<uuid:object_id>/', views.attachment_upload, name='attachment_upload'),
    path('attachments/<uuid:pk>/download/', views.attachment_download, name='attachment_download'),
    path('attachments/<uuid:pk>/delete/', views.attachment_delete, name='attachment_delete'),

    # Usage
    path('usage/create/<uuid:authorization_id>/', views.usage_create, name='usage_create'),
    path('usage/list/<uuid:authorization_id>/', views.usage_list, name='usage_list'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # API
    path('api/patient/<uuid:patient_id>/', views.api_patient_info, name='api_patient_info'),
    path('api/authorization/<uuid:authorization_id>/', views.api_authorization_info, name='api_authorization_info'),
]
