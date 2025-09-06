"""
Modelos para el módulo de Cuentas por Cobrar (CxC).
Incluye clientes, facturas, notas crédito/débito, pagos y gestión de cartera.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Period, Currency
from accounting.models_accounts import Account, CostCenter, Project

# Importar todos los modelos de accounts_receivable
from .models_customer import CustomerType, Customer
from .models_invoice import Invoice, InvoiceLine
from .models_payment import Payment, PaymentAllocation, CustomerStatement
