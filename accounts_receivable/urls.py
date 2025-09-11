"""
URLs para el módulo de cuentas por cobrar.
"""

from django.urls import path
from . import views

app_name = 'accounts_receivable'

urlpatterns = [
    # Main views
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Customer management
    path('customers/', views.customer_list, name='customer_list'),
    # path('customers/new/', views.new_customer, name='new_customer'),
    # path('customers/<uuid:customer_id>/', views.customer_detail, name='customer_detail'),
    # path('customers/<uuid:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    
    # Invoice management
    # path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/new/', views.new_invoice, name='new_invoice'),
    # path('invoices/<uuid:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    # path('invoices/<uuid:invoice_id>/edit/', views.edit_invoice, name='edit_invoice'),
    
    # Payment management
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/new/', views.new_payment, name='new_payment'),
    path('payments/<uuid:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # API endpoints
    path('api/customers/', views.get_customers_json, name='get_customers_json'),
    path('api/customer-invoices/', views.get_customer_invoices, name='get_customer_invoices'),
]

