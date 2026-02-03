# Health Score Dashboard v2.2 - Resumo das Alterações

## 🚀 Novas Funcionalidades

### 1. Análise por Região
- **3 abas superiores**: Todos, Espanhol, Brasil, Internacional
- Filtragem automática baseada na coluna `translation`
- Espanhol: es_AR, es_ES, es_LA, es_MX
- Brasil: pt_BR
- Internacional: todos os outros idiomas

### 2. Composição do Score Atualizada
- **Removido**: Score de Login da pontuação geral
- **Engajamento**: 30% de peso
- **Compras**: 70% de peso

### 3. Análise VIP Dinâmica
- Cards visuais por nível VIP (1-5)
- Cores e ícones diferenciados:
  - 💎 Ametista (Nível 1)
  - 💠 Topázio (Nível 2)
  - 🔷 Esmeralda (Nível 3)
  - 🔶 Opala (Nível 4)
  - 👑 Berilo (Nível 5)
- Estatísticas por nível VIP

### 4. Sistema de Abas
- **4 abas de navegação**:
  - 📊 Visão Geral
  - 💎 Análise VIP
  - 👥 Jogadores
  - ⚙️ Benchmarks

### 5. Parâmetros Dinâmicos
- Cálculo automático de médias, medianas e desvios padrão
- Benchmarks baseados nos dados reais do upload
- Exportação em Excel com múltiplas abas

## 📁 Arquivos Alterados

| Arquivo | Alterações |
|---------|-----------|
| `app.py` | Backend com filtros de região, cálculo de scores |
| `static/app.js` | Frontend com navegação de abas e regiões |
| `static/style.css` | Estilos para abas de região e VIP |
| `templates/index.html` | Layout com sistema de abas |
| `requirements.txt` | Dependências do projeto |

## 🎯 Como Usar

1. Execute `python app.py`
2. Acesse `http://localhost:8000`
3. Faça upload de um arquivo Excel/CSV
4. Navegue entre as regiões e abas

## ⌨️ Atalhos de Teclado

### Regiões (Ctrl + tecla):
- `Ctrl + A` ou `Ctrl + 0` - Todos
- `Ctrl + E` - Espanhol
- `Ctrl + B` - Brasil
- `Ctrl + I` - Internacional

### Abas (1-4):
- `1` - Visão Geral
- `2` - Análise VIP
- `3` - Jogadores
- `4` - Benchmarks
