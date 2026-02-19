@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Health Score Dashboard v2.8.0
echo ========================================
echo.
echo Iniciando servidor...
echo Aguarde...
echo.

start "" http://localhost:8080

HealthScoreDashboard.exe

echo.
echo Servidor encerrado.
pause
