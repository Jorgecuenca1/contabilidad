"""
URLs para el módulo de cuentas por cobrar.
"""

from django.urls import path
from . import views

app_name = 'accounts_receivable'

urlpatterns = [
    path('new-invoice/', views.new_invoice, name='new_invoice'),
    path('new-payment/', views.new_payment, name='new_payment'),
    path('api/customers/', views.get_customers_json, name='get_customers_json'),
    path('api/customer-invoices/', views.get_customer_invoices, name='get_customer_invoices'),
]

