"""
Admin del módulo Quirófano
"""

from django.contrib import admin
from .models import (
    OperatingRoom, SurgicalProcedure, Surgery,
    AnesthesiaNote, SurgicalSupply, PostOperativeNote
)


@admin.register(OperatingRoom)
class OperatingRoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_name', 'room_type', 'status', 'is_active']
    list_filter = ['status', 'room_type', 'is_active']
    search_fields = ['room_number', 'room_name']


@admin.register(SurgicalProcedure)
class SurgicalProcedureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'specialty', 'complexity', 'is_active']
    list_filter = ['specialty', 'complexity', 'is_active']
    search_fields = ['code', 'name']


@admin.register(Surgery)
class SurgeryAdmin(admin.ModelAdmin):
    list_display = ['surgery_number', 'patient', 'surgical_procedure', 'scheduled_date', 'status']
    list_filter = ['status', 'urgency', 'scheduled_date']
    search_fields = ['surgery_number', 'patient__nombre']


@admin.register(AnesthesiaNote)
class AnesthesiaNoteAdmin(admin.ModelAdmin):
    list_display = ['surgery', 'asa_classification', 'anesthesia_type', 'created_at']
    list_filter = ['asa_classification', 'anesthesia_type']


@admin.register(SurgicalSupply)
class SurgicalSupplyAdmin(admin.ModelAdmin):
    list_display = ['surgery', 'name', 'supply_type', 'lot_number', 'quantity']
    list_filter = ['supply_type']
    search_fields = ['name', 'lot_number']


@admin.register(PostOperativeNote)
class PostOperativeNoteAdmin(admin.ModelAdmin):
    list_display = ['surgery', 'patient_condition', 'pain_scale', 'created_at']
    list_filter = ['created_at']
