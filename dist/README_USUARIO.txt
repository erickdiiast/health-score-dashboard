================================================================================
  HEALTH SCORE DASHBOARD v2.8.0
  Sistema de Análise de Saúde e Engajamento de Jogadores
================================================================================

📋 REQUISITOS MÍNIMOS
--------------------------------------------------------------------------------
- Windows 10 ou superior (64 bits)
- 4GB de RAM
- 100MB de espaço em disco
- Navegador web (Chrome, Firefox, Edge)

🚀 COMO USAR
--------------------------------------------------------------------------------
1. Descompacte o arquivo HealthScoreDashboard.zip

2. Execute o arquivo:
   HealthScoreDashboard.exe

3. Aguarde a janela "Health Score Dashboard" abrir
   (Pode levar alguns segundos na primeira execução)

4. Acesse no navegador:
   http://localhost:8080

5. Para fechar o aplicativo:
   - Feche a janela do console, OU
   - Pressione CTRL+C na janela do console

📊 FLUXO DE TRABALHO RECOMENDADO
--------------------------------------------------------------------------------
1. FAÇA UPLOAD do arquivo CSV com dados dos jogadores
   - Arraste o arquivo ou clique em "Selecionar Arquivo"
   - Formatos suportados: .csv, .xlsx, .xls

2. ANALISE o dashboard
   - Verifique os scores de Engajamento, Compras e Geral
   - Observe a distribuição por clusters
   - Identifique jogadores em risco

3. SALVE O SNAPSHOT
   - Clique em "💾 Salvar Dados do Dia" (Resumo Executivo)
   - Selecione a data correspondente aos dados
   - Isso permite acompanhamento histórico

4. ACOMPANHE A JORNADA
   - Use a aba "Jornada do Jogador" para ver evolução individual
   - Busque por PID específico
   - Veja tendências (▲ alta, ▼ baixa, ~ estável, * novo)

📁 FORMATO DO CSV/EXCEL
--------------------------------------------------------------------------------
Colunas obrigatórias:
- pid (ou player_id): ID único do jogador
- nivel_vip: Nível VIP (1-5)
- lastLogin: Data do último login (YYYY-MM-DD)
- ultima_compra: Data da última compra (YYYY-MM-DD)
- qtd_logins_3d: Quantidade de logins nos últimos 3 dias
- qtd_compras_7d: Quantidade de compras nos últimos 7 dias
- ticket_medio_7d: Ticket médio de compras (7 dias)
- qtd_torneios_3d: Torneios jogados (3 dias)
- qtd_maratonas_3d: Maratonas jogadas (3 dias)
- qtd_missoes_3d: Missões completadas (3 dias)
- qtd_promos_3d: Promoções participadas (3 dias)

🏷️ CLUSTERS (CATEGORIAS)
--------------------------------------------------------------------------------
⭐ Elite          - Score ≥ 80 (Top performers)
🏆 VIP Ativo      - Score 70-79 (VIPs engajados)
📈 Bom            - Score 60-69 (Bom desempenho)
📊 Estável        - Score 50-59 (Engajamento moderado)
⚠️ Atenção        - Score 40-49 (Atenção necessária)
🚨 Risco Alto     - Score < 40 (Baixo em ambas métricas)
🚨 Queda Receita  - Score compras < 35 (Engajado mas não compra)
🚨 Queda Engaj.   - Score engajamento < 35 (Compra mas não engaja)
💎 Churn Iminente - Score < 35 em ambos (Alto risco de churn)

💾 ONDE OS DADOS SÃO ARMAZENADOS
--------------------------------------------------------------------------------
Os dados são salvos localmente no arquivo:
   historico.db (banco de dados SQLite)

Este arquivo é criado automaticamente na pasta onde o executável está localizado.

⚠️ IMPORTANTE
--------------------------------------------------------------------------------
- NÃO delete o arquivo historico.db se quiser manter o histórico
- Faça backup do historico.db periodicamente
- Cada snapshot salvo ocupa espaço no banco de dados
- Para limpar o histórico, use a aba "Histórico" no dashboard

🔧 SOLUÇÃO DE PROBLEMAS
--------------------------------------------------------------------------------
PROBLEMA: "Não consigo acessar localhost:8080"
SOLUÇÃO: Verifique se o antivirus/firewall não está bloqueando o aplicativo

PROBLEMA: "O executável não abre"
SOLUÇÃO: Execute como Administrador ou verifique se está desbloqueado
          (Propriedades do arquivo > Desbloquear)

PROBLEMA: "Dados não aparecem após upload"
SOLUÇÃO: Verifique se o CSV tem as colunas corretas (pid, nivel_vip, etc.)

📞 SUPORTE
--------------------------------------------------------------------------------
Para dúvidas ou problemas, entre em contato com quem lhe forneceu
este software.

================================================================================
  Versão 2.8.0 - Fevereiro 2026
  Desenvolvido com FastAPI + SQLite + Vanilla JS
================================================================================
