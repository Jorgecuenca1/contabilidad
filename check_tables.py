#!/usr/bin/env python
"""
Script para verificar las tablas de la base de datos.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%accounting%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print("Tablas de accounting:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Verificar si existen journal entry lines
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%journal%'
            ORDER BY name
        """)
        
        journal_tables = cursor.fetchall()
        print("\nTablas de journal:")
        for table in journal_tables:
            print(f"- {table[0]}")

if __name__ == "__main__":
    check_tables()