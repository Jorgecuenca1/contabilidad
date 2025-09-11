import os

# Lista completa de archivos que contienen @require_company_access
files_to_fix = [
    'accounting/views.py',
    'accounts_payable/views.py',
    'accounts_receivable/views.py',
    'budget/views.py',
    'fixed_assets/views.py',
    'inventory/views.py',
    'payroll/views.py',
    'public_sector/views.py',
    'reports/views.py',
    'taxes/views.py',
    'third_parties/views.py',
    'treasury/views.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Processing {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if needs import
        has_decorator = '@require_company_access' in content
        has_import = 'from core.utils import get_current_company, require_company_access' in content
        
        if has_decorator and not has_import:
            lines = content.split('\n')
            
            # Find position after last import
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    import_end = i + 1
                elif line.strip() and not line.startswith('#') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                    break
            
            # Insert the import after other imports
            lines.insert(import_end, 'from core.utils import get_current_company, require_company_access')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"  FIXED {file_path}")
        else:
            print(f"  OK {file_path}")

print("All files processed successfully!")