"""
Modelos para el módulo de Activos Fijos.
Incluye activos, depreciación y movimientos.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import Company, User, Period, Currency
from accounting.models_accounts import Account, CostCenter, Project

# Importar todos los modelos de fixed_assets
from .models_asset import AssetCategory, FixedAsset
