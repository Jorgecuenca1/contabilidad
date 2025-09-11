"""
URL configuration for contabilidad_multiempresa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/profile/', login_required(lambda request: redirect('/'))),  # Redirigir profile al dashboard
    path('accounts/', include('django.contrib.auth.urls')),  # Añadido para login/logout
    path('', include('core.urls')),
    path('accounting/', include('accounting.urls')),
    path('accounts_receivable/', include('accounts_receivable.urls')),
    path('accounts_payable/', include('accounts_payable.urls')),
    path('treasury/', include('treasury.urls')),
    path('reports/', include('reports.urls')),
    path('payroll/', include('payroll.urls')),
    path('taxes/', include('taxes.urls')),
    path('public-sector/', include('public_sector.urls')),
    path('inventory/', include('inventory.urls')),
    path('fixed-assets/', include('fixed_assets.urls')),
    path('budget/', include('budget.urls')),
    path('third-parties/', include('third_parties.urls')),
    path('gynecology/', include('gynecology.urls')),
    path('laboratory/', include('laboratory.urls')),
    
    # Nuevos módulos de salud
    path('medical-records/', include('medical_records.urls')),
    path('medical-appointments/', include('medical_appointments.urls')),
    path('medical-procedures/', include('medical_procedures.urls')),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
