#!/usr/bin/env python
"""
Script para eliminar cuentas duplicadas del PUC usando SQL directo.
"""

import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import connection

def clean_duplicate_accounts():
    """
    Elimina cuentas duplicadas manteniendo solo la primera de cada código.
    """
    print("Iniciando limpieza de cuentas duplicadas...")
    
    with connection.cursor() as cursor:
        # Contar duplicados antes
        cursor.execute("""
            SELECT code, COUNT(*) as count 
            FROM accounting_accounts 
            GROUP BY code 
            HAVING COUNT(*) > 1
            ORDER BY code
        """)
        
        duplicates = cursor.fetchall()
        print(f"Códigos duplicados encontrados: {len(duplicates)}")
        
        total_to_delete = 0
        for code, count in duplicates:
            print(f"- Código {code}: {count} cuentas")
            total_to_delete += count - 1  # Mantener 1, eliminar el resto
        
        print(f"Total de cuentas a eliminar: {total_to_delete}")
        
        if total_to_delete > 0:
            response = input(f"\n¿Eliminar {total_to_delete} cuentas duplicadas? (si/no): ")
            if response.lower() in ['si', 's', 'yes', 'y']:
                
                # Eliminar duplicados manteniendo el registro más antiguo (menor created_at)
                cursor.execute("""
                    DELETE FROM accounting_accounts 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM accounting_accounts 
                        GROUP BY code
                    )
                """)
                
                deleted_count = cursor.rowcount
                print(f"[OK] {deleted_count} cuentas duplicadas eliminadas")
                
                # Verificar resultado
                cursor.execute("SELECT COUNT(*) FROM accounting_accounts")
                total_remaining = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
                unique_codes = cursor.fetchone()[0]
                
                print(f"[OK] Cuentas restantes: {total_remaining}")
                print(f"[OK] Códigos únicos: {unique_codes}")
                
                if total_remaining == unique_codes:
                    print("[OK] No quedan duplicados")
                else:
                    print("[ERROR] Aún existen duplicados")
            else:
                print("Operación cancelada")
        else:
            print("No hay duplicados para eliminar")

if __name__ == "__main__":
    clean_duplicate_accounts()