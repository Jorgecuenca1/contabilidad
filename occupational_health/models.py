"""
Modelos del módulo Salud Ocupacional
Exámenes ocupacionales, aptitud laboral y reportes empresariales
"""

from django.db import models
from django.db.models import Max
import uuid
from core.models import Company, User
from patients.models import Patient


class OccupationalExam(models.Model):
    """
    Examen Ocupacional - Ingreso, Periódico, Retiro
    Evaluación médica ocupacional completa
    """
    EXAM_TYPE_CHOICES = [
        ('ingreso', 'Examen de Ingreso'),
        ('periodico', 'Examen Periódico'),
        ('retiro', 'Examen de Retiro'),
        ('reingreso', 'Examen de Reingreso'),
        ('cambio_ocupacion', 'Cambio de Ocupación'),
        ('post_incapacidad', 'Post-Incapacidad'),
    ]

    STATUS_CHOICES = [
        ('programado', 'Programado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='occupational_exams')
    exam_number = models.CharField(max_length=50, unique=True, verbose_name='Número de Examen')

    # Información del trabajador/paciente
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='occupational_exams', verbose_name='Trabajador')

    # Información laboral
    company_name = models.CharField(max_length=200, verbose_name='Empresa empleadora', help_text='Empresa donde trabaja el paciente')
    job_position = models.CharField(max_length=200, verbose_name='Cargo')
    work_area = models.CharField(max_length=200, blank=True, verbose_name='Área de trabajo')
    years_in_position = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Años en el cargo')
    work_schedule = models.CharField(max_length=100, blank=True, verbose_name='Horario laboral')

    # Tipo y fecha de examen
    exam_type = models.CharField(max_length=30, choices=EXAM_TYPE_CHOICES, verbose_name='Tipo de examen')
    exam_date = models.DateTimeField(verbose_name='Fecha y hora del examen')
    examiner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='occupational_exams_as_examiner', verbose_name='Médico examinador')

    # Historia ocupacional
    previous_jobs = models.TextField(blank=True, verbose_name='Trabajos anteriores', help_text='Historia laboral previa')
    occupational_exposures = models.TextField(blank=True, verbose_name='Exposiciones ocupacionales',
                                              help_text='Físicas, químicas, biológicas, ergonómicas, psicosociales')
    use_of_ppe = models.TextField(blank=True, verbose_name='Uso de EPP', help_text='Elementos de protección personal utilizados')

    # Antecedentes personales
    personal_medical_history = models.TextField(blank=True, verbose_name='Antecedentes médicos personales')
    family_medical_history = models.TextField(blank=True, verbose_name='Antecedentes médicos familiares')
    current_medications = models.TextField(blank=True, verbose_name='Medicación actual')
    allergies = models.TextField(blank=True, verbose_name='Alergias')

    # Hábitos
    smoking = models.CharField(max_length=50, blank=True, verbose_name='Tabaquismo', help_text='Sí/No, cantidad')
    alcohol = models.CharField(max_length=50, blank=True, verbose_name='Consumo de alcohol')
    physical_activity = models.CharField(max_length=100, blank=True, verbose_name='Actividad física')

    # Examen físico general
    blood_pressure = models.CharField(max_length=20, blank=True, verbose_name='Presión arterial')
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia cardíaca')
    respiratory_rate = models.IntegerField(null=True, blank=True, verbose_name='Frecuencia respiratoria')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Temperatura (°C)')
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso (kg)')
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Talla (cm)')
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='IMC')

    # Examen por sistemas
    head_neck_exam = models.TextField(blank=True, verbose_name='Cabeza y cuello')
    cardiovascular_exam = models.TextField(blank=True, verbose_name='Cardiovascular')
    respiratory_exam = models.TextField(blank=True, verbose_name='Respiratorio')
    abdominal_exam = models.TextField(blank=True, verbose_name='Abdominal')
    musculoskeletal_exam = models.TextField(blank=True, verbose_name='Osteomuscular')
    neurological_exam = models.TextField(blank=True, verbose_name='Neurológico')
    dermatological_exam = models.TextField(blank=True, verbose_name='Piel y anexos')

    # Exámenes complementarios solicitados
    laboratory_tests_ordered = models.TextField(blank=True, verbose_name='Laboratorios solicitados')
    imaging_studies_ordered = models.TextField(blank=True, verbose_name='Imágenes solicitadas')
    other_tests_ordered = models.TextField(blank=True, verbose_name='Otros exámenes solicitados')

    # Resultados y diagnóstico
    diagnosis = models.TextField(blank=True, verbose_name='Diagnóstico')
    findings = models.TextField(blank=True, verbose_name='Hallazgos relevantes')

    # Estado y observaciones
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='programado', verbose_name='Estado')
    observations = models.TextField(blank=True, verbose_name='Observaciones generales')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='occupational_exams_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_exam'
        verbose_name = 'Examen Ocupacional'
        verbose_name_plural = 'Exámenes Ocupacionales'
        ordering = ['-exam_date']
        indexes = [
            models.Index(fields=['company', 'exam_type']),
            models.Index(fields=['patient', 'exam_date']),
        ]

    def __str__(self):
        return f"{self.exam_number} - {self.patient.third_party.get_full_name()} - {self.get_exam_type_display()}"

    def save(self, *args, **kwargs):
        if not self.exam_number:
            # Auto-generar número de examen
            last_exam = OccupationalExam.objects.filter(company=self.company).aggregate(
                last_number=Max('exam_number')
            )
            if last_exam['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_exam['last_number'])))
                    self.exam_number = f"EXOCU-{last_num + 1:07d}"
                except ValueError:
                    self.exam_number = "EXOCU-0000001"
            else:
                self.exam_number = "EXOCU-0000001"

        # Calcular IMC si hay peso y talla
        if self.weight and self.height and self.height > 0:
            height_m = float(self.height) / 100
            self.bmi = float(self.weight) / (height_m ** 2)

        super().save(*args, **kwargs)


class LaboratoryTest(models.Model):
    """Exámenes de laboratorio complementarios al examen ocupacional"""
    TEST_TYPE_CHOICES = [
        ('hematologia', 'Hematología Completa'),
        ('glicemia', 'Glicemia'),
        ('perfil_lipidico', 'Perfil Lipídico'),
        ('creatinina', 'Creatinina'),
        ('parcial_orina', 'Parcial de Orina'),
        ('colinesterasa', 'Colinesterasa'),
        ('espirometria', 'Espirometría'),
        ('audiometria', 'Audiometría'),
        ('visiometria', 'Visiometría'),
        ('rayos_x', 'Rayos X'),
        ('electrocardiograma', 'Electrocardiograma'),
        ('otro', 'Otro'),
    ]

    RESULT_STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('normal', 'Normal'),
        ('alterado', 'Alterado'),
        ('critico', 'Crítico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='occupational_lab_tests')
    exam = models.ForeignKey(OccupationalExam, on_delete=models.CASCADE, related_name='laboratory_tests', verbose_name='Examen ocupacional')

    test_type = models.CharField(max_length=30, choices=TEST_TYPE_CHOICES, verbose_name='Tipo de examen')
    test_name = models.CharField(max_length=200, verbose_name='Nombre del examen')
    test_date = models.DateField(verbose_name='Fecha de realización')

    result_value = models.TextField(blank=True, verbose_name='Resultado')
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS_CHOICES, default='pendiente', verbose_name='Estado del resultado')
    reference_values = models.TextField(blank=True, verbose_name='Valores de referencia')
    interpretation = models.TextField(blank=True, verbose_name='Interpretación')

    laboratory_name = models.CharField(max_length=200, blank=True, verbose_name='Laboratorio')
    performed_by = models.CharField(max_length=200, blank=True, verbose_name='Realizado por')

    observations = models.TextField(blank=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='lab_tests_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_lab_test'
        verbose_name = 'Examen de Laboratorio'
        verbose_name_plural = 'Exámenes de Laboratorio'
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.test_name} - {self.exam.exam_number}"


class WorkAptitude(models.Model):
    """
    Aptitud Laboral - Concepto médico sobre capacidad para trabajar
    """
    APTITUDE_CHOICES = [
        ('apto', 'Apto'),
        ('apto_con_restricciones', 'Apto con Restricciones'),
        ('apto_con_recomendaciones', 'Apto con Recomendaciones'),
        ('no_apto_temporal', 'No Apto Temporal'),
        ('no_apto_permanente', 'No Apto Permanente'),
        ('aplazado', 'Aplazado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_aptitudes')
    aptitude_number = models.CharField(max_length=50, unique=True, verbose_name='Número de concepto')

    exam = models.OneToOneField(OccupationalExam, on_delete=models.CASCADE, related_name='work_aptitude', verbose_name='Examen ocupacional')

    aptitude = models.CharField(max_length=30, choices=APTITUDE_CHOICES, verbose_name='Aptitud laboral')
    issue_date = models.DateField(verbose_name='Fecha de emisión')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Vigencia hasta')

    # Restricciones y recomendaciones
    restrictions = models.TextField(blank=True, verbose_name='Restricciones laborales',
                                   help_text='Limitaciones específicas para el trabajo')
    recommendations = models.TextField(blank=True, verbose_name='Recomendaciones',
                                      help_text='Recomendaciones médicas y de salud ocupacional')

    # Seguimiento
    requires_follow_up = models.BooleanField(default=False, verbose_name='Requiere seguimiento')
    follow_up_date = models.DateField(null=True, blank=True, verbose_name='Fecha de seguimiento')
    follow_up_notes = models.TextField(blank=True, verbose_name='Notas de seguimiento')

    # Justificación médica
    medical_justification = models.TextField(verbose_name='Justificación médica del concepto')

    observations = models.TextField(blank=True, verbose_name='Observaciones adicionales')

    issued_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='aptitudes_issued', verbose_name='Emitido por')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='aptitudes_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_aptitude'
        verbose_name = 'Aptitud Laboral'
        verbose_name_plural = 'Aptitudes Laborales'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.aptitude_number} - {self.get_aptitude_display()}"

    def save(self, *args, **kwargs):
        if not self.aptitude_number:
            # Auto-generar número de aptitud
            last_aptitude = WorkAptitude.objects.filter(company=self.company).aggregate(
                last_number=Max('aptitude_number')
            )
            if last_aptitude['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_aptitude['last_number'])))
                    self.aptitude_number = f"APT-{last_num + 1:07d}"
                except ValueError:
                    self.aptitude_number = "APT-0000001"
            else:
                self.aptitude_number = "APT-0000001"

        super().save(*args, **kwargs)


class OccupationalRisk(models.Model):
    """Riesgos ocupacionales identificados en el examen"""
    RISK_TYPE_CHOICES = [
        ('fisico', 'Físico'),
        ('quimico', 'Químico'),
        ('biologico', 'Biológico'),
        ('ergonomico', 'Ergonómico'),
        ('psicosocial', 'Psicosocial'),
        ('mecanico', 'Mecánico'),
        ('electrico', 'Eléctrico'),
        ('locativo', 'Locativo'),
    ]

    RISK_LEVEL_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='occupational_risks')
    exam = models.ForeignKey(OccupationalExam, on_delete=models.CASCADE, related_name='occupational_risks', verbose_name='Examen')

    risk_type = models.CharField(max_length=20, choices=RISK_TYPE_CHOICES, verbose_name='Tipo de riesgo')
    risk_description = models.TextField(verbose_name='Descripción del riesgo')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, verbose_name='Nivel de riesgo')

    exposure_time = models.CharField(max_length=100, blank=True, verbose_name='Tiempo de exposición')
    control_measures = models.TextField(blank=True, verbose_name='Medidas de control existentes')
    recommended_controls = models.TextField(blank=True, verbose_name='Controles recomendados')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='risks_identified')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_risk'
        verbose_name = 'Riesgo Ocupacional'
        verbose_name_plural = 'Riesgos Ocupacionales'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_risk_type_display()} - {self.get_risk_level_display()}"


class HealthRecommendation(models.Model):
    """Recomendaciones de salud ocupacional"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('ergonomica', 'Ergonómica'),
        ('higiene_industrial', 'Higiene Industrial'),
        ('seguridad', 'Seguridad'),
        ('medicina_preventiva', 'Medicina Preventiva'),
        ('estilos_vida', 'Estilos de Vida Saludable'),
    ]

    PRIORITY_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='health_recommendations')
    exam = models.ForeignKey(OccupationalExam, on_delete=models.CASCADE, related_name='health_recommendations', verbose_name='Examen')

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='Categoría')
    recommendation = models.TextField(verbose_name='Recomendación')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, verbose_name='Prioridad')

    implementation_deadline = models.DateField(null=True, blank=True, verbose_name='Plazo de implementación')
    responsible_person = models.CharField(max_length=200, blank=True, verbose_name='Responsable')

    implemented = models.BooleanField(default=False, verbose_name='Implementada')
    implementation_date = models.DateField(null=True, blank=True, verbose_name='Fecha de implementación')
    implementation_notes = models.TextField(blank=True, verbose_name='Notas de implementación')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recommendations_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_recommendation'
        verbose_name = 'Recomendación de Salud'
        verbose_name_plural = 'Recomendaciones de Salud'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.get_category_display()} - {self.get_priority_display()}"


class CompanyReport(models.Model):
    """Reportes empresariales de salud ocupacional"""
    REPORT_TYPE_CHOICES = [
        ('consolidado_examenes', 'Consolidado de Exámenes'),
        ('ausentismo', 'Ausentismo Laboral'),
        ('accidentalidad', 'Accidentalidad'),
        ('morbilidad', 'Morbilidad'),
        ('riesgos_identificados', 'Riesgos Identificados'),
        ('aptitudes', 'Aptitudes Laborales'),
        ('seguimiento', 'Seguimiento y Control'),
        ('estadistico', 'Estadístico'),
        ('personalizado', 'Personalizado'),
    ]

    STATUS_CHOICES = [
        ('borrador', 'Borrador'),
        ('generado', 'Generado'),
        ('enviado', 'Enviado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='occupational_reports')
    report_number = models.CharField(max_length=50, unique=True, verbose_name='Número de reporte')

    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES, verbose_name='Tipo de reporte')
    report_title = models.CharField(max_length=200, verbose_name='Título del reporte')

    # Período del reporte
    period_start = models.DateField(verbose_name='Período desde')
    period_end = models.DateField(verbose_name='Período hasta')

    # Filtros aplicados
    client_company = models.CharField(max_length=200, blank=True, verbose_name='Empresa cliente',
                                     help_text='Empresa para la que se genera el reporte')
    work_area_filter = models.CharField(max_length=200, blank=True, verbose_name='Filtro por área')
    job_position_filter = models.CharField(max_length=200, blank=True, verbose_name='Filtro por cargo')

    # Contenido del reporte
    summary = models.TextField(blank=True, verbose_name='Resumen ejecutivo')
    findings = models.TextField(blank=True, verbose_name='Hallazgos principales')
    statistics = models.JSONField(default=dict, blank=True, verbose_name='Estadísticas')
    recommendations = models.TextField(blank=True, verbose_name='Recomendaciones generales')
    conclusions = models.TextField(blank=True, verbose_name='Conclusiones')

    # Anexos y archivos
    attachments_description = models.TextField(blank=True, verbose_name='Descripción de anexos')

    # Estado y generación
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrador', verbose_name='Estado')
    generated_date = models.DateField(null=True, blank=True, verbose_name='Fecha de generación')
    sent_date = models.DateField(null=True, blank=True, verbose_name='Fecha de envío')
    recipient = models.CharField(max_length=200, blank=True, verbose_name='Destinatario')

    observations = models.TextField(blank=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='occupational_reports_created', verbose_name='Creado por')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'occupational_health_report'
        verbose_name = 'Reporte Empresarial'
        verbose_name_plural = 'Reportes Empresariales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'report_type']),
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"{self.report_number} - {self.report_title}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            # Auto-generar número de reporte
            last_report = CompanyReport.objects.filter(company=self.company).aggregate(
                last_number=Max('report_number')
            )
            if last_report['last_number']:
                try:
                    last_num = int(''.join(filter(str.isdigit, last_report['last_number'])))
                    self.report_number = f"REP-{last_num + 1:07d}"
                except ValueError:
                    self.report_number = "REP-0000001"
            else:
                self.report_number = "REP-0000001"

        super().save(*args, **kwargs)
