#!/usr/bin/env python
"""
Script simple para eliminar duplicados sin actualizar referencias.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import connection, transaction

def simple_dedup():
    """
    Elimina cuentas duplicadas manteniendo solo la primera por código.
    """
    print("Eliminando duplicados simples...")
    
    with connection.cursor() as cursor:
        
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM accounting_accounts")
        total_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
        unique_codes = cursor.fetchone()[0]
        
        print(f"Antes: {total_before} cuentas, {unique_codes} códigos únicos")
        
        if total_before == unique_codes:
            print("No hay duplicados")
            return
        
        # Obtener IDs para eliminar (mantener el primer ID de cada código)
        cursor.execute("""
            SELECT a1.id 
            FROM accounting_accounts a1
            WHERE EXISTS (
                SELECT 1 FROM accounting_accounts a2 
                WHERE a2.code = a1.code AND a2.id < a1.id
            )
        """)
        
        ids_to_delete = [row[0] for row in cursor.fetchall()]
        print(f"Cuentas a eliminar: {len(ids_to_delete)}")
        
        if ids_to_delete:
            try:
                with transaction.atomic():
                    # Eliminar cuentas duplicadas
                    placeholders = ','.join(['?' for _ in ids_to_delete])
                    cursor.execute(f"DELETE FROM accounting_accounts WHERE id IN ({placeholders})", ids_to_delete)
                    
                    print(f"[OK] {len(ids_to_delete)} cuentas eliminadas")
            except Exception as e:
                print(f"[ERROR] No se pudieron eliminar las cuentas: {e}")
                print("Probablemente hay referencias de foreign keys. Necesita limpieza manual.")
                return False
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM accounting_accounts")
        total_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT code) FROM accounting_accounts")
        unique_after = cursor.fetchone()[0]
        
        print(f"Después: {total_after} cuentas, {unique_after} códigos únicos")
        
        if total_after == unique_after:
            print("[OK] Todos los duplicados eliminados")
            return True
        else:
            print("[ERROR] Aún hay duplicados")
            return False

if __name__ == "__main__":
    simple_dedup()