@echo off
chcp 65001 >nul
echo ==========================================
echo   Health Score Dashboard - GitHub Uploader
echo ==========================================
echo.

set /p GITHUB_USER="Digite seu usuário do GitHub: "
set /p REPO_NAME="Digite o nome do repositório (ex: health-score-dashboard): "

cd /d "%~dp0"

echo.
echo [1/6] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Git não encontrado!
    echo Baixe em: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo OK: Git encontrado

echo.
echo [2/6] Inicializando repositório...
git init

echo.
echo [3/6] Configurando gitignore...
if not exist ".gitignore" (
    echo __pycache__ > .gitignore
    echo *.pyc >> .gitignore
    echo *.pyo >> .gitignore
    echo *.pyd >> .gitignore
    echo .Python >> .gitignore
    echo *.so >> .gitignore
    echo .env >> .gitignore
    echo .venv >> .gitignore
    echo venv/ >> .gitignore
    echo .idea/ >> .gitignore
    echo .vscode/ >> .gitignore
    echo *.xlsx >> .gitignore
    echo *.csv >> .gitignore
    echo test_*.py >> .gitignore
)

echo.
echo [4/6] Adicionando arquivos...
git add .

echo.
echo [5/6] Fazendo commit...
git commit -m "Primeira versão do Health Score Dashboard v2.1"

echo.
echo [6/6] Conectando ao GitHub...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo.
echo ==========================================
echo Enviando para o GitHub...
echo ==========================================
echo.
echo Se pedir senha, use um Personal Access Token:
echo https://github.com/settings/tokens
echo.

git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ERRO: Não foi possível enviar.
    echo Tentando com 'master' em vez de 'main'...
    git branch -M master
    git push -u origin master
)

echo.
echo ==========================================
if errorlevel 1 (
    echo FALHOU - Verifique o erro acima
) else (
    echo SUCESSO! 
    echo Seu código está em: https://github.com/%GITHUB_USER%/%REPO_NAME%
)
echo ==========================================
pause
