#!/usr/bin/env python3
"""
Script final para arreglar TODOS los archivos que tienen @require_company_access 
pero no tienen la importación correcta
"""

import os
import re

def fix_all_remaining_files():
    """Arreglar todos los archivos que tienen decorators pero faltan imports."""
    
    # Buscar todos los archivos views.py en el proyecto
    view_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'views.py' and not root.startswith('./.'):
                view_files.append(os.path.join(root, file))
    
    for file_path in view_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si tiene el decorador pero no el import
            has_decorator = '@require_company_access' in content
            has_import = 'from core.utils import get_current_company, require_company_access' in content
            
            if has_decorator and not has_import:
                print(f"Arreglando {file_path}...")
                
                lines = content.split('\n')
                
                # Encontrar donde insertar el import (después de otros imports)
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        insert_index = i + 1
                    elif line.strip() and not line.startswith('#') and not line.startswith('"""'):
                        break
                
                # Insertar el import
                lines.insert(insert_index, 'from core.utils import get_current_company, require_company_access')
                
                # Escribir el archivo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print(f"  ✓ Arreglado {file_path}")
            else:
                print(f"  - {file_path} ya está correcto")
                
        except Exception as e:
            print(f"  ✗ Error en {file_path}: {e}")
    
    print("\n🎉 Corrección completa finalizada!")

if __name__ == "__main__":
    fix_all_remaining_files()