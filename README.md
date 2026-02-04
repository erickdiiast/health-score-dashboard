# 🎮 Health Score Dashboard

Aplicação web para análise de saúde e engajamento de jogadores. Processa dados CSV e gera dashboards com métricas de login, engajamento e compras.

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Health%20Score-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)

## ✨ Funcionalidades

- 📤 **Upload de CSV** - Importe dados brutos dos jogadores
- 🧮 **Cálculo Automático** - Scores de Login, Engajamento e Compras
- 🏷️ **Segmentação** - Categoriza jogadores: Elite, Muito Bom, Estável, Baixo, Risco
- 📊 **Visualizações** - Gráficos interativos com Chart.js
- 👑 **Top Players** - Ranking dos melhores jogadores
- ⚠️ **Alertas** - Identifica jogadores em risco
- 💾 **Exportação** - Download em CSV ou Excel

## 🚀 Instalação

1. **Clone ou acesse o projeto:**
```bash
cd Kimi
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

## ▶️ Como Usar

### Iniciar o servidor:
```bash
python app.py
```

Ou com uvicorn diretamente:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Acessar a aplicação:
Abra o navegador em: `http://localhost:8000`

## 📁 Formato do CSV de Entrada

O arquivo CSV deve conter colunas com dados dos jogadores. Colunas recomendadas:

| Coluna | Descrição |
|--------|-----------|
| `player_id` | ID único do jogador |
| `ultimo_login` | Data do último login (YYYY-MM-DD) |
| `logins_7d` | Número de logins nos últimos 7 dias |
| `tempo_jogo_min` | Tempo de jogo em minutos |
| `nivel` | Nível atual do jogador |
| `partidas_7d` | Partidas jogadas nos últimos 7 dias |
| `valor_gasto_total` | Valor total gasto em compras |
| `num_compras` | Número de compras realizadas |
| `dias_ultima_compra` | Dias desde a última compra |

### Exemplo de CSV:
```csv
player_id,ultimo_login,logins_7d,tempo_jogo_min,nivel,partidas_7d,valor_gasto_total,num_compras,dias_ultima_compra
PLAYER_0001,2026-01-28,5,120,25,15,150.00,3,5
PLAYER_0002,2026-01-30,3,45,10,8,0.00,0,30
```

## 📊 Categorias de Saúde

| Categoria | Score | Descrição |
|-----------|-------|-----------|
| 🏆 **Elite** | ≥ 80 | Jogadores altamente engajados e compradores |
| ✅ **Muito Bom** | 65-79 | Boa saúde geral |
| 📊 **Estável** | 50-64 | Engajamento moderado |
| ⚠️ **Baixo** | 35-49 | Atenção necessária |
| 🚨 **Risco - Queda em Receita** | < 35 | score_compras < score_engajamento |
| 🚨 **Risco - Queda em Engajamento** | < 35 | score_engajamento ≤ score_compras |

## 🧮 Fórmulas de Cálculo

### Score de Login (30%)
```
Score Login = 100 × exp(-dias_inativo / 7)
```

### Score de Engajamento (30%)
```
Score Engajamento = média(
  tempo_jogo / 60 min,
  nível / 50,
  partidas_7d / 20
)
```

### Score de Compras (30%)
```
Score Compras = média(
  valor_gasto / 100,
  num_compras / 5,
  100 × exp(-dias_ultima_compra / 30)
)
```

### Score Geral
```
Score Geral = Engajamento × 0.3 + Compras × 0.7
```

## 🛠️ Tecnologias

- **Backend:** Python + FastAPI
- **Frontend:** HTML5 + CSS3 + JavaScript
- **Visualização:** Chart.js
- **Processamento:** Pandas + NumPy
- **Estilização:** CSS Moderno (Glassmorphism)

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página principal |
| POST | `/api/upload` | Upload de CSV |
| GET | `/api/dados` | Dados processados |
| GET | `/api/sample` | Gerar dados de exemplo |
| GET | `/api/export/csv` | Exportar CSV |
| GET | `/api/export/excel` | Exportar Excel |

## 📝 Estrutura do Projeto

```
Kimi/
├── app.py              # Backend FastAPI
├── requirements.txt    # Dependências Python
├── README.md          # Documentação
├── static/
│   ├── style.css      # Estilos CSS
│   └── app.js         # Frontend JavaScript
└── templates/
    └── index.html     # Página principal
```

## 🎯 Próximos Passos

- [ ] Autenticação de usuários
- [ ] Histórico de processamentos
- [ ] Comparação de períodos
- [ ] Alertas automáticos por email
- [ ] API para integração com CRM

---

**Desenvolvido com 💙 para análise de engajamento de jogadores**
