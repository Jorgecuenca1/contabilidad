import os

# Lista específica de archivos que sabemos que necesitan el fix
files_to_fix = [
    'budget/views.py',
    'public_sector/views.py',
    'reports/views.py',
    'payroll/views.py',
    'taxes/views.py',
    'treasury/views.py',
    'third_parties/views.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Checking {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if has decorator but not import
        has_decorator = '@require_company_access' in content
        has_import = 'from core.utils import get_current_company, require_company_access' in content
        
        if has_decorator and not has_import:
            print(f"Fixing {file_path}...")
            
            lines = content.split('\n')
            
            # Find where to insert import
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_index = i + 1
                elif line.strip() and not line.startswith('#') and not line.startswith('"""'):
                    break
            
            # Insert the import
            lines.insert(insert_index, 'from core.utils import get_current_company, require_company_access')
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"Fixed {file_path}")

print("Done!")