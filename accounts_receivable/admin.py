"""
Configuración del admin para Cuentas por Cobrar.
"""

from django.contrib import admin
from .models_customer import CustomerType, Customer
from .models_invoice import Invoice, InvoiceLine
from .models_payment import Payment, PaymentAllocation, CustomerStatement


@admin.register(CustomerType)
class CustomerTypeAdmin(admin.ModelAdmin):
    """Admin para tipos de cliente."""
    list_display = ('code', 'name', 'company', 'credit_limit_default', 'credit_days_default', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin para clientes."""
    list_display = ('code', 'business_name', 'document_number', 'customer_type', 'credit_limit', 'is_active')
    list_filter = ('company', 'customer_type', 'regime', 'is_active', 'is_blocked')
    search_fields = ('code', 'business_name', 'document_number', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'code', 'document_type', 'document_number', 'verification_digit')
        }),
        ('Datos Personales/Empresariales', {
            'fields': ('business_name', 'trade_name', 'first_name', 'last_name')
        }),
        ('Clasificación', {
            'fields': ('customer_type', 'regime')
        }),
        ('Contacto', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'phone', 'mobile', 'email', 'website')
        }),
        ('Configuración Comercial', {
            'fields': ('credit_limit', 'credit_days', 'discount_percentage')
        }),
        ('Cuentas Contables', {
            'fields': ('receivable_account', 'advance_account')
        }),
        ('Configuración Fiscal', {
            'fields': ('is_tax_responsible', 'tax_responsibilities')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_blocked', 'block_reason')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


class InvoiceLineInline(admin.TabularInline):
    """Inline para líneas de factura."""
    model = InvoiceLine
    extra = 1
    fields = ('product_code', 'description', 'quantity', 'unit_price', 'tax_rate', 'line_total')
    readonly_fields = ('line_total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin para facturas."""
    list_display = ('number', 'series', 'customer', 'date', 'due_date', 'total_amount', 'balance', 'status')
    list_filter = ('company', 'status', 'type', 'date', 'electronic_invoice')
    search_fields = ('number', 'customer__business_name', 'reference')
    readonly_fields = ('balance', 'created_at', 'updated_at')
    inlines = [InvoiceLineInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'number', 'series', 'type', 'customer')
        }),
        ('Fechas', {
            'fields': ('date', 'due_date')
        }),
        ('Referencias', {
            'fields': ('reference', 'purchase_order')
        }),
        ('Montos', {
            'fields': ('currency', 'exchange_rate', 'subtotal', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Pagos', {
            'fields': ('paid_amount', 'balance')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Facturación Electrónica', {
            'fields': ('electronic_invoice', 'cufe', 'xml_file', 'pdf_file'),
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin para pagos de clientes."""
    list_display = ('number', 'customer', 'date', 'amount', 'payment_method', 'status')
    list_filter = ('company', 'status', 'payment_method', 'date')
    search_fields = ('number', 'customer__business_name', 'reference')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'number', 'customer')
        }),
        ('Fechas', {
            'fields': ('date', 'value_date')
        }),
        ('Monto', {
            'fields': ('currency', 'exchange_rate', 'amount')
        }),
        ('Método de Pago', {
            'fields': ('payment_method', 'reference')
        }),
        ('Contabilización', {
            'fields': ('cash_account', 'is_posted')
        }),
        ('Estado', {
            'fields': ('status',)
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


@admin.register(CustomerStatement)
class CustomerStatementAdmin(admin.ModelAdmin):
    """Admin para estados de cuenta."""
    list_display = ('customer', 'period_start', 'period_end', 'closing_balance', 'is_sent')
    list_filter = ('company', 'is_sent', 'period_end')
    search_fields = ('customer__business_name',)
    readonly_fields = ('created_at',)