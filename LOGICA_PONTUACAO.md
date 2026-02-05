# Análise Detalhada da Lógica de Pontuação

## 🎯 Visão Geral do Sistema

O sistema calcula **3 scores independentes** que se combinam em um **score geral**:

```
┌─────────────────────────────────────────────────────────────┐
│                    SCORE GERAL                              │
│              (Engajamento × 30%) + (Compras × 70%)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
   ┌────▼────┐                                ┌────▼────┐
   │ ENGAJA- │                                │ COMPRAS │
   │ MENTO   │                                │         │
   │  (30%)  │                                │  (70%)  │
   └────┬────┘                                └────┬────┘
        │                                           │
   ┌────┴──────────────────┐                 ┌────┴──────────────────┐
   │ • Atividades (60%)    │                 │ • Quantidade (40%)    │
   │ • Nível VIP (40%)     │                 │ • Ticket (35%)        │
   │                       │                 │ • Recência (25%)      │
   └───────────────────────┘                 └───────────────────────┘
```

---

## 📊 1. SCORE DE LOGIN (Componente auxiliar)

### Objetivo
Medir a **fidelidade de acesso** - quão ativamente o jogador usa a plataforma.

### Fórmula
```python
Score Login = Média entre:
  ├─ Recência do último login (decaimento exponencial)
  └─ Frequência de logins (últimos 3 dias)
```

### Detalhamento

#### 1.1 Recência (Quanto tempo desde o último login?)
```
Fórmula: 100 × e^(-dias/7)

Exemplos:
• Hoje:     100 × e^0    = 100 pontos
• 7 dias:   100 × e^-1   = 37 pontos  
• 14 dias:  100 × e^-2   = 14 pontos
• 30 dias:  100 × e^-4.3 = 1 ponto
```

**Por que faz sentido?**
- Quanto mais tempo sem logar, menor o score
- Decaimento exponencial = perda rápida inicial, depois estabiliza
- 7 dias na fórmula = semana natural de uso

#### 1.2 Frequência (Quantos logins em 3 dias?)
```
Fórmula: min(qtd_logins × factor, 100)

Factor = 100 / (média_logins × 1.5)
```

**Por que faz sentido?**
- Se média é 2 logins/3dias, factor = 33.33
- 2 logins → 66 pontos (bom, não excelente)
- 3 logins → 100 pontos (acima da média)
- Limita em 100 para não distorcer

---

## 🎮 2. SCORE DE ENGAJAMENTO (30% do geral)

### Objetivo
Medir o **quanto o jogador interage** com a plataforma (jogos, eventos).

### Fórmula Ponderada
```python
Score Engajamento = (Atividades × 0.60) + (VIP × 0.40)
```

### 2.1 Atividades (60% do score de engajamento)

#### Pesos das Atividades
| Atividade | Peso | Por quê? |
|-----------|------|----------|
| **Maratonas** | 2.5 | Eventos mais importantes, engajamento alto |
| **Torneios** | 2.0 | Competição = alto envolvimento |
| **Missões** | 1.5 | Atividades diárias |
| **Promoções** | 1.0 | Engajamento passivo |

#### Cálculo do Fator Dinâmico
```python
Para cada métrica:
  factor = 100 / (média_3dias × 1.5)

Exemplo (Torneios):
  Se média = 15 torneios em 3 dias:
  factor = 100 / (15 × 1.5) = 4.44
  
  Jogador com 15 torneios:
  score = 15 × 4.44 = 66 pontos (bom)
  
  Jogador com 22 torneios:
  score = 22 × 4.44 = 98 pontos (excelente)
```

**Por que 1.5 na fórmula?**
- 1.0× média = score 66 (dentro do esperado)
- 1.5× média = score 100 (excelente, meta a atingir)
- Cria benchmark desafiador mas alcançável

#### Média Ponderada das Atividades
```python
Atividades Score = (Torneios×2 + Maratonas×2.5 + Missões×1.5 + Promos×1) 
                    ÷ (2 + 2.5 + 1.5 + 1)
```

**Por que pesos diferentes?**
- Maratonas têm peso maior = eventos mais valiosos
- Torneios = competição ativa
- Missões = engajamento rotineiro
- Promoções = engajamento reativo (menor valor)

### 2.2 Nível VIP (40% do score de engajamento)

#### Fórmula
```python
VIP Score = 20 + ((nivel - 1) / 4) × 80

VIP 1 (Ametista):  20 + 0   = 20 pontos
VIP 2 (Topázio):   20 + 20  = 40 pontos
VIP 3 (Esmeralda): 20 + 40  = 60 pontos
VIP 4 (Opala):     20 + 50  = 70 pontos
VIP 5 (Berilo):    20 + 80  = 100 pontos
```

**Por que faz sentido?**
- VIP reflete histórico de comprometimento
- Não é 0-100 linear (VIP 1 não é 0, é 20)
- Reconhece que mesmo VIP 1 tem algum valor
- VIP 5 tem score máximo = tratamento premium justificado

---

## 💰 3. SCORE DE COMPRAS (70% do geral)

### Objetivo
Medir o **valor monetário** do jogador - aspecto mais importante para CRM.

### Fórmula Ponderada
```python
Score Compras = (Quantidade × 0.40) + (Ticket × 0.35) + (Recência × 0.25)
```

### 3.1 Quantidade de Compras (40% - Maior peso!)

#### Lógica
```python
Score Qtd = (qtd_real / (média_qtd × 1.5)) × 100

Exemplo:
  Média geral = 2 compras/semana
  Meta (1.5x) = 3 compras/semana
  
  Jogador com 3 compras: 100 pontos
  Jogador com 2 compras: 66 pontos
  Jogador com 1 compra:  33 pontos
```

**Por que é o fator mais importante (40%)?**
- Frequência de compra = hábito = previsibilidade de receita
- Jogador que compra toda semana > jogador que compra 1x ao mês
- Facilita previsão de receita e planejamento

### 3.2 Ticket Médio (35%)

#### Lógica
```python
Score Ticket = (ticket_real / (média_ticket × 1.5)) × 100
```

**Por que 35% e não mais?**
- Ticket alto é bom, mas compra única é arriscada
- Exemplo: 1 compra de R$500 < 5 compras de R$100
- Frequência gera mais valor no longo prazo

### 3.3 Recência da Compra (25%)

#### Lógica
```python
Score Recência = 100 × e^(-dias_desde_compra/30)

Hoje:          100 pontos
7 dias:        79 pontos
30 dias:       37 pontos
60 dias:       14 pontos
90 dias:        5 pontos
```

**Por que 30 dias no denominador?**
- Mês = ciclo natural de compra
- Após 30 dias sem comprar, score cai drasticamente
- Alerta precoce para churn

---

## 🎯 4. SCORE GERAL (Composição Final)

### Fórmula
```python
Score Geral = (Engajamento × 0.30) + (Compras × 0.70)
```

### Por que 70% Compras / 30% Engajamento?

| Aspecto | Justificativa |
|---------|---------------|
| **Compras 70%** | O que gera receita direta. Sem compra, engajamento alto não paga as contas |
| **Engajamento 30%** | Indicador de saúde e potencial futuro. Jogador engajado tem maior LTV |

### Exemplo Prático

```
Jogador A:
  - Engajamento: 80 pontos
  - Compras: 40 pontos
  - Score Geral: 80×0.3 + 40×0.7 = 24 + 28 = 52 (Estável)
  
Jogador B:
  - Engajamento: 40 pontos  
  - Compras: 80 pontos
  - Score Geral: 40×0.3 + 80×0.7 = 12 + 56 = 68 (Bom)
  
Conclusão: Jogador B é mais valioso apesar de menos engajado
```

---

## 🏷️ 5. CATEGORIZAÇÃO (Para Ações de CRM)

### Hierarquia de Decisão

```
1. É OPORTUNIDADE? (Eng > 60, Comp < 40)
   ├─ Sim + VIP ≥ 3 → 💰 Oportunidade VIP
   └─ Sim + VIP < 3 → 💰 Oportunidade

2. É POTENCIAL? (Eng > 40, Comp 30-50)
   └─ Sim → 🎯 Potencial

3. Categorizar por Score Geral:
   ├─ ≥ 90 → ⭐ Elite
   ├─ 80-89 → 🏆 VIP Ativo
   ├─ 65-79 → 📈 Bom
   ├─ 50-64 → 📊 Estável
   ├─ 40-49 → ⚠️ Atenção
   ├─ 25-39 → 🚨 Risco Alto
   └─ < 25 → 💎 Churn Iminente
```

### Por que Oportunidade antes do Score Geral?

**Lógica de Negócio:**
- Jogador com alto engajamento + baixas compras = OURO para CRM
- Já provou que gosta da plataforma (engajamento alto)
- Não está convertendo em receita (compras baixas)
- **Ação certeira = resultado rápido**

### Identificação de Tipo de Risco

```python
Se Score < 35:
  Se Compras < Engajamento:
    → 🚨 Risco: Queda em Receita
    (Está ativo mas não compra)
  
  Se Engajamento ≤ Compras:
    → 🚨 Risco: Queda em Engajamento
    (Comprou mas sumiu da plataforma)
```

---

## 📈 6. EXPECTATIVA POR VIP

### Benchmarks de Performance

| VIP | Compras Esperadas | Ticket Esperado | Label |
|-----|-------------------|-----------------|-------|
| 1 | 1/semana | R$ 20 | Iniciante |
| 2 | 2/semana | R$ 35 | Regular |
| 3 | 3/semana | R$ 50 | Fiel |
| 4 | 4/semana | R$ 75 | Premium |
| 5 | 5+/semana | R$ 100+ | Elite |

### Cálculo de Status
```python
Performance = (Qtd Real / Qtd Esperada × 0.6) + 
              (Ticket Real / Ticket Esperado × 0.4)

≥ 120% → 🏆 Superando
≥ 90%  → ✅ Dentro da meta
≥ 60%  → ⚠️ Abaixo
< 60%  → 🚨 Crítico
```

---

## ✅ Resumo: Por que Essa Lógica Funciona?

### 1. **Ponderação Reflete Prioridade de Negócio**
- Compras (70%) > Engajamento (30%) = Foco em resultado financeiro

### 2. **Benchmarks Dinâmicos**
- Médias calculadas dos dados reais = sempre relevante
- 1.5× média = 100 pontos = meta desafiadora

### 3. **Recência é Crucial**
- Decaimento exponencial = alerta precoce de churn
- 30 dias sem compra = score cai para 37%

### 4. **Oportunidades Identificadas**
- Alto engajamento + baixas compras = potencial não aproveitado
- Ação de CRM nesses casos tem alto ROI

### 5. **Granularidade Adequada**
- 12 categorias diferentes = ações específicas
- Não agrupa "Risco" em um balaio só

### 6. **Expectativa por VIP**
- Compara performance real vs esperada para o nível
- VIP 5 com 1 compra é crítico, VIP 1 com 1 compra é normal

---

## 🎲 Exemplo Completo

### Dados do Jogador
```
VIP: 3 (Esmeralda)
Compras (7d): 2
Ticket Médio: R$ 45
Última compra: 5 dias atrás
Torneios (3d): 12
Maratonas (3d): 4
Missões (3d): 8
Último login: ontem
```

### Cálculos
```
1. SCORE COMPRAS (70%):
   • Quantidade: (2 / (3×1.5))×100 = 44 pts × 0.40 = 17.6
   • Ticket: (45 / (50×1.5))×100 = 60 pts × 0.35 = 21.0
   • Recência: 100×e^(-5/30) = 84 pts × 0.25 = 21.0
   • Total: 17.6 + 21.0 + 21.0 = 59.6

2. SCORE ENGAJAMENTO (30%):
   • Atividades: média ponderada ≈ 70 pts × 0.60 = 42.0
   • VIP: 60 pts × 0.40 = 24.0
   • Total: 42.0 + 24.0 = 66.0

3. SCORE GERAL:
   • 59.6×0.7 + 66.0×0.3 = 41.7 + 19.8 = 61.5

4. CATEGORIA: 📊 Estável
```

### Ação CRM Recomendada
"📱 Manter ritmo + Notificações" - Jogador está dentro da expectativa para VIP 3, pode ser incentivado a aumentar frequência de compra.
