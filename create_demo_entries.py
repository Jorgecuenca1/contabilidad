#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company, User, Currency
from accounting.models import ChartOfAccounts, Account, JournalEntry, JournalEntryLine, JournalType

def create_demo_journal_entries():
    """Crear asientos contables de demostración"""
    
    # Obtener usuario admin
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("[ERROR] No admin user found.")
        return
    
    # Obtener empresa con cuentas
    company = Company.objects.filter(name__icontains='Manufactura').first()
    if not company:
        print("[ERROR] Company not found.")
        return
        
    chart = company.chart_of_accounts
    accounts = Account.objects.filter(chart_of_accounts=chart, is_detail=True)
    
    if accounts.count() < 4:
        print(f"[ERROR] Not enough detail accounts. Found: {accounts.count()}")
        return
    
    # Obtener tipo de diario
    journal_type, created = JournalType.objects.get_or_create(
        company=company,
        code='GJ',
        defaults={
            'name': 'Diario General', 
            'description': 'Diario General para asientos contables',
            'sequence_prefix': 'GJ-',
            'next_number': 1,
            'created_by': admin_user
        }
    )
    
    # Obtener moneda
    currency = Currency.objects.filter(code='COP').first()
    if not currency:
        currency = Currency.objects.first()
    
    if not currency:
        print("[ERROR] No currency found.")
        return
    
    print(f"[INFO] Creating demo entries for: {company.name}")
    print(f"[INFO] Using {accounts.count()} detail accounts")
    
    # Lista de cuentas disponibles
    account_list = list(accounts[:10])  # Usar las primeras 10 cuentas
    
    demo_entries = [
        # Asiento 1: Venta de mercancía
        {
            'description': 'Venta de mercancías del mes',
            'date': date.today() - timedelta(days=30),
            'lines': [
                {'account': account_list[0], 'debit': Decimal('1500000'), 'credit': Decimal('0')},
                {'account': account_list[1], 'debit': Decimal('0'), 'credit': Decimal('1500000')},
            ]
        },
        
        # Asiento 2: Compra de inventario
        {
            'description': 'Compra de inventario para reventa',
            'date': date.today() - timedelta(days=25),
            'lines': [
                {'account': account_list[2], 'debit': Decimal('800000'), 'credit': Decimal('0')},
                {'account': account_list[3], 'debit': Decimal('0'), 'credit': Decimal('800000')},
            ]
        },
        
        # Asiento 3: Pago de gastos operacionales
        {
            'description': 'Pago de gastos administrativos',
            'date': date.today() - timedelta(days=20),
            'lines': [
                {'account': account_list[4], 'debit': Decimal('300000'), 'credit': Decimal('0')},
                {'account': account_list[0], 'debit': Decimal('0'), 'credit': Decimal('300000')},
            ]
        },
        
        # Asiento 4: Pago a proveedores
        {
            'description': 'Pago a proveedores nacionales',
            'date': date.today() - timedelta(days=15),
            'lines': [
                {'account': account_list[5], 'debit': Decimal('500000'), 'credit': Decimal('0')},
                {'account': account_list[0], 'debit': Decimal('0'), 'credit': Decimal('500000')},
            ]
        },
        
        # Asiento 5: Recaudo de clientes
        {
            'description': 'Recaudo de cartera de clientes',
            'date': date.today() - timedelta(days=10),
            'lines': [
                {'account': account_list[0], 'debit': Decimal('1200000'), 'credit': Decimal('0')},
                {'account': account_list[6], 'debit': Decimal('0'), 'credit': Decimal('1200000')},
            ]
        }
    ]
    
    created_count = 0
    for entry_data in demo_entries:
        # Obtener siguiente número único
        import time
        unique_number = f"DEMO-{int(time.time())}-{created_count + 1}"
        
        # Crear asiento contable
        journal_entry = JournalEntry.objects.create(
            company=company,
            journal_type=journal_type,
            number=unique_number,
            date=entry_data['date'],
            description=entry_data['description'],
            currency=currency,
            reference=f'DEMO-{created_count + 1}',
            created_by=admin_user
        )
        
        # Crear líneas del asiento
        for line_data in entry_data['lines']:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=line_data['account'],
                debit=line_data['debit'],
                credit=line_data['credit'],
                description=entry_data['description']
            )
        
        created_count += 1
        print(f"[OK] Created journal entry: {journal_entry.number}")
    
    print(f"[COMPLETED] Created {created_count} demo journal entries")
    
    # Mostrar resumen de cuentas con movimientos
    print("\n[SUMMARY] Accounts with movements:")
    for account in account_list[:7]:  # Las que se usaron
        print(f"  - {account.code}: {account.name}")

if __name__ == '__main__':
    create_demo_journal_entries()