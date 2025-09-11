"""
Configuración del admin para los modelos de tesorería.
"""

from django.contrib import admin
from .models_bank import Bank, BankAccount, CashAccount
from .models_movement import BankMovement, CashMovement
from .models_reconciliation import BankReconciliation, CashFlow


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    """Admin para bancos."""
    list_display = ('code', 'name', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('code', 'name')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin para cuentas bancarias."""
    list_display = ('code', 'name', 'company', 'bank', 'account_number', 'current_balance', 'status')
    list_filter = ('company', 'bank', 'status', 'account_type')
    search_fields = ('code', 'name', 'account_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CashAccount)
class CashAccountAdmin(admin.ModelAdmin):
    """Admin para cuentas de caja."""
    list_display = ('code', 'name', 'company', 'current_balance', 'max_balance', 'status')
    list_filter = ('company', 'status')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BankMovement)
class BankMovementAdmin(admin.ModelAdmin):
    """Admin para movimientos bancarios."""
    list_display = ('bank_account', 'date', 'movement_type', 'amount', 'balance', 'description')
    list_filter = ('bank_account__company', 'movement_type', 'date')
    search_fields = ('transaction_id', 'reference', 'description')
    readonly_fields = ('created_at',)


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    """Admin para movimientos de caja."""
    list_display = ('company', 'number', 'cash_account', 'movement_type', 'amount', 'date')
    list_filter = ('company', 'movement_type', 'date')
    search_fields = ('number', 'third_party_name', 'concept')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    """Admin para conciliaciones bancarias."""
    list_display = ('company', 'number', 'bank_account', 'period_end', 'status', 'difference')
    list_filter = ('company', 'status', 'period_end')
    search_fields = ('number',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    """Admin para flujo de caja."""
    list_display = ('company', 'period', 'category', 'date', 'net_flow')
    list_filter = ('company', 'category', 'period')
    search_fields = ('description',)
    readonly_fields = ('created_at',)
