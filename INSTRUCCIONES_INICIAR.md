# 🚀 INSTRUCCIONES PARA INICIAR EL SERVIDOR

## ⚡ INICIO RÁPIDO

### Opción 1: Usando el script automático (RECOMENDADO)

Simplemente haz doble clic en:
```
reiniciar_servidor.bat
```

O ejecútalo desde la terminal:
```bash
reiniciar_servidor.bat
```

### Opción 2: Comando manual

```bash
python manage.py runserver 8000
```

---

## 📍 ACCESO AL SISTEMA

Una vez que el servidor esté corriendo, accede a:

```
http://127.0.0.1:8000/
```

**Credenciales:**
- Usuario: `admin`
- Contraseña: `admin`

---

## 🏥 VER LOS MÓDULOS DE SALUD

1. **Inicia sesión** con las credenciales de arriba

2. **Selecciona la empresa:**
   - En el selector de empresas, elige: **"Hospital Nivel 4 Demo"**

3. **Verás en el dashboard:**
   - Sección: **"Módulos del Sector Salud"**
   - Contador: **(25 activos)**
   - 25 tarjetas de módulos incluyendo:
     * 🩸 Banco de Sangre
     * 🏥 Urgencias
     * 🔬 Laboratorio Clínico
     * 📋 Diagnósticos CIE-10
     * Y 21 módulos más...

---

## ⚙️ CONFIGURAR MÓDULOS

Si quieres activar/desactivar módulos:

1. Click en el botón **"Configurar Módulos"** (esquina superior derecha del dashboard)

2. Verás todos los módulos organizados por categoría

3. Usa los **toggles** para activar/desactivar

4. Los módulos desactivados **NO aparecerán** en el dashboard

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### El servidor no inicia

```bash
# Mata todos los procesos Python
taskkill /F /IM python.exe

# Espera 3 segundos

# Inicia de nuevo
python manage.py runserver 8000
```

### Error de template o cache

```bash
# Limpia el cache
del /S /Q __pycache__
del /S /Q *.pyc

# Reinicia el servidor
reiniciar_servidor.bat
```

### Puerto 8000 ocupado

```bash
# Usa otro puerto
python manage.py runserver 8001
```

Luego accede a: `http://127.0.0.1:8001/`

---

## 📊 VERIFICAR MÓDULOS DE SALUD

Para ver un resumen de todos los módulos:

```bash
python verify_health_modules.py
```

Esto mostrará:
- Total de módulos registrados
- Módulos activos por empresa
- Lista completa de módulos

---

## 📚 DOCUMENTACIÓN

- **HEALTH_MODULES_STATUS.md** - Estado completo de módulos
- **CAMBIOS_DASHBOARD_SALUD.md** - Detalles técnicos de implementación

---

## ✅ CHECKLIST DE VERIFICACIÓN

Cuando accedas al sistema, deberías ver:

- [ ] Página de login funciona
- [ ] Puedes iniciar sesión con admin/admin
- [ ] Aparece selector de empresas
- [ ] Puedes seleccionar "Hospital Nivel 4 Demo"
- [ ] El dashboard carga correctamente
- [ ] Aparece la sección "Módulos del Sector Salud"
- [ ] Ves **(25 activos)** en el contador
- [ ] Ves tarjetas de módulos con iconos
- [ ] Ves el módulo "Banco de Sangre" con icono 🩸
- [ ] Puedes hacer click en "Configurar Módulos"

---

## 🆘 SOPORTE

Si algo no funciona:

1. Verifica que estás en el directorio correcto:
   ```bash
   dir manage.py
   ```

2. Verifica que Python está instalado:
   ```bash
   python --version
   ```

3. Verifica que Django está instalado:
   ```bash
   python -c "import django; print(django.get_version())"
   ```

---

**¡Todo está listo para usar! Solo ejecuta `reiniciar_servidor.bat` y accede a http://127.0.0.1:8000/** 🎉
