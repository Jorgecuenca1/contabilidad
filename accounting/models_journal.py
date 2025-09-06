"""
Modelos para diarios contables y asientos.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid
import hashlib

from core.models import Company, User, Period, Currency
from .models_accounts import Account, CostCenter, Project


class JournalType(models.Model):
    """
    Tipos de diarios contables (Ventas, Compras, Bancos, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_types')
    
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración de numeración
    sequence_prefix = models.CharField(max_length=10, blank=True)
    next_number = models.IntegerField(default=1)
    
    # Configuración
    requires_approval = models.BooleanField(default=False)
    auto_post = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_journal_types'
        verbose_name = 'Tipo de Diario'
        verbose_name_plural = 'Tipos de Diario'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_next_sequence(self):
        """Obtiene el siguiente número de secuencia."""
        sequence = f"{self.sequence_prefix}{self.next_number:06d}"
        self.next_number += 1
        self.save(update_fields=['next_number'])
        return sequence


class JournalEntry(models.Model):
    """
    Asientos contables del sistema de doble partida.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('posted', 'Contabilizado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    journal_type = models.ForeignKey(JournalType, on_delete=models.PROTECT, related_name='entries')
    period = models.ForeignKey(Period, on_delete=models.PROTECT, null=True, blank=True)
    
    # Identificación
    number = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    
    # Fechas
    date = models.DateField()
    posting_date = models.DateTimeField(null=True, blank=True)
    
    # Montos
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado y control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_balanced = models.BooleanField(default=False)
    
    # Hash para integridad
    hash_value = models.CharField(max_length=64, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='journal_entries_created')
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='journal_entries_posted')
    
    class Meta:
        db_table = 'accounting_journal_entries'
        verbose_name = 'Asiento Contable'
        verbose_name_plural = 'Asientos Contables'
        unique_together = ['company', 'number']
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['journal_type']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        """Validaciones y cálculos antes de guardar."""
        if not self.number:
            self.number = self.journal_type.get_next_sequence()
        
        # Calcular totales
        self.calculate_totals()
        
        # Generar hash para integridad
        self.generate_hash()
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calcula los totales de débito y crédito."""
        lines = self.lines.all()
        self.total_debit = sum(line.debit for line in lines)
        self.total_credit = sum(line.credit for line in lines)
        self.is_balanced = self.total_debit == self.total_credit
    
    def generate_hash(self):
        """Genera hash para verificar integridad del asiento."""
        data = f"{self.company_id}{self.number}{self.date}{self.total_debit}{self.total_credit}"
        self.hash_value = hashlib.sha256(data.encode()).hexdigest()
    
    def post(self, user):
        """Contabiliza el asiento."""
        if self.status != 'draft':
            raise ValidationError("Solo se pueden contabilizar asientos en borrador")
        
        if not self.is_balanced:
            raise ValidationError("El asiento debe estar balanceado")
        
        self.status = 'posted'
        self.posting_date = timezone.now()
        self.posted_by = user
        self.save()
    
    def cancel(self):
        """Cancela el asiento."""
        if self.status == 'posted':
            raise ValidationError("No se puede cancelar un asiento contabilizado")
        
        self.status = 'cancelled'
        self.save()


class JournalEntryLine(models.Model):
    """
    Líneas de los asientos contables (movimientos individuales).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    
    # Cuenta contable
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    
    # Descripción del movimiento
    description = models.CharField(max_length=200)
    
    # Montos
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Dimensiones analíticas
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Referencia adicional
    third_party_id = models.CharField(max_length=50, blank=True, help_text="ID del tercero")
    
    # Orden en el asiento
    line_number = models.IntegerField(default=1)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounting_journal_entry_lines'
        verbose_name = 'Línea de Asiento'
        verbose_name_plural = 'Líneas de Asiento'
        ordering = ['journal_entry', 'line_number']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['cost_center']),
            models.Index(fields=['project']),
        ]
    
    def __str__(self):
        return f"{self.journal_entry.number} - {self.account.code} - {self.description[:30]}"
    
    def clean(self):
        """Validaciones del modelo."""
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Una línea no puede tener débito y crédito al mismo tiempo")
        
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Una línea debe tener débito o crédito")
        
        if not self.account.is_detail:
            raise ValidationError("Solo se pueden usar cuentas de detalle en los asientos")
    
    def save(self, *args, **kwargs):
        """Validaciones antes de guardar."""
        self.clean()
        super().save(*args, **kwargs)
        
        # Recalcular totales del asiento padre
        if self.journal_entry_id:
            self.journal_entry.calculate_totals()
            self.journal_entry.save(update_fields=['total_debit', 'total_credit', 'is_balanced'])

