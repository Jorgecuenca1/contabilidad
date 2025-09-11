from django.contrib import admin
from .models import EmployeeType, Employee, PayrollConcept, PayrollPeriod, Payroll, PayrollDetail, LaborBenefit


@admin.register(EmployeeType)
class EmployeeTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['code', 'name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_code', 'first_name', 'last_name', 'document_number', 'position', 'basic_salary', 'is_active']
    list_filter = ['is_active', 'employee_type', 'company', 'contract_type', 'status']
    search_fields = ['employee_code', 'first_name', 'last_name', 'document_number', 'email']
    fieldsets = [
        ('Información Básica', {
            'fields': ('company', 'employee_type', 'employee_code', 'status')
        }),
        ('Información Personal', {
            'fields': ('document_type', 'document_number', 'first_name', 'last_name', 'birth_date', 'gender', 'marital_status')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'mobile', 'address', 'city', 'state')
        }),
        ('Información Laboral', {
            'fields': ('hire_date', 'termination_date', 'contract_type', 'position', 'department', 'cost_center')
        }),
        ('Información Salarial', {
            'fields': ('salary_type', 'basic_salary', 'transportation_allowance', 'other_fixed_income')
        }),
        ('Seguridad Social', {
            'fields': ('eps_code', 'eps_name', 'pension_fund_code', 'pension_fund_name', 'arl_code', 'arl_name', 'ccf_code', 'ccf_name')
        }),
        ('Información Bancaria', {
            'fields': ('bank_account', 'bank_name', 'account_type')
        }),
    ]


@admin.register(PayrollConcept)
class PayrollConceptAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'concept_type', 'calculation_type', 'is_active']
    list_filter = ['company', 'concept_type', 'calculation_type', 'is_active']
    search_fields = ['code', 'name']
    fieldsets = [
        ('Información Básica', {
            'fields': ('company', 'code', 'name', 'description', 'concept_type', 'calculation_type')
        }),
        ('Configuración de Cálculo', {
            'fields': ('percentage', 'fixed_value', 'formula')
        }),
        ('Configuración Contable', {
            'fields': ('account',)
        }),
        ('Configuración de Afectaciones', {
            'fields': ('affects_social_security', 'affects_parafiscals', 'affects_labor_benefits', 'affects_income_tax')
        }),
        ('Configuración de Reportes', {
            'fields': ('show_in_payslip', 'show_in_certificate')
        }),
    ]


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'period_type', 'start_date', 'end_date', 'payment_date', 'status']
    list_filter = ['company', 'period_type', 'status']
    search_fields = ['name']
    date_hierarchy = 'start_date'
    readonly_fields = ['total_earnings', 'total_deductions', 'total_employer_contributions', 'total_net_pay']


class PayrollDetailInline(admin.TabularInline):
    model = PayrollDetail
    extra = 0
    readonly_fields = ['amount']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'days_worked', 'total_earnings', 'total_deductions', 'net_pay', 'status']
    list_filter = ['status', 'payroll_period__company', 'payroll_period']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_code']
    readonly_fields = ['total_earnings', 'total_deductions', 'total_employer_contributions', 'net_pay']
    inlines = [PayrollDetailInline]


@admin.register(PayrollDetail)
class PayrollDetailAdmin(admin.ModelAdmin):
    list_display = ['payroll', 'concept', 'quantity', 'rate', 'amount']
    list_filter = ['concept__concept_type', 'payroll__payroll_period__company']
    search_fields = ['payroll__employee__first_name', 'payroll__employee__last_name', 'concept__name']


@admin.register(LaborBenefit)
class LaborBenefitAdmin(admin.ModelAdmin):
    list_display = ['employee', 'benefit_type', 'period_start', 'period_end', 'amount', 'status', 'payment_date']
    list_filter = ['company', 'benefit_type', 'status']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_code']
    date_hierarchy = 'payment_date'