"""
URLs para el módulo de contabilidad.
"""

from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('new-journal-entry/', views.new_journal_entry, name='new_journal_entry'),
    path('chart-of-accounts/', views.chart_of_accounts, name='chart_of_accounts'),
    path('api/accounts/', views.get_accounts_json, name='get_accounts_json'),
]

