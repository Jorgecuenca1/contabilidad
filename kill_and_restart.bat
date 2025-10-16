@echo off
echo ===============================================
echo  MATANDO PROCESOS Y REINICIANDO SERVIDOR
echo ===============================================
echo.

echo [1/3] Matando todos los procesos Python en puerto 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Matando proceso PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo       Procesos eliminados!
echo.

echo [2/3] Esperando 2 segundos...
timeout /t 2 /nobreak >nul
echo       Listo!
echo.

echo [3/3] Iniciando servidor en http://127.0.0.1:8000/
echo.
echo ===============================================
echo  SERVIDOR INICIADO - Presiona Ctrl+C para detener
echo ===============================================
echo.

python manage.py runserver 8000
