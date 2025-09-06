"""
Configuración del admin para Cuentas por Pagar.
"""

from django.contrib import admin
from .models_supplier import SupplierType, Supplier
from .models_bill import PurchaseInvoice, PurchaseInvoiceLine
from .models_payment import SupplierPayment, PaymentAllocation, PaymentSchedule, SupplierStatement


@admin.register(SupplierType)
class SupplierTypeAdmin(admin.ModelAdmin):
    """Admin para tipos de proveedor."""
    list_display = ('code', 'name', 'company', 'payment_days_default', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin para proveedores."""
    list_display = ('code', 'business_name', 'document_number', 'supplier_type', 'payment_days', 'is_active')
    list_filter = ('company', 'supplier_type', 'supplier_class', 'regime', 'is_active', 'is_blocked')
    search_fields = ('code', 'business_name', 'document_number', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'code', 'document_type', 'document_number', 'verification_digit')
        }),
        ('Datos Empresariales', {
            'fields': ('business_name', 'trade_name', 'first_name', 'last_name')
        }),
        ('Clasificación', {
            'fields': ('supplier_type', 'supplier_class', 'regime')
        }),
        ('Contacto', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'phone', 'mobile', 'email', 'website')
        }),
        ('Contacto Comercial', {
            'fields': ('contact_name', 'contact_phone', 'contact_email')
        }),
        ('Configuración Comercial', {
            'fields': ('payment_days', 'discount_percentage')
        }),
        ('Cuentas Contables', {
            'fields': ('payable_account', 'advance_account', 'expense_account')
        }),
        ('Configuración Fiscal', {
            'fields': ('is_tax_agent', 'tax_responsibilities')
        }),
        ('Retenciones', {
            'fields': (
                'applies_income_tax_retention', 'income_tax_retention_rate',
                'applies_vat_retention', 'vat_retention_rate',
                'applies_ica_retention', 'ica_retention_rate'
            )
        }),
        ('Información Bancaria', {
            'fields': ('bank_name', 'bank_account_type', 'bank_account_number')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_blocked', 'block_reason')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


class PurchaseInvoiceLineInline(admin.TabularInline):
    """Inline para líneas de factura de compra."""
    model = PurchaseInvoiceLine
    extra = 1
    fields = ('product_code', 'description', 'quantity', 'unit_price', 'tax_rate', 'line_total')
    readonly_fields = ('line_total',)


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    """Admin para facturas de compra."""
    list_display = ('number', 'supplier_invoice_number', 'supplier', 'date', 'due_date', 'total_amount', 'net_amount', 'balance', 'status')
    list_filter = ('company', 'status', 'type', 'date', 'requires_approval')
    search_fields = ('number', 'supplier_invoice_number', 'supplier__business_name', 'reference')
    readonly_fields = ('net_amount', 'balance', 'created_at', 'updated_at')
    inlines = [PurchaseInvoiceLineInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'number', 'supplier_invoice_number', 'type', 'supplier')
        }),
        ('Fechas', {
            'fields': ('date', 'due_date', 'received_date')
        }),
        ('Referencias', {
            'fields': ('reference', 'purchase_order')
        }),
        ('Montos', {
            'fields': ('currency', 'exchange_rate', 'subtotal', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Retenciones', {
            'fields': ('income_tax_retention', 'vat_retention', 'ica_retention', 'other_retentions', 'net_amount')
        }),
        ('Pagos', {
            'fields': ('paid_amount', 'balance')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Aprobación', {
            'fields': ('requires_approval', 'approved_by', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Archivos', {
            'fields': ('pdf_file', 'xml_file'),
            'classes': ('collapse',)
        }),
        ('Contabilización', {
            'fields': ('is_posted',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    """Admin para pagos a proveedores."""
    list_display = ('number', 'supplier', 'date', 'amount', 'payment_method', 'status')
    list_filter = ('company', 'status', 'payment_method', 'date', 'requires_approval')
    search_fields = ('number', 'supplier__business_name', 'reference', 'check_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'number', 'supplier')
        }),
        ('Fechas', {
            'fields': ('date', 'value_date')
        }),
        ('Monto', {
            'fields': ('currency', 'exchange_rate', 'amount')
        }),
        ('Método de Pago', {
            'fields': ('payment_method', 'reference', 'check_number', 'bank_account')
        }),
        ('Contabilización', {
            'fields': ('cash_account', 'is_posted')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Aprobación', {
            'fields': ('requires_approval', 'approved_by', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    """Admin para aplicaciones de pago."""
    list_display = ('payment', 'invoice', 'amount', 'created_at')
    list_filter = ('payment__company', 'created_at')
    search_fields = ('payment__number', 'invoice__number')


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    """Admin para programación de pagos."""
    list_display = ('invoice', 'supplier', 'scheduled_date', 'amount', 'priority', 'status')
    list_filter = ('company', 'status', 'priority', 'scheduled_date')
    search_fields = ('invoice__number', 'supplier__business_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SupplierStatement)
class SupplierStatementAdmin(admin.ModelAdmin):
    """Admin para estados de cuenta de proveedores."""
    list_display = ('supplier', 'period_start', 'period_end', 'closing_balance')
    list_filter = ('company', 'period_end')
    search_fields = ('supplier__business_name',)
    readonly_fields = ('created_at',)