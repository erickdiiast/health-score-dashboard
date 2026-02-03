# Guia para Publicar no GitHub

## Opção 1: Criar Novo Repositório

### 1. Crie um repositório no GitHub
- Acesse: https://github.com/new
- Nome: `health-score-dashboard`
- Descrição: `Dashboard de Health Score para análise de engajamento de jogadores`
- Deixe público ou privado conforme preferir
- NÃO inicialize com README (já temos um)

### 2. Execute estes comandos no terminal:

```bash
cd "C:\Users\Eric Dias\Downloads\Kimi"

# Inicializa o git
git init

# Configura seu usuário (se ainda não configurou)
git config user.email "seu-email@exemplo.com"
git config user.name "Seu Nome"

# Adiciona todos os arquivos
git add .

# Faz o commit
git commit -m "Primeira versão do Health Score Dashboard"

# Conecta ao GitHub (substitua SEU_USUARIO pelo seu usuário do GitHub)
git remote add origin https://github.com/SEU_USUARIO/health-score-dashboard.git

# Envia para o GitHub
git push -u origin main
```

---

## Opção 2: Usar Repositório Existente

Se você já tem um repositório:

```bash
cd "C:\Users\Eric Dias\Downloads\Kimi"
git init
git add .
git commit -m "Adicionando Health Score Dashboard"
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git
git push -u origin main
```

---

## Resolvendo Problemas Comuns

### Erro: "git não é reconhecido"
Baixe e instale o Git: https://git-scm.com/download/win

### Erro: "main ou master?"
Se o comando der erro com "main", tente:
```bash
git branch -m master
git push -u origin master
```

### Erro de autenticação:
Ao executar `git push`, o Git pode pedir:
- Username: seu usuário do GitHub
- Password: use um **Personal Access Token** (não a senha normal)

Para criar um token: https://github.com/settings/tokens → Generate new token

---

## Arquivos que serão enviados:

```
Kimi/
├── app.py              # Backend FastAPI
├── requirements.txt    # Dependências Python
├── README.md          # Documentação
├── README_GITHUB.md   # Este arquivo
├── static/
│   ├── style.css      # Estilos
│   └── app.js         # Frontend
└── templates/
    └── index.html     # Página principal
```
