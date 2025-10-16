"""
Admin del módulo Banco de Sangre
"""

from django.contrib import admin
from .models import (
    Donor, Donation, BloodComponent, ScreeningTest,
    CompatibilityTest, Transfusion
)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ['donor_code', 'get_donor_name', 'blood_type', 'donor_type', 'status', 'total_donations']
    list_filter = ['blood_type', 'donor_type', 'status']
    search_fields = ['donor_code', 'document_number', 'first_name', 'last_name']

    def get_donor_name(self, obj):
        if obj.third_party:
            return obj.third_party.get_full_name()
        return f"{obj.first_name} {obj.last_name}"
    get_donor_name.short_description = 'Nombre'


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donation_number', 'donor', 'donation_type', 'donation_date', 'status']
    list_filter = ['donation_type', 'status', 'adverse_reaction']
    search_fields = ['donation_number', 'donor__donor_code']
    date_hierarchy = 'donation_date'


@admin.register(BloodComponent)
class BloodComponentAdmin(admin.ModelAdmin):
    list_display = ['component_code', 'component_type', 'blood_type', 'volume_ml', 'status', 'expiration_date']
    list_filter = ['component_type', 'blood_type', 'status']
    search_fields = ['component_code']
    date_hierarchy = 'expiration_date'


@admin.register(ScreeningTest)
class ScreeningTestAdmin(admin.ModelAdmin):
    list_display = ['donation', 'test_type', 'result', 'test_date']
    list_filter = ['test_type', 'result']
    date_hierarchy = 'test_date'


@admin.register(CompatibilityTest)
class CompatibilityTestAdmin(admin.ModelAdmin):
    list_display = ['patient', 'blood_component', 'test_type', 'result', 'test_date']
    list_filter = ['test_type', 'result']
    date_hierarchy = 'test_date'


@admin.register(Transfusion)
class TransfusionAdmin(admin.ModelAdmin):
    list_display = ['transfusion_number', 'patient', 'blood_component', 'status', 'adverse_reaction']
    list_filter = ['status', 'adverse_reaction']
    search_fields = ['transfusion_number', 'patient__name']
    date_hierarchy = 'created_at'
