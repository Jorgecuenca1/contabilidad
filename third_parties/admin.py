from django.contrib import admin
from .models import ThirdParty, ThirdPartyType, ThirdPartyContact, ThirdPartyAddress, ThirdPartyDocument, CompanyExtended


@admin.register(ThirdPartyType)
class ThirdPartyTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'is_customer', 'is_supplier']
    list_filter = ['company', 'is_customer', 'is_supplier']
    search_fields = ['code', 'name']


class ThirdPartyContactInline(admin.TabularInline):
    model = ThirdPartyContact
    extra = 0


class ThirdPartyAddressInline(admin.TabularInline):
    model = ThirdPartyAddress
    extra = 0


class ThirdPartyDocumentInline(admin.TabularInline):
    model = ThirdPartyDocument
    extra = 0


@admin.register(ThirdParty)
class ThirdPartyAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'get_full_name', 'person_type', 'is_customer', 'is_supplier', 'is_active']
    list_filter = ['person_type', 'is_customer', 'is_supplier', 'is_active', 'tax_regime']
    search_fields = ['document_number', 'first_name', 'last_name', 'trade_name', 'email']
    inlines = [ThirdPartyContactInline, ThirdPartyAddressInline, ThirdPartyDocumentInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'person_type', 'document_type', 'document_number', 'verification_digit')
        }),
        ('Nombre', {
            'fields': ('first_name', 'middle_name', 'last_name', 'second_last_name', 'trade_name')
        }),
        ('Clasificación', {
            'fields': ('is_customer', 'is_supplier', 'is_shareholder', 'is_bank', 'is_government')
        }),
        ('Información Tributaria', {
            'fields': ('tax_regime', 'taxpayer_type', 'is_vat_responsible', 'is_withholding_agent', 
                      'is_self_withholding', 'is_great_contributor')
        }),
        ('Contacto', {
            'fields': ('address', 'city', 'state', 'country', 'phone', 'mobile', 'email', 'website')
        }),
        ('Información Comercial', {
            'fields': ('credit_limit', 'payment_term_days', 'discount_percentage', 'rating')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_blocked', 'block_reason')
        }),
    )


@admin.register(CompanyExtended)
class CompanyExtendedAdmin(admin.ModelAdmin):
    list_display = ['company', 'company_type', 'company_size', 'economic_sector']
    list_filter = ['company_type', 'company_size', 'economic_sector', 'is_public_entity']
    search_fields = ['company__name', 'company__tax_id']