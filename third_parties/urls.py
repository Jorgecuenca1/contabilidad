from django.urls import path
from . import views

app_name = 'third_parties'

urlpatterns = [
    # CRUD de terceros
    path('', views.third_party_list, name='list'),
    path('create/', views.third_party_create, name='create'),
    path('<int:pk>/', views.third_party_detail, name='detail'),
    path('<int:pk>/edit/', views.third_party_edit, name='edit'),
    path('<int:pk>/delete/', views.third_party_delete, name='delete'),
    
    # API endpoints
    path('api/search/', views.api_search_third_parties, name='api_search'),
    path('api/verify-nit/', views.api_verify_nit, name='api_verify_nit'),
]