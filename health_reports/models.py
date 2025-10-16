"""
Modelos del módulo Reportes Clínicos
Reportes e indicadores clínicos
"""

from django.db import models
import uuid
from core.models import Company, User


class Health_reportsModule(models.Model):
    """Modelo base del módulo Reportes Clínicos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_reports_base'
        verbose_name = 'Reportes Clínicos'
        verbose_name_plural = 'Reportes Clínicos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
