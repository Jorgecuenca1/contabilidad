#!/usr/bin/env python
"""
Script para eliminar selectores de empresa de todas las plantillas.
"""

import os
import re
import glob

def remove_company_selectors():
    """
    Elimina selectores de empresa de todas las plantillas HTML.
    """
    template_files = glob.glob('templates/**/*.html', recursive=True)
    
    print(f"Procesando {len(template_files)} archivos de plantillas...")
    
    # Patrones para detectar selectores de empresa
    company_select_patterns = [
        r'<div[^>]*>[\s\S]*?<label[^>]*>.*?[Ee]mpresa.*?</label>[\s\S]*?<select[^>]*name=["\']company["\'][^>]*>[\s\S]*?</select>[\s\S]*?</div>',
        r'<div[^>]*col[^>]*>[\s\S]*?<label[^>]*>.*?[Ee]mpresa.*?</label>[\s\S]*?<select[^>]*name=["\']company["\'][^>]*>[\s\S]*?</select>[\s\S]*?</div>',
    ]
    
    # Plantilla de reemplazo
    company_info_replacement = '''                        <!-- Empresa Seleccionada -->
                        <div class="col-12 mb-3">
                            <div class="alert alert-info">
                                <i class="bi bi-building"></i> <strong>Empresa:</strong> {{ current_company.name }}{% if current_company.tax_id %} - {{ current_company.tax_id }}{% endif %}
                                <small class="d-block">Trabajando con la empresa seleccionada en el dashboard</small>
                            </div>
                        </div>'''
    
    files_updated = 0
    
    for file_path in template_files:
        if 'dashboard.html' in file_path and 'core' in file_path:
            # No tocar el dashboard principal
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Buscar y reemplazar selectores de empresa
            for pattern in company_select_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    content = re.sub(pattern, company_info_replacement, content, flags=re.IGNORECASE | re.MULTILINE)
                    print(f"  Actualizado: {file_path}")
            
            # También buscar patrones más simples
            simple_patterns = [
                (r'<option value="">Seleccione empresa\.\.\.</option>[\s\S]*?{% for company in companies %}[\s\S]*?{% endfor %}', ''),
                (r'{% for company in companies %}[\s\S]*?<option value="{{ company\.id }}">.*?</option>[\s\S]*?{% endfor %}', ''),
            ]
            
            for pattern, replacement in simple_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
            
            # Si hubo cambios, escribir el archivo
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_updated += 1
                
        except Exception as e:
            print(f"  Error procesando {file_path}: {e}")
    
    print(f"\nActualización completada:")
    print(f"- Archivos procesados: {len(template_files)}")
    print(f"- Archivos actualizados: {files_updated}")

if __name__ == "__main__":
    remove_company_selectors()