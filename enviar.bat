@echo off
chcp 65001 >nul
echo ================================================
echo       ENVIAR PARA O GITHUB
echo ================================================
echo.

cd /d "%~dp0"

echo Verificando alteracoes...
git status --short

echo.
set /p BUILD="Deseja compilar o executavel tambem? (s/n): "

if /i "%BUILD%"=="s" (
    echo.
    echo ================================================
    echo    COMPILANDO EXECUTAVEL...
    echo ================================================
    echo.
    
    echo Limpando build anterior...
    if exist "build" rmdir /s /q "build"
    if exist "dist\HealthScoreDashboard" rmdir /s /q "dist\HealthScoreDashboard"
    if exist "dist\HealthScoreDashboard.exe" del /f /q "dist\HealthScoreDashboard.exe"
    if exist "dist\HealthScoreDashboard.zip" del /f /q "dist\HealthScoreDashboard.zip"
    
    echo Compilando...
    pip install -q pyinstaller
    pyinstaller build.spec --clean
    
    echo.
    echo Criando ZIP...
    cd dist
    powershell Compress-Archive -Path "HealthScoreDashboard" -DestinationPath "HealthScoreDashboard.zip" -Force
    cd ..
    
    echo.
    echo Executavel atualizado!
)

echo.
set /p MENSAGEM="Mensagem do commit: "
if "%MENSAGEM%"=="" set MENSAGEM=Atualizacao

echo.
echo Adicionando arquivos ao git...
git add .

echo Criando commit...
git commit -m "%MENSAGEM%"

echo Enviando para o GitHub...
git push origin main

echo.
echo ================================================
echo           ENVIO CONCLUIDO!
echo ================================================
pause
