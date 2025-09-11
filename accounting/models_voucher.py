"""
Modelos para tipos de comprobantes contables colombianos.
Implementa los 18 tipos de comprobantes según normas colombianas.
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid

from core.models import Company, User


class VoucherType(models.Model):
    """
    Tipos de comprobantes contables según normatividad colombiana.
    Incluye los 18 tipos de comprobantes estándar.
    """
    
    # Códigos oficiales de comprobantes en Colombia
    VOUCHER_TYPE_CHOICES = [
        ('CI', 'Comprobante de Ingresos'),
        ('CE', 'Comprobante de Egresos'), 
        ('CG', 'Comprobante General'),
        ('CC', 'Comprobante de Contabilidad'),
        ('CN', 'Nota Contable'),
        ('CB', 'Comprobante de Bancos'),
        ('CA', 'Comprobante de Ajustes'),
        ('CR', 'Comprobante de Reversión'),
        ('CP', 'Comprobante de Provisiones'),
        ('CT', 'Comprobante de Traslados'),
        ('CX', 'Comprobante de Causación'),
        ('CO', 'Comprobante de Operaciones'),
        ('CK', 'Comprobante de Cierre'),
        ('CS', 'Comprobante de Saldos'),
        ('CV', 'Comprobante de Ventas'),
        ('CM', 'Comprobante de Compras'),
        ('CF', 'Comprobante de Facturación'),
        ('CL', 'Comprobante de Liquidación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='voucher_types')
    
    code = models.CharField(max_length=3, choices=VOUCHER_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración de numeración
    prefix = models.CharField(max_length=10, blank=True, help_text="Prefijo del consecutivo")
    next_number = models.IntegerField(default=1)
    number_length = models.IntegerField(default=6, help_text="Longitud del número")
    
    # Configuración funcional
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    auto_post = models.BooleanField(default=False)
    
    # Control de períodos
    allow_past_dates = models.BooleanField(default=False)
    allow_future_dates = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'accounting_voucher_types'
        verbose_name = 'Tipo de Comprobante'
        verbose_name_plural = 'Tipos de Comprobante'
        unique_together = ['company', 'code']
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_next_number(self):
        """
        Genera el siguiente número de consecutivo para este tipo de comprobante.
        """
        number_str = str(self.next_number).zfill(self.number_length)
        full_number = f"{self.prefix}{number_str}" if self.prefix else number_str
        
        # Incrementar el contador
        self.next_number += 1
        self.save(update_fields=['next_number'])
        
        return full_number
    
    def clean(self):
        """Validaciones del modelo."""
        if self.number_length < 1 or self.number_length > 10:
            raise ValidationError("La longitud del número debe estar entre 1 y 10")
    
    @classmethod
    def create_default_types(cls, company, user):
        """
        Crea los tipos de comprobante por defecto para una empresa.
        """
        default_types = [
            ('CI', 'Comprobante de Ingresos', 'Para registrar ingresos de efectivo y bancos'),
            ('CE', 'Comprobante de Egresos', 'Para registrar egresos de efectivo y bancos'),
            ('CG', 'Comprobante General', 'Para asientos contables generales'),
            ('CC', 'Comprobante de Contabilidad', 'Para ajustes y reclasificaciones contables'),
            ('CN', 'Nota Contable', 'Para notas contables y ajustes menores'),
            ('CB', 'Comprobante de Bancos', 'Para movimientos bancarios'),
            ('CA', 'Comprobante de Ajustes', 'Para ajustes de fin de período'),
            ('CR', 'Comprobante de Reversión', 'Para reversar asientos contables'),
            ('CP', 'Comprobante de Provisiones', 'Para provisiones y estimaciones'),
            ('CT', 'Comprobante de Traslados', 'Para traslados entre cuentas'),
            ('CX', 'Comprobante de Causación', 'Para causaciones y devengos'),
            ('CO', 'Comprobante de Operaciones', 'Para operaciones especiales'),
            ('CK', 'Comprobante de Cierre', 'Para cierre de períodos contables'),
            ('CS', 'Comprobante de Saldos', 'Para apertura de saldos iniciales'),
            ('CV', 'Comprobante de Ventas', 'Para facturación y ventas'),
            ('CM', 'Comprobante de Compras', 'Para compras y adquisiciones'),
            ('CF', 'Comprobante de Facturación', 'Para procesos de facturación'),
            ('CL', 'Comprobante de Liquidación', 'Para liquidaciones y nómina'),
        ]
        
        created_types = []
        for code, name, description in default_types:
            voucher_type, created = cls.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'created_by': user,
                    'prefix': code,
                    'requires_approval': code in ['CA', 'CR', 'CK', 'CS'],  # Tipos críticos
                }
            )
            if created:
                created_types.append(voucher_type)
        
        return created_types