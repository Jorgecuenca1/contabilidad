"""
URLs del módulo Quirófano
"""

from django.urls import path
from . import views

app_name = 'surgery'

urlpatterns = [
    # Dashboard
    path('', views.surgery_dashboard, name='dashboard'),

    # Operating Rooms
    path('operating-rooms/', views.operating_room_list, name='operating_room_list'),
    path('operating-rooms/create/', views.operating_room_create, name='operating_room_create'),
    path('operating-rooms/<uuid:room_id>/', views.operating_room_detail, name='operating_room_detail'),
    path('operating-rooms/<uuid:room_id>/update/', views.operating_room_update, name='operating_room_update'),

    # Surgical Procedures
    path('procedures/', views.surgical_procedure_list, name='surgical_procedure_list'),
    path('procedures/create/', views.surgical_procedure_create, name='surgical_procedure_create'),
    path('procedures/<uuid:procedure_id>/', views.surgical_procedure_detail, name='surgical_procedure_detail'),
    path('procedures/<uuid:procedure_id>/update/', views.surgical_procedure_update, name='surgical_procedure_update'),

    # Surgeries
    path('surgeries/', views.surgery_list, name='surgery_list'),
    path('surgeries/create/', views.surgery_create, name='surgery_create'),
    path('surgeries/<uuid:surgery_id>/', views.surgery_detail, name='surgery_detail'),
    path('surgeries/<uuid:surgery_id>/update/', views.surgery_update, name='surgery_update'),

    # Anesthesia Notes
    path('surgeries/<uuid:surgery_id>/anesthesia-note/create/', views.anesthesia_note_create, name='anesthesia_note_create'),
    path('surgeries/<uuid:surgery_id>/anesthesia-note/', views.anesthesia_note_detail, name='anesthesia_note_detail'),
    path('surgeries/<uuid:surgery_id>/anesthesia-note/update/', views.anesthesia_note_update, name='anesthesia_note_update'),

    # Surgical Supplies
    path('surgeries/<uuid:surgery_id>/supplies/', views.surgical_supply_list, name='surgical_supply_list'),
    path('surgeries/<uuid:surgery_id>/supplies/add/', views.surgical_supply_add, name='surgical_supply_add'),

    # Post-Operative Notes
    path('surgeries/<uuid:surgery_id>/postop-note/create/', views.postop_note_create, name='postop_note_create'),
    path('surgeries/<uuid:surgery_id>/postop-note/', views.postop_note_detail, name='postop_note_detail'),
    path('surgeries/<uuid:surgery_id>/postop-note/update/', views.postop_note_update, name='postop_note_update'),
]
