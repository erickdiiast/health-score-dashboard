# Opções de Deploy Gratuito

## Opção 1: Render.com (Recomendado ⭐)
**Gratuito, fácil e com URL pública**

### Passos:
1. Acesse https://render.com e crie uma conta (gratuita)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório do GitHub
4. Configure:
   - **Name**: health-score-dashboard
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Clique em "Create Web Service"

**Prós:**
- ✅ Gratuito para sempre
- ✅ URL pública (https://seu-app.onrender.com)
- ✅ Banco SQLite persistente
- ✅ Deploy automático ao fazer push no GitHub
- ✅ SSL/HTTPS incluso

**Contras:**
- ⚠️ App "dorme" após 15 min de inatividade (demora ~30s para acordar)
- ⚠️ Limite de 512 MB RAM

---

## Opção 2: PythonAnywhere
**Especializado em Python**

### Passos:
1. Acesse https://www.pythonanywhere.com (conta gratuita)
2. Vá em "Web" → "Add a new web app"
3. Escolha "Manual configuration" → Python 3.10
4. Clone seu repo ou faça upload dos arquivos
5. Configure o WSGI apontando para `app.py`

**Prós:**
- ✅ Sempre ligado (não dorme)
- ✅ Especializado em Python
- ✅ Console Python online

**Contras:**
- ⚠️ Domínio é seu-usuario.pythonanywhere.com
- ⚠️ Limite de CPU/dia
- ⚠️ Interface menos moderna

---

## Opção 3: Railway.app
**Muito fácil, interface moderna**

### Passos:
1. https://railway.app (login com GitHub)
2. "New Project" → "Deploy from GitHub repo"
3. Selecione seu repositório
4. Railway detecta automaticamente (Python)
5. Adicione variável de ambiente `PORT=8080`

**Prós:**
- ✅ Interface muito bonita
- ✅ Deploy automático
- ✅ Banco de dados incluso

**Contras:**
- ⚠️ Plano gratuito tem limite de US$ 5/mês de uso
- ⚠️ Pode acabar os créditos

---

## Opção 4: Ngrok (Temporário)
**Para testes rápidos - só funciona com seu PC ligado**

### Passos:
1. Baixe o ngrok em https://ngrok.com
2. Crie conta gratuita e autentique
3. Inicie seu app local: `python app.py`
4. Em outro terminal: `ngrok http 8080`
5. Copie a URL https que o ngrok fornece

**Prós:**
- ✅ Rápido para testar
- ✅ URL muda a cada vez (ou fixa no plano pago)

**Contras:**
- ❌ PC precisa ficar ligado
- ❌ URL muda a cada execução (no plano gratuito)

---

## Recomendação

Para uso contínuo e compartilhamento com equipe:
👉 **Use o Render.com** (Opção 1)

É o mais simples, gratuito e atende perfeitamente para esse caso.

---

## Configuração para Deploy

Antes de fazer deploy, precisamos ajustar algumas coisas no código:

### 1. Criar `requirements.txt` atualizado:
```
fastapi
uvicorn
pandas
numpy
openpyxl
python-multipart
jinja2
```

### 2. Ajustar `app.py` para usar porta dinâmica:
```python
import os
port = int(os.environ.get("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=port)
```

### 3. Criar `render.yaml` (opcional, facilita):
```yaml
services:
  - type: web
    name: health-score-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

Quer que eu prepare o código para deploy no Render?
