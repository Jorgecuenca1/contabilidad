@echo off
echo ===============================================
echo  REINICIANDO SERVIDOR DJANGO
echo ===============================================
echo.
echo [1/4] Limpiando cache de Python...
del /S /Q __pycache__ >nul 2>&1
del /S /Q *.pyc >nul 2>&1
echo       Cache limpiado!
echo.
echo [2/4] Limpiando cache de Django...
python manage.py shell -c "from django.core.cache import cache; cache.clear()" >nul 2>&1
echo       Cache de Django limpiado!
echo.
echo [3/4] Verificando configuracion...
python manage.py check --deploy
echo.
echo [4/4] Iniciando servidor en http://127.0.0.1:8000/
echo.
echo ===============================================
echo  SERVIDOR INICIADO
echo  Presiona Ctrl+C para detener
echo ===============================================
echo.
python manage.py runserver 8000
