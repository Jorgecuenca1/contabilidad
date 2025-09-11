import os

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
        print(f"Fixing {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check if it has the import already
        has_import = any('from core.utils import get_current_company, require_company_access' in line for line in lines[:20])
        
        if not has_import:
            # Find where to insert
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('from django') or line.startswith('from .'):
                    insert_pos = i + 1
                elif line.startswith('from core.models'):
                    insert_pos = i + 1
                    break
            
            lines.insert(insert_pos, 'from core.utils import get_current_company, require_company_access')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"Fixed {file_path}")

print("Done!")