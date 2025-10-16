"""
Modelos del módulo de Cardiología
Gestión especializada de estudios cardiovasculares
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class CardiologyConsultation(models.Model):
    """
    Consulta de cardiología
    """
    CONSULTATION_TYPE_CHOICES = [
        ('first_time', 'Primera Vez'),
        ('follow_up', 'Control'),
        ('post_surgical', 'Post-Quirúrgico'),
        ('pre_surgical', 'Pre-Quirúrgico'),
        ('emergency', 'Urgencia'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_progress', 'En Curso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='cardiology_consultations')

    # Información de la consulta
    consultation_date = models.DateTimeField(default=timezone.now)
    consultation_type = models.CharField(max_length=30, choices=CONSULTATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Cardiólogo
    cardiologist = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='cardiology_consultations')

    # Motivo de consulta cardiovascular
    chief_complaint = models.TextField(help_text="Motivo de consulta")
    cardiovascular_history = models.TextField(blank=True, help_text="Antecedentes cardiovasculares")

    # Factores de riesgo cardiovascular
    has_hypertension = models.BooleanField(default=False, verbose_name="Hipertensión")
    has_diabetes = models.BooleanField(default=False, verbose_name="Diabetes")
    has_dyslipidemia = models.BooleanField(default=False, verbose_name="Dislipidemia")
    is_smoker = models.BooleanField(default=False, verbose_name="Fumador")
    has_family_history_cvd = models.BooleanField(default=False, verbose_name="Antecedente familiar de ECV")
    is_sedentary = models.BooleanField(default=False, verbose_name="Sedentarismo")
    has_obesity = models.BooleanField(default=False, verbose_name="Obesidad")

    # Signos vitales cardiovasculares
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)

    # Examen cardiovascular
    cardiac_auscultation = models.TextField(blank=True, help_text="Auscultación cardíaca")
    peripheral_pulses = models.TextField(blank=True, help_text="Pulsos periféricos")
    edema_presence = models.BooleanField(default=False)
    edema_description = models.CharField(max_length=200, blank=True)

    # Diagnóstico
    primary_diagnosis_code = models.CharField(max_length=10, blank=True)
    primary_diagnosis_description = models.CharField(max_length=500, blank=True)
    secondary_diagnoses = models.TextField(blank=True)

    # Plan de manejo
    treatment_plan = models.TextField(blank=True)
    medications_prescribed = models.TextField(blank=True)

    # Órdenes de estudios
    ecg_ordered = models.BooleanField(default=False, verbose_name="ECG ordenado")
    echo_ordered = models.BooleanField(default=False, verbose_name="Ecocardiograma ordenado")
    stress_test_ordered = models.BooleanField(default=False, verbose_name="Prueba de esfuerzo ordenada")
    holter_ordered = models.BooleanField(default=False, verbose_name="Holter ordenado")

    # Seguimiento
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_instructions = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='cardio_consults_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_consultations'
        verbose_name = 'Consulta de Cardiología'
        verbose_name_plural = 'Consultas de Cardiología'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"{self.consultation_number} - {self.patient}"


class Electrocardiogram(models.Model):
    """
    Electrocardiograma (ECG)
    """
    ECG_TYPE_CHOICES = [
        ('resting', 'Reposo'),
        ('stress', 'Esfuerzo'),
        ('holter', 'Holter'),
        ('event_monitor', 'Monitor de Eventos'),
    ]

    RHYTHM_CHOICES = [
        ('sinus_rhythm', 'Ritmo Sinusal'),
        ('atrial_fibrillation', 'Fibrilación Auricular'),
        ('atrial_flutter', 'Flutter Auricular'),
        ('svt', 'Taquicardia Supraventricular'),
        ('ventricular_tachycardia', 'Taquicardia Ventricular'),
        ('bradycardia', 'Bradicardia'),
        ('other', 'Otro'),
    ]

    RESULT_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Anormal'),
        ('borderline', 'Limítrofe'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    ecg_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='electrocardiograms')
    cardiology_consultation = models.ForeignKey(CardiologyConsultation, on_delete=models.PROTECT,
                                               null=True, blank=True, related_name='electrocardiograms')

    # Información del estudio
    ecg_date = models.DateTimeField(default=timezone.now)
    ecg_type = models.CharField(max_length=30, choices=ECG_TYPE_CHOICES, default='resting')

    # Técnico que realiza
    performed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='ecgs_performed')
    # Cardiólogo que interpreta
    interpreted_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                      related_name='ecgs_interpreted')

    # Parámetros del ECG
    heart_rate = models.IntegerField(validators=[MinValueValidator(20), MaxValueValidator(300)],
                                    help_text="Frecuencia cardíaca (lpm)")
    pr_interval = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                     help_text="Intervalo PR (ms)")
    qrs_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      help_text="Duración QRS (ms)")
    qt_interval = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                     help_text="Intervalo QT (ms)")
    qtc_interval = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      help_text="QTc corregido (ms)")

    # Eje eléctrico
    p_wave_axis = models.IntegerField(null=True, blank=True, help_text="Eje de onda P (grados)")
    qrs_axis = models.IntegerField(null=True, blank=True, help_text="Eje QRS (grados)")
    t_wave_axis = models.IntegerField(null=True, blank=True, help_text="Eje de onda T (grados)")

    # Ritmo
    rhythm = models.CharField(max_length=30, choices=RHYTHM_CHOICES, default='sinus_rhythm')
    rhythm_description = models.CharField(max_length=300, blank=True)

    # Hallazgos
    findings = models.TextField(help_text="Hallazgos electrocardiográficos")
    has_st_changes = models.BooleanField(default=False, verbose_name="Cambios en el segmento ST")
    has_t_wave_changes = models.BooleanField(default=False, verbose_name="Cambios en onda T")
    has_q_waves = models.BooleanField(default=False, verbose_name="Ondas Q patológicas")
    has_hypertrophy = models.BooleanField(default=False, verbose_name="Hipertrofia")
    has_conduction_block = models.BooleanField(default=False, verbose_name="Bloqueo de conducción")

    # Interpretación
    interpretation = models.TextField(help_text="Interpretación clínica")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='normal')

    # Conclusiones y recomendaciones
    conclusion = models.TextField()
    recommendations = models.TextField(blank=True)

    # Archivo digital del ECG
    ecg_file = models.FileField(upload_to='cardiology/ecg/%Y/%m/', null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='ecgs_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_electrocardiograms'
        verbose_name = 'Electrocardiograma'
        verbose_name_plural = 'Electrocardiogramas'
        ordering = ['-ecg_date']

    def __str__(self):
        return f"ECG {self.ecg_number} - {self.patient} - {self.ecg_date.strftime('%Y-%m-%d')}"


class Echocardiogram(models.Model):
    """
    Ecocardiograma (Echocardiogram)
    """
    ECHO_TYPE_CHOICES = [
        ('transthoracic', 'Transtorácico (TTE)'),
        ('transesophageal', 'Transesofágico (TEE)'),
        ('stress', 'Estrés'),
        ('fetal', 'Fetal'),
    ]

    RESULT_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Anormal'),
        ('borderline', 'Limítrofe'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    echo_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='echocardiograms')
    cardiology_consultation = models.ForeignKey(CardiologyConsultation, on_delete=models.PROTECT,
                                               null=True, blank=True, related_name='echocardiograms')

    # Información del estudio
    echo_date = models.DateTimeField(default=timezone.now)
    echo_type = models.CharField(max_length=30, choices=ECHO_TYPE_CHOICES, default='transthoracic')

    # Personal
    performed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='echos_performed')
    interpreted_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                      related_name='echos_interpreted')

    # Datos antropométricos
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bsa_m2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                help_text="Superficie corporal (m²)")

    # Signos vitales
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)

    # DIMENSIONES Y FUNCIÓN VENTRICULAR IZQUIERDA
    # Diámetros
    lv_end_diastolic_diameter = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                   verbose_name="DDVI", help_text="Diámetro diastólico VI (mm)")
    lv_end_systolic_diameter = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                  verbose_name="DSVI", help_text="Diámetro sistólico VI (mm)")

    # Volúmenes
    lv_end_diastolic_volume = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                                  help_text="Volumen diastólico VI (ml)")
    lv_end_systolic_volume = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                                 help_text="Volumen sistólico VI (ml)")

    # Función ventricular
    ejection_fraction = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                          verbose_name="FEVI", help_text="Fracción de eyección VI (%)")
    fractional_shortening = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                               help_text="Acortamiento fraccional (%)")

    # Paredes del ventrículo izquierdo
    ivs_thickness = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                       verbose_name="SIV", help_text="Grosor tabique interventricular (mm)")
    posterior_wall_thickness = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                  verbose_name="PP", help_text="Grosor pared posterior (mm)")

    # AURÍCULA IZQUIERDA
    left_atrium_diameter = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                             help_text="Diámetro aurícula izquierda (mm)")
    left_atrium_volume = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                            help_text="Volumen aurícula izquierda (ml)")

    # VÁLVULAS CARDÍACAS
    # Válvula mitral
    mitral_valve_normal = models.BooleanField(default=True)
    mitral_stenosis = models.BooleanField(default=False)
    mitral_regurgitation = models.CharField(max_length=20, blank=True,
                                          help_text="Grado: leve/moderada/severa")

    # Válvula aórtica
    aortic_valve_normal = models.BooleanField(default=True)
    aortic_stenosis = models.BooleanField(default=False)
    aortic_regurgitation = models.CharField(max_length=20, blank=True)

    # Válvula tricúspide
    tricuspid_valve_normal = models.BooleanField(default=True)
    tricuspid_regurgitation = models.CharField(max_length=20, blank=True)

    # Válvula pulmonar
    pulmonary_valve_normal = models.BooleanField(default=True)
    pulmonary_regurgitation = models.CharField(max_length=20, blank=True)

    # Presiones
    estimated_rvsp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                        help_text="Presión sistólica VD estimada (mmHg)")

    # OTROS HALLAZGOS
    pericardial_effusion = models.BooleanField(default=False)
    pericardial_effusion_description = models.CharField(max_length=300, blank=True)

    thrombus_present = models.BooleanField(default=False)
    thrombus_description = models.CharField(max_length=300, blank=True)

    # Hallazgos generales
    findings = models.TextField(help_text="Hallazgos ecocardiográficos detallados")

    # Conclusión
    conclusion = models.TextField()
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='normal')
    recommendations = models.TextField(blank=True)

    # Archivos
    echo_images = models.FileField(upload_to='cardiology/echo/%Y/%m/', null=True, blank=True)
    echo_video = models.FileField(upload_to='cardiology/echo/video/%Y/%m/', null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='echos_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_echocardiograms'
        verbose_name = 'Ecocardiograma'
        verbose_name_plural = 'Ecocardiogramas'
        ordering = ['-echo_date']

    def __str__(self):
        return f"ECO {self.echo_number} - {self.patient} - {self.echo_date.strftime('%Y-%m-%d')}"


class StressTest(models.Model):
    """
    Prueba de Esfuerzo (Ergometría)
    """
    PROTOCOL_CHOICES = [
        ('bruce', 'Bruce'),
        ('modified_bruce', 'Bruce Modificado'),
        ('naughton', 'Naughton'),
        ('ellestad', 'Ellestad'),
        ('ramp', 'Rampa'),
    ]

    STOP_REASON_CHOICES = [
        ('target_heart_rate', 'Frecuencia cardíaca objetivo'),
        ('fatigue', 'Fatiga'),
        ('chest_pain', 'Dolor torácico'),
        ('dyspnea', 'Disnea'),
        ('st_changes', 'Cambios ST'),
        ('arrhythmia', 'Arritmia'),
        ('blood_pressure', 'Presión arterial anormal'),
        ('patient_request', 'Solicitud del paciente'),
    ]

    RESULT_CHOICES = [
        ('negative', 'Negativa para isquemia'),
        ('positive', 'Positiva para isquemia'),
        ('non_diagnostic', 'No diagnóstica'),
        ('indeterminate', 'Indeterminada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    test_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='stress_tests')
    cardiology_consultation = models.ForeignKey(CardiologyConsultation, on_delete=models.PROTECT,
                                               null=True, blank=True, related_name='stress_tests')

    # Información del estudio
    test_date = models.DateTimeField(default=timezone.now)
    protocol_used = models.CharField(max_length=30, choices=PROTOCOL_CHOICES, default='bruce')

    # Personal
    performed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='stress_tests_performed')
    supervised_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                     related_name='stress_tests_supervised')

    # Datos basales
    baseline_bp_systolic = models.IntegerField(help_text="PA sistólica basal")
    baseline_bp_diastolic = models.IntegerField(help_text="PA diastólica basal")
    baseline_heart_rate = models.IntegerField(help_text="FC basal")

    # Datos del ejercicio
    exercise_duration_minutes = models.DecimalField(max_digits=5, decimal_places=2,
                                                   help_text="Duración del ejercicio")
    max_heart_rate_achieved = models.IntegerField(help_text="FC máxima alcanzada")
    max_heart_rate_predicted = models.IntegerField(help_text="FC máxima predicha (220-edad)")
    percentage_max_hr = models.DecimalField(max_digits=5, decimal_places=2,
                                           help_text="% FC máxima alcanzada")

    max_bp_systolic = models.IntegerField(help_text="PA sistólica máxima")
    max_bp_diastolic = models.IntegerField(help_text="PA diastólica máxima")

    # Datos de carga
    max_mets_achieved = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                           help_text="METs alcanzados")
    max_stage_reached = models.CharField(max_length=50, blank=True)

    # Motivo de detención
    stop_reason = models.CharField(max_length=30, choices=STOP_REASON_CHOICES)
    stop_reason_details = models.TextField(blank=True)

    # Síntomas durante la prueba
    chest_pain_during_test = models.BooleanField(default=False)
    dyspnea_during_test = models.BooleanField(default=False)
    dizziness_during_test = models.BooleanField(default=False)
    symptoms_description = models.TextField(blank=True)

    # Cambios electrocardiográficos
    st_segment_changes = models.BooleanField(default=False)
    st_segment_description = models.TextField(blank=True)
    arrhythmias_detected = models.BooleanField(default=False)
    arrhythmias_description = models.TextField(blank=True)

    # Datos de recuperación
    recovery_heart_rate_1min = models.IntegerField(null=True, blank=True,
                                                   help_text="FC 1 min post-ejercicio")
    recovery_bp_systolic = models.IntegerField(null=True, blank=True)
    recovery_bp_diastolic = models.IntegerField(null=True, blank=True)

    # Resultado e interpretación
    result = models.CharField(max_length=30, choices=RESULT_CHOICES)
    interpretation = models.TextField(help_text="Interpretación de la prueba")
    conclusion = models.TextField()
    recommendations = models.TextField(blank=True)

    # Archivos
    test_report = models.FileField(upload_to='cardiology/stress_test/%Y/%m/', null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='stress_tests_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_stress_tests'
        verbose_name = 'Prueba de Esfuerzo'
        verbose_name_plural = 'Pruebas de Esfuerzo'
        ordering = ['-test_date']

    def __str__(self):
        return f"Prueba Esfuerzo {self.test_number} - {self.patient}"


class HolterMonitoring(models.Model):
    """
    Monitoreo Holter de 24-48 horas
    """
    DURATION_CHOICES = [
        ('24h', '24 horas'),
        ('48h', '48 horas'),
        ('72h', '72 horas'),
        ('7d', '7 días'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    holter_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='holter_monitorings')
    cardiology_consultation = models.ForeignKey(CardiologyConsultation, on_delete=models.PROTECT,
                                               null=True, blank=True, related_name='holter_monitorings')

    # Información del estudio
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='24h')

    # Personal
    placed_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                 related_name='holters_placed')
    interpreted_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                      related_name='holters_interpreted')

    # ANÁLISIS DEL RITMO
    # Ritmo predominante
    predominant_rhythm = models.CharField(max_length=100)
    total_beats = models.IntegerField(help_text="Total de latidos en el período")

    # Frecuencia cardíaca
    min_heart_rate = models.IntegerField(help_text="FC mínima")
    min_hr_time = models.TimeField(null=True, blank=True)
    max_heart_rate = models.IntegerField(help_text="FC máxima")
    max_hr_time = models.TimeField(null=True, blank=True)
    average_heart_rate = models.IntegerField(help_text="FC promedio")

    # ARRITMIAS SUPRAVENTRICULARES
    total_supraventricular_ectopics = models.IntegerField(default=0,
                                                         help_text="Extrasístoles supraventriculares")
    supraventricular_couplets = models.IntegerField(default=0)
    supraventricular_runs = models.IntegerField(default=0)
    atrial_fibrillation_episodes = models.IntegerField(default=0)
    svt_episodes = models.IntegerField(default=0, help_text="Episodios de taquicardia supraventricular")

    # ARRITMIAS VENTRICULARES
    total_ventricular_ectopics = models.IntegerField(default=0,
                                                    help_text="Extrasístoles ventriculares")
    ventricular_couplets = models.IntegerField(default=0)
    ventricular_runs = models.IntegerField(default=0)
    ventricular_tachycardia_episodes = models.IntegerField(default=0)

    # PAUSAS
    longest_pause_duration = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                                help_text="Pausa más larga (segundos)")
    significant_pauses_count = models.IntegerField(default=0,
                                                  help_text="Pausas > 2.0 segundos")

    # VARIABILIDAD DE FRECUENCIA CARDÍACA
    sdnn = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                              help_text="SDNN (ms) - Desviación estándar NN")
    sdann = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                               help_text="SDANN (ms)")
    rmssd = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                               help_text="RMSSD (ms)")

    # SEGMENTO ST
    st_segment_changes = models.BooleanField(default=False)
    st_elevation_episodes = models.IntegerField(default=0)
    st_depression_episodes = models.IntegerField(default=0)
    st_changes_description = models.TextField(blank=True)

    # SÍNTOMAS CORRELACIONADOS
    patient_symptoms_diary = models.TextField(blank=True,
                                             help_text="Diario de síntomas del paciente")
    symptom_rhythm_correlation = models.TextField(blank=True,
                                                  help_text="Correlación síntomas-ritmo")

    # Hallazgos e interpretación
    findings = models.TextField(help_text="Hallazgos del Holter")
    interpretation = models.TextField()
    conclusion = models.TextField()
    recommendations = models.TextField(blank=True)

    # Archivos
    holter_report = models.FileField(upload_to='cardiology/holter/%Y/%m/', null=True, blank=True)
    raw_data_file = models.FileField(upload_to='cardiology/holter/data/%Y/%m/', null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='holters_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_holter_monitoring'
        verbose_name = 'Holter'
        verbose_name_plural = 'Holter Monitorings'
        ordering = ['-start_datetime']

    def __str__(self):
        return f"Holter {self.holter_number} - {self.patient}"


class CardiovascularRiskAssessment(models.Model):
    """
    Evaluación de Riesgo Cardiovascular
    """
    RISK_LEVEL_CHOICES = [
        ('low', 'Bajo'),
        ('moderate', 'Moderado'),
        ('high', 'Alto'),
        ('very_high', 'Muy Alto'),
    ]

    SCORE_TYPE_CHOICES = [
        ('framingham', 'Framingham'),
        ('procam', 'PROCAM'),
        ('score', 'SCORE'),
        ('reynolds', 'Reynolds'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)

    assessment_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('third_parties.ThirdParty', on_delete=models.PROTECT,
                               related_name='cardiovascular_risk_assessments')
    cardiology_consultation = models.ForeignKey(CardiologyConsultation, on_delete=models.PROTECT,
                                               related_name='risk_assessments')

    # Información de la evaluación
    assessment_date = models.DateField(default=timezone.now)
    evaluated_by = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT,
                                    related_name='risk_assessments_performed')

    # Datos demográficos
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Femenino')])

    # Factores de riesgo
    systolic_blood_pressure = models.IntegerField()
    is_on_antihypertensive_treatment = models.BooleanField(default=False)

    total_cholesterol = models.DecimalField(max_digits=5, decimal_places=2,
                                           help_text="Colesterol total (mg/dL)")
    hdl_cholesterol = models.DecimalField(max_digits=5, decimal_places=2,
                                         help_text="HDL (mg/dL)")
    ldl_cholesterol = models.DecimalField(max_digits=5, decimal_places=2,
                                         help_text="LDL (mg/dL)")
    triglycerides = models.DecimalField(max_digits=6, decimal_places=2,
                                       help_text="Triglicéridos (mg/dL)")

    fasting_glucose = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                         help_text="Glucosa en ayunas (mg/dL)")
    hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                               help_text="HbA1c (%)")

    is_diabetic = models.BooleanField(default=False)
    is_smoker = models.BooleanField(default=False)

    # Cálculo de riesgo
    score_type = models.CharField(max_length=30, choices=SCORE_TYPE_CHOICES, default='framingham')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2,
                                    help_text="Puntaje de riesgo")
    risk_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                         help_text="% de riesgo a 10 años")
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)

    # Objetivos terapéuticos
    target_ldl = models.DecimalField(max_digits=5, decimal_places=2,
                                    help_text="LDL objetivo (mg/dL)")
    target_blood_pressure = models.CharField(max_length=20,
                                            help_text="PA objetivo (ej: 130/80)")

    # Recomendaciones
    lifestyle_recommendations = models.TextField()
    pharmacological_recommendations = models.TextField(blank=True)
    follow_up_plan = models.TextField()

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT,
                                  related_name='cvd_risk_assessments_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cardiology_risk_assessments'
        verbose_name = 'Evaluación de Riesgo Cardiovascular'
        verbose_name_plural = 'Evaluaciones de Riesgo Cardiovascular'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"Riesgo CV {self.assessment_number} - {self.patient} - {self.get_risk_level_display()}"
