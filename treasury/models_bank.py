"""
Modelos de bancos y cuentas bancarias.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Period, Currency
from accounting.models_accounts import Account


class Bank(models.Model):
    """
    Entidades bancarias.
    """
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Configuración para conciliación
    statement_format = models.CharField(max_length=20, default='csv', help_text="Formato de extractos")
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'treasury_banks'
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class BankAccount(models.Model):
    """
    Cuentas bancarias de la empresa.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Cuenta Corriente'),
        ('savings', 'Cuenta de Ahorros'),
        ('credit', 'Línea de Crédito'),
        ('investment', 'Cuenta de Inversión'),
        ('payroll', 'Cuenta de Nómina'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('closed', 'Cerrada'),
        ('blocked', 'Bloqueada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    
    # Configuración
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Límites
    overdraft_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cuenta contable
    accounting_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='bank_accounts')
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Configuración de conciliación
    auto_reconcile = models.BooleanField(default=False)
    reconcile_tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bank_accounts_created')
    
    class Meta:
        db_table = 'treasury_bank_accounts'
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
        unique_together = ['company', 'code']
        ordering = ['code']
        indexes = [
            models.Index(fields=['company', 'bank']),
            models.Index(fields=['account_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.bank.name})"
    
    def get_available_balance(self):
        """Obtiene el saldo disponible (incluyendo sobregiro)."""
        return self.current_balance + self.overdraft_limit
    
    def update_balance(self, amount):
        """Actualiza el saldo de la cuenta."""
        self.current_balance += amount
        self.save(update_fields=['current_balance'])


class CashAccount(models.Model):
    """
    Cuentas de caja (efectivo).
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('closed', 'Cerrada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cash_accounts')
    
    # Identificación
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100, blank=True)
    
    # Configuración
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Límites
    max_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cuenta contable
    accounting_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='cash_accounts')
    
    # Responsable
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_cash_accounts')
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_accounts_created')
    
    class Meta:
        db_table = 'treasury_cash_accounts'
        verbose_name = 'Cuenta de Caja'
        verbose_name_plural = 'Cuentas de Caja'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def update_balance(self, amount):
        """Actualiza el saldo de la caja."""
        self.current_balance += amount
        self.save(update_fields=['current_balance'])




