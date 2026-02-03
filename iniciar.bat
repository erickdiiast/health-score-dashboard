@echo off
echo ==========================================
echo   Health Score Dashboard - Instalador
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python primeiro em python.org
    pause
    exit /b 1
)
echo OK: Python encontrado

echo.
echo [2/3] Instalando dependencias...
python -m pip install --user fastapi uvicorn pandas numpy openpyxl python-multipart
if errorlevel 1 (
    echo Tentando instalacao alternativa...
    python -m ensurepip --default-pip
    python -m pip install --user fastapi uvicorn pandas numpy openpyxl python-multipart
)

echo.
echo [3/3] Iniciando o servidor...
echo.
echo Acesse no navegador: http://localhost:8000
echo Pressione CTRL+C para parar
echo.
pause

python app.py