# Guia de Commit - Health Score Dashboard

## Opção 1: Usar o Script Automático

Dê 2 cliques no arquivo `commit.bat`

## Opção 2: Comandos Manuais

Se o script não funcionar, execute no terminal:

```bash
cd "C:\Users\Eric Dias\Downloads\Kimi"

# Configurar usuário (se ainda não configurou)
git config user.name "Seu Nome"
git config user.email "seu-email@exemplo.com"

# Verificar status
git status

# Adicionar arquivos
git add app.py
git add static/app.js
git add static/style.css
git add templates/index.html
git add requirements.txt

# Fazer commit
git commit -m "Health Score Dashboard v2.2 - Analise por regiao, VIP dinamico"

# Verificar log
git log --oneline -5
```

## Opção 3: GitHub Desktop (Mais Fácil)

1. Baixe: https://desktop.github.com
2. Abra o GitHub Desktop
3. File > Add local repository
4. Selecione a pasta `Kimi`
5. Veja as alterações e clique em "Commit to main"

## Status do Projeto

- ✅ Backend completo (FastAPI)
- ✅ Frontend responsivo (HTML/CSS/JS)
- ✅ Análise por região (BR/ES/INT)
- ✅ Análise por nível VIP
- ✅ Parâmetros dinâmicos
- ✅ Exportação CSV/Excel
- ✅ Sistema de abas
