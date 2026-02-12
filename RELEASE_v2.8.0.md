# Health Score Dashboard v2.8.0

## 🚀 Nova Funcionalidade: Jornada do Jogador

### Aba "Jornada do Jogador"
Nova aba superior que permite acompanhar a evolução individual de cada jogador ao longo do tempo.

#### Funcionalidades:
- **Busca por PID**: Digite o Player ID para visualizar histórico completo
- **Período configurável**: Escolha entre 7, 15, 30, 60 ou 90 dias de histórico
- **Dashboard individual** com:
  - Score atual e cluster
  - Número de mudanças de cluster
  - Dias no cluster atual
  - Tendência (crescente/decrescente/estável)
- **Gráfico de evolução**: Visualização temporal dos scores (Geral, Compras, Engajamento)
- **Timeline de clusters**: Histórico visual de movimentação entre clusters
- **Métricas detalhadas**: Estatísticas de compras e engajamento (maior, menor, média, tendência)
- **Tabela de histórico**: Registro diário completo com variações

#### Como usar:
1. Vá para a aba "Jornada do Jogador"
2. Digite o Player ID no campo de busca
3. Selecione o período desejado
4. Clique em "Buscar"

> **Nota**: Para visualizar o histórico, é necessário ter dados salvos no banco (via upload de arquivos anteriores).

---

## 📊 Versão Atual: 2.8.0

### Funcionalidades existentes:
- ✅ Z-Score para cálculo de scores (Compras 70%, Engajamento 30%)
- ✅ Acompanhamento individual de jogadores (player_snapshots)
- ✅ Tags de tendência (↑ ↓ ~ *) nos clusters
- ✅ Filtros por região (BR, ES, INT)
- ✅ Filtros por nível VIP (Ametista a Berilo)
- ✅ Exportação CSV e Excel
- ✅ Histórico de snapshots
- ✅ Resumo executivo

---

## 📁 Arquivos do Projeto

```
Kimi/
├── app.py                  # Backend FastAPI
├── build_exe.py            # Script de build
├── templates/
│   └── index.html          # Interface principal
├── static/
│   ├── style.css           # Estilos
│   └── app.js              # Frontend JavaScript
└── RELEASE_v2.8.0.md       # Este arquivo
```

---

## 🔧 Build do Executável

```bash
cd Kimi
python build_exe.py
```

O executável será gerado em `dist/HealthScoreDashboard.exe`

---

## 📅 Data da Release
05/02/2026 - v2.8.0
