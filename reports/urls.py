"""
URLs para el módulo de reportes.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('financial/', views.financial_reports, name='financial_reports'),
    
    # Generación de reportes
    path('generate/balance-sheet/', views.generate_balance_sheet, name='generate_balance_sheet'),
    path('generate/income-statement/', views.generate_income_statement, name='generate_income_statement'),
    path('generate/trial-balance/', views.generate_trial_balance, name='generate_trial_balance'),
    path('generate/aging-report/', views.generate_aging_report, name='generate_aging_report'),
    path('generate/general-ledger/', views.generate_general_ledger, name='generate_general_ledger'),
    
    # APIs
    path('api/company/<uuid:company_id>/accounts/', views.get_company_accounts, name='company_accounts'),
]




