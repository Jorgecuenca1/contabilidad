from django.contrib import admin
from .models import (
    BudgetPeriod, BudgetRubro, CDP, CDPDetail, 
    RP, RPDetail, BudgetObligation, PAC,
    BudgetModification, BudgetModificationDetail, BudgetExecution
)


@admin.register(BudgetPeriod)
class BudgetPeriodAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'company', 'status', 'initial_budget', 'current_budget']
    list_filter = ['status', 'company', 'year']
    search_fields = ['name', 'year']


@admin.register(BudgetRubro)
class BudgetRubroAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'rubro_type', 'current_appropriation', 'cdp_amount', 'available_appropriation']
    list_filter = ['rubro_type', 'period', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['available_appropriation', 'available_cdp', 'available_rp']


class CDPDetailInline(admin.TabularInline):
    model = CDPDetail
    extra = 1


@admin.register(CDP)
class CDPAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'total_amount', 'available_amount', 'state']
    list_filter = ['state', 'date', 'company']
    search_fields = ['number', 'concept', 'request_person']
    inlines = [CDPDetailInline]
    readonly_fields = ['available_amount']


class RPDetailInline(admin.TabularInline):
    model = RPDetail
    extra = 1


@admin.register(RP)
class RPAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'beneficiary_name', 'total_amount', 'state']
    list_filter = ['state', 'contract_type', 'date']
    search_fields = ['number', 'beneficiary_name', 'beneficiary_id']
    inlines = [RPDetailInline]


@admin.register(BudgetObligation)
class BudgetObligationAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'rp', 'net_amount', 'paid_amount', 'state']
    list_filter = ['state', 'date']
    search_fields = ['number', 'concept']


@admin.register(PAC)
class PACAdmin(admin.ModelAdmin):
    list_display = ['period', 'rubro', 'total_programmed']
    list_filter = ['period', 'company']
    search_fields = ['rubro__name', 'rubro__code']