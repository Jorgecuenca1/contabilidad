"""
Modelos para el módulo de Inventarios.
Incluye productos, bodegas, movimientos y control de stock.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Period, Currency
from accounting.models_accounts import Account, CostCenter, Project

# Importar todos los modelos de inventory
from .models_product import ProductCategory, UnitOfMeasure, Product
