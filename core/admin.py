"""
Configuración del admin para los modelos del núcleo.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Country, Company, Currency, ExchangeRate, 
    AuditLog, SystemConfiguration
)
from .models_extended import (
    FiscalYear, Period, UserCompanyPermission
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizado para usuarios."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'document_number')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'phone', 'document_type', 'document_number', 'is_active_2fa')
        }),
    )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin para países."""
    list_display = ('code', 'name', 'currency_code', 'currency_symbol')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin para empresas."""
    list_display = ('name', 'tax_id', 'country', 'regime', 'sector', 'is_active')
    list_filter = ('country', 'regime', 'sector', 'is_active')
    search_fields = ('name', 'legal_name', 'tax_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'legal_name', 'tax_id', 'tax_id_dv')
        }),
        ('Localización', {
            'fields': ('country', 'address', 'city', 'state', 'postal_code')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Configuración Contable', {
            'fields': ('regime', 'sector', 'functional_currency')
        }),
        ('Configuración Fiscal', {
            'fields': ('fiscal_year_start', 'fiscal_year_end')
        }),
        ('Representante Legal', {
            'fields': ('legal_representative', 'legal_rep_document')
        }),
        ('Configuraciones', {
            'fields': ('logo', 'is_active', 'settings')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    """Admin para años fiscales."""
    list_display = ('company', 'year', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'year')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    """Admin para períodos contables."""
    list_display = ('fiscal_year', 'month', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'fiscal_year__year')
    search_fields = ('fiscal_year__company__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserCompanyPermission)
class UserCompanyPermissionAdmin(admin.ModelAdmin):
    """Admin para permisos usuario-empresa."""
    list_display = ('user', 'company', 'permission_level')
    list_filter = ('permission_level',)
    search_fields = ('user__username', 'company__name')


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin para monedas."""
    list_display = ('code', 'name', 'symbol', 'decimal_places', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin para tipos de cambio."""
    list_display = ('company', 'from_currency', 'to_currency', 'rate', 'date', 'rate_type')
    list_filter = ('rate_type', 'date')
    search_fields = ('company__name', 'from_currency__code', 'to_currency__code')
    readonly_fields = ('created_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin para logs de auditoría."""
    list_display = ('user', 'company', 'action', 'model_name', 'object_repr', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'company__name', 'object_repr')
    readonly_fields = ('hash_value', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin para configuraciones del sistema."""
    list_display = ('key', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')