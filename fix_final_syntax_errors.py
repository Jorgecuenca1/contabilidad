#!/usr/bin/env python3
"""
Script para arreglar los errores de sintaxis finales en los archivos de views
que quedaron después de las modificaciones automatizadas.
"""

import os
import re

def fix_syntax_errors():
    """Arreglar los errores de sintaxis en los archivos de views."""
    
    view_files = [
        'accounting/views.py',
        'accounts_payable/views.py', 
        'accounts_receivable/views.py',
        'treasury/views.py',
        'payroll/views.py',
        'taxes/views.py'
    ]
    
    for file_path in view_files:
        if os.path.exists(file_path):
            print(f"Arreglando {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detectar si el archivo tiene errores de imports mal ubicados dentro de try/except
            lines = content.split('\n')
            new_lines = []
            found_import_in_try = False
            
            for i, line in enumerate(lines):
                # Si encontramos un import dentro de un try block, lo movemos al principio
                if 'from core.utils import get_current_company, require_company_access' in line:
                    # Verificar si está dentro de un try/except mal ubicado
                    if i > 0:
                        prev_lines = lines[max(0, i-10):i]
                        if any('try:' in prev_line and 'except' not in prev_line for prev_line in prev_lines):
                            found_import_in_try = True
                            continue  # Saltamos esta línea, la agregaremos al principio
                
                new_lines.append(line)
            
            # Si encontramos import mal ubicado, agregar al principio después de otros imports
            if found_import_in_try:
                final_lines = []
                import_section_ended = False
                
                for line in new_lines:
                    final_lines.append(line)
                    
                    # Detectar el final de la sección de imports para agregar nuestro import
                    if (line.startswith('from ') or line.startswith('import ')) and not import_section_ended:
                        continue
                    elif not import_section_ended and line.strip() == '':
                        continue
                    elif not import_section_ended and not (line.startswith('from ') or line.startswith('import ') or line.strip() == '' or line.startswith('#') or line.startswith('"""') or line.startswith("'''")):
                        # Insertar nuestro import antes de esta línea
                        final_lines.insert(-1, 'from core.utils import get_current_company, require_company_access')
                        final_lines.insert(-1, '')
                        import_section_ended = True
                
                new_lines = final_lines
            
            # Verificar si ya tiene el import correcto al principio
            has_correct_import = any('from core.utils import get_current_company, require_company_access' in line 
                                   for line in new_lines[:20])
            
            if not has_correct_import:
                # Encontrar donde insertar el import
                insert_index = 0
                for i, line in enumerate(new_lines):
                    if line.startswith('from ') or line.startswith('import '):
                        insert_index = i + 1
                    elif not line.strip() or line.startswith('#'):
                        continue
                    else:
                        break
                
                new_lines.insert(insert_index, 'from core.utils import get_current_company, require_company_access')
                new_lines.insert(insert_index + 1, '')
            
            # Escribir el archivo corregido
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print(f"✓ Arreglado {file_path}")
    
    print("\n🎉 Corrección de errores de sintaxis completada!")

if __name__ == "__main__":
    fix_syntax_errors()