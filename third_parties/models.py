"""
Modelos para Gestión Completa de Terceros
Personas Naturales y Jurídicas con toda la información colombiana
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import Company, User


class ThirdPartyType(models.Model):
    """Tipos de terceros"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='third_party_types')
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    is_shareholder = models.BooleanField(default=False)
    is_bank = models.BooleanField(default=False)
    
    class Meta:
        unique_together = [['company', 'code']]
    
    def __str__(self):
        return self.name


class ThirdParty(models.Model):
    """Modelo maestro de Terceros - Personas Naturales y Jurídicas"""
    
    # Tipos de persona
    PERSON_TYPE_CHOICES = [
        ('NATURAL', 'Persona Natural'),
        ('JURIDICA', 'Persona Jurídica')
    ]
    
    # Tipos de documento
    DOCUMENT_TYPE_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('PA', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad'),
        ('RC', 'Registro Civil'),
        ('NUIP', 'NUIP'),
        ('DIE', 'Documento de Identificación Extranjero')
    ]
    
    # Régimen tributario
    TAX_REGIME_CHOICES = [
        ('COMUN', 'Régimen Común'),
        ('SIMPLIFICADO', 'Régimen Simplificado'),
        ('NO_RESPONSABLE', 'No Responsable'),
        ('GRAN_CONTRIBUYENTE', 'Gran Contribuyente'),
        ('AUTORRETENEDOR', 'Autorretenedor'),
        ('EXTRANJERO', 'Régimen Extranjero')
    ]
    
    # Tipo de contribuyente
    TAXPAYER_TYPE_CHOICES = [
        ('NO_APLICA', 'No Aplica'),
        ('PERSONA_NATURAL', 'Persona Natural'),
        ('PERSONA_JURIDICA', 'Persona Jurídica'),
        ('GRAN_CONTRIBUYENTE', 'Gran Contribuyente'),
        ('ENTIDAD_PUBLICA', 'Entidad Pública'),
        ('REGIMEN_SIMPLIFICADO', 'Régimen Simplificado')
    ]
    
    # Género
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro')
    ]
    
    # Información básica
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='third_parties')
    person_type = models.CharField(max_length=10, choices=PERSON_TYPE_CHOICES)
    tax_code = models.CharField(max_length=2, blank=True, help_text="Código tributario: 13 para personas naturales, 31 para jurídicas")
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=20)
    verification_digit = models.CharField(max_length=1, blank=True)  # DV para NIT
    
    # Campos para personas naturales
    nombre = models.CharField('Primer Nombre', max_length=100, blank=True)
    segundo_nombre = models.CharField('Segundo Nombre', max_length=100, blank=True)
    primer_apellido = models.CharField('Primer Apellido', max_length=100, blank=True)
    segundo_apellido = models.CharField('Segundo Apellido', max_length=100, blank=True)
    
    # Campos para personas jurídicas
    razon_social = models.CharField('Razón Social', max_length=200, blank=True)
    
    # Campo unificado (se mantiene para compatibilidad)
    first_name = models.CharField(max_length=100, blank=True)  # Primer nombre o Razón Social
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    second_last_name = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)  # Nombre comercial
    
    # Información personal adicional
    birth_date = models.DateField('Fecha de Nacimiento', null=True, blank=True)
    gender = models.CharField('Género', max_length=10, choices=GENDER_CHOICES, blank=True)
    
    # Clasificación
    third_party_types = models.ManyToManyField(ThirdPartyType, blank=True)
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    is_shareholder = models.BooleanField(default=False)
    is_bank = models.BooleanField(default=False)
    is_government = models.BooleanField(default=False)
    is_payer = models.BooleanField(default=False)  # EPS, Aseguradora, Pagador de Salud
    
    # Información tributaria
    tax_regime = models.CharField(max_length=20, choices=TAX_REGIME_CHOICES, default='COMUN')
    taxpayer_type = models.CharField(max_length=30, choices=TAXPAYER_TYPE_CHOICES, default='NO_APLICA')
    is_vat_responsible = models.BooleanField(default=True)  # Responsable de IVA
    is_ica_agent = models.BooleanField(default=False)  # Agente de ICA
    is_withholding_agent = models.BooleanField(default=False)  # Agente retenedor
    is_self_withholding = models.BooleanField(default=False)  # Autorretenedor
    is_great_contributor = models.BooleanField(default=False)  # Gran contribuyente
    great_contributor_resolution = models.CharField(max_length=100, blank=True)
    
    # Información de contacto y geográfica
    address = models.CharField('Dirección', max_length=200)
    neighborhood = models.CharField('Barrio', max_length=100, blank=True)
    city = models.CharField('Ciudad', max_length=100)
    state = models.CharField('Departamento', max_length=100)
    country = models.CharField('País', max_length=100, default='Colombia')
    postal_code = models.CharField('Código Postal', max_length=20, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Información adicional para personas jurídicas
    economic_activity = models.CharField(max_length=200, blank=True)  # Actividad económica
    ciiu_code = models.CharField(max_length=10, blank=True)  # Código CIIU
    legal_representative = models.CharField(max_length=200, blank=True)
    legal_rep_document = models.CharField(max_length=20, blank=True)
    
    # Información bancaria
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_type = models.CharField(max_length=20, choices=[
        ('SAVINGS', 'Cuenta de Ahorros'),
        ('CHECKING', 'Cuenta Corriente')
    ], blank=True)
    bank_account_number = models.CharField(max_length=30, blank=True)
    
    # Información comercial
    credit_limit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    payment_term_days = models.IntegerField(default=30)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Información de contacto adicional
    contact_person = models.CharField(max_length=200, blank=True)
    contact_position = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # RUT y documentos
    has_rut = models.BooleanField(default=False)
    rut_file = models.FileField(upload_to='third_parties/rut/', blank=True, null=True)
    chamber_commerce_file = models.FileField(upload_to='third_parties/chamber/', blank=True, null=True)
    
    # Estados
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    
    # Calificación
    rating = models.CharField(max_length=10, choices=[
        ('AAA', 'Excelente'),
        ('AA', 'Muy Bueno'),
        ('A', 'Bueno'),
        ('B', 'Regular'),
        ('C', 'Malo'),
        ('D', 'Muy Malo')
    ], blank=True)
    
    # Observaciones
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)  # Notas internas no visibles al tercero
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_third_parties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_third_parties')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'document_type', 'document_number']]
        ordering = ['first_name', 'last_name']
        verbose_name = 'Tercero'
        verbose_name_plural = 'Terceros'
    
    def __str__(self):
        name = self.get_full_name()
        return f"{name} - {self.document_number} ({self.get_person_type_display()})"
    
    def get_full_name(self):
        """Obtiene el nombre completo"""
        if self.person_type == 'NATURAL':
            # Usar los campos específicos para personas naturales si están disponibles
            if self.nombre or self.primer_apellido:
                parts = [self.nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido]
                return ' '.join(filter(None, parts))
            else:
                # Fallback a campos legacy
                parts = [self.first_name, self.middle_name, self.last_name, self.second_last_name]
                return ' '.join(filter(None, parts))
        else:
            # Para personas jurídicas
            return self.razon_social or self.trade_name or self.first_name
    
    def calculate_verification_digit(self):
        """Calcula el dígito de verificación para NIT"""
        if self.document_type != 'NIT':
            return ''
        
        nit = self.document_number
        vpri = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        
        suma = 0
        for i, digit in enumerate(reversed(nit)):
            suma += int(digit) * vpri[i]
        
        residuo = suma % 11
        
        if residuo > 1:
            return str(11 - residuo)
        else:
            return str(residuo)
    
    def save(self, *args, **kwargs):
        # Calcular dígito de verificación si es NIT
        if self.document_type == 'NIT' and not self.verification_digit:
            self.verification_digit = self.calculate_verification_digit()
        
        # Establecer código tributario según tipo de persona
        if self.person_type == 'NATURAL':
            self.tax_code = '13'
            # Sincronizar campos para personas naturales
            if self.nombre and self.primer_apellido and not self.first_name:
                self.first_name = self.nombre
                self.last_name = self.primer_apellido
                self.middle_name = self.segundo_nombre
                self.second_last_name = self.segundo_apellido
        elif self.person_type == 'JURIDICA':
            self.tax_code = '31'
            if not self.taxpayer_type:
                self.taxpayer_type = 'PERSONA_JURIDICA'
            # Sincronizar campos para personas jurídicas
            if self.razon_social and not self.first_name:
                self.first_name = self.razon_social
        
        super().save(*args, **kwargs)
        
        # Sincronizar con Customer si es cliente
        if self.is_customer:
            self._sync_to_customer()
        
        # Sincronizar con Supplier si es proveedor
        if self.is_supplier:
            self._sync_to_supplier()
    
    def _sync_to_customer(self):
        """Sincroniza datos con el modelo Customer en accounts_receivable"""
        try:
            from accounts_receivable.models_customer import Customer, CustomerType
            
            # Buscar si ya existe el customer
            customer = Customer.objects.filter(
                company=self.company,
                document_number=self.document_number,
                document_type=self.document_type
            ).first()
            
            # Si no existe, crear uno nuevo
            if not customer:
                # Obtener o crear tipo de cliente por defecto
                customer_type, created = CustomerType.objects.get_or_create(
                    company=self.company,
                    code='GENERAL',
                    defaults={
                        'name': 'Cliente General',
                        'created_by': self.created_by
                    }
                )
                
                # Obtener cuenta por cobrar por defecto (13050001 - Clientes Nacionales)
                from accounting.models_accounts import Account
                receivable_account = Account.objects.filter(
                    company=self.company,
                    code__startswith='1305'
                ).first()
                
                if receivable_account:
                    customer = Customer.objects.create(
                        company=self.company,
                        code=self.document_number,
                        document_type=self.document_type,
                        document_number=self.document_number,
                        verification_digit=self.verification_digit,
                        business_name=self.get_full_name(),
                        trade_name=self.trade_name,
                        first_name=self.first_name,
                        last_name=self.last_name,
                        customer_type=customer_type,
                        address=self.address,
                        city=self.city,
                        state=self.state,
                        country=self.country,
                        postal_code=self.postal_code,
                        phone=self.phone,
                        mobile=self.mobile,
                        email=self.email,
                        credit_limit=self.credit_limit,
                        credit_days=self.payment_term_days,
                        receivable_account=receivable_account,
                        created_by=self.created_by
                    )
            else:
                # Actualizar datos existentes
                customer.business_name = self.get_full_name()
                customer.trade_name = self.trade_name
                customer.first_name = self.first_name
                customer.last_name = self.last_name
                customer.address = self.address
                customer.city = self.city
                customer.state = self.state
                customer.country = self.country
                customer.postal_code = self.postal_code
                customer.phone = self.phone
                customer.mobile = self.mobile
                customer.email = self.email
                customer.credit_limit = self.credit_limit
                customer.credit_days = self.payment_term_days
                customer.save()
                
        except Exception as e:
            print(f"Error sincronizando cliente: {e}")
    
    def _sync_to_supplier(self):
        """Sincroniza datos con el modelo Supplier en accounts_payable"""
        try:
            from accounts_payable.models_supplier import Supplier, SupplierType
            
            # Buscar si ya existe el supplier
            supplier = Supplier.objects.filter(
                company=self.company,
                document_number=self.document_number,
                document_type=self.document_type
            ).first()
            
            # Si no existe, crear uno nuevo
            if not supplier:
                # Obtener o crear tipo de proveedor por defecto
                supplier_type, created = SupplierType.objects.get_or_create(
                    company=self.company,
                    code='GENERAL',
                    defaults={
                        'name': 'Proveedor General',
                        'created_by': self.created_by
                    }
                )
                
                # Obtener cuenta por pagar por defecto (22050001 - Proveedores Nacionales)
                from accounting.models_accounts import Account
                payable_account = Account.objects.filter(
                    company=self.company,
                    code__startswith='2205'
                ).first()
                
                if payable_account:
                    supplier = Supplier.objects.create(
                        company=self.company,
                        code=self.document_number,
                        document_type=self.document_type,
                        document_number=self.document_number,
                        verification_digit=self.verification_digit,
                        business_name=self.get_full_name(),
                        trade_name=self.trade_name,
                        first_name=self.first_name,
                        last_name=self.last_name,
                        supplier_type=supplier_type,
                        address=self.address,
                        city=self.city,
                        state=self.state,
                        country=self.country,
                        postal_code=self.postal_code,
                        phone=self.phone,
                        mobile=self.mobile,
                        email=self.email,
                        contact_name=self.contact_person,
                        contact_phone=self.contact_phone,
                        contact_email=self.contact_email,
                        payment_days=self.payment_term_days,
                        payable_account=payable_account,
                        created_by=self.created_by
                    )
            else:
                # Actualizar datos existentes
                supplier.business_name = self.get_full_name()
                supplier.trade_name = self.trade_name
                supplier.first_name = self.first_name
                supplier.last_name = self.last_name
                supplier.address = self.address
                supplier.city = self.city
                supplier.state = self.state
                supplier.country = self.country
                supplier.postal_code = self.postal_code
                supplier.phone = self.phone
                supplier.mobile = self.mobile
                supplier.email = self.email
                supplier.contact_name = self.contact_person
                supplier.contact_phone = self.contact_phone
                supplier.contact_email = self.contact_email
                supplier.payment_days = self.payment_term_days
                supplier.save()
                
        except Exception as e:
            print(f"Error sincronizando proveedor: {e}")


class CompanyExtended(models.Model):
    """Extensión del modelo Company con información completa"""
    COMPANY_TYPE_CHOICES = [
        ('PUBLIC', 'Empresa Pública'),
        ('PRIVATE', 'Empresa Privada'),
        ('MIXED', 'Empresa Mixta'),
        ('NGO', 'ONG/Sin Ánimo de Lucro'),
        ('GOVERNMENT', 'Entidad Gubernamental'),
        ('COOPERATIVE', 'Cooperativa'),
        ('SOLE_PROPRIETOR', 'Persona Natural Comerciante')
    ]
    
    COMPANY_SIZE_CHOICES = [
        ('MICRO', 'Microempresa'),
        ('SMALL', 'Pequeña Empresa'),
        ('MEDIUM', 'Mediana Empresa'),
        ('LARGE', 'Gran Empresa')
    ]
    
    SECTOR_CHOICES = [
        ('AGRICULTURE', 'Agricultura'),
        ('MINING', 'Minería'),
        ('MANUFACTURING', 'Manufactura'),
        ('UTILITIES', 'Servicios Públicos'),
        ('CONSTRUCTION', 'Construcción'),
        ('COMMERCE', 'Comercio'),
        ('TRANSPORT', 'Transporte'),
        ('FINANCE', 'Financiero'),
        ('SERVICES', 'Servicios'),
        ('GOVERNMENT', 'Gobierno'),
        ('EDUCATION', 'Educación'),
        ('HEALTH', 'Salud'),
        ('TECHNOLOGY', 'Tecnología')
    ]
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='extended_info')
    
    # Clasificación de empresa
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES)
    company_size = models.CharField(max_length=10, choices=COMPANY_SIZE_CHOICES)
    economic_sector = models.CharField(max_length=20, choices=SECTOR_CHOICES)
    
    # Información legal
    legal_name = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    incorporation_date = models.DateField(null=True, blank=True)
    incorporation_number = models.CharField(max_length=50, blank=True)
    
    # Información DIAN
    is_great_contributor = models.BooleanField(default=False)
    great_contributor_from = models.DateField(null=True, blank=True)
    is_self_withholding = models.BooleanField(default=False)
    self_withholding_resolution = models.CharField(max_length=100, blank=True)
    
    # Facturación electrónica
    electronic_invoice_enabled = models.BooleanField(default=False)
    invoice_prefix = models.CharField(max_length=10, blank=True)
    invoice_resolution = models.CharField(max_length=100, blank=True)
    invoice_resolution_date = models.DateField(null=True, blank=True)
    invoice_from_number = models.IntegerField(null=True, blank=True)
    invoice_to_number = models.IntegerField(null=True, blank=True)
    technical_key = models.CharField(max_length=200, blank=True)
    
    # Representación legal
    legal_representative_name = models.CharField(max_length=200)
    legal_representative_document = models.CharField(max_length=20)
    legal_representative_position = models.CharField(max_length=100, default='Representante Legal')
    
    # Revisor fiscal
    has_fiscal_reviewer = models.BooleanField(default=False)
    fiscal_reviewer_name = models.CharField(max_length=200, blank=True)
    fiscal_reviewer_document = models.CharField(max_length=20, blank=True)
    fiscal_reviewer_professional_card = models.CharField(max_length=50, blank=True)
    
    # Información para entidades públicas
    is_public_entity = models.BooleanField(default=False)
    public_entity_type = models.CharField(max_length=100, blank=True)
    public_entity_code = models.CharField(max_length=50, blank=True)
    territorial_entity = models.CharField(max_length=100, blank=True)  # Municipio, Departamento, etc.
    
    # Información de grupo empresarial
    is_part_of_group = models.BooleanField(default=False)
    business_group_name = models.CharField(max_length=200, blank=True)
    parent_company_nit = models.CharField(max_length=20, blank=True)
    
    # Certificaciones y registros
    iso_certifications = models.TextField(blank=True)
    chamber_commerce_registration = models.CharField(max_length=50, blank=True)
    chamber_commerce_renewal_date = models.DateField(null=True, blank=True)
    
    # Capital y patrimonio
    share_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    paid_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_assets = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_employees = models.IntegerField(default=0)
    
    # Configuración contable
    fiscal_year_start_month = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    uses_ifrs = models.BooleanField(default=False)  # NIIF
    accounting_framework = models.CharField(max_length=50, choices=[
        ('IFRS_FULL', 'NIIF Plenas'),
        ('IFRS_SME', 'NIIF para PYMES'),
        ('IFRS_MICRO', 'NIIF para Microempresas'),
        ('PUBLIC_ACCOUNTING', 'Contabilidad Pública'),
        ('SIMPLIFIED', 'Régimen Simplificado')
    ], default='IFRS_SME')
    
    # Logos y documentos
    logo = models.ImageField(upload_to='companies/logos/', blank=True, null=True)
    header_image = models.ImageField(upload_to='companies/headers/', blank=True, null=True)
    footer_image = models.ImageField(upload_to='companies/footers/', blank=True, null=True)
    digital_signature = models.FileField(upload_to='companies/signatures/', blank=True, null=True)
    
    # Configuración de reportes
    report_header_text = models.TextField(blank=True)
    report_footer_text = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Información Extendida de Empresa'
        verbose_name_plural = 'Información Extendida de Empresas'
    
    def __str__(self):
        return f"{self.legal_name} ({self.get_company_type_display()})"
    
    def is_sme(self):
        """Determina si es PYME"""
        return self.company_size in ['MICRO', 'SMALL', 'MEDIUM']


class ThirdPartyContact(models.Model):
    """Contactos adicionales de terceros"""
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.third_party.get_full_name()}"


class ThirdPartyAddress(models.Model):
    """Direcciones adicionales de terceros"""
    ADDRESS_TYPE_CHOICES = [
        ('MAIN', 'Principal'),
        ('BILLING', 'Facturación'),
        ('SHIPPING', 'Envío'),
        ('BRANCH', 'Sucursal'),
        ('WAREHOUSE', 'Bodega'),
        ('OTHER', 'Otra')
    ]
    
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='MAIN')
    name = models.CharField(max_length=100, blank=True)  # Nombre de la sucursal o referencia
    address = models.CharField(max_length=200)
    neighborhood = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Colombia')
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_primary', 'address_type']
        verbose_name_plural = 'Third Party Addresses'
    
    def __str__(self):
        return f"{self.get_address_type_display()} - {self.address}"


class ThirdPartyDocument(models.Model):
    """Documentos asociados a terceros"""
    DOCUMENT_TYPE_CHOICES = [
        ('RUT', 'RUT'),
        ('CC', 'Cámara de Comercio'),
        ('BANK_CERT', 'Certificación Bancaria'),
        ('FINANCIAL_STATES', 'Estados Financieros'),
        ('COMMERCIAL_REF', 'Referencias Comerciales'),
        ('CONTRACT', 'Contrato'),
        ('POLICY', 'Póliza'),
        ('OTHER', 'Otro')
    ]
    
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='third_parties/documents/')
    description = models.TextField(blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.third_party.get_full_name()}"