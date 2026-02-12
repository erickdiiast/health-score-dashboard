# 🎮 Health Score Dashboard v2.8.0

Aplicação web para análise de saúde e engajamento de jogadores com tracking individual ao longo do tempo. Processa dados CSV e gera dashboards com métricas de login, engajamento, compras e histórico de evolução.

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Health%20Score-blue)
![Python](https://img.shields.io/badge/Python-3.14+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)
![Version](https://img.shields.io/badge/Version-2.8.0-orange)

## ✨ Funcionalidades

### 📤 Upload e Processamento
- **Upload de CSV** - Importe dados brutos dos jogadores sem prompt de data (seleção de data no momento de salvar snapshot)
- **Cálculo Automático** - Scores de Login, Engajamento e Compras usando Z-Score
- **Segmentação** - 9 categorias de jogadores com hierarquia clara

### 📊 Dashboard e Análise
- **Visualizações** - Gráficos interativos com Chart.js
- **Clusters** - Segmentação com indicadores de tendência (▲ ▼ ~ *)
- **Resumo Executivo** - Salvar snapshot com data customizada
- **Histórico** - Comparativo de snapshots salvos

### 🛤️ Jornada do Jogador (NOVO v2.8)
- **Busca por PID** - Visualize histórico individual de qualquer jogador
- **Timeline** - Evolução dos scores ao longo de 90 dias
- **Tendências** - Indicadores visuais de alta/baixa/estabilidade
- **Tabela de Evolução** - Valores diários com formatação colorida

### 💾 Gerenciamento
- **Exportação** - Download em CSV ou Excel
- **Snapshots** - Persistência de dados com tracking individual
- **Deleção** - Remover snapshots antigos com cleanup de dados relacionados

## 🚀 Instalação

### Executável (Recomendado)
1. Baixe `HealthScoreDashboard.exe`
2. Execute o arquivo
3. Acesse `http://localhost:8000` no navegador

### Código Fonte
```bash
cd Kimi
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

## ▶️ Como Usar

### Fluxo de Trabalho
1. **Upload CSV** - Faça upload dos dados do dia
2. **Review Dashboard** - Analise os clusters e tendências
3. **Salvar Snapshot** - Clique em "Salvar Dados do Dia" e selecione a data
4. **Verificar Jornada** - Use a aba "Jornada do Jogador" para ver evolução individual

### Formato do CSV de Entrada

| Coluna | Descrição |
|--------|-----------|
| `player_id` | ID único do jogador |
| `days_since_last_login` | Dias desde último login |
| `days_since_last_purchase` | Dias desde última compra |
| `qtd_logins_7d` | Número de logins na última semana |
| `qtd_torneios_7d` | Torneios jogados (7 dias) |
| `qtd_maratonas_7d` | Maratonas jogadas (7 dias) |
| `qtd_missoes_7d` | Missões completadas (7 dias) |
| `qtd_promos_7d` | Promoções participadas (7 dias) |
| `qtd_compras_7d` | Compras realizadas (7 dias) |
| `ticket_medio_7d` | Ticket médio de compras |
| `vlr_apostado_7d` | Valor apostado (7 dias) |
| `vlr_ganho_7d` | Valor ganho (7 dias) |

## 🏷️ Clusters de Saúde

| Cluster | Score | Descrição |
|---------|-------|-----------|
| ⭐ Elite | ≥ 80 | Top performers - alta receita + engajamento |
| 🏆 VIP Ativo | 70-79 | VIPs engajados e comprando |
| 📈 Bom | 60-69 | Bom engajamento e receita |
| 📊 Estável | 50-59 | Engajamento moderado |
| ⚠️ Atenção | 40-49 | Atenção necessária |
| 🚨 Risco Alto | < 40 | Score baixo em ambas métricas |
| 🚨 Risco: Queda Receita | score_compras < 35 | Engajado mas não compra |
| 🚨 Risco: Queda Engajamento | score_engajamento < 35 | Compra mas não engaja |
| 💎 Churn Iminente | < 35 nos dois | Alto risco de churn |

## 🧮 Fórmulas de Cálculo (Z-Score)

### Score de Login
```
Score Login = 100 × exp(-dias_inativo / 7)
```

### Score de Engajamento (Z-Score)
Baseado em atividades: torneios, maratonas, missões, promoções, logins
```
Score = 50 + ((valor - média) / desvio_padrão × 25)
```
Média da base = 50 pontos

### Score de Compras (Z-Score)
Baseado em: qtd_compras_7d e ticket_medio_7d
```
Score = 50 + ((valor - média) / desvio_padrão × 25)
```

### Score Geral
```
Score Geral = Engajamento × 0.4 + Compras × 0.6
```

## 📈 Tendências (Jornada do Jogador)

| Indicador | Significado |
|-----------|-------------|
| ▲ | Tendência de alta (> 5% de melhora) |
| ▼ | Tendência de baixa (> 5% de piora) |
| ~ | Estável (dentro de ±5%) |
| * | Novo (primeira aparição) |

## 🛠️ Tecnologias

- **Backend:** Python 3.14 + FastAPI + Pandas + NumPy
- **Frontend:** Vanilla JavaScript + Chart.js
- **Banco de Dados:** SQLite com tracking individual
- **Empacotamento:** PyInstaller

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página principal |
| POST | `/api/upload` | Upload de CSV |
| GET | `/api/dados` | Dados processados |
| POST | `/api/historico/salvar` | Salvar snapshot |
| GET | `/api/historico` | Listar snapshots |
| DELETE | `/api/historico/{id}` | Deletar snapshot |
| GET | `/api/player/{id}/evolucao` | Evolução individual |
| GET | `/api/export/csv` | Exportar CSV |
| GET | `/api/export/excel` | Exportar Excel |

## 📝 Estrutura do Projeto

```
Kimi/
├── app.py              # Backend FastAPI + lógica de Z-Score
├── build_exe.py        # Script de build PyInstaller
├── requirements.txt    # Dependências Python
├── README.md          # Documentação
├── historico.db       # SQLite com player_snapshots
├── static/
│   ├── style.css      # Estilos CSS (Glassmorphism)
│   └── app.js         # Frontend + Jornada do Jogador
└── templates/
    └── index.html     # Página principal
```

## 🔄 Changelog

### v2.8.0 (12/02/2026)
- **Jornada do Jogador**: Nova aba para tracking individual de jogadores
- **Persistência Aprimorada**: `player_snapshots` salvos ao salvar snapshot
- **Tendências**: Indicadores visuais baseados em histórico de 90 dias
- **Remoção do prompt de data no upload**: Data selecionada ao salvar snapshot
- **Fix timezone**: Formatação de datas sem conversão de timezone
- **Fix duplicados**: Índice UNIQUE em (player_id, data)

### v2.7.0
- Tracking individual de jogadores
- Tabela `player_snapshots` no banco de dados

### v2.6.0
- Sistema de snapshots com data customizada
- Histórico comparativo

### v2.5.0
- Clusters com indicadores de tendência
- Correção de bugs no cálculo de Z-Score

## 📦 Build

Para gerar o executável:
```bash
cd Kimi
python build_exe.py
```

Resultado: `dist/HealthScoreDashboard.exe`

---

**Desenvolvido com 💙 para análise de engajamento de jogadores**
