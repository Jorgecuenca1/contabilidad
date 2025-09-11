# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Django-based Multi-Company Accounting System** (Sistema Contable Multiempresa) fully adapted for Colombian accounting standards and regulations. The system is a complete ERP solution with modules for accounting, payroll, taxes, treasury, accounts payable/receivable, and more.

## Development Commands

### Starting the Development Server
```bash
python manage.py runserver
```
Access at: http://127.0.0.1:8000/
- Default credentials: admin/admin

### Database Management
```bash
# Create new migrations after model changes
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Load initial demo data (companies, users, accounts)
python manage.py load_demo_data

# Load missing data if needed
python manage.py load_missing_data
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounting
python manage.py test accounts_payable
python manage.py test payroll
```

## Architecture

### Core Structure
The system follows a modular Django architecture with each business domain as a separate app:

- **core**: Base models (Company, User, Currency, Period, CostCenter)
- **accounting**: Journal entries, chart of accounts (PUC), voucher types
- **accounts_receivable**: Sales invoices, customer payments, client management
- **accounts_payable**: Purchase invoices, supplier payments, vendor management  
- **treasury**: Bank movements, bank reconciliation
- **payroll**: Employee management, Colombian social security (EPS, Pensión, ARL, CCF)
- **taxes**: Tax declarations (DIAN), IVA, withholdings
- **reports**: Financial and operational reporting

### Key Technical Details

- **Multi-tenancy**: Complete data segregation by company using foreign keys
- **Double-entry bookkeeping**: Automatic validation of debit/credit balance
- **Colombian compliance**: PUC (Plan Único de Cuentas), 18 voucher types, DIAN requirements
- **Automatic accounting**: All transactions auto-generate journal entries
- **Custom HTML interfaces**: No Django Admin dependency, Bootstrap 5 UI

### Database
- SQLite for development (db.sqlite3)
- Models use Django ORM with proper relationships and constraints
- All models include company foreign key for multi-tenancy

### Important Models Relationships
- Every transaction model has `company` and `created_by` fields
- JournalEntry uses `voucher_type` for Colombian compliance
- All financial documents auto-create JournalEntry records
- BankAccount links to ChartAccount for automatic posting

## Colombian Accounting Standards

The system implements:
- **PUC** (Plan Único de Cuentas): Full Colombian chart of accounts
- **Voucher Types**: CI, CE, CG, CC, CN, CB, CA, CR, CP, CT, CX, CO, CK, CS, CV, CM
- **Tax rates**: IVA 19%, 5%, withholdings as per DIAN
- **Social Security**: EPS, Pension, ARL, CCF with correct percentages
- **DIAN compliance**: Forms for IVA, Renta, ICA declarations

## Development Notes

- Always maintain double-entry accounting balance in journal entries
- Ensure all financial operations create appropriate journal entries
- Use existing voucher types; don't create new ones without Colombian accounting justification
- Preserve multi-company data segregation in all queries
- Follow existing UI patterns using Bootstrap 5 and vanilla JavaScript
- Templates are in `templates/` organized by app name