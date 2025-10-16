# FLUJO DEL SISTEMA RIPS - EXPLICACIÓN DETALLADA

## 📋 RESUMEN EJECUTIVO

Este documento explica cómo implementé el módulo RIPS y el flujo de atención de pacientes para generar los archivos RIPS requeridos por el sistema de salud colombiano.

---

## ❓ TU PREGUNTA CLAVE

> "La apertura del paciente se hace desde la consulta o la recepción del paciente. El RIPS se genera de la factura, cierto?"

**RESPUESTA:** Sí, tienes razón. Aquí está cómo lo implementé:

---

## 🔄 FLUJO ACTUAL IMPLEMENTADO

### **Opción A: Flujo con Episodio de Atención (Implementado)**

```
1. RECEPCIÓN/ADMISIÓN
   ├─ Paciente llega a la IPS
   ├─ Se crea un "Episodio de Atención" manualmente
   ├─ Se selecciona: Paciente, EPS/Aseguradora, Tipo de episodio
   └─ Estado: ACTIVO

2. ATENCIÓN Y SERVICIOS
   ├─ Paciente recibe servicios (consultas, medicamentos, imágenes, etc.)
   ├─ Cada servicio se registra en su módulo correspondiente:
   │  ├─ Consultas → módulo cardiology, gynecology, etc.
   │  ├─ Medicamentos → módulo pharmacy
   │  ├─ Imágenes → módulo imaging
   │  ├─ Hospitalización → módulo hospitalization
   │  └─ etc.
   ├─ Cada servicio se vincula automáticamente al episodio activo del paciente
   └─ Vínculo: EpisodeService (GenericForeignKey)

3. CIERRE DEL EPISODIO
   ├─ Cuando el paciente termina su atención
   ├─ Se "cierra" el episodio manualmente
   ├─ Se registra diagnóstico de egreso (CIE-10)
   ├─ Se calcula el costo total de todos los servicios
   └─ Estado: CERRADO

4. FACTURACIÓN
   ├─ Desde el episodio cerrado se genera la factura
   ├─ La factura incluye TODOS los servicios del episodio
   ├─ Cada servicio se convierte en un HealthInvoiceItem
   ├─ El HealthInvoiceItem tiene GenericForeignKey al servicio original
   └─ Estado factura: EMITIDA

5. GENERACIÓN DE RIPS
   ├─ Desde la factura emitida se genera el RIPS
   ├─ El RIPS se construye leyendo los servicios vinculados en la factura
   ├─ Se generan archivos JSON/XML según normativa MinSalud
   └─ Archivos RIPS listos para enviar a EPS
```

---

## 🤔 ¿ESTÁ BIEN ESTE FLUJO?

### **POSIBLE PROBLEMA:**

El flujo implementado requiere **crear manualmente un "Episodio de Atención"** antes de dar servicios al paciente. Esto puede ser:

❌ **Redundante** - Si los módulos de consulta ya manejan la recepción del paciente
❌ **Extra trabajo** - El personal debe "abrir episodio" antes de atender
❌ **No realista** - En la práctica, el paciente llega y recibe atención directamente

### **FLUJO ALTERNATIVO (Más Realista):**

```
1. RECEPCIÓN
   ├─ Paciente llega
   └─ Se registra consulta/servicio DIRECTAMENTE en su módulo

2. ATENCIÓN
   ├─ Se dan servicios normalmente
   └─ NO se requiere "abrir episodio" manualmente

3. FACTURACIÓN
   ├─ Al momento de facturar:
   │  ├─ Se seleccionan los servicios del paciente (por fecha, etc.)
   │  ├─ Se crea la factura con esos servicios
   │  └─ Se crea el episodio AUTOMÁTICAMENTE (en background)
   └─ O se factura sin concepto de episodio

4. RIPS
   ├─ Se genera desde la factura
   └─ Lee los servicios de la factura para generar el RIPS
```

---

## 🏗️ ARQUITECTURA TÉCNICA IMPLEMENTADA

### **1. Modelos Clave**

#### **AttentionEpisode**
```python
# Agrupa TODOS los servicios de un paciente desde admisión hasta egreso
- episode_number: EP-2025-000001
- patient: FK → Patient
- payer: FK → ThirdParty (EPS)
- status: active / closed / billed / cancelled
- admission_date: Fecha de ingreso
- discharge_date: Fecha de egreso
- total_cost: Costo total calculado
- invoice: OneToOne → HealthInvoice
```

#### **EpisodeService**
```python
# Vincula CUALQUIER servicio al episodio (GenericForeignKey)
- episode: FK → AttentionEpisode
- service_type: consultation / medication / imaging / hospitalization
- content_type: FK → ContentType (Django)
- object_id: UUID del servicio original
- service_object: GenericForeignKey (apunta al servicio)
- service_cost: Costo del servicio
```

#### **HealthInvoiceItem** (Modificado)
```python
# Item de factura vinculado a servicio original
- invoice: FK → HealthInvoice
- service_type: consultation / procedure / medication / etc.
- service_code: Código CUPS/CUM
- content_type: FK → ContentType (NUEVO)
- object_id: UUID (NUEVO)
- service_object: GenericForeignKey (NUEVO - apunta al servicio original)
```

### **2. Flujo de Datos**

```
SERVICIO ORIGINAL                    EPISODIO                         FACTURA
-----------------                    --------                         -------
Dispensing (Pharmacy)    ─────┐
                              │
ImagingOrder (Imaging)   ─────┤
                              ├──→  EpisodeService  ──→  AttentionEpisode
Consultation (Cardiology)─────┤       (vínculo)              │
                              │                              │
Admission (Hospitalization)───┘                              │
                                                             │
                                                             ▼
                                                      HealthInvoice
                                                             │
                                                             ▼
                                                      HealthInvoiceItem
                                                      (con GenericFK)
                                                             │
                                                             ▼
                                                        RIPS Files
                                                        (JSON/XML)
```

### **3. Generación de RIPS**

**Archivo:** `rips/utils.py`

**Función principal:** `generate_rips_json(invoice)`

**Proceso:**
1. Lee la factura (HealthInvoice)
2. Lee todos los items (HealthInvoiceItem)
3. Por cada item:
   - Lee el servicio original usando `service_object` (GenericFK)
   - Extrae datos según tipo de servicio
   - Clasifica como: Consulta / Procedimiento / Medicamento / Urgencia
4. Genera estructura JSON según Resolución 3374/2000
5. Guarda archivo en `media/rips/<company_id>/`

**Ejemplo de datos extraídos:**
```python
# Para un medicamento
{
    "codPrestador": "860000111",
    "consecutivo": "1",
    "fechaSuministro": "2025-10-15",
    "codigoMedicamento": "19840247",  # Código CUM
    "nombreMedicamento": "ACETAMINOFEN 500 MG",
    "cantidadSuministrada": 20,
    "valorUnitario": 200,
    "valorTotal": 4000
}
```

---

## 🎯 URLs Y VISTAS

### **Dashboard RIPS**
```
URL: /rips/
Vista: rips.views.dashboard
Muestra: Estadísticas, episodios activos, pendientes de facturar, archivos RIPS
```

### **Gestión de Episodios**
```
/rips/episodios/                    → Lista de episodios
/rips/episodios/crear/              → Crear episodio (MANUAL)
/rips/episodios/<id>/               → Detalle del episodio
/rips/episodios/<id>/cerrar/        → Cerrar episodio
/rips/episodios/<id>/facturar/      → Generar factura del episodio
```

### **Generación de RIPS**
```
/rips/generar/                      → Seleccionar factura para generar RIPS
/rips/archivos/                     → Lista de archivos RIPS generados
/rips/descargar/<invoice_id>/       → Descargar RIPS JSON
```

---

## 📊 CATÁLOGOS REQUERIDOS

### **CUPS (Procedimientos)**
```bash
python manage.py load_cups_codes --sample
```
Carga 55 procedimientos comunes:
- Consultas médicas
- Laboratorio clínico
- Imágenes diagnósticas
- Procedimientos quirúrgicos
- Odontología, fisioterapia, etc.

### **CUM (Medicamentos)**
```bash
python manage.py load_cum_codes --sample
```
Carga 60+ medicamentos comunes:
- Analgésicos
- Antibióticos
- Antihipertensivos
- Antidiabéticos, etc.

---

## ❗ PREGUNTA PARA TI (USUARIO)

### **¿Este flujo está bien o hay que cambiarlo?**

#### **OPCIÓN 1: Mantener Episodio Manual (Actual)**
✅ Control explícito de inicio/fin de atención
✅ Agrupa todos los servicios automáticamente
❌ Requiere paso extra al recibir paciente
❌ Puede olvidarse abrir episodio

#### **OPCIÓN 2: Episodio Automático**
✅ No requiere acción manual
✅ Se crea automáticamente al dar primer servicio
✅ Más fluido para el personal
❌ Menos control explícito
❌ Requiere modificar vistas de cada módulo

#### **OPCIÓN 3: Sin Episodios (Más Simple)**
✅ Súper simple
✅ Se factura directamente servicios seleccionados
❌ No hay concepto de "atención completa"
❌ Puede ser más difícil agrupar servicios relacionados

---

## 🔍 ¿QUÉ OPCIÓN PREFIERES?

**Por favor dime:**

1. **¿Está bien el flujo actual con episodios manuales?**
   - Si SÍ → Perfecto, solo hay que cargar los catálogos y probar
   - Si NO → ¿Prefieres Opción 2 (automático) u Opción 3 (sin episodios)?

2. **¿En tu flujo de trabajo real:**
   - ¿El personal abre una "atención" al recibir al paciente?
   - ¿O se va directo a dar el servicio (consulta, medicamento, etc.)?

3. **¿Cómo facturan actualmente?**
   - ¿Por paciente completo (todos sus servicios)?
   - ¿Por servicio individual?
   - ¿Por día/periodo?

**Con tu respuesta puedo ajustar el sistema para que se ajuste exactamente a tu flujo de trabajo real.**

---

## 📝 ESTADO ACTUAL DEL CÓDIGO

✅ **Completado:**
- Modelos RIPS completos
- Vínculo de servicios con GenericForeignKey
- Templates HTML (7 archivos)
- Vistas CRUD para episodios
- Generación de RIPS JSON
- Comandos de carga de catálogos (CUPS/CUM)

⏳ **Pendiente según tu respuesta:**
- Ajustar flujo si es necesario
- Integrar con módulos existentes (consulta, farmacia, etc.)
- Vincular automáticamente servicios a episodios (si decides mantenerlos)

---

## 🚀 PRÓXIMOS PASOS

**Si el flujo está bien:**
1. Cargar catálogos CUPS y CUM
2. Crear algunos terceros marcados como EPS (is_payer=True)
3. Crear un episodio de prueba
4. Simular servicios
5. Cerrar episodio
6. Generar factura
7. Generar RIPS
8. Revisar archivo JSON generado

**Si hay que ajustar:**
1. Me dices qué cambiar
2. Ajusto los modelos/vistas
3. Creamos migraciones
4. Probamos el nuevo flujo

---

## 📞 ESPERO TU FEEDBACK

Dime qué opinas del flujo y cómo prefieres que funcione para ajustarlo a tu operación real.
