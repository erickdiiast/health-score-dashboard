@echo off
chcp 65001 >nul
echo ==========================================
echo   Configurar GitHub - Health Score Dashboard
echo ==========================================
echo.

cd /d "%~dp0"

REM Configura usuario
git config user.email "erickdiias@gmail.com"
git config user.name "erickdiiast"

echo Configuracao Git:
echo   Email: erickdiias@gmail.com
echo   Nome: erickdiiast
echo.

REM Verifica se ja tem repositorio
if exist .git (
    echo Repostorio Git ja existe!
    echo.
    echo Deseja enviar para GitHub? (S/N)
    set /p CONFIRMAR=
    if /I "%CONFIRMAR%"=="S" goto :enviar
    exit /b
)

:criar
REM Inicializa repositorio
echo [1/4] Inicializando repositorio...
git init

echo.
echo [2/4] Adicionando arquivos...
git add app.py static/app.js static/style.css templates/index.html requirements.txt README.md COMMIT_CHANGES.md GIT_GUIDE.md 2>nul
git add *.md *.txt *.py 2>nul

echo.
echo [3/4] Fazendo commit...
git commit -m "Health Score Dashboard v2.2 - Analise por regiao BR/ES/INT, VIP dinamico, peso Compras 70%, Engajamento 30%"

echo.
echo [4/4] Preparando para GitHub...
:enviar

set REPO_URL=https://github.com/erickdiiast/health-score-dashboard.git

echo.
echo ==========================================
echo   ATENCAO - Instrucoes importantes:
echo ==========================================
echo.
echo 1. Crie o repositorio no GitHub primeiro:
echo    https://github.com/new
echo.
echo 2. Nome do repositorio: health-score-dashboard
echo.
echo 3. DEIXE desmarcado:
echo    [ ] Add a README
echo    [ ] Add .gitignore
echo    [ ] Choose a license
echo.
echo 4. Clique em "Create repository"
echo.
echo 5. Volte aqui e pressione qualquer tecla para continuar
echo.
pause

echo.
echo Configurando remote...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo Verificando branch...
git branch

echo.
echo Enviando para GitHub...
echo.
echo IMPORTANTE: Quando pedir senha, use um Personal Access Token!
echo Crie em: https://github.com/settings/tokens
echo.
echo Pressione qualquer tecla para continuar...
pause >nul

git push -u origin main 2>nul
if errorlevel 1 (
    echo Tentando com branch 'master'...
    git branch -M master
    git push -u origin master
)

echo.
echo ==========================================
if errorlevel 1 (
    echo   ERRO ao enviar!
    echo   Verifique se o repositorio existe no GitHub
    echo   e se voce usou o token correto.
) else (
    echo   SUCESSO!
    echo   Seu codigo esta em: %REPO_URL%
)
echo ==========================================
pause
