"""
Módulo de Diagnósticos CIE-10
Sistema completo de catalogación de enfermedades según la Clasificación Internacional de Enfermedades (CIE-10)
Adaptado para normativa colombiana - Resolución 3374 de 2000 y actualizaciones del Ministerio de Salud
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

from core.models import Company, User


class CIE10Version(models.Model):
    """
    Versión del catálogo CIE-10 (para control de versiones del catálogo)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    version_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código de Versión',
        help_text="Ej: CIE10-2023, CIE10-ES-2024"
    )
    name = models.CharField(max_length=200, verbose_name='Nombre')
    release_date = models.DateField(verbose_name='Fecha de Publicación')
    description = models.TextField(blank=True, verbose_name='Descripción')

    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_current = models.BooleanField(
        default=False,
        verbose_name='Versión Actual',
        help_text="Versión actual en uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        db_table = 'diagnostics_cie10_versions'
        verbose_name = 'Versión CIE-10'
        verbose_name_plural = 'Versiones CIE-10'
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.version_code} - {self.name}"


class CIE10Chapter(models.Model):
    """
    Capítulos del CIE-10 (22 capítulos principales)
    Ej: Capítulo I (A00-B99) - Ciertas enfermedades infecciosas y parasitarias
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        CIE10Version,
        on_delete=models.CASCADE,
        related_name='chapters'
    )

    code = models.CharField(
        max_length=10,
        verbose_name='Código del Capítulo',
        help_text="Código del capítulo (I, II, III, etc.)"
    )
    name = models.CharField(max_length=300, verbose_name='Nombre del Capítulo')
    code_range_start = models.CharField(
        max_length=10,
        verbose_name='Código Inicial',
        help_text="Ej: A00"
    )
    code_range_end = models.CharField(
        max_length=10,
        verbose_name='Código Final',
        help_text="Ej: B99"
    )

    order = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        db_table = 'diagnostics_cie10_chapters'
        verbose_name = 'Capítulo CIE-10'
        verbose_name_plural = 'Capítulos CIE-10'
        unique_together = ['version', 'code']
        ordering = ['order', 'code']

    def __str__(self):
        return f"Cap. {self.code}: {self.name} ({self.code_range_start}-{self.code_range_end})"


class CIE10Group(models.Model):
    """
    Grupos o bloques dentro de un capítulo CIE-10
    Ej: A00-A09 - Enfermedades infecciosas intestinales
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(
        CIE10Chapter,
        on_delete=models.CASCADE,
        related_name='groups'
    )

    code_range_start = models.CharField(max_length=10, verbose_name='Código Inicial')
    code_range_end = models.CharField(max_length=10, verbose_name='Código Final')
    name = models.CharField(max_length=300, verbose_name='Nombre del Grupo')

    order = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        db_table = 'diagnostics_cie10_groups'
        verbose_name = 'Grupo CIE-10'
        verbose_name_plural = 'Grupos CIE-10'
        ordering = ['order', 'code_range_start']

    def __str__(self):
        return f"{self.code_range_start}-{self.code_range_end}: {self.name}"


class CIE10Diagnosis(models.Model):
    """
    Diagnóstico CIE-10 individual
    Incluye todos los campos requeridos para Colombia (RIPS, facturación, autorizaciones, SIVIGILA)
    """
    GENDER_CHOICES = [
        ('A', 'Ambos'),
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    USE_CHOICES = [
        ('morbidity', 'Morbilidad'),
        ('mortality', 'Mortalidad'),
        ('both', 'Ambos'),
    ]

    DEATH_TYPE_CHOICES = [
        ('not_applicable', 'No aplica'),
        ('basic', 'Causa básica'),
        ('intermediate', 'Causa intermedia'),
        ('immediate', 'Causa inmediata'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        CIE10Version,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    chapter = models.ForeignKey(
        CIE10Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Capítulo'
    )
    group = models.ForeignKey(
        CIE10Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Grupo'
    )

    # Código CIE-10 (campo principal)
    code = models.CharField(
        max_length=10,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z][0-9]{2}(\.[0-9X]{1,2})?$',
                message='Formato CIE-10 inválido. Use: A00 o A00.1'
            )
        ],
        verbose_name='Código CIE-10',
        help_text="Ej: A00, A00.1, Z99.9"
    )
    name = models.CharField(
        max_length=500,
        verbose_name='Descripción del Diagnóstico'
    )

    # Nivel jerárquico
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Diagnóstico Padre'
    )
    level = models.IntegerField(
        default=0,
        verbose_name='Nivel Jerárquico',
        help_text="3=categoría, 4=subcategoría, 5=sub-subcategoría"
    )

    # Metadatos de clasificación
    is_category = models.BooleanField(
        default=False,
        verbose_name='Es Categoría',
        help_text="Código de 3 caracteres"
    )
    is_subcategory = models.BooleanField(
        default=False,
        verbose_name='Es Subcategoría',
        help_text="Código de 4+ caracteres"
    )

    # Restricciones de uso por sexo y edad
    applicable_gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='A',
        verbose_name='Sexo Aplicable'
    )
    min_age_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Edad Mínima (días)',
        help_text="Edad mínima en días (365 días = 1 año)"
    )
    max_age_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Edad Máxima (días)',
        help_text="Edad máxima en días (dejar vacío si no aplica)"
    )

    # Uso del diagnóstico
    use_in = models.CharField(
        max_length=20,
        choices=USE_CHOICES,
        default='both',
        verbose_name='Uso en'
    )

    # Tipo para certificado de defunción
    death_type = models.CharField(
        max_length=20,
        choices=DEATH_TYPE_CHOICES,
        default='not_applicable',
        verbose_name='Tipo de Causa de Muerte'
    )

    # Campos específicos para Colombia
    mandatory_notification = models.BooleanField(
        default=False,
        verbose_name='Notificación Obligatoria (SIVIGILA)',
        help_text='Marcar si es enfermedad de notificación obligatoria al INS'
    )
    high_cost = models.BooleanField(
        default=False,
        verbose_name='Alto Costo',
        help_text='Diagnóstico de enfermedad de alto costo (CAC)'
    )
    rare_disease = models.BooleanField(
        default=False,
        verbose_name='Enfermedad Huérfana/Rara',
        help_text='Enfermedad huérfana según normativa colombiana'
    )
    chronic_disease = models.BooleanField(
        default=False,
        verbose_name='Enfermedad Crónica',
        help_text='Enfermedad crónica no transmisible'
    )
    requires_authorization = models.BooleanField(
        default=False,
        verbose_name='Requiere Autorización',
        help_text='Requiere autorización previa de la EPS'
    )

    # Notas clínicas y aclaraciones
    includes = models.TextField(
        blank=True,
        verbose_name='Incluye',
        help_text="Condiciones incluidas en este código"
    )
    excludes = models.TextField(
        blank=True,
        verbose_name='Excluye',
        help_text="Condiciones excluidas de este código"
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas Adicionales',
        help_text="Notas clínicas o aclaraciones"
    )

    # Sinónimos y términos de búsqueda
    synonyms = models.TextField(
        blank=True,
        verbose_name='Sinónimos',
        help_text='Términos alternativos separados por comas'
    )
    search_vector = models.TextField(
        blank=True,
        verbose_name='Vector de Búsqueda',
        help_text="Vector de búsqueda normalizado (auto-generado)"
    )

    # Estadísticas de uso
    use_count = models.IntegerField(
        default=0,
        verbose_name='Contador de Uso',
        help_text="Veces que se ha usado este diagnóstico"
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Uso'
    )

    # Control de vigencia
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name='Válido Desde'
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Válido Hasta'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_deprecated = models.BooleanField(default=False, verbose_name='Obsoleto')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diagnostics_cie10_diagnoses'
        verbose_name = 'Diagnóstico CIE-10'
        verbose_name_plural = 'Diagnósticos CIE-10'
        unique_together = ['version', 'code']
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['version', 'is_active']),
            models.Index(fields=['chapter']),
            models.Index(fields=['mandatory_notification']),
            models.Index(fields=['high_cost']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_full_name(self):
        """Retorna código y nombre completo"""
        return f"{self.code} - {self.name}"

    def increment_use_count(self):
        """Incrementa el contador de uso y actualiza última fecha"""
        self.use_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['use_count', 'last_used'])

    def is_valid_for_gender(self, gender):
        """Verifica si el diagnóstico aplica para el sexo indicado"""
        if self.applicable_gender == 'A':
            return True
        return self.applicable_gender == gender

    def is_valid_for_age(self, age_in_days):
        """Verifica si el diagnóstico aplica para la edad indicada"""
        if self.min_age_days is not None and age_in_days < self.min_age_days:
            return False
        if self.max_age_days is not None and age_in_days > self.max_age_days:
            return False
        return True

    def get_age_range_text(self):
        """Retorna el rango de edad en texto legible"""
        if not self.min_age_days and not self.max_age_days:
            return "Todas las edades"

        min_text = ""
        max_text = ""

        if self.min_age_days:
            if self.min_age_days < 365:
                min_text = f"{self.min_age_days} días"
            else:
                min_text = f"{self.min_age_days // 365} años"

        if self.max_age_days:
            if self.max_age_days < 365:
                max_text = f"{self.max_age_days} días"
            else:
                max_text = f"{self.max_age_days // 365} años"

        if min_text and max_text:
            return f"De {min_text} a {max_text}"
        elif min_text:
            return f"Desde {min_text}"
        elif max_text:
            return f"Hasta {max_text}"

        return "Todas las edades"


class FavoriteDiagnosis(models.Model):
    """
    Diagnósticos favoritos por usuario/empresa para acceso rápido
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='favorite_diagnoses'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_diagnoses'
    )
    diagnosis = models.ForeignKey(
        CIE10Diagnosis,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    specialty = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Especialidad Médica',
        help_text="Ej: Cardiología, Pediatría, Medicina Interna"
    )
    order = models.IntegerField(default=0, verbose_name='Orden')
    notes = models.TextField(blank=True, verbose_name='Notas Personales')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnostics_favorite_diagnoses'
        verbose_name = 'Diagnóstico Favorito'
        verbose_name_plural = 'Diagnósticos Favoritos'
        unique_together = ['company', 'user', 'diagnosis']
        ordering = ['order', 'diagnosis__code']

    def __str__(self):
        return f"{self.user.username} - {self.diagnosis.code}"


class DiagnosisImportLog(models.Model):
    """
    Registro de importaciones masivas del catálogo CIE-10
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('partial', 'Parcial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='diagnosis_imports',
        null=True,
        blank=True
    )
    version = models.ForeignKey(
        CIE10Version,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports'
    )

    # Archivo importado
    file_name = models.CharField(max_length=255, verbose_name='Nombre del Archivo')
    file_path = models.FileField(
        upload_to='diagnostics/imports/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Archivo'
    )
    file_type = models.CharField(
        max_length=20,
        default='csv',
        verbose_name='Tipo de Archivo',
        help_text='csv, xlsx, xml'
    )

    # Estadísticas
    total_records = models.IntegerField(default=0, verbose_name='Total de Registros')
    successful_imports = models.IntegerField(default=0, verbose_name='Importados Exitosamente')
    failed_imports = models.IntegerField(default=0, verbose_name='Fallos')
    skipped_imports = models.IntegerField(default=0, verbose_name='Omitidos')
    updated_records = models.IntegerField(default=0, verbose_name='Actualizados')

    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    progress_percentage = models.IntegerField(default=0, verbose_name='Progreso (%)')

    # Detalles y logs
    error_log = models.TextField(blank=True, verbose_name='Log de Errores')
    import_notes = models.TextField(blank=True, verbose_name='Notas de Importación')
    summary = models.TextField(blank=True, verbose_name='Resumen')

    # Metadata
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Iniciado')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completado')
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name='Duración (segundos)')
    imported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='diagnosis_imports',
        verbose_name='Importado Por'
    )

    class Meta:
        db_table = 'diagnostics_import_logs'
        verbose_name = 'Log de Importación'
        verbose_name_plural = 'Logs de Importación'
        ordering = ['-started_at']

    def __str__(self):
        return f"Importación {self.file_name} - {self.get_status_display()}"

    def calculate_success_rate(self):
        """Calcula el porcentaje de éxito"""
        if self.total_records == 0:
            return 0
        return round((self.successful_imports / self.total_records) * 100, 2)

    def mark_completed(self):
        """Marca la importación como completada"""
        self.completed_at = timezone.now()
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)
        self.status = 'completed' if self.failed_imports == 0 else 'partial'
        self.progress_percentage = 100
        self.save()

    def mark_failed(self, error_message):
        """Marca la importación como fallida"""
        self.completed_at = timezone.now()
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)
        self.status = 'failed'
        self.error_log = error_message
        self.save()
