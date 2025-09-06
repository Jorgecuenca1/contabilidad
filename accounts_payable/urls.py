from django.urls import path
from . import views

app_name = 'accounts_payable'

urlpatterns = [
    path('new-purchase-invoice/', views.new_purchase_invoice, name='new_purchase_invoice'),
    path('supplier-payment/', views.supplier_payment, name='supplier_payment'),
]
