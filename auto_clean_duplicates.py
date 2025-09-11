#!/usr/bin/env python
"""
Script para eliminar automáticamente cuentas duplicadas del PUC.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import connection, transaction

def auto_clean_duplicates():
    """
    Elimina automáticamente cuentas duplicadas manteniendo solo la primera de cada código.
    """
    print("Limpiando cuentas duplicadas automáticamente...")
    
    with connection.cursor() as cursor:
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM accounting_accounts")
        total_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
        unique_codes_before = cursor.fetchone()[0]
        
        print(f"Antes: {total_before} cuentas, {unique_codes_before} códigos únicos")
        print(f"Duplicados: {total_before - unique_codes_before} cuentas")
        
        if total_before > unique_codes_before:
            with transaction.atomic():
                # Eliminar duplicados manteniendo el registro más antiguo
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
            total_after = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
            unique_codes_after = cursor.fetchone()[0]
            
            print(f"Después: {total_after} cuentas, {unique_codes_after} códigos únicos")
            
            if total_after == unique_codes_after:
                print("[OK] Limpieza completada. No quedan duplicados.")
                return True
            else:
                print("[ERROR] Aún existen duplicados")
                return False
        else:
            print("No hay duplicados para limpiar")
            return True

if __name__ == "__main__":
    auto_clean_duplicates()