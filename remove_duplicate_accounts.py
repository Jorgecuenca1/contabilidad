#!/usr/bin/env python
"""
Script para eliminar cuentas duplicadas del PUC y dejar solo una copia compartida.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from accounting.models import Account, ChartOfAccounts
from collections import defaultdict
from django.db import transaction

def remove_duplicate_accounts():
    """
    Elimina cuentas duplicadas manteniendo solo una copia de cada código del PUC.
    """
    print("Iniciando eliminación de cuentas duplicadas...")
    
    # Agrupar cuentas por código
    accounts_by_code = defaultdict(list)
    all_accounts = Account.objects.all().order_by('created_at')
    
    for account in all_accounts:
        accounts_by_code[account.code].append(account)
    
    # Estadísticas
    total_accounts = len(all_accounts)
    duplicate_codes = 0
    accounts_to_delete = []
    
    print(f"Total de cuentas encontradas: {total_accounts}")
    
    # Procesar cada código
    for code, accounts in accounts_by_code.items():
        if len(accounts) > 1:
            duplicate_codes += 1
            print(f"[DUPLICADO] Código {code}: {len(accounts)} cuentas")
            
            # Mantener la primera cuenta (más antigua) y marcar las demás para eliminación
            accounts_to_keep = accounts[0]
            accounts_to_delete.extend(accounts[1:])
            
            print(f"  - Mantener: {accounts_to_keep.name} (ID: {accounts_to_keep.id})")
            for account in accounts[1:]:
                print(f"  - Eliminar: {account.name} (ID: {account.id})")
    
    print(f"\nResumen:")
    print(f"- Códigos duplicados: {duplicate_codes}")
    print(f"- Cuentas a eliminar: {len(accounts_to_delete)}")
    print(f"- Cuentas a mantener: {total_accounts - len(accounts_to_delete)}")
    
    # Confirmar eliminación
    if accounts_to_delete:
        response = input(f"\n¿Desea eliminar {len(accounts_to_delete)} cuentas duplicadas? (si/no): ")
        if response.lower() in ['si', 's', 'yes', 'y']:
            with transaction.atomic():
                for account in accounts_to_delete:
                    print(f"Eliminando: {account.code} - {account.name}")
                    account.delete()
            
            print(f"\n[OK] {len(accounts_to_delete)} cuentas duplicadas eliminadas exitosamente.")
            
            # Verificar resultado
            remaining_accounts = Account.objects.all()
            remaining_codes = set(account.code for account in remaining_accounts)
            print(f"[OK] Cuentas restantes: {len(remaining_accounts)}")
            print(f"[OK] Códigos únicos: {len(remaining_codes)}")
            
        else:
            print("Operación cancelada.")
    else:
        print("No hay cuentas duplicadas para eliminar.")

if __name__ == "__main__":
    remove_duplicate_accounts()