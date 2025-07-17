@echo off
REM --- Script para activar un entorno virtual, instalar dependencias y ejecutar migraciones en un proyecto existente ---
TITLE Asistente de Proyecto Django

REM --- Verifica si estamos en la carpeta raiz de un proyecto de Django ---
echo Verificando si 'manage.py' existe en el directorio actual...
if not exist manage.py (
    echo.
    echo [ERROR] El archivo 'manage.py' no se encuentra.
    echo Por favor, ejecuta este script desde la carpeta raiz de tu proyecto Django.
    echo.
    pause
    exit /b
)
echo Proyecto de Django detectado.

REM --- Verifica si Python esta instalado y en el PATH ---
echo Verificando la instalacion de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python no se encuentra en el PATH.
    echo Por favor, instala Python desde python.org y asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b
)
echo Python encontrado!

REM --- Nombre del directorio para el entorno virtual ---
set VENV_DIR=venv

REM --- Verifica si el directorio del entorno virtual ya existe ---
if exist %VENV_DIR% (
    echo.
    echo El entorno virtual '%VENV_DIR%' ya existe. Saltando la creacion.
) else (
    echo.
    echo Creando el entorno virtual en la carpeta '%VENV_DIR%'...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] No se pudo crear el entorno virtual.
        echo.
        pause
        exit /b
    )
    echo Entorno virtual creado con exito.
)

REM --- Instala las dependencias ---
echo.
echo Instalando dependencias...
if exist requirements.txt (
    echo Se encontro 'requirements.txt'. Instalando paquetes...
    call %VENV_DIR%\Scripts\pip.exe install -r requirements.txt >nul
) else (
    echo No se encontro 'requirements.txt'. Instalando solo Django...
    call %VENV_DIR%\Scripts\pip.exe install django >nul
)
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudieron instalar las dependencias.
    echo Verifica tu conexion a internet y el archivo 'requirements.txt' si existe.
    echo.
    pause
    exit /b
)
echo Dependencias instaladas con exito!

REM --- Ejecuta las migraciones ---
echo.
echo Ejecutando migraciones de la base de datos...
call %VENV_DIR%\Scripts\python.exe manage.py makemigrations
call %VENV_DIR%\Scripts\python.exe manage.py migrate
echo.
echo Migraciones finalizadas.

echo.
echo -----------------------------------------------------------------
echo.
echo  ENTORNO LISTO
echo.
echo  Se abrira una nueva ventana de comandos con el entorno virtual
echo  activado y dentro de tu proyecto.
echo.
echo  En esa nueva ventana, puedes iniciar el servidor de desarrollo con:
echo  python manage.py runserver
echo.
echo -----------------------------------------------------------------
pause

REM --- Inicia una nueva ventana de comandos con el entorno activado ---
start "Consola de Django" cmd /k "%VENV_DIR%\Scripts\activate.bat"

exit
