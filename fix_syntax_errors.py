#!/usr/bin/env python
"""
Script para corregir errores de sintaxis causados por imports duplicados.
"""

import os
import re
import glob

def fix_syntax_errors():
    """
    Corrige errores de sintaxis en archivos de vistas.
    """
    view_files = glob.glob('*/views.py')
    
    print(f"Corrigiendo errores de sintaxis en {len(view_files)} archivos...")
    
    files_fixed = 0
    
    for file_path in view_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Buscar imports duplicados mal colocados
            # Patrón: líneas que empiezan directamente con "from core.utils import" sin indentación
            pattern1 = r'^from core\.utils import get_current_company, require_company_access$'
            
            # Si encuentra este patrón, lo elimina (ya está importado arriba)
            if re.search(pattern1, content, re.MULTILINE):
                content = re.sub(pattern1, '', content, flags=re.MULTILINE)
                print(f"  - Eliminado import duplicado en: {file_path}")
            
            # Patrón 2: imports mal ubicados dentro de try/except
            pattern2 = r'(\s+)(from core\.utils import get_current_company, require_company_access\s*\n)'
            if re.search(pattern2, content):
                content = re.sub(pattern2, '', content)
                print(f"  - Eliminado import mal ubicado en: {file_path}")
            
            # Si hubo cambios, escribir el archivo
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed += 1
                
        except Exception as e:
            print(f"  Error procesando {file_path}: {e}")
    
    print(f"\nCorreción completada:")
    print(f"- Archivos procesados: {len(view_files)}")
    print(f"- Archivos corregidos: {files_fixed}")

if __name__ == "__main__":
    fix_syntax_errors()