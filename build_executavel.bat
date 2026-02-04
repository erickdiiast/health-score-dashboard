@echo off
chcp 65001 >nul
echo ================================================
echo      BUILD DO EXECUTAVEL
echo ================================================
echo.

cd /d "%~dp0"

echo Limpando build anterior...
if exist "build" rmdir /s /q "build"
if exist "dist\HealthScoreDashboard" rmdir /s /q "dist\HealthScoreDashboard"
if exist "dist\HealthScoreDashboard.exe" del /f /q "dist\HealthScoreDashboard.exe"
if exist "dist\HealthScoreDashboard.zip" del /f /q "dist\HealthScoreDashboard.zip"

echo.
echo Instalando PyInstaller (se necessario)...
pip install -q pyinstaller

echo.
echo Compilando executavel...
pyinstaller build.spec --clean

echo.
echo Criando ZIP do executavel...
cd dist
powershell Compress-Archive -Path "HealthScoreDashboard" -DestinationPath "HealthScoreDashboard.zip" -Force
cd ..

echo.
echo ================================================
echo    BUILD CONCLUIDO!
echo ================================================
echo.
echo Executavel: dist\HealthScoreDashboard.exe
echo ZIP: dist\HealthScoreDashboard.zip
echo.
pause
