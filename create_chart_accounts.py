#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company, User
from accounting.models import ChartOfAccounts, AccountType, Account

def create_chart_of_accounts():
    companies = Company.objects.all()
    
    # Obtener usuario admin
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ No admin user found. Please create an admin user first.")
        return
    
    for company in companies:
        # Verificar si ya tiene Plan de Cuentas
        chart, created = ChartOfAccounts.objects.get_or_create(
            company=company,
            defaults={
                'name': f'Plan Único de Cuentas - {company.name}',
                'description': f'PUC según Decreto 2650 para {company.name}',
                'account_code_length': 6,
                'cost_center_required': False,
                'created_by': admin_user
            }
        )
        
        if created:
            print(f'[OK] Created chart of accounts for: {company.name}')
        else:
            print(f'[INFO] Chart already exists for: {company.name}')
        
        # Crear cuentas básicas del PUC si no existen
        create_basic_puc_accounts(chart)

def create_basic_puc_accounts(chart):
    """Crear las cuentas básicas del PUC colombiano"""
    
    # Obtener tipos de cuenta
    try:
        asset_type = AccountType.objects.get(name='Activo')
        liability_type = AccountType.objects.get(name='Pasivo') 
        equity_type = AccountType.objects.get(name='Patrimonio')
        income_type = AccountType.objects.get(name='Ingresos')
        expense_type = AccountType.objects.get(name='Gastos')
        cost_type = AccountType.objects.get(name='Costos')
    except AccountType.DoesNotExist:
        print('[ERROR] Account types not found. Please run load_initial_data first.')
        return

    basic_accounts = [
        # ACTIVOS (Clase 1)
        ('1', 'ACTIVOS', asset_type, None, False),
        ('11', 'DISPONIBLE', asset_type, '1', False),
        ('1105', 'CAJA', asset_type, '11', False),
        ('110505', 'Caja General', asset_type, '1105', True),
        ('1110', 'BANCOS', asset_type, '11', False),
        ('111005', 'Bancos Nacionales', asset_type, '1110', True),
        ('12', 'INVERSIONES', asset_type, '1', False),
        ('13', 'DEUDORES', asset_type, '1', False),
        ('1305', 'CLIENTES', asset_type, '13', False),
        ('130505', 'Clientes Nacionales', asset_type, '1305', True),
        
        # PASIVOS (Clase 2)
        ('2', 'PASIVOS', liability_type, None, False),
        ('21', 'OBLIGACIONES FINANCIERAS', liability_type, '2', False),
        ('2105', 'BANCOS NACIONALES', liability_type, '21', False),
        ('210505', 'Sobregiros', liability_type, '2105', True),
        ('22', 'PROVEEDORES', liability_type, '2', False),
        ('2205', 'PROVEEDORES NACIONALES', liability_type, '22', False),
        ('220505', 'Proveedores Nacionales', liability_type, '2205', True),
        
        # PATRIMONIO (Clase 3)
        ('3', 'PATRIMONIO', equity_type, None, False),
        ('31', 'CAPITAL SOCIAL', equity_type, '3', False),
        ('3105', 'CAPITAL SUSCRITO Y PAGADO', equity_type, '31', False),
        ('310505', 'Capital Autorizado', equity_type, '3105', True),
        
        # INGRESOS (Clase 4)
        ('4', 'INGRESOS', income_type, None, False),
        ('41', 'INGRESOS OPERACIONALES', income_type, '4', False),
        ('4135', 'COMERCIO AL POR MAYOR Y AL POR MENOR', income_type, '41', False),
        ('413505', 'Venta de Mercancías', income_type, '4135', True),
        
        # GASTOS (Clase 5)
        ('5', 'GASTOS', expense_type, None, False),
        ('51', 'GASTOS OPERACIONALES DE ADMINISTRACION', expense_type, '5', False),
        ('5105', 'GASTOS DE PERSONAL', expense_type, '51', False),
        ('510506', 'Sueldos', expense_type, '5105', True),
        
        # COSTOS (Clase 6)
        ('6', 'COSTOS DE VENTAS', cost_type, None, False),
        ('61', 'COSTO DE VENTAS Y DE PRESTACION DE SERVICIOS', cost_type, '6', False),
        ('6135', 'COMERCIO AL POR MAYOR Y AL POR MENOR', cost_type, '61', False),
        ('613505', 'Costo de Mercancías Vendidas', cost_type, '6135', True),
    ]
    
    created_count = 0
    for code, name, account_type, parent_code, is_detail in basic_accounts:
        # Buscar cuenta padre
        parent = None
        if parent_code:
            parent = Account.objects.filter(
                chart_of_accounts=chart, 
                code=parent_code
            ).first()
        
        # Crear cuenta si no existe
        account, created = Account.objects.get_or_create(
            chart_of_accounts=chart,
            code=code,
            defaults={
                'name': name,
                'account_type': account_type,
                'parent': parent,
                'is_detail': is_detail,
                'is_active': True,
                'description': f'Cuenta {name} del PUC',
                'created_by': chart.created_by
            }
        )
        
        if created:
            created_count += 1
    
    print(f'   [ACCOUNTS] Created {created_count} new accounts for {chart.company.name}')

if __name__ == '__main__':
    create_chart_of_accounts()