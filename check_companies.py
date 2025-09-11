#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company
from accounting.models import ChartOfAccounts

def check_companies():
    companies = Company.objects.all()
    print(f'Total companies: {companies.count()}')
    
    for company in companies:
        coa = ChartOfAccounts.objects.filter(company=company).first()
        has_chart = bool(coa)
        print(f'Company: {company.name} - Has Chart: {has_chart}')
        if has_chart:
            accounts_count = coa.accounts.count()
            print(f'  - Accounts count: {accounts_count}')

if __name__ == '__main__':
    check_companies()