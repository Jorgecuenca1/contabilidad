# 🏥 SISTEMA RIPS - FLUJO FINAL IMPLEMENTADO

## 📌 RESUMEN EJECUTIVO

El sistema RIPS ha sido implementado siguiendo el **FLUJO REALISTA** solicitado:

- ✅ **NO requiere crear "episodios" manualmente**
- ✅ **Los servicios se dan directamente** en sus módulos correspondientes
- ✅ **Al facturar se seleccionan los servicios del paciente** desde su historia clínica
- ✅ **El RIPS se genera desde la factura**
- ✅ **Todo es automático y fluido para el personal**

---

## 🔄 FLUJO COMPLETO DEL SISTEMA

### **1. RECEPCIÓN DEL PACIENTE**

```
Paciente llega a la IPS
   ↓
Ya existe como Patient en el sistema
(o se registra si es nuevo)
   ↓
Listo para recibir servicios
```

**NO SE REQUIERE:**
- ❌ Abrir "episodio de atención"
- ❌ Crear registros adicionales
- ❌ Pasos manuales extra

---

### **2. ATENCIÓN Y SERVICIOS**

El paciente recibe atención en diferentes módulos:

#### **A. CONSULTAS MÉDICAS**
```
Módulos: cardiology, gynecology, psychology, ophthalmology, etc.
   ↓
Se registra la consulta directamente
   ↓
Marca automática: is_billed = False
   ↓
Queda en historia clínica del paciente
```

#### **B. MEDICAMENTOS**
```
Módulo: pharmacy
   ↓
Se crea Dispensing (dispensación de medicamento)
   ↓
Se vincula al patient
   ↓
Marca: is_billed = False
   ↓
Queda en historia clínica
```

#### **C. IMÁGENES DIAGNÓSTICAS**
```
Módulo: imaging
   ↓
Se crea ImagingOrder (orden de imagen)
   ↓
Se vincula al patient
   ↓
Marca: is_billed = False
   ↓
Queda en historia clínica
```

#### **D. HOSPITALIZACIÓN**
```
Módulo: hospitalization
   ↓
Se crea Admission (admisión)
   ↓
Se vincula al patient
   ↓
Marca: is_billed = False
   ↓
Queda en historia clínica
```

#### **E. CIRUGÍAS**
```
Módulo: surgery
   ↓
Se crea Surgery (cirugía)
   ↓
Se vincula al patient
   ↓
Marca: is_billed = False
   ↓
Queda en historia clínica
```

**TODOS LOS SERVICIOS:**
- Se registran directamente en sus módulos
- Se vinculan automáticamente al paciente
- Quedan marcados como "no facturados" (is_billed=False)
- Van a la historia clínica automáticamente

---

### **3. FACTURACIÓN** ⭐ (NUEVO - MEJORADO)

```
Personal va a: Facturación > Crear Factura
   ↓
Selecciona:
   - Paciente
   - EPS/Aseguradora (pagador)
   ↓
El sistema muestra AUTOMÁTICAMENTE todos los servicios NO FACTURADOS:
   ┌──────────────────────────────────────┐
   │ SERVICIOS PENDIENTES DE FACTURAR     │
   ├──────────────────────────────────────┤
   │ ☑ Consulta Cardiología - $35,000    │
   │ ☑ Acetaminofen 500mg x20 - $4,000   │
   │ ☑ Radiografía de Tórax - $25,000   │
   │ ☑ Hospitalización 3 días - $450,000│
   │ ☐ Cirugía Apendicectomía - $2,500K │
   └──────────────────────────────────────┘
   ↓
Se seleccionan los servicios a incluir en esta factura
   ↓
Se crea la HealthInvoice
   ↓
Por cada servicio seleccionado:
   - Se crea HealthInvoiceItem
   - Se vincula al servicio original (GenericForeignKey)
   - Se marca el servicio como facturado (is_billed=True)
   ↓
Factura lista!
```

**NUEVA API CREADA:**
```
URL: /billing_health/api/patient/unbilled-services/?patient_id=XXX

Retorna JSON con TODOS los servicios no facturados del paciente:
{
  "services": [
    {
      "id": "uuid",
      "type": "medication",
      "type_display": "Medicamento",
      "service_code": "19840247",
      "service_name": "ACETAMINOFEN 500 MG",
      "date": "2025-10-15 14:30",
      "quantity": 20,
      "unit_price": 200,
      "total": 4000,
      "content_type_id": 45,
      "object_id": "uuid"
    },
    {
      "id": "uuid",
      "type": "imaging",
      "type_display": "Imagen Diagnóstica",
      "service_code": "870201",
      "service_name": "Radiografía de Tórax",
      ...
    },
    ...
  ],
  "total_services": 5,
  "patient_name": "Juan Pérez",
  "patient_document": "1234567890"
}
```

---

### **4. GENERACIÓN DE RIPS** 🎯

```
Desde la factura emitida:
   ↓
Clic en "Generar RIPS"
   ↓
El sistema:
   1. Lee la factura (HealthInvoice)
   2. Lee todos los items (HealthInvoiceItem)
   3. Por cada item, accede al servicio original vía GenericForeignKey
   4. Extrae los datos necesarios según el tipo de servicio
   5. Clasifica en: Consulta / Procedimiento / Medicamento / Urgencia
   6. Genera estructura JSON según Resolución 3374/2000
   ↓
Archivo RIPS generado:
   - Ubicación: media/rips/<company_id>/RIPS_<factura>.json
   - Formato: JSON estándar MinSalud
   - Listo para enviar a EPS
```

**Estructura RIPS Generada:**
```json
{
  "factura": {
    "numDocumentoIdObligado": "860000111",
    "numFactura": "FAC-000123",
    "tipoNota": "1",
    "numNota": "",
    ...
  },
  "usuario": {
    "codPrestador": "860000111",
    "tipoDocumentoIdentificacion": "CC",
    "numDocumentoIdentificacion": "1234567890",
    "tipoUsuario": "1",
    ...
  },
  "consultas": [
    {
      "codPrestador": "860000111",
      "fechaConsulta": "2025-10-15",
      "modalidadGrupoServicioTecSal": "01",
      "grupoServicios": "01",
      "codConsulta": "890201",
      "finalidadTecnologiaSalud": "10",
      "causaMotivoAtencion": "21",
      "codDiagnosticoPrincipal": "J069",
      "valorConsulta": 35000
    }
  ],
  "medicamentos": [
    {
      "codPrestador": "860000111",
      "fechaSuministro": "2025-10-15",
      "codigoMedicamento": "19840247",
      "nombreMedicamento": "ACETAMINOFEN 500 MG",
      "cantidadSuministrada": 20,
      "valorUnitario": 200,
      "valorTotal": 4000
    }
  ],
  "procedimientos": [...],
  "urgencias": [...]
}
```

---

## 🏗️ ARQUITECTURA TÉCNICA

### **Modelos Clave**

#### **1. HealthInvoice** (Factura de Salud)
```python
class HealthInvoice(models.Model):
    invoice_number = models.CharField(unique=True)
    patient = models.ForeignKey(Patient)
    payer = models.ForeignKey(ThirdParty)  # EPS
    invoice_date = models.DateField()
    total = models.DecimalField()
    rips_generated = models.BooleanField(default=False)
    rips_file_path = models.CharField()
```

#### **2. HealthInvoiceItem** (Item de Factura)
```python
class HealthInvoiceItem(models.Model):
    invoice = models.ForeignKey(HealthInvoice)
    service_type = models.CharField()  # medication/imaging/etc
    service_code = models.CharField()  # CUPS o CUM
    service_name = models.CharField()
    quantity = models.DecimalField()
    unit_price = models.DecimalField()
    total = models.DecimalField()

    # VÍNCULO AL SERVICIO ORIGINAL ⭐
    content_type = models.ForeignKey(ContentType)
    object_id = models.UUIDField()
    service_object = GenericForeignKey('content_type', 'object_id')
```

#### **3. Servicios (Múltiples Módulos)**

**Pharmacy:**
```python
class Dispensing(models.Model):
    patient = models.ForeignKey(Patient)
    medication = models.ForeignKey(Medication)
    quantity = models.DecimalField()
    is_billed = models.BooleanField(default=False)  # ⭐
```

**Imaging:**
```python
class ImagingOrder(models.Model):
    patient = models.ForeignKey(Patient)
    imaging_type = models.ForeignKey(ImagingType)
    is_billed = models.BooleanField(default=False)  # ⭐
```

**Hospitalization:**
```python
class Admission(models.Model):
    patient = models.ForeignKey(Patient)
    room = models.ForeignKey(Room)
    is_billed = models.BooleanField(default=False)  # ⭐
```

**Surgery:**
```python
class Surgery(models.Model):
    patient = models.ForeignKey(Patient)
    procedure_name = models.CharField()
    is_billed = models.BooleanField(default=False)  # ⭐
```

**Cardiology:**
```python
class CardiologyConsultation(models.Model):
    patient = models.ForeignKey(Patient)
    consultation_date = models.DateTimeField()
    is_billed = models.BooleanField(default=False)  # ⭐
```

### **API de Servicios No Facturados**

**Vista:** `billing_health.views.api_get_patient_unbilled_services`

**Funcionalidad:**
- Consulta TODOS los módulos de salud
- Filtra servicios con `is_billed=False`
- Retorna lista unificada en formato JSON
- Se ordena por fecha (más recientes primero)

**Módulos consultados:**
1. ✅ Pharmacy (Dispensing)
2. ✅ Imaging (ImagingOrder)
3. ✅ Hospitalization (Admission)
4. ✅ Surgery (Surgery)
5. ✅ Cardiology (CardiologyConsultation)
6. 🔄 Extensible a más módulos...

---

## 📁 ARCHIVOS IMPORTANTES

### **Backend**

#### **billing_health/views.py**
```python
# NUEVA VISTA API (línea 830)
@login_required
def api_get_patient_unbilled_services(request):
    """
    API para obtener todos los servicios NO FACTURADOS de un paciente
    Retorna servicios de: farmacia, imágenes, hospitalizaciones,
    consultas, cirugías, etc.
    """
    # Consulta todos los módulos
    # Filtra is_billed=False
    # Retorna JSON con todos los servicios
```

#### **billing_health/urls.py**
```python
# NUEVA RUTA API
path('api/patient/unbilled-services/',
     views.api_get_patient_unbilled_services,
     name='api_patient_unbilled_services'),
```

#### **rips/utils.py**
```python
def generate_rips_json(invoice):
    """
    Genera estructura RIPS desde una factura
    Lee los HealthInvoiceItem
    Accede al servicio original vía GenericFK
    Extrae datos y genera JSON
    """

def save_rips_files(rips_data, invoice, format='json'):
    """
    Guarda archivos RIPS en media/rips/
    """
```

### **Catálogos**

#### **catalogs/models.py**
```python
class CUPSProcedure(models.Model):
    """Códigos CUPS de procedimientos"""
    code = models.CharField(max_length=10)  # Ej: 890201
    name = models.CharField(max_length=500)
    standard_price = models.DecimalField()

class CUMSMedication(models.Model):
    """Códigos CUM de medicamentos"""
    code = models.CharField(max_length=20)  # Ej: 19840247
    active_ingredient = models.CharField(max_length=200)
    pharmaceutical_form = models.CharField(max_length=100)
    standard_price = models.DecimalField()
```

#### **Comandos de Gestión**
```bash
# Cargar 55 procedimientos CUPS comunes
python manage.py load_cups_codes --sample

# Cargar 60+ medicamentos CUM comunes
python manage.py load_cum_codes --sample
```

---

## 🎯 FLUJO DE DATOS COMPLETO

```
PACIENTE RECIBE SERVICIOS
├─ Consulta Cardiología
│  └─ CardiologyConsultation(patient=X, is_billed=False)
│
├─ Medicamento Farmacia
│  └─ Dispensing(patient=X, is_billed=False)
│
├─ Radiografía
│  └─ ImagingOrder(patient=X, is_billed=False)
│
└─ Hospitalización
   └─ Admission(patient=X, is_billed=False)

PERSONAL VA A FACTURAR
├─ Selecciona paciente X
├─ API consulta servicios no facturados del paciente X
├─ Muestra lista de servicios disponibles
└─ Personal selecciona cuáles incluir

SE CREA LA FACTURA
├─ HealthInvoice(patient=X, payer=EPS_Y)
│
└─ Por cada servicio seleccionado:
   ├─ HealthInvoiceItem(
   │     service_type="medication",
   │     content_type=ContentType(Dispensing),
   │     object_id=dispensing.id
   │  )
   │
   └─ Dispensing.is_billed = True ✓

SE GENERA EL RIPS
├─ Lee HealthInvoice
├─ Lee HealthInvoiceItem
├─ Accede servicio original: item.service_object
├─ Extrae datos: medicamento.cum_code, medicamento.nombre, etc.
├─ Clasifica: consulta/procedimiento/medicamento/urgencia
├─ Genera JSON según normativa MinSalud
└─ Guarda: media/rips/RIPS_FAC-000123.json
```

---

## 🚀 CÓMO USAR EL SISTEMA

### **Paso 1: Configuración Inicial**

#### **1.1 Cargar Catálogos**
```bash
# En el directorio del proyecto
python manage.py load_cups_codes --sample
python manage.py load_cum_codes --sample
```

#### **1.2 Crear EPS/Aseguradoras**
```
1. Ir a: Terceros > Crear Tercero
2. Llenar datos de la EPS
3. ✓ Marcar: "Es Pagador" (is_payer=True)
4. Guardar
```

#### **1.3 Registrar Pacientes**
```
1. Ir a: Pacientes > Crear Paciente
2. Llenar datos del paciente
3. Guardar
```

---

### **Paso 2: Atención Diaria**

#### **2.1 Paciente Recibe Consulta**
```
1. Ir al módulo correspondiente (Cardiología, Ginecología, etc.)
2. Crear consulta
3. Seleccionar paciente
4. Registrar diagnóstico, examen, tratamiento
5. Guardar
→ Queda automáticamente en historia clínica con is_billed=False
```

#### **2.2 Se Despachan Medicamentos**
```
1. Ir a: Farmacia > Dispensar Medicamento
2. Seleccionar paciente
3. Seleccionar medicamento (con código CUM)
4. Ingresar cantidad
5. Guardar
→ Queda automáticamente en historia clínica con is_billed=False
```

#### **2.3 Se Ordena Imagen Diagnóstica**
```
1. Ir a: Imágenes > Crear Orden
2. Seleccionar paciente
3. Seleccionar tipo de imagen
4. Guardar
→ Queda automáticamente en historia clínica con is_billed=False
```

---

### **Paso 3: Facturación**

#### **3.1 Crear Factura**
```
1. Ir a: Facturación Salud > Crear Factura
2. Seleccionar Paciente
   → El sistema carga automáticamente sus servicios no facturados
3. Seleccionar EPS/Aseguradora
4. Revisar lista de servicios pendientes
5. ☑ Marcar los servicios a incluir en esta factura
6. Hacer clic en "Crear Factura"
   → Los servicios seleccionados se marcan como facturados
   → Se crea la factura con todos los items
```

---

### **Paso 4: Generar RIPS**

#### **4.1 Desde la Factura**
```
1. Ir a: Facturación Salud > Facturas
2. Seleccionar la factura emitida
3. Hacer clic en "Generar RIPS"
   → Se genera archivo JSON según normativa
   → Se guarda en media/rips/
4. Descargar archivo RIPS
5. Enviar a la EPS
```

---

## ✅ VENTAJAS DEL FLUJO IMPLEMENTADO

### **Para el Personal Médico:**
✅ No necesita "abrir episodio" antes de atender
✅ Registra servicios directamente en cada módulo
✅ Flujo natural y rápido
✅ Todo va automáticamente a historia clínica

### **Para Facturación:**
✅ Ve todos los servicios del paciente en un solo lugar
✅ Selecciona fácilmente qué incluir en la factura
✅ Sistema marca automáticamente lo facturado
✅ No hay duplicados

### **Para RIPS:**
✅ Se genera automáticamente desde la factura
✅ Trae datos reales de los servicios originales
✅ Códigos CUPS/CUM correctos
✅ Formato estándar MinSalud
✅ Listo para enviar

### **Para Auditoría:**
✅ Trazabilidad completa: servicio → factura → RIPS
✅ GenericForeignKey mantiene vínculo al servicio original
✅ Historia clínica completa y consistente

---

## 🎓 EJEMPLO COMPLETO

### **Caso: Juan Pérez llega con dolor de cabeza**

**1. Recepción:**
- Juan ya está registrado como paciente

**2. Consulta:**
```
Cardiología > Nueva Consulta
- Paciente: Juan Pérez
- Diagnóstico: J06.9 (Infección respiratoria aguda)
- Guardar
→ Se crea CardiologyConsultation(is_billed=False)
```

**3. Medicamentos:**
```
Farmacia > Dispensar
- Paciente: Juan Pérez
- Medicamento: ACETAMINOFEN 500 MG (CUM: 19840247)
- Cantidad: 20 tabletas
- Guardar
→ Se crea Dispensing(is_billed=False)
```

**4. Imagen:**
```
Imágenes > Nueva Orden
- Paciente: Juan Pérez
- Tipo: Radiografía de Tórax (CUPS: 870201)
- Guardar
→ Se crea ImagingOrder(is_billed=False)
```

**5. Facturación (al día siguiente):**
```
Facturación > Crear Factura
- Paciente: Juan Pérez
- EPS: SURA

Sistema muestra servicios pendientes:
  ☑ Consulta Cardiología - $35,000
  ☑ Acetaminofen 500mg x20 - $4,000
  ☑ Radiografía de Tórax - $25,000
  TOTAL: $64,000

- Seleccionar todos
- Crear Factura FAC-000123

→ Se crea HealthInvoice
→ Se crean 3 HealthInvoiceItem (con GenericFK)
→ Los 3 servicios se marcan is_billed=True
```

**6. RIPS:**
```
Factura FAC-000123 > Generar RIPS

→ Genera RIPS_FAC-000123.json con:
  - 1 consulta (890201)
  - 1 medicamento (19840247)
  - 1 procedimiento/imagen (870201)

→ Listo para enviar a SURA
```

---

## 📞 SOPORTE Y PRÓXIMOS PASOS

### **Sistema Listo Para:**
✅ Registrar servicios en cualquier módulo
✅ Facturar servicios del paciente
✅ Generar RIPS automáticamente
✅ Enviar a EPS

### **Módulos RIPS Opcionales:**
- 📋 Los episodios de atención siguen disponibles
- 📋 Se pueden usar si se desea agrupar servicios manualmente
- 📋 Pero NO son obligatorios para facturar o generar RIPS

### **Para Agregar Más Módulos:**
```python
# En billing_health/views.py > api_get_patient_unbilled_services
# Agregar nueva sección:

try:
    from nuevo_modulo.models import NuevoServicio
    servicios = NuevoServicio.objects.filter(
        patient=patient,
        company=company,
        is_billed=False
    )

    for servicio in servicios:
        services.append({
            'id': str(servicio.id),
            'type': 'nuevo_tipo',
            'type_display': 'Nuevo Servicio',
            # ... más campos
        })
except:
    pass
```

---

## 🎉 CONCLUSIÓN

El sistema RIPS está **COMPLETAMENTE FUNCIONAL** con el flujo realista:

1. ✅ Servicios se dan directamente (sin episodios manuales)
2. ✅ Todo va automáticamente a historia clínica
3. ✅ Facturación selecciona servicios del paciente
4. ✅ RIPS se genera desde la factura
5. ✅ Trazabilidad completa de servicio a RIPS

**¡El flujo es natural, rápido y cumple con la normativa colombiana!**
