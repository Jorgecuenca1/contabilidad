"""Script para verificar los módulos de salud cargados"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company
from core.models_modules import SystemModule, CompanyModule

print("=" * 60)
print("VERIFICACION DE MODULOS DE SALUD")
print("=" * 60)

# Verificar módulos registrados
health_modules = SystemModule.objects.filter(category='healthcare').order_by('name')
print(f"\n[1] Total modulos de salud registrados: {health_modules.count()}")
print("\nListado de modulos:")
for i, module in enumerate(health_modules, 1):
    print(f"  {i:2}. [{module.code:25}] {module.name}")
    print(f"      Icon: {module.icon_class:20} | URL: {module.url_pattern}")

# Verificar empresas de salud
health_companies = Company.objects.filter(category='salud', is_active=True)
print(f"\n[2] Empresas del sector salud: {health_companies.count()}")
for company in health_companies:
    print(f"  - {company.name}")

# Verificar módulos activados por empresa
if health_companies.exists():
    print("\n[3] Modulos activados por empresa:")
    for company in health_companies:
        activated = CompanyModule.objects.filter(
            company=company,
            module__category='healthcare',
            is_enabled=True
        ).select_related('module')
        print(f"\n  Empresa: {company.name}")
        print(f"  Total activados: {activated.count()}")
        print("  Modulos:")
        for cm in activated[:10]:  # Mostrar primeros 10
            print(f"    - {cm.module.name}")
        if activated.count() > 10:
            print(f"    ... y {activated.count() - 10} modulos mas")

print("\n" + "=" * 60)
print("VERIFICACION COMPLETADA")
print("=" * 60)
