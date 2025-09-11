"""
Servicios para el módulo de activos fijos.
Incluye cálculo y contabilización automática de depreciación.
"""

from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal
from datetime import date

from core.models import Company
from accounting.models_accounts import Account
from accounting.models_journal import JournalEntry, JournalEntryLine, JournalType
from .models_asset import FixedAsset, DepreciationEntry


class DepreciationService:
    """
    Servicio para manejo de depreciación de activos fijos.
    """
    
    def __init__(self, company):
        self.company = company
        
    def calculate_period_depreciation(self, year, month, assets=None):
        """
        Calcula la depreciación de un período para los activos especificados.
        """
        if assets is None:
            assets = FixedAsset.objects.filter(
                company=self.company,
                status='active'
            )
        
        results = []
        
        for asset in assets:
            # Verificar si ya existe un registro para este período
            existing_entry = DepreciationEntry.objects.filter(
                company=self.company,
                asset=asset,
                period_year=year,
                period_month=month
            ).first()
            
            if existing_entry:
                continue
                
            # Calcular depreciación mensual
            monthly_depreciation = asset.calculate_monthly_depreciation()
            
            if monthly_depreciation > 0:
                # Crear registro de depreciación
                depreciation_entry = DepreciationEntry(
                    company=self.company,
                    asset=asset,
                    period_year=year,
                    period_month=month,
                    depreciation_date=date(year, month, min(28, date(year, month, 1).replace(day=1, month=month+1 if month < 12 else 1, year=year if month < 12 else year+1).day-1)),
                    currency=asset.currency,
                    depreciation_amount=monthly_depreciation,
                    accumulated_before=asset.accumulated_depreciation,
                    method_used=asset.depreciation_method,
                    status='draft'
                )
                
                results.append(depreciation_entry)
        
        return results
    
    @transaction.atomic
    def process_period_depreciation(self, year, month, user, assets=None, create_journal_entries=True):
        """
        Procesa la depreciación del período y crea los asientos contables.
        """
        depreciation_entries = self.calculate_period_depreciation(year, month, assets)
        processed_entries = []
        
        for entry in depreciation_entries:
            entry.created_by = user
            entry.save()
            
            # Actualizar activo
            entry.asset.accumulated_depreciation = entry.accumulated_after
            entry.asset.net_book_value = entry.asset.acquisition_cost - entry.asset.accumulated_depreciation
            entry.asset.save()
            
            # Crear asiento contable si se solicita
            if create_journal_entries:
                journal_entry = self._create_depreciation_journal_entry(entry, user)
                entry.journal_entry = journal_entry
                entry.status = 'posted'
                entry.save()
            
            processed_entries.append(entry)
        
        return processed_entries
    
    def _create_depreciation_journal_entry(self, depreciation_entry, user):
        """
        Crea el asiento contable para la depreciación.
        """
        asset = depreciation_entry.asset
        category = asset.category
        
        # Obtener tipo de comprobante para depreciación
        voucher_type = JournalType.objects.filter(
            company=self.company,
            code='CD'  # Comprobante de Depreciación
        ).first()
        
        if not voucher_type:
            # Usar comprobante de egreso como alternativa
            voucher_type = JournalType.objects.filter(
                company=self.company,
                code='CE'
            ).first()
        
        # Generar número de comprobante
        next_number = JournalEntry.objects.filter(
            company=self.company,
            voucher_type=voucher_type,
            period__year=depreciation_entry.period_year
        ).count() + 1
        
        voucher_number = f"{voucher_type.code}-{depreciation_entry.period_year}-{next_number:06d}"
        
        # Crear el asiento
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            voucher_type=voucher_type,
            voucher_number=voucher_number,
            transaction_date=depreciation_entry.depreciation_date,
            description=f"Depreciación {asset.code} - {asset.name} - {depreciation_entry.period_month:02d}/{depreciation_entry.period_year}",
            reference_document=f"DEP-{asset.code}",
            currency=depreciation_entry.currency,
            total_debit=depreciation_entry.depreciation_amount,
            total_credit=depreciation_entry.depreciation_amount,
            created_by=user
        )
        
        # Línea de débito - Gasto por depreciación
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=category.expense_account,
            cost_center=asset.cost_center,
            description=f"Gasto depreciación {asset.name}",
            debit=depreciation_entry.depreciation_amount,
            credit=Decimal('0')
        )
        
        # Línea de crédito - Depreciación acumulada
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=category.depreciation_account,
            cost_center=asset.cost_center,
            description=f"Depreciación acumulada {asset.name}",
            debit=Decimal('0'),
            credit=depreciation_entry.depreciation_amount
        )
        
        # Actualizar número de comprobante en el entry
        depreciation_entry.voucher_number = voucher_number
        
        return journal_entry
    
    def get_depreciation_schedule(self, asset, start_date=None):
        """
        Genera el cronograma de depreciación para un activo.
        """
        if not start_date:
            start_date = asset.start_depreciation_date
        
        schedule = []
        current_date = start_date
        remaining_cost = asset.depreciable_amount
        accumulated = Decimal('0')
        
        # Calcular depreciación mensual
        monthly_depreciation = asset.calculate_monthly_depreciation()
        
        total_months = (asset.useful_life_years * 12) + asset.useful_life_months
        
        for month in range(total_months):
            if remaining_cost <= 0:
                break
                
            # Ajustar último período si es necesario
            if month == total_months - 1:
                depreciation_amount = remaining_cost
            else:
                depreciation_amount = min(monthly_depreciation, remaining_cost)
            
            accumulated += depreciation_amount
            remaining_cost -= depreciation_amount
            
            schedule.append({
                'period': month + 1,
                'date': current_date,
                'depreciation': depreciation_amount,
                'accumulated': accumulated,
                'book_value': asset.acquisition_cost - accumulated
            })
            
            # Siguiente mes
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return schedule
    
    def validate_depreciation_compliance(self, asset):
        """
        Valida que la depreciación cumpla con las normas colombianas.
        """
        issues = []
        
        # Validar tasa máxima DIAN
        if not asset.validate_colombian_compliance():
            max_rate = asset.get_colombian_max_depreciation_rate()
            current_rate = (asset.calculate_monthly_depreciation() * 12 / asset.acquisition_cost * 100)
            issues.append({
                'type': 'tax_compliance',
                'message': f'Tasa de depreciación ({current_rate:.2f}%) excede máximo DIAN ({max_rate:.2f}%)',
                'severity': 'error'
            })
        
        # Validar vida útil mínima
        if asset.useful_life_years < 1:
            issues.append({
                'type': 'useful_life',
                'message': 'Vida útil debe ser al menos 1 año',
                'severity': 'error'
            })
        
        # Validar valor residual
        if asset.residual_value >= asset.acquisition_cost:
            issues.append({
                'type': 'residual_value',
                'message': 'Valor residual debe ser menor al costo de adquisición',
                'severity': 'error'
            })
        
        # Validar activos de menor cuantía para 2024/2025
        uvt_2024 = 47065
        uvt_2025 = 49799
        minor_threshold_2024 = uvt_2024 * 50  # $2,353,250
        minor_threshold_2025 = uvt_2025 * 50  # $2,489,950
        
        current_year = timezone.now().year
        if current_year == 2024 and asset.acquisition_cost <= minor_threshold_2024:
            issues.append({
                'type': 'minor_asset',
                'message': f'Activo menor cuantía 2024 (≤${minor_threshold_2024:,.0f}) puede depreciarse 100% en año de adquisición',
                'severity': 'info'
            })
        elif current_year >= 2025 and asset.acquisition_cost <= minor_threshold_2025:
            issues.append({
                'type': 'minor_asset',
                'message': f'Activo menor cuantía 2025 (≤${minor_threshold_2025:,.0f}) puede depreciarse 100% en año de adquisición',
                'severity': 'info'
            })
        
        return issues
    
    def get_period_summary(self, year, month):
        """
        Obtiene resumen de depreciación del período.
        """
        entries = DepreciationEntry.objects.filter(
            company=self.company,
            period_year=year,
            period_month=month
        )
        
        return {
            'total_entries': entries.count(),
            'total_depreciation': entries.aggregate(
                total=models.Sum('depreciation_amount')
            )['total'] or Decimal('0'),
            'posted_entries': entries.filter(status='posted').count(),
            'draft_entries': entries.filter(status='draft').count(),
        }