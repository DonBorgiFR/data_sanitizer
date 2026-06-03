@echo off
:: Desactiva la salida de comandos para hacer el proceso más limpio
title Lanzador de DataSanitizer

echo ====================================================================
echo             INICIANDO DATA SANITIZER ERP ENGINE (V4.0.0)
echo ====================================================================
echo.

:: 1. Detectar Python 3.10+ de forma ordenada
echo [>] Buscando Python 3.10+ en el sistema...

:: Probar py -3.10
py -3.10 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py -3.10
    goto python_found
)

:: Probar py
py -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    goto python_found
)

:: Probar python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    goto python_found
)

:: Si ninguno funciona, reportar error y salir
echo [ERROR] No se encontro ninguna instalacion valida de Python 3.10 o superior.
echo Por favor, asegurese de tener instalado Python 3.10+ y que este agregado al PATH.
echo.
pause
exit /b 1

:python_found
echo [>] Se detecto un interprete de Python valido: "%PYTHON_CMD%"
echo.

:: 2. Verificar o crear el entorno virtual (.venv)
if not exist .venv (
    echo [>] No se encontro el entorno virtual .venv. Creando uno nuevo...
    %PYTHON_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        echo Asegurese de tener permisos de escritura en este directorio.
        echo.
        pause
        exit /b 1
    )
    echo [>] Entorno virtual .venv creado con exito.
    set RUN_INSTALL=1
) else (
    set RUN_INSTALL=0
)

:: 3. Activar el entorno virtual
echo [>] Activando entorno virtual (.venv)...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual en '.venv\Scripts\activate.bat'.
    echo.
    pause
    exit /b 1
)

:: 4. Comprobar presencia de dependencias criticas
if "%RUN_INSTALL%"=="0" (
    echo [>] Verificando dependencias instaladas: streamlit, pandas, openpyxl...
    python -c "import streamlit, pandas, openpyxl" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [>] Faltan dependencias criticas en el entorno. Se procedera con la instalacion.
        set RUN_INSTALL=1
    )
)

:: 5. Actualizar pip e instalar dependencias si es necesario
if "%RUN_INSTALL%"=="1" (
    echo [>] Actualizando gestor de paquetes pip...
    python -m pip install --upgrade pip
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] No se pudo actualizar pip.
        echo.
        pause
        exit /b 1
    )
    echo [>] Instalando requerimientos desde requirements.txt...
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Error al instalar las dependencias de requirements.txt.
        echo.
        pause
        exit /b 1
    )
    echo [>] Instalacion de dependencias completada con exito.
    echo.
) else (
    echo [>] Dependencias verificadas con exito. Iniciando...
    echo.
)

:: 6. Lanzar Streamlit
echo ====================================================================
echo [>] Iniciando el servidor local de la aplicacion grafica...
echo [>] Esto abrira automaticamente una ventana en tu navegador...
echo.
echo (Puedes cerrar esta ventana de consola cuando termines de usar la app)
echo ====================================================================
echo.

python -m streamlit run app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar la aplicacion.
    echo.
    pause
)
