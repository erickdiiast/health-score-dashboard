# Deploy no PythonAnywhere - Guia Completo

## ✅ Por que PythonAnywhere?
- **Sempre ligado** (não dorme igual ao Render)
- **Especializado em Python**
- **Console Python online** (pode rodar scripts direto)
- **Banco de dados MySQL gratuito** (opcional)

---

## 📋 Passo a Passo

### ETAPA 1: Criar Conta

1. Acesse: **https://www.pythonanywhere.com**
2. Clique em **"Start running Python online in less than a minute"**
3. Preencha:
   - Username: `seu-nome` (será seu domínio: `seu-nome.pythonanywhere.com`)
   - Email
   - Senha
4. Clique **"Create account"**
5. Confirme seu email

---

### ETAPA 2: Iniciar Console Bash

1. Faça login no PythonAnywhere
2. No dashboard, clique em **"Bash"** (logo abaixo de "Start a new console")
3. Escolha **"Bash"** (não Python 3.10)

Você verá um terminal. Execute os comandos abaixo:

---

### ETAPA 3: Clonar o Repositório

No terminal Bash, execute:

```bash
# Vá para a pasta home
cd ~

# Clone seu repositório
git clone https://github.com/erickdiiast/health-score-dashboard.git

# Entre na pasta
cd health-score-dashboard

# Verifique os arquivos
ls -la
```

---

### ETAPA 4: Criar Virtual Environment

```bash
# Crie um ambiente virtual chamado "venv"
python3.10 -m venv venv

# Ative o ambiente
source venv/bin/activate

# Você verá (venv) no início da linha
```

---

### ETAPA 5: Instalar Dependências

```bash
# Certifique-se que está na pasta do projeto e com venv ativado
cd ~/health-score-dashboard
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Instale também o asgiref (necessário para FastAPI)
pip install asgiref
```

---

### ETAPA 6: Criar Arquivo WSGI

O PythonAnywhere precisa de um arquivo especial para rodar FastAPI.

1. No dashboard, clique em **"Files"** (menu superior)
2. Clique em **"Open another file..."**
3. Digite: `/var/www/seu-nome_pythonanywhere_com_wsgi.py`
   (troque `seu-nome` pelo seu username)

4. Cole este conteúdo:

```python
import sys
import os

# Adiciona o caminho do projeto
path = '/home/seu-nome/health-score-dashboard'
if path not in sys.path:
    sys.path.insert(0, path)

# Ativa o virtual environment
activate_this = '/home/seu-nome/health-score-dashboard/venv/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

# Importa o app FastAPI
from app import app as application
```

**IMPORTANTE:** Troque `seu-nome` pelo seu username do PythonAnywhere em 3 lugares no código acima!

5. Clique **"Save"**

---

### ETAPA 7: Configurar Web App

1. Volte ao **Dashboard** (clique no logo PythonAnywhere)
2. Clique em **"Web"** (menu superior)
3. Clique em **"Add a new web app"**
4. Selecione **"Manual configuration"**
5. Selecione **"Python 3.10"**
6. Clique **"Next"**

---

### ETAPA 8: Configurar Caminhos

Na página de configuração do web app:

#### Source code:
```
/home/seu-nome/health-score-dashboard
```

#### Working directory:
```
/home/seu-nome/health-score-dashboard
```

#### WSGI configuration file:
```
/var/www/seu-nome_pythonanywhere_com_wsgi.py
```

#### Virtualenv:
```
/home/seu-nome/health-score-dashboard/venv
```

(Troque `seu-nome` pelo seu username)

---

### ETAPA 9: Configurar Static Files

Ainda na página do web app, role até **"Static files"**:

Clique em **"Enter URL"** e **"Enter path"**:

- **URL:** `/static`
- **Directory:** `/home/seu-nome/health-score-dashboard/static`

Clique **"Add"**

Adicione outro para templates (se necessário):
- **URL:** `/templates`
- **Directory:** `/home/seu-nome/health-score-dashboard/templates`

---

### ETAPA 10: Ajustar app.py para PythonAnywhere

Precisamos garantir que o app use os caminhos corretos.

1. No dashboard, clique em **"Files"**
2. Navegue até: `health-score-dashboard/app.py`
3. Procure por onde define o caminho do banco de dados

Adicione no início do arquivo (depois dos imports):

```python
import os

# Detecta se está no PythonAnywhere
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ

# Ajusta caminhos se necessário
if IS_PYTHONANYWHERE:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "historico.db")
else:
    DB_PATH = "historico.db"
```

---

### ETAPA 11: Recarregar o App

1. Volte para **"Web"** no menu superior
2. Clique no nome do seu app
3. Role até o topo
4. Clique no botão grande verde **"Reload"**

---

### ETAPA 12: Acessar seu App

Seu app estará em:
```
https://seu-nome.pythonanywhere.com
```

Clique no link que aparece na página do web app!

---

## 🔧 Comandos Úteis

### Para atualizar o código (após fazer push no GitHub):

```bash
# No console Bash
cd ~/health-score-dashboard
git pull
source venv/bin/activate
pip install -r requirements.txt  # se mudou dependências

# Depois vá em Web > Reload
```

### Para ver logs de erro:

1. Vá em **"Web"** no menu
2. Clique no nome do seu app
3. Procure pelos links:
   - **"Error log"** - erros da aplicação
   - **"Access log"** - acessos
   - **"Server log"** - logs do servidor

### Para reiniciar tudo:

```bash
# No console Bash
pkill -f uvicorn
# Depois vá em Web > Reload
```

---

## ⚠️ Limitações do Plano Gratuito

| Recurso | Limite |
|---------|--------|
| CPU | 100 segundos/dia |
| Disco | 512 MB |
| Banco MySQL | Sim, gratuito |
| Domínio | `seu-nome.pythonanywhere.com` |
| HTTPS | ✅ Sim |

---

## 🐛 Problemas Comuns

### "ModuleNotFoundError"
```bash
# Certifique-se de ativar o venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"
```bash
# Verifique permissões
chmod -R 755 ~/health-score-dashboard
```

### "Address already in use"
```bash
# Mate processos antigos
pkill -f uvicorn
pkill -f python
```

### Arquivos estáticos não carregam
- Verifique se configurou a URL `/static` corretamente
- Verifique se o caminho está correto

---

## ✅ Checklist Final

Antes de usar, verifique:
- [ ] Conta criada e email confirmado
- [ ] Repositório clonado
- [ ] Virtual environment criado e ativado
- [ ] Dependências instaladas
- [ ] Arquivo WSGI criado com caminhos corretos
- [ ] Web app configurada (source, working dir, WSGI, virtualenv)
- [ ] Static files configurados
- [ ] App recarregado (botão Reload verde)
- [ ] Acessou a URL e funcionou!

---

## 📝 Script de Instalação Automática

Cole isso no console Bash (troque SEU-NOME pelo seu username):

```bash
#!/bin/bash
NOME="SEU-NOME"

cd ~
git clone https://github.com/erickdiiast/health-score-dashboard.git
cd health-score-dashboard
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install asgiref

echo "✅ Instalação completa!"
echo "Agora configure o Web App no dashboard"
```

---

Precisa de ajuda com algum passo específico? 🚀
