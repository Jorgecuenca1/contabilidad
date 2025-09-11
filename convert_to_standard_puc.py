#!/usr/bin/env python
"""
Script para convertir las cuentas existentes a formato estándar PUC,
eliminando duplicados y marcando todas como cuentas estándar del PUC colombiano.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import connection, transaction
from collections import defaultdict

def convert_to_standard_puc():
    """
    Convierte las cuentas duplicadas a un formato estándar único del PUC colombiano.
    """
    print("Convirtiendo cuentas a formato estándar PUC...")
    
    with connection.cursor() as cursor:
        
        # 1. Obtener todas las cuentas agrupadas por código
        cursor.execute("""
            SELECT code, GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM accounting_accounts 
            GROUP BY code 
            ORDER BY code
        """)
        
        accounts_data = cursor.fetchall()
        
        # 2. Procesar cada grupo de cuentas
        with transaction.atomic():
            accounts_kept = 0
            accounts_updated = 0
            
            for code, ids_str, count in accounts_data:
                ids = ids_str.split(',')
                
                if count == 1:
                    # Cuenta única: solo actualizar para marcar como estándar PUC
                    cursor.execute("""
                        UPDATE accounting_accounts 
                        SET chart_of_accounts_id = NULL
                        WHERE id = ?
                    """, [ids[0]])
                    accounts_kept += 1
                    
                else:
                    # Cuentas duplicadas: mantener la primera, eliminar las demás
                    account_to_keep = ids[0]
                    accounts_to_remove = ids[1:]
                    
                    # Actualizar referencias en journal lines para que apunten a la cuenta que mantenemos
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("""
                            UPDATE accounting_journal_entry_lines 
                            SET account_id = ? 
                            WHERE account_id = ?
                        """, [account_to_keep, account_to_remove])
                    
                    # Actualizar otras referencias (inventory, treasury, etc.)
                    # BankAccount
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("""
                            UPDATE treasury_bankaccount 
                            SET accounting_account_id = ? 
                            WHERE accounting_account_id = ?
                        """, [account_to_keep, account_to_remove])
                    
                    # CashAccount
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("""
                            UPDATE treasury_cashaccount 
                            SET accounting_account_id = ? 
                            WHERE accounting_account_id = ?
                        """, [account_to_keep, account_to_remove])
                    
                    # Customer accounts
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("""
                            UPDATE accounts_receivable_customer 
                            SET receivable_account_id = ? 
                            WHERE receivable_account_id = ?
                        """, [account_to_keep, account_to_remove])
                        
                        cursor.execute("""
                            UPDATE accounts_receivable_customer 
                            SET advance_account_id = ? 
                            WHERE advance_account_id = ?
                        """, [account_to_keep, account_to_remove])
                    
                    # Supplier accounts
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("""
                            UPDATE accounts_payable_supplier 
                            SET payable_account_id = ? 
                            WHERE payable_account_id = ?
                        """, [account_to_keep, account_to_remove])
                        
                        cursor.execute("""
                            UPDATE accounts_payable_supplier 
                            SET advance_account_id = ? 
                            WHERE advance_account_id = ?
                        """, [account_to_keep, account_to_remove])
                        
                        cursor.execute("""
                            UPDATE accounts_payable_supplier 
                            SET expense_account_id = ? 
                            WHERE expense_account_id = ?
                        """, [account_to_keep, account_to_remove])
                    
                    # Ahora eliminar las cuentas duplicadas
                    for account_to_remove in accounts_to_remove:
                        cursor.execute("DELETE FROM accounting_accounts WHERE id = ?", [account_to_remove])
                    
                    # Actualizar la cuenta que mantenemos como estándar PUC
                    cursor.execute("""
                        UPDATE accounting_accounts 
                        SET chart_of_accounts_id = NULL
                        WHERE id = ?
                    """, [account_to_keep])
                    
                    accounts_kept += 1
                    accounts_updated += len(accounts_to_remove)
            
            print(f"[OK] Cuentas mantenidas: {accounts_kept}")
            print(f"[OK] Cuentas eliminadas: {accounts_updated}")
        
        # 3. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM accounting_accounts")
        total_accounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
        unique_codes = cursor.fetchone()[0]
        
        print(f"[OK] Total cuentas después: {total_accounts}")
        print(f"[OK] Códigos únicos: {unique_codes}")
        
        if total_accounts == unique_codes:
            print("[OK] Conversión completada. Todas las cuentas son ahora estándar PUC.")
            return True
        else:
            print("[ERROR] Aún existen duplicados")
            return False

if __name__ == "__main__":
    convert_to_standard_puc()