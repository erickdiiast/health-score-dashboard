@echo off
chcp 65001 >nul
echo ================================================
echo       ENVIAR ALTERACOES PARA O GITHUB
echo ================================================
echo.

cd /d "%~dp0"

echo Verificando alteracoes...
git status --short

echo.
set /p MENSAGEM="Digite a mensagem do commit: "

if "%MENSAGEM%"=="" set MENSAGEM=Atualizacao

echo.
echo Adicionando arquivos...
git add .

echo.
echo Criando commit...
git commit -m "%MENSAGEM%"

echo.
echo Enviando para o GitHub...
git push origin main

echo.
echo ================================================
echo           ENVIO CONCLUIDO!
echo ================================================
pause
