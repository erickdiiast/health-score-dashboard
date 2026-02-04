@echo off
chcp 65001 >nul
echo ==========================================
echo   Atualizar GitHub - Health Score Dashboard
echo ==========================================
echo.

cd /d "%~dp0"

REM Configura usuario
git config user.email "erickdiias@gmail.com"
git config user.name "erickdiiast"

echo [1/4] Verificando status...
git status

echo.
echo [2/4] Adicionando todas as mudancas...
git add -A

echo.
echo [3/4] Fazendo commit...
git commit -m "v2.2 - Analise por regiao BR/ES/INT, VIP dinamico, peso Compras 70%, Engajamento 30%"

echo.
echo [4/4] Enviando para GitHub...
echo.
echo Quando pedir senha, use seu Personal Access Token!
git push

echo.
echo ==========================================
if errorlevel 1 (
    echo   ERRO ao enviar!
) else (
    echo   SUCESSO! Codigo atualizado no GitHub.
)
echo ==========================================
pause
