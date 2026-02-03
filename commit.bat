@echo off
chcp 65001 >nul
echo ==========================================
echo   Fazendo Commit - Health Score Dashboard
echo ==========================================
echo.

cd /d "%~dp0"

REM Verifica se git está disponível
git --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Git nao encontrado!
    echo Instale o Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Configura usuario se necessario
echo Verificando configuracao do Git...
git config user.name >nul 2>&1
if errorlevel 1 (
    echo.
    set /p GIT_NAME="Digite seu nome para o Git: "
    git config user.name "%GIT_NAME%"
)

git config user.email >nul 2>&1
if errorlevel 1 (
    echo.
    set /p GIT_EMAIL="Digite seu email para o Git: "
    git config user.email "%GIT_EMAIL%"
)

echo.
echo [1/4] Adicionando arquivos...
git add app.py
git add static/app.js
git add static/style.css
git add templates/index.html
git add requirements.txt
git add README.md 2>nul
git add *.bat 2>nul

echo.
echo [2/4] Status dos arquivos:
git status --short

echo.
echo [3/4] Fazendo commit...
git commit -m "Health Score Dashboard v2.2 - Analise por regiao (BR/ES/INT), VIP dinamico, peso Compras 70%%, Engajamento 30%%"

echo.
echo [4/4] Verificando log...
git log --oneline -3

echo.
echo ==========================================
echo   Commit realizado com sucesso!
echo ==========================================
echo.
pause
