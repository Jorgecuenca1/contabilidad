"""
URLs para el módulo de inventario.
"""

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('new-product/', views.new_product, name='new_product'),
    path('product/<uuid:product_id>/', views.product_detail, name='product_detail'),
    path('product/<uuid:product_id>/edit/', views.edit_product, name='edit_product'),
    path('stock-movement/', views.stock_movement, name='stock_movement'),
    path('stock-report/', views.stock_report, name='stock_report'),
    path('api/products/', views.get_products_json, name='get_products_json'),
]

