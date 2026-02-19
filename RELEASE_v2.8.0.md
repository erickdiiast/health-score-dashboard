# Health Score Dashboard v2.8.0 - Release Notes

**Data:** 12 de Fevereiro de 2026

---

## 🎯 Principais Novidades

### 🛤️ Jornada do Jogador (Player Journey)
Nova aba dedicada ao tracking individual de jogadores com:
- **Busca por PID** - Encontre qualquer jogador pelo ID
- **Timeline de 90 dias** - Visualize a evolução completa
- **Tendências visuais** - ▲ (alta), ▼ (baixa), ~ (estável), * (novo)
- **Tabela detalhada** - Evolução diária com formatação colorida

### 🔄 Fluxo de Dados Simplificado
**Remoção do prompt de data no upload:**
- Upload de arquivo: apenas processamento em memória
- Salvar snapshot: data selecionada no momento do save
- Player snapshots: salvos automaticamente com a data do snapshot

Isso corrige o problema onde todos os jogadores apareciam como "novos" (*).

### 📊 Tendências Inteligentes
Agora as tendências são calculadas corretamente:
- Compara primeiro e último registro dos últimos 90 dias
- Apenas jogadores com histórico real mostram ▲ ▼ ou ~
- Jogadores com apenas 1 registro mostram * (novo)

### 🐛 Correções de Bugs
- **Timezone fix**: Datas agora são formatadas sem conversão de timezone (evita "dia anterior")
- **Duplicados**: Índice UNIQUE em (player_id, data) evita registros duplicados
- **Deleção**: Contagem correta de registros afetados ao deletar snapshots

---

## 📁 Arquivos

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `HealthScoreDashboard.exe` | Executável standalone | 68.7 MB |
| `HealthScoreDashboard.zip` | Versão zipada | 65.1 MB |

---

## 🚀 Como Usar

### Novo Fluxo de Trabalho:

1. **Inicie o aplicativo**
   ```
   .​\HealthScoreDashboard.exe
   ```

2. **Acesse no navegador**
   ```
   http://localhost:8000
   ```

3. **Faça upload do CSV**
   - Arraste o arquivo ou clique em "Selecionar Arquivo"
   - O processamento é feito em memória (sem salvar ainda)

4. **Analise o dashboard**
   - Verifique os clusters e scores
   - Observe as tendências (▲ ▼ ~ *)

5. **Salve o snapshot**
   - Clique em "💾 Salvar Dados do Dia"
   - Selecione a data desejada
   - Os dados individuais são salvos automaticamente

6. **Verifique a jornada**
   - Vá para a aba "Jornada do Jogador"
   - Busque por um PID
   - Veja a evolução ao longo do tempo

---

## 🧪 Teste Completo

Para verificar se tudo está funcionando:

1. Faça upload de um CSV com dados de hoje
2. Salve o snapshot com a data de hoje
3. Faça upload de um CSV com dados de ontem (simulado)
4. Salve o snapshot com a data de ontem
5. Vá em "Jornada do Jogador" e busque um PID que exista em ambos
6. Verifique se aparecem 2 registros com tendência (▲ ▼ ou ~), não *

---

## 🗄️ Estrutura do Banco de Dados

### Tabela `player_snapshots`
```sql
CREATE TABLE player_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    data DATE NOT NULL,
    score_geral REAL,
    score_engajamento REAL,
    score_compras REAL,
    cluster TEXT,
    qtd_logins_7d INTEGER,
    qtd_compras_7d INTEGER,
    ticket_medio_7d REAL,
    vlr_apostado_7d REAL,
    vlr_ganho_7d REAL,
    FOREIGN KEY (data) REFERENCES historico(data)
);

CREATE UNIQUE INDEX idx_player_data ON player_snapshots(player_id, data);
```

---

## 📊 Cálculos

### Z-Score
```
Score = 50 + ((valor - média) / desvio_padrão × 25)
```

### Clusters
| Cluster | Score | Ícone |
|---------|-------|-------|
| Elite | ≥ 80 | ⭐ |
| VIP Ativo | 70-79 | 🏆 |
| Bom | 60-69 | 📈 |
| Estável | 50-59 | 📊 |
| Atenção | 40-49 | ⚠️ |
| Risco Alto | < 40 | 🚨 |
| Queda Receita | score_compras < 35 | 🚨 |
| Queda Engajamento | score_engajamento < 35 | 🚨 |
| Churn Iminente | < 35 nos dois | 💎 |

---

## 🔗 Links

- **Repositório:** https://github.com/erickdiiast/health-score-dashboard
- **Issues:** https://github.com/erickdiiast/health-score-dashboard/issues

---

**Desenvolvido com 💙 para análise de engajamento de jogadores**
