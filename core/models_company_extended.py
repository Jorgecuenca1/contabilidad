"""
Extensión del modelo Company con información completa
para personas naturales y jurídicas
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Company


class CompanyExtended(models.Model):
    """
    Información extendida de la empresa
    La empresa puede ser Persona Natural o Jurídica
    """
    
    # Tipo de persona (la empresa misma)
    PERSON_TYPE_CHOICES = [
        ('NATURAL', 'Persona Natural'),
        ('JURIDICA', 'Persona Jurídica')
    ]
    
    # Tipo de documento
    DOCUMENT_TYPE_CHOICES = [
        ('NIT', 'NIT'),
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad')
    ]
    
    # Clasificación de empresa
    COMPANY_TYPE_CHOICES = [
        ('PUBLIC', 'Empresa Pública'),
        ('PRIVATE', 'Empresa Privada'),
        ('MIXED', 'Empresa Mixta'),
        ('NGO', 'ONG/Sin Ánimo de Lucro'),
        ('GOVERNMENT', 'Entidad Gubernamental'),
        ('COOPERATIVE', 'Cooperativa'),
        ('FOUNDATION', 'Fundación'),
        ('ASSOCIATION', 'Asociación'),
        ('SOLE_PROPRIETOR', 'Persona Natural Comerciante'),
        ('SAS', 'Sociedad por Acciones Simplificada'),
        ('SA', 'Sociedad Anónima'),
        ('LTDA', 'Sociedad Limitada'),
        ('EU', 'Empresa Unipersonal'),
        ('SC', 'Sociedad Colectiva'),
        ('SCA', 'Sociedad en Comandita por Acciones'),
        ('SCS', 'Sociedad en Comandita Simple')
    ]
    
    # Tamaño de empresa según Ley 590 de 2000 y Ley 905 de 2004
    COMPANY_SIZE_CHOICES = [
        ('MICRO', 'Microempresa'),  # Hasta 10 empleados, activos < 500 SMMLV
        ('SMALL', 'Pequeña Empresa'),  # 11-50 empleados, activos 501-5000 SMMLV
        ('MEDIUM', 'Mediana Empresa'),  # 51-200 empleados, activos 5001-30000 SMMLV
        ('LARGE', 'Gran Empresa')  # > 200 empleados, activos > 30000 SMMLV
    ]
    
    # Régimen tributario
    TAX_REGIME_CHOICES = [
        ('COMMON', 'Régimen Común'),
        ('SIMPLIFIED', 'Régimen Simplificado'),
        ('SPECIAL', 'Régimen Especial'),
        ('NO_RESPONSIBLE', 'No Responsable de IVA'),
        ('GREAT_CONTRIBUTOR', 'Gran Contribuyente'),
        ('SELF_WITHHOLDING', 'Autorretenedor'),
        ('SIMPLE', 'Régimen Simple de Tributación')
    ]
    
    # Sector económico
    ECONOMIC_SECTOR_CHOICES = [
        ('AGRICULTURE', 'Agricultura, Ganadería, Caza y Silvicultura'),
        ('MINING', 'Explotación de Minas y Canteras'),
        ('MANUFACTURING', 'Industrias Manufactureras'),
        ('UTILITIES', 'Suministro de Electricidad, Gas y Agua'),
        ('CONSTRUCTION', 'Construcción'),
        ('COMMERCE', 'Comercio'),
        ('HOTELS', 'Hoteles y Restaurantes'),
        ('TRANSPORT', 'Transporte, Almacenamiento y Comunicaciones'),
        ('FINANCE', 'Intermediación Financiera'),
        ('REAL_ESTATE', 'Actividades Inmobiliarias'),
        ('PUBLIC_ADMIN', 'Administración Pública y Defensa'),
        ('EDUCATION', 'Educación'),
        ('HEALTH', 'Servicios Sociales y de Salud'),
        ('SERVICES', 'Otras Actividades de Servicios'),
        ('TECHNOLOGY', 'Tecnología e Informática')
    ]
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='extended')
    
    # Tipo de persona y documento
    person_type = models.CharField(max_length=10, choices=PERSON_TYPE_CHOICES, default='JURIDICA')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES, default='NIT')
    
    # Para personas naturales
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    second_last_name = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Clasificación empresarial
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='PRIVATE')
    company_size = models.CharField(max_length=10, choices=COMPANY_SIZE_CHOICES, default='SMALL')
    economic_sector = models.CharField(max_length=20, choices=ECONOMIC_SECTOR_CHOICES)
    
    # Información tributaria
    tax_regime = models.CharField(max_length=20, choices=TAX_REGIME_CHOICES, default='COMMON')
    is_vat_responsible = models.BooleanField(default=True)
    is_great_contributor = models.BooleanField(default=False)
    great_contributor_resolution = models.CharField(max_length=100, blank=True)
    great_contributor_from = models.DateField(null=True, blank=True)
    
    is_self_withholding = models.BooleanField(default=False)
    self_withholding_resolution = models.CharField(max_length=100, blank=True)
    
    is_ica_agent = models.BooleanField(default=False)  # Agente de retención ICA
    is_simple_regime = models.BooleanField(default=False)  # Régimen Simple de Tributación
    
    # Información comercial
    trade_name = models.CharField(max_length=200, blank=True)
    ciiu_code = models.CharField(max_length=10, blank=True)  # Código CIIU principal
    secondary_ciiu_codes = models.TextField(blank=True)  # Códigos CIIU secundarios
    economic_activity = models.TextField(blank=True)
    
    # Datos de constitución
    incorporation_date = models.DateField(null=True, blank=True)
    incorporation_number = models.CharField(max_length=50, blank=True)  # Escritura pública
    incorporation_notary = models.CharField(max_length=100, blank=True)
    
    # Registro mercantil
    chamber_commerce_registration = models.CharField(max_length=50, blank=True)
    chamber_commerce_date = models.DateField(null=True, blank=True)
    chamber_commerce_renewal = models.DateField(null=True, blank=True)
    
    # Capital social (para personas jurídicas)
    authorized_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    subscribed_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    paid_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Información financiera
    total_assets = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_liabilities = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_equity = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    annual_revenue = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Empleados
    total_employees = models.IntegerField(default=0)
    
    # Representación legal
    has_legal_representative = models.BooleanField(default=True)
    legal_rep_name = models.CharField(max_length=200, blank=True)
    legal_rep_document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES, blank=True)
    legal_rep_document = models.CharField(max_length=20, blank=True)
    legal_rep_position = models.CharField(max_length=100, default='Representante Legal')
    
    # Revisor fiscal
    requires_fiscal_reviewer = models.BooleanField(default=False)
    fiscal_reviewer_name = models.CharField(max_length=200, blank=True)
    fiscal_reviewer_document = models.CharField(max_length=20, blank=True)
    fiscal_reviewer_professional_card = models.CharField(max_length=50, blank=True)
    fiscal_reviewer_firm = models.CharField(max_length=200, blank=True)
    
    # Contador
    accountant_name = models.CharField(max_length=200, blank=True)
    accountant_document = models.CharField(max_length=20, blank=True)
    accountant_professional_card = models.CharField(max_length=50, blank=True)
    
    # Facturación electrónica DIAN
    electronic_invoice_enabled = models.BooleanField(default=False)
    invoice_prefix = models.CharField(max_length=10, blank=True)
    invoice_resolution = models.CharField(max_length=100, blank=True)
    invoice_resolution_date = models.DateField(null=True, blank=True)
    invoice_from_number = models.IntegerField(null=True, blank=True)
    invoice_to_number = models.IntegerField(null=True, blank=True)
    technical_key = models.CharField(max_length=200, blank=True)
    test_set_id = models.CharField(max_length=100, blank=True)  # TestSetId DIAN
    
    # Nómina electrónica
    payroll_electronic_enabled = models.BooleanField(default=False)
    payroll_prefix = models.CharField(max_length=10, blank=True)
    payroll_software_id = models.CharField(max_length=100, blank=True)
    payroll_software_pin = models.CharField(max_length=10, blank=True)
    
    # Información para entidades públicas
    is_public_entity = models.BooleanField(default=False)
    public_entity_type = models.CharField(max_length=100, blank=True)
    public_entity_order = models.CharField(max_length=50, choices=[
        ('NATIONAL', 'Orden Nacional'),
        ('TERRITORIAL', 'Orden Territorial'),
        ('DEPARTMENTAL', 'Orden Departamental'),
        ('MUNICIPAL', 'Orden Municipal'),
        ('DISTRICT', 'Orden Distrital')
    ], blank=True)
    public_budget_code = models.CharField(max_length=50, blank=True)
    
    # Grupo empresarial
    is_part_of_group = models.BooleanField(default=False)
    business_group_name = models.CharField(max_length=200, blank=True)
    parent_company_nit = models.CharField(max_length=20, blank=True)
    is_holding = models.BooleanField(default=False)
    is_subsidiary = models.BooleanField(default=False)
    
    # Marco normativo contable
    accounting_framework = models.CharField(max_length=50, choices=[
        ('IFRS_FULL', 'NIIF Plenas (Grupo 1)'),
        ('IFRS_SME', 'NIIF para PYMES (Grupo 2)'),
        ('IFRS_MICRO', 'NIIF Simplificadas (Grupo 3)'),
        ('PUBLIC_ACCOUNTING', 'Contabilidad Pública (Res. 533/2015)'),
        ('PUBLIC_COMPANIES', 'Empresas Públicas (Res. 414/2014)'),
        ('SIMPLIFIED', 'Régimen Simplificado')
    ], default='IFRS_SME')
    
    # Archivos y documentos
    rut_file = models.FileField(upload_to='companies/rut/', blank=True, null=True)
    chamber_commerce_file = models.FileField(upload_to='companies/chamber/', blank=True, null=True)
    legal_rep_id_file = models.FileField(upload_to='companies/legal_rep/', blank=True, null=True)
    
    # Logos e imágenes
    logo = models.ImageField(upload_to='companies/logos/', blank=True, null=True)
    logo_invoice = models.ImageField(upload_to='companies/logos/', blank=True, null=True)
    digital_signature = models.FileField(upload_to='companies/signatures/', blank=True, null=True)
    stamp_image = models.ImageField(upload_to='companies/stamps/', blank=True, null=True)
    
    # Configuración de reportes
    report_header = models.TextField(blank=True)
    report_footer = models.TextField(blank=True)
    invoice_header = models.TextField(blank=True)
    invoice_footer = models.TextField(blank=True)
    invoice_terms = models.TextField(blank=True)
    
    # Información bancaria principal
    main_bank = models.CharField(max_length=100, blank=True)
    main_account_type = models.CharField(max_length=20, choices=[
        ('SAVINGS', 'Cuenta de Ahorros'),
        ('CHECKING', 'Cuenta Corriente')
    ], blank=True)
    main_account_number = models.CharField(max_length=30, blank=True)
    
    # Certificaciones
    iso_certifications = models.TextField(blank=True)
    other_certifications = models.TextField(blank=True)
    
    # Configuración contable
    fiscal_year_start_month = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    uses_cost_centers = models.BooleanField(default=True)
    uses_projects = models.BooleanField(default=False)
    uses_third_parties = models.BooleanField(default=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Información Extendida de Empresa'
        verbose_name_plural = 'Información Extendida de Empresas'
    
    def __str__(self):
        if self.person_type == 'NATURAL':
            return f"{self.get_full_name()} ({self.company.tax_id})"
        return f"{self.company.legal_name} ({self.company.tax_id})"
    
    def get_full_name(self):
        """Para personas naturales"""
        if self.person_type == 'NATURAL':
            parts = [self.first_name, self.middle_name, self.last_name, self.second_last_name]
            return ' '.join(filter(None, parts))
        return self.company.legal_name
    
    def is_sme(self):
        """Determina si es PYME"""
        return self.company_size in ['MICRO', 'SMALL', 'MEDIUM']
    
    def requires_electronic_invoice(self):
        """Determina si requiere facturación electrónica"""
        # Según calendario DIAN
        return self.is_great_contributor or self.electronic_invoice_enabled
    
    def get_tax_responsibilities(self):
        """Obtiene las responsabilidades tributarias"""
        responsibilities = []
        
        if self.is_vat_responsible:
            responsibilities.append('O-13: Responsable de IVA')
        if self.is_great_contributor:
            responsibilities.append('O-15: Gran Contribuyente')
        if self.is_self_withholding:
            responsibilities.append('O-23: Autorretenedor')
        if self.tax_regime == 'COMMON':
            responsibilities.append('O-48: Régimen Común')
        elif self.tax_regime == 'SIMPLIFIED':
            responsibilities.append('O-49: Régimen Simplificado')
        
        return responsibilities