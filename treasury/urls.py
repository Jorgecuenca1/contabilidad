from django.urls import path
from . import views

app_name = 'treasury'

urlpatterns = [
    # Dashboard principal de tesorería
    path('', views.treasury_dashboard, name='dashboard'),
    
    # Cuentas bancarias
    path('bank-accounts/', views.bank_account_list, name='bank_account_list'),
    path('bank-accounts/new/', views.bank_account_create, name='bank_account_create'),
    path('bank-accounts/<uuid:pk>/edit/', views.bank_account_edit, name='bank_account_edit'),
    
    # Cuentas de caja
    path('cash-accounts/', views.cash_account_list, name='cash_account_list'),
    path('cash-accounts/new/', views.cash_account_create, name='cash_account_create'),
    path('cash-accounts/<uuid:pk>/edit/', views.cash_account_edit, name='cash_account_edit'),
    
    # Movimientos bancarios
    path('bank-movement/', views.bank_movement, name='bank_movement'),
    path('bank-movements/', views.bank_movement_list, name='bank_movement_list'),
    
    # Movimientos de caja
    path('cash-movement/', views.cash_movement, name='cash_movement'),
    path('cash-movements/', views.cash_movement_list, name='cash_movement_list'),
    
    # Conciliación bancaria
    path('bank-reconciliation/', views.bank_reconciliation, name='bank_reconciliation'),
    path('bank-reconciliations/', views.bank_reconciliation_list, name='bank_reconciliation_list'),
    
    # Flujo de caja
    path('cash-flow/', views.cash_flow, name='cash_flow'),
    path('cash-flow/report/', views.cash_flow_report, name='cash_flow_report'),
]
