#!/usr/bin/env python
"""
Script para actualizar todas las vistas para que usen la empresa de la sesión.
"""

import os
import re
import glob

def update_views_for_session_company():
    """
    Actualiza todas las vistas para usar la empresa de la sesión.
    """
    view_files = glob.glob('*/views.py')
    
    print(f"Procesando {len(view_files)} archivos de vistas...")
    
    files_updated = 0
    
    for file_path in view_files:
        # Saltar el views.py de core que maneja la selección de empresa
        if 'core' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 1. Agregar imports si no existen
            if 'from core.utils import get_current_company, require_company_access' not in content:
                # Buscar el último import de core.models o similar
                import_pattern = r'(from core\.models import.*?\n)'
                if re.search(import_pattern, content):
                    content = re.sub(
                        import_pattern,
                        r'\1from core.utils import get_current_company, require_company_access\n',
                        content
                    )
                else:
                    # Si no hay imports de core, agregar después de los imports de Django
                    django_imports_end = re.search(r'(from django\..*?\n)(?!\n*from django\.)', content, re.MULTILINE | re.DOTALL)
                    if django_imports_end:
                        content = content[:django_imports_end.end()] + '\nfrom core.utils import get_current_company, require_company_access\n' + content[django_imports_end.end():]
            
            # 2. Actualizar funciones de vista
            # Patrón para detectar vistas que usan company_id del POST
            company_post_pattern = r'(\s+company_id = request\.POST\.get\([\'"]company[\'"]\).*?\n\s+.*?company = Company\.objects\.get\(id=company_id\))'
            
            if re.search(company_post_pattern, content, re.MULTILINE):
                # Reemplazar por empresa de la sesión
                content = re.sub(
                    company_post_pattern,
                    r'\n                company = current_company',
                    content,
                    flags=re.MULTILINE
                )
                print(f"  - Actualizada lógica POST en: {file_path}")
            
            # 3. Agregar decorator @require_company_access a vistas que necesitan empresa
            view_functions = re.findall(r'@login_required\ndef (\w+)\(request\):', content)
            
            for func_name in view_functions:
                # No actualizar vistas que ya tienen el decorator
                if f'@require_company_access\ndef {func_name}' in content:
                    continue
                    
                # Agregar el decorator y la variable current_company
                old_pattern = rf'@login_required\ndef {func_name}\(request\):'
                new_pattern = f'@login_required\n@require_company_access\ndef {func_name}(request):\n    current_company = request.current_company\n'
                
                if re.search(old_pattern, content):
                    content = re.sub(old_pattern, new_pattern, content)
                    print(f"  - Agregado decorator a {func_name} en: {file_path}")
            
            # 4. Actualizar contextos que incluyen 'companies'
            context_pattern = r"'companies': Company\.objects\.filter\(is_active=True\),"
            if re.search(context_pattern, content):
                content = re.sub(context_pattern, "'current_company': current_company,", content)
                print(f"  - Actualizado contexto en: {file_path}")
            
            # Si hubo cambios, escribir el archivo
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_updated += 1
                
        except Exception as e:
            print(f"  Error procesando {file_path}: {e}")
    
    print(f"\nActualización completada:")
    print(f"- Archivos procesados: {len(view_files)}")
    print(f"- Archivos actualizados: {files_updated}")

if __name__ == "__main__":
    update_views_for_session_company()