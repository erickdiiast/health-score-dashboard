# Análise da Pontuação Atual

## 📊 Estrutura Atual

### Composição do Score Geral
- **Engajamento: 30%**
- **Compras: 70%**

### Componentes do Score de Compras (70%)
- Quantidade de compras (7 dias)
- Ticket médio (7 dias)  
- Recência da última compra

**Problema:** Todos têm o MESMO PESO (média simples)

### Componentes do Score de Engajamento (30%)
- Nível VIP
- Torneios (3 dias)
- Maratonas (3 dias)
- Missões (3 dias)
- Promoções (3 dias)

---

## ❌ Problemas Identificados

### 1. **Peso Igual para Compras e Ticket**
```
Jogador A: 10 compras × R$ 10 = R$ 100 total
Jogador B: 2 compras × R$ 50 = R$ 100 total

Pontuação atual: A = B (injusto!)
```

### 2. **Sem Segmentação por VIP**
- Um VIP 5 com pouca atividade pontua igual a um VIP 1
- Não considera expectativa diferente por nível

### 3. **Categorias Muito Largas**
- "Risco: Queda em Receita" agrupa todos com score < 35
- Não diferencia "quase estável" de "crítico"

### 4. **Falta Indicador de Oportunidade**
- Não identifica jogadores com bom engajamento mas compras baixas
- Perdemos oportunidades de converter engajamento em receita

---

## ✅ Proposta de Melhoria

### Novo Sistema de Pontuação

#### 1. **Score de Compras (70%) - Ponderado**
```
Score Compras = (Qtd Compras × 0.4) + (Ticket Médio × 0.35) + (Recência × 0.25)
```

| Componente | Peso | Por quê? |
|------------|------|----------|
| Quantidade | 40% | Frequência gera hábito |
| Ticket Médio | 35% | Valor monetário direto |
| Recência | 25% | Quanto mais recente, melhor |

#### 2. **Score de Engajamento (30%) - Ponderado**
```
Score Engajamento = (Atividade × 0.6) + (VIP × 0.4)
```

| Componente | Peso | Por quê? |
|------------|------|----------|
| Atividades (torneios+maratonas+missões+promos) | 60% | Ação real do jogador |
| Nível VIP | 40% | Comprometimento histórico |

#### 3. **Expectativa por Nível VIP**

| VIP | Expectativa de Compras | Expectativa de Ticket |
|-----|------------------------|----------------------|
| 1 (Ametista) | 1 compra/7 dias | R$ 20 |
| 2 (Topázio) | 2 compras/7 dias | R$ 35 |
| 3 (Esmeralda) | 3 compras/7 dias | R$ 50 |
| 4 (Opala) | 4 compras/7 dias | R$ 75 |
| 5 (Berilo) | 5+ compras/7 dias | R$ 100+ |

#### 4. **Novas Categorias para Ações de CRM**

| Categoria | Score | Ação CRM |
|-----------|-------|----------|
| 💎 **Churn Iminente** | < 20 | Ação imediata - ligação |
| 🚨 **Risco Alto** | 20-34 | Oferta especial urgente |
| ⚠️ **Atenção** | 35-49 | Reengajamento ativo |
| 📊 **Estável** | 50-64 | Manter ritmo |
| 📈 **Bom** | 65-79 | Incentivar mais compras |
| 🏆 **VIP Ativo** | 80-89 | Benefícios exclusivos |
| ⭐ **Elite** | 90+ | Tratamento premium |
| 💰 **Oportunidade** | Engaj > 60, Comp < 40 | Converter em comprador |
| 🎯 **Potencial** | Engaj > 40, Comp < 30 | Nutrir com conteúdo |

#### 5. **Indicadores de Tendência**

Além do score atual, mostrar:
- 📉 Em queda (score caiu > 10 pontos)
- 📈 Em alta (score subiu > 10 pontos)
- ➡️ Estável (variação < 10 pontos)

---

## 🎯 Exemplo Prático

### Cenário: 3 Jogadores

| Jogador | VIP | Compras | Ticket | Engajamento | Score Atual | Score Novo | Categoria |
|---------|-----|---------|--------|-------------|-------------|------------|-----------|
| Ana | 1 | 1×R$20 | Baixo | Alto | 45 | 52 | Estável |
| Bruno | 3 | 5×R$80 | Alto | Médio | 68 | 78 | Bom |
| Carlos | 5 | 0×R$0 | Zero | Alto | 25 | 35 | Oportunidade |

**Ações CRM sugeridas:**
- **Ana**: Manter engajamento, oferta de pacote pequeno
- **Bruno**: Upsell para VIP 4, benefícios exclusivos
- **Carlos**: URGENTE - oferta de boas-vindas VIP, converter engajamento em compra

---

Quer que eu implemente essas melhorias?
