from django.urls import path
from . import views

app_name = 'treasury'

urlpatterns = [
    path('bank-movement/', views.bank_movement, name='bank_movement'),
    path('bank-reconciliation/', views.bank_reconciliation, name='bank_reconciliation'),
]
