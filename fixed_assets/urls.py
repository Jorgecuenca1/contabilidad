"""
URLs para el módulo de activos fijos.
"""

from django.urls import path
from . import views

app_name = 'fixed_assets'

urlpatterns = [
    path('', views.fixed_assets_dashboard, name='dashboard'),
    path('assets/', views.asset_list, name='asset_list'),
    path('new-asset/', views.new_asset, name='new_asset'),
    path('asset/<uuid:asset_id>/', views.asset_detail, name='asset_detail'),
    path('asset/<uuid:asset_id>/edit/', views.edit_asset, name='edit_asset'),
    path('depreciation/', views.depreciation_report, name='depreciation_report'),
    path('calculate-depreciation/', views.calculate_depreciation, name='calculate_depreciation'),
    path('api/assets/', views.get_assets_json, name='get_assets_json'),
]

