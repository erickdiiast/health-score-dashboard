@echo off
cd /d "%~dp0"
echo ==========================================
echo   Enviando para o GitHub (sem Git)
echo ==========================================
echo.
python upload_github.py
