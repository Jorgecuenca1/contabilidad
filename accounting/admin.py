"""
Configuración del admin para los modelos contables.
"""

from django.contrib import admin
from .models_accounts import (
    AccountType, ChartOfAccounts, Account, CostCenter, Project
)
from .models_journal import (
    JournalType, JournalEntry, JournalEntryLine
)


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    """Admin para tipos de cuenta."""
    list_display = ('code', 'name', 'type', 'nature', 'is_balance_sheet', 'is_income_statement')
    list_filter = ('type', 'nature', 'is_balance_sheet', 'is_income_statement')
    search_fields = ('code', 'name')


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    """Admin para plan de cuentas."""
    list_display = ('company', 'name', 'account_code_length', 'created_at')
    list_filter = ('company',)
    search_fields = ('company__name', 'name')
    readonly_fields = ('created_at', 'updated_at')


class AccountAdmin(admin.ModelAdmin):
    """Admin para cuentas contables."""
    list_display = ('code', 'name', 'account_type', 'control_type', 'is_active', 'is_detail')
    list_filter = ('account_type', 'control_type', 'is_active', 'is_detail', 'chart_of_accounts__company')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('chart_of_accounts', 'parent', 'code', 'name', 'description')
        }),
        ('Configuración', {
            'fields': ('account_type', 'control_type', 'level')
        }),
        ('Comportamiento', {
            'fields': ('is_active', 'is_detail', 'requires_third_party', 'requires_cost_center', 'requires_project')
        }),
        ('Moneda', {
            'fields': ('currency', 'allow_multi_currency')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Account, AccountAdmin)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    """Admin para centros de costo."""
    list_display = ('code', 'name', 'company', 'manager', 'is_active', 'has_budget')
    list_filter = ('company', 'is_active', 'has_budget')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin para proyectos."""
    list_display = ('code', 'name', 'company', 'status', 'start_date', 'end_date', 'manager')
    list_filter = ('company', 'status')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(JournalType)
class JournalTypeAdmin(admin.ModelAdmin):
    """Admin para tipos de diario."""
    list_display = ('code', 'name', 'company', 'sequence_prefix', 'next_number', 'requires_approval', 'is_active')
    list_filter = ('company', 'requires_approval', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


class JournalEntryLineInline(admin.TabularInline):
    """Inline para líneas de asiento."""
    model = JournalEntryLine
    extra = 2
    fields = ('account', 'description', 'debit', 'credit', 'cost_center', 'project')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    """Admin para asientos contables."""
    list_display = ('number', 'company', 'date', 'journal_type', 'status', 'total_debit', 'total_credit')
    list_filter = ('company', 'status', 'journal_type', 'date')
    search_fields = ('number', 'description', 'reference')
    readonly_fields = ('hash_value', 'created_at', 'updated_at', 'posting_date')
    inlines = [JournalEntryLineInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'number', 'journal_type', 'period', 'date')
        }),
        ('Descripción', {
            'fields': ('reference', 'description')
        }),
        ('Estado', {
            'fields': ('status', 'posting_date')
        }),
        ('Totales', {
            'fields': ('total_debit', 'total_credit')
        }),
        ('Moneda', {
            'fields': ('currency',)
        }),
        ('Auditoría', {
            'fields': ('hash_value', 'created_at', 'updated_at', 'created_by', 'posted_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar asientos contabilizados."""
        if obj and obj.status == 'posted':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    """Admin para líneas de asiento."""
    list_display = ('journal_entry', 'line_number', 'account', 'debit', 'credit', 'cost_center')
    list_filter = ('journal_entry__company', 'account__account_type')
    search_fields = ('journal_entry__number', 'account__code', 'account__name', 'description')
    readonly_fields = ('created_at',)