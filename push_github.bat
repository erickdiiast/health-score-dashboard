@echo off
chcp 65001 >nul
echo ==========================================
echo   Push para GitHub - Health Score Dashboard
echo ==========================================
echo.

cd /d "%~dp0"

REM Configura usuario
git config user.email "erickdiias@gmail.com"
git config user.name "erickdiiast"

echo [1/5] Verificando repositorio...
git status

echo.
echo [2/5] Adicionando arquivos...
git add app.py static/app.js static/style.css templates/index.html requirements.txt README.md COMMIT_CHANGES.md GIT_GUIDE.md

echo.
echo [3/5] Fazendo commit...
git commit -m "Health Score Dashboard v2.2 - Analise por regiao BR/ES/INT, VIP dinamico, peso Compras 70%, Engajamento 30%"

echo.
echo [4/5] Configurando remote...
git remote remove origin 2>nul
git remote add origin https://github.com/erickdiiast/health-score-dashboard.git

echo.
echo [5/5] Enviando para GitHub...
echo.
echo IMPORTANTE: Quando solicitado, use seu Personal Access Token como senha!
echo Crie um token em: https://github.com/settings/tokens
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo Tentando com 'master'...
    git branch -M master
    git push -u origin master
)

echo.
echo ==========================================
echo   Processo concluido!
echo ==========================================
pause
