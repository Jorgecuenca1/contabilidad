"""
Configuración del Admin para el módulo de Facturación de Salud
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import (
    HealthTariff, HealthInvoice, HealthInvoiceItem,
    HealthPayment, InvoiceGlosa
)


@admin.register(HealthTariff)
class HealthTariffAdmin(admin.ModelAdmin):
    """
    Administración de tarifarios de salud
    """
    list_display = [
        'name', 'tariff_type', 'valid_from', 'is_active_badge',
        'uvr_display', 'smmlv_display', 'increment_display', 'company'
    ]
    list_filter = ['is_active', 'tariff_type', 'company', 'valid_from']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'valid_from'

    fieldsets = (
        ('Información General', {
            'fields': ('company', 'tariff_type', 'name', 'description')
        }),
        ('Vigencia', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Valores Base', {
            'fields': ('uvr_value', 'smmlv_value', 'global_increment_percentage')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    is_active_badge.short_description = 'Estado'

    def uvr_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.uvr_value)
    uvr_display.short_description = 'UVR'

    def smmlv_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.smmlv_value)
    smmlv_display.short_description = 'SMMLV'

    def increment_display(self, obj):
        return format_html('<span>{}%</span>', obj.global_increment_percentage)
    increment_display.short_description = 'Incremento'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HealthInvoice)
class HealthInvoiceAdmin(admin.ModelAdmin):
    """
    Administración de facturas de salud
    """
    list_display = [
        'invoice_number', 'invoice_date', 'payer_name', 'patient_name',
        'invoice_type', 'status_badge', 'total_display', 'has_glosa_badge',
        'rips_badge'
    ]
    list_filter = [
        'status', 'invoice_type', 'has_glosa', 'rips_generated',
        'company', 'invoice_date'
    ]
    search_fields = [
        'invoice_number', 'payer__name', 'patient__name',
        'patient__document_number', 'contract_number'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'approved_at',
        'rips_generation_date', 'subtotal', 'total'
    ]
    raw_id_fields = ['payer', 'patient', 'tariff']
    date_hierarchy = 'invoice_date'
    ordering = ['-invoice_date', '-invoice_number']

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'company', 'invoice_number', 'invoice_date', 'invoice_type',
                'status'
            )
        }),
        ('Partes', {
            'fields': ('payer', 'patient', 'contract_number', 'tariff')
        }),
        ('Resolución DIAN', {
            'fields': (
                'dian_resolution', 'authorized_range_from', 'authorized_range_to',
                'resolution_date'
            ),
            'classes': ('collapse',)
        }),
        ('Totales', {
            'fields': (
                'subtotal', 'discount_amount', 'tax_amount', 'copayment_amount',
                'moderator_fee_amount', 'total'
            )
        }),
        ('RIPS', {
            'fields': ('rips_generated', 'rips_generation_date', 'rips_file_path'),
            'classes': ('collapse',)
        }),
        ('Glosas', {
            'fields': ('has_glosa', 'glosa_amount'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'created_by', 'created_at', 'updated_at', 'approved_by',
                'approved_at', 'issued_date'
            ),
            'classes': ('collapse',)
        }),
    )

    def payer_name(self, obj):
        return obj.payer.name if obj.payer else '-'
    payer_name.short_description = 'Pagador'

    def patient_name(self, obj):
        if obj.patient:
            return format_html(
                '{}<br><small>{}</small>',
                obj.patient.name,
                obj.patient.document_number
            )
        return '-'
    patient_name.short_description = 'Paciente'

    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'blue',
            'approved': 'green',
            'issued': 'teal',
            'paid': 'darkgreen',
            'cancelled': 'red',
            'glosa': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def total_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.total)
    total_display.short_description = 'Total'

    def has_glosa_badge(self, obj):
        if obj.has_glosa:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ ${:,.2f}</span>',
                obj.glosa_amount
            )
        return '-'
    has_glosa_badge.short_description = 'Glosa'

    def rips_badge(self, obj):
        if obj.rips_generated:
            return format_html('<span style="color: green;">✓ Generado</span>')
        return format_html('<span style="color: gray;">Pendiente</span>')
    rips_badge.short_description = 'RIPS'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class HealthInvoiceItemInline(admin.TabularInline):
    """
    Inline para items de factura
    """
    model = HealthInvoiceItem
    extra = 0
    readonly_fields = ['total_amount']
    fields = [
        'service_type', 'service_code', 'service_name', 'service_date',
        'quantity', 'unit_price', 'total_amount', 'copayment', 'moderator_fee'
    ]


@admin.register(HealthInvoiceItem)
class HealthInvoiceItemAdmin(admin.ModelAdmin):
    """
    Administración de items de factura
    """
    list_display = [
        'invoice_number', 'service_type', 'service_code_display',
        'service_name_truncated', 'quantity', 'unit_price_display', 'total_display',
        'is_glosa_badge'
    ]
    list_filter = ['service_type', 'is_glosa', 'invoice__company']
    search_fields = [
        'invoice__invoice_number', 'service_code', 'service_name',
        'diagnosis_code'
    ]
    readonly_fields = ['created_at', 'total_amount']
    raw_id_fields = ['invoice']

    fieldsets = (
        ('Factura', {
            'fields': ('invoice',)
        }),
        ('Servicio', {
            'fields': (
                'service_type', 'service_code', 'service_name', 'diagnosis_code', 'service_date'
            )
        }),
        ('Cantidades y Precios', {
            'fields': (
                'quantity', 'unit_price', 'total_amount',
                'copayment', 'moderator_fee'
            )
        }),
        ('Autorización', {
            'fields': ('authorization_number',),
            'classes': ('collapse',)
        }),
        ('Glosa', {
            'fields': ('is_glosa', 'glosa_reason'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def invoice_number(self, obj):
        return obj.invoice.invoice_number
    invoice_number.short_description = 'Factura'

    def service_code_display(self, obj):
        return format_html('<strong>{}</strong>', obj.service_code)
    service_code_display.short_description = 'Código'

    def service_name_truncated(self, obj):
        if len(obj.service_name) > 50:
            return f"{obj.service_name[:50]}..."
        return obj.service_name
    service_name_truncated.short_description = 'Servicio'

    def unit_price_display(self, obj):
        return format_html('${:,.2f}', obj.unit_price)
    unit_price_display.short_description = 'Precio Unit.'

    def total_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.total_amount)
    total_display.short_description = 'Total'

    def is_glosa_badge(self, obj):
        if obj.is_glosa:
            return format_html('<span style="color: orange;">⚠️ Glosado</span>')
        return '-'
    is_glosa_badge.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HealthPayment)
class HealthPaymentAdmin(admin.ModelAdmin):
    """
    Administración de pagos de facturas
    """
    list_display = [
        'invoice_number', 'payment_date', 'payment_method',
        'amount_display', 'reference_number', 'company'
    ]
    list_filter = ['payment_method', 'company', 'payment_date']
    search_fields = [
        'invoice__invoice_number', 'reference_number', 'notes'
    ]
    readonly_fields = ['created_at']
    raw_id_fields = ['invoice']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']

    fieldsets = (
        ('Información del Pago', {
            'fields': ('company', 'invoice', 'payment_date', 'payment_method')
        }),
        ('Montos', {
            'fields': ('amount', 'reference', 'notes')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def invoice_number(self, obj):
        return obj.invoice.invoice_number
    invoice_number.short_description = 'Factura'

    def amount_display(self, obj):
        return format_html('<strong style="color: green;">${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Monto'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InvoiceGlosa)
class InvoiceGlosaAdmin(admin.ModelAdmin):
    """
    Administración de glosas de facturas
    """
    list_display = [
        'invoice_number', 'glosa_number', 'status_badge',
        'glosa_amount_display', 'accepted_amount_display', 'created_at'
    ]
    list_filter = ['status', 'company', 'glosa_date']
    search_fields = [
        'invoice__invoice_number', 'glosa_number', 'reason', 'response'
    ]
    readonly_fields = ['created_at', 'response_date']
    raw_id_fields = ['invoice']
    date_hierarchy = 'glosa_date'
    ordering = ['-glosa_date']

    fieldsets = (
        ('Información de la Glosa', {
            'fields': (
                'company', 'invoice', 'glosa_number', 'glosa_date', 'status'
            )
        }),
        ('Montos', {
            'fields': ('glosa_amount', 'accepted_amount')
        }),
        ('Detalles', {
            'fields': ('reason', 'response_deadline')
        }),
        ('Respuesta', {
            'fields': ('response', 'response_date'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def invoice_number(self, obj):
        return obj.invoice.invoice_number
    invoice_number.short_description = 'Factura'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'in_review': 'blue',
            'accepted': 'red',
            'rejected': 'green',
            'partially_accepted': 'purple',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def glosa_amount_display(self, obj):
        return format_html(
            '<strong style="color: red;">${:,.2f}</strong>',
            obj.glosa_amount
        )
    glosa_amount_display.short_description = 'Monto Glosa'

    def accepted_amount_display(self, obj):
        if obj.accepted_amount and obj.accepted_amount > 0:
            return format_html(
                '<strong style="color: orange;">${:,.2f}</strong>',
                obj.accepted_amount
            )
        return '-'
    accepted_amount_display.short_description = 'Monto Aceptado'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
