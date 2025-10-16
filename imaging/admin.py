"""
Admin del módulo Imágenes Diagnósticas
"""

from django.contrib import admin
from .models import (
    ImagingModality, ImagingEquipment, ImagingOrder, ImagingStudy,
    ImagingReport, ImagingImage, QualityControlCheck
)


@admin.register(ImagingModality)
class ImagingModalityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'base_price', 'requires_contrast', 'requires_fasting', 'is_active')
    list_filter = ('requires_contrast', 'requires_sedation', 'requires_fasting', 'is_active')
    search_fields = ('code', 'name', 'description')


@admin.register(ImagingEquipment)
class ImagingEquipmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'modality', 'status', 'room_location', 'is_active')
    list_filter = ('modality', 'status', 'is_active')
    search_fields = ('code', 'name', 'manufacturer', 'model', 'serial_number')


@admin.register(ImagingOrder)
class ImagingOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'patient', 'modality', 'priority', 'status', 'ordering_date', 'ordering_physician')
    list_filter = ('status', 'priority', 'modality', 'ordering_date')
    search_fields = ('order_number', 'patient__third_party__name', 'patient__medical_record_number')
    date_hierarchy = 'ordering_date'


@admin.register(ImagingStudy)
class ImagingStudyAdmin(admin.ModelAdmin):
    list_display = ('study_number', 'order', 'equipment_used', 'performing_technologist', 'study_date', 'status')
    list_filter = ('status', 'contrast_used', 'dicom_stored', 'study_date')
    search_fields = ('study_number', 'order__order_number', 'study_instance_uid')
    date_hierarchy = 'study_date'


@admin.register(ImagingReport)
class ImagingReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'study', 'radiologist', 'report_date', 'status', 'is_critical', 'is_normal')
    list_filter = ('status', 'is_critical', 'is_normal', 'digitally_signed', 'report_date')
    search_fields = ('report_number', 'study__study_number', 'findings', 'impression')
    date_hierarchy = 'report_date'


@admin.register(ImagingImage)
class ImagingImageAdmin(admin.ModelAdmin):
    list_display = ('study', 'image_type', 'created_at')
    list_filter = ('image_type', 'created_at')
    search_fields = ('study__study_number', 'sop_instance_uid')


@admin.register(QualityControlCheck)
class QualityControlCheckAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'check_date', 'performed_by', 'check_type', 'result')
    list_filter = ('result', 'check_type', 'check_date')
    search_fields = ('equipment__name', 'equipment__code', 'performed_by__username')
    date_hierarchy = 'check_date'
