#!/usr/bin/env python3
"""
Script para adicionar tooltips em todos os gráficos e clusters do Health Score Dashboard
"""

import re

# Ler o arquivo HTML
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Tooltips para KPIs
tooltips_kpi = {
    'Total Jogadores': 'Total de jogadores analisados no período. Inclui todos os jogadores ativos que fizeram pelo menos uma ação (login, compra ou atividade) nos últimos 3 dias.',
    '% Ativos': 'Porcentagem de jogadores que realizaram login nos últimos 3 dias. Indica o nível de atividade da base de jogadores. Acima de 70% é considerado excelente.',
    'Pontuação Geral': 'Média do Health Score de todos os jogadores. Composto por 70% Compras (quantidade, ticket, recência) + 30% Engajamento (torneios, maratonas, missões, promoções, login).',
    'Elite': 'Jogadores com Health Score ≥ 80. São os jogadores mais valiosos, com alta frequência de compras e engajamento. Prioridade máxima para retenção.',
}

# Tooltips para Scores
content = content.replace(
    'Scores de Saúde (Composição: Engajamento 30% + Compras 70%)</h3>',
    '''Scores de Saúde (Composição: Engajamento 30% + Compras 70%)
                        <span class="info-tooltip tooltip-wide"><span class="tooltip-text">O Health Score é calculado com base em dois pilares: COMPRAS (70%) - quantidade de compras nos últimos 7 dias (40%), ticket médio (35%) e recência da última compra (25%); e ENGENHARIA (30%) - torneios, maratonas, missões, promoções e login nos últimos 3 dias.</span></span>
                    </h3>'''
)

content = content.replace(
    '<span class="score-title">Engajamento (30%)</span>',
    '<span class="score-title">Engajamento (30%) <span class="info-tooltip"><span class="tooltip-text">Média de atividades nos últimos 3 dias: torneios, maratonas, missões, promoções e logins. Considera apenas jogadores que participaram de cada atividade.</span></span></span>'
)

content = content.replace(
    '<span class="score-title">Compras (70%)</span>',
    '<span class="score-title">Compras (70%) <span class="info-tooltip"><span class="tooltip-text">Baseado em 3 fatores: quantidade de compras nos últimos 7 dias (40%), ticket médio (35%) e recência da última compra (25%). Benchmarks calculados dinamicamente da base.</span></span></span>'
)

# Tooltips para Gráficos - Visão Geral
content = content.replace(
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Categoria</h4>',
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Categoria <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Distribuição percentual dos jogadores em 6 categorias baseadas no Health Score: Elite (≥80), Muito Bom (65-79), Estável (50-64), Baixo (35-49), Risco Receita (<35, compras < engajamento) e Risco Engajamento (<35, engajamento ≤ compras).</span></span></h4>'
)

content = content.replace(
    '<h4><i class="fas fa-chart-bar"></i> Composição do Health Score</h4>',
    '<h4><i class="fas fa-chart-bar"></i> Composição do Health Score <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Visão detalhada da composição do Health Score médio da base: Score de Login (baseado em último acesso e frequência), Score de Engajamento (atividades nos últimos 3 dias) e Score de Compras (quantidade, ticket e recência).</span></span></h4>'
)

# Tooltips para Categorias
content = content.replace(
    '<h3><i class="fas fa-layer-group"></i> Distribuição de Categorias</h3>',
    '<h3><i class="fas fa-layer-group"></i> Distribuição de Categorias <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Detalhamento de cada categoria de saúde com porcentagem da base total. Cada categoria representa um segmento de jogadores com comportamentos similares de compra e engajamento.</span></span></h3>'
)

# Tooltips para cada categoria
content = content.replace(
    '<span class="categoria-nome">Elite</span>',
    '<span class="categoria-nome">Elite <span class="info-tooltip"><span class="tooltip-text">Score ≥ 80. Jogadores com excelente performance em compras e engajamento. São a base mais valiosa e devem receber atenção especial para retenção.</span></span></span>'
)

content = content.replace(
    '<span class="categoria-nome">Muito Bom</span>',
    '<span class="categoria-nome">Muito Bom <span class="info-tooltip"><span class="tooltip-text">Score 65-79. Jogadores engajados com boa frequência de compras. Potencial para se tornarem Elite com incentivos adequados.</span></span></span>'
)

content = content.replace(
    '<span class="categoria-nome">Estável</span>',
    '<span class="categoria-nome">Estável <span class="info-tooltip"><span class="tooltip-text">Score 50-64. Jogadores com comportamento consistente mas com espaço para crescimento. Foco em aumentar frequência de compras.</span></span></span>'
)

content = content.replace(
    '<span class="categoria-nome">Baixo</span>',
    '<span class="categoria-nome">Baixo <span class="info-tooltip"><span class="tooltip-text">Score 35-49. Jogadores com baixa atividade. Requerem ações de reengajamento para evitar churn.</span></span></span>'
)

content = content.replace(
    '<span class="categoria-nome">Risco: Queda em Receita</span>',
    '<span class="categoria-nome">Risco: Queda em Receita <span class="info-tooltip"><span class="tooltip-text">Score < 35 onde engajamento > compras. Jogadores estão ativos mas não comprando. Prioridade para campanhas de conversão.</span></span></span>'
)

content = content.replace(
    '<span class="categoria-nome">Risco: Queda em Engajamento</span>',
    '<span class="categoria-nome">Risco: Queda em Engajamento <span class="info-tooltip"><span class="tooltip-text">Score < 35 onde compras ≥ engajamento. Jogadores compram pouco e têm baixo engajamento. Risco iminente de churn total.</span></span></span>'
)

# Tooltips para Resumo Executivo - KPIs
content = content.replace(
    '<span class="kpi-label">Total Jogadores</span>',
    '<span class="kpi-label">Total Jogadores <span class="info-tooltip"><span class="tooltip-text">Total de jogadores analisados no snapshot atual. Comparado com o período anterior para mostrar tendência.</span></span></span>'
)

content = content.replace(
    '<span class="kpi-label">% Ativos</span>',
    '<span class="kpi-label">% Ativos <span class="info-tooltip"><span class="tooltip-text">Porcentagem de jogadores com login nos últimos 3 dias. Métrica chave de saúde da base.</span></span></span>'
)

content = content.replace(
    '<span class="kpi-label">Score Geral</span>',
    '<span class="kpi-label">Score Geral <span class="info-tooltip"><span class="tooltip-text">Média do Health Score de todos os jogadores. Variação mostra se a base está melhorando ou piorando.</span></span></span>'
)

content = content.replace(
    '<span class="kpi-label">Score Compras</span>',
    '<span class="kpi-label">Score Compras <span class="info-tooltip"><span class="tooltip-text">Média do score de compras (70% do total). Composto por quantidade, ticket médio e recência.</span></span></span>'
)

content = content.replace(
    '<span class="kpi-label">Score Engajamento</span>',
    '<span class="kpi-label">Score Engajamento <span class="info-tooltip"><span class="tooltip-text">Média do score de engajamento (30% do total). Baseado em atividades nos últimos 3 dias.</span></span></span>'
)

# Tooltips para Gráficos - Executivo
content = content.replace(
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Cluster</h4>',
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Cluster <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Distribuição atual dos jogadores nos 6 clusters de saúde. Permite visualizar rapidamente a composição da base e identificar concentrações de risco.</span></span></h4>'
)

content = content.replace(
    '<h4><i class="fas fa-chart-line"></i> Evolução dos Indicadores</h4>',
    '<h4><i class="fas fa-chart-line"></i> Evolução dos Indicadores <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Evolução temporal dos principais indicadores. Score Geral mostra a média de saúde da base e % Ativos mostra o nível de engajamento ao longo do tempo.</span></span></h4>'
)

content = content.replace(
    '<h4><i class="fas fa-table"></i> Resumo por Cluster</h4>',
    '<h4><i class="fas fa-table"></i> Resumo por Cluster <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Detalhamento quantitativo de cada cluster: quantidade absoluta, porcentagem da base total e tendência comparada ao período anterior.</span></span></h4>'
)

content = content.replace(
    '<h4><i class="fas fa-history"></i> Histórico de Snapshots</h4>',
    '<h4><i class="fas fa-history"></i> Histórico de Snapshots <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Histórico completo de snapshots salvos. Cada linha representa uma análise diária. É possível deletar snapshots individuais se necessário.</span></span></h4>'
)

# Tooltips para Análise VIP
content = content.replace(
    '<h3><i class="fas fa-gem"></i> Análise por Nível VIP</h3>',
    '<h3><i class="fas fa-gem"></i> Análise por Nível VIP <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Análise segmentada por nível VIP (Ametista, Topázio, Esmeralda, Opala, Berilo). Mostra comportamento, saúde e distribuição de cada segmento VIP.</span></span></h3>'
)

content = content.replace(
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Nível VIP</h4>',
    '<h4><i class="fas fa-chart-pie"></i> Distribuição por Nível VIP <span class="info-tooltip"><span class="tooltip-text">Distribuição percentual da base entre os 5 níveis VIP.</span></span></h4>'
)

content = content.replace(
    '<h4><i class="fas fa-chart-bar"></i> Scores Médios por Nível VIP</h4>',
    '<h4><i class="fas fa-chart-bar"></i> Scores Médios por Nível VIP <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Comparação do Health Score médio entre níveis VIP. Permite identificar quais segmentos estão mais saudáveis.</span></span></h4>'
)

# Tooltips para Jogadores
content = content.replace(
    '<h3><i class="fas fa-trophy"></i> Top 10 Jogadores</h3>',
    '<h3><i class="fas fa-trophy"></i> Top 10 Jogadores <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Os 10 jogadores com maior Health Score atual. Ranking baseado na pontuação combinada de compras (70%) e engajamento (30%).</span></span></h3>'
)

content = content.replace(
    '<h3><i class="fas fa-money-bill-wave"></i> Risco: Queda em Receita</h3>',
    '<h3><i class="fas fa-money-bill-wave"></i> Risco: Queda em Receita <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Jogadores com Score Geral < 35 onde o engajamento é maior que as compras. Estão ativos no app mas não convertendo em receita. Prioridade para campanhas de recuperação de receita.</span></span></h3>'
)

content = content.replace(
    '<h3><i class="fas fa-chart-line"></i> Risco: Queda em Engajamento</h3>',
    '<h3><i class="fas fa-chart-line"></i> Risco: Queda em Engajamento <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Jogadores com Score Geral < 35 onde as compras são maiores ou iguais ao engajamento. Baixa atividade no app. Risco iminente de churn total.</span></span></h3>'
)

# Tooltips para Clusters
content = content.replace(
    '<h3><i class="fas fa-layer-group"></i> Top 50 Jogadores por Cluster</h3>',
    '<h3><i class="fas fa-layer-group"></i> Top 50 Jogadores por Cluster <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Lista dos 50 melhores jogadores de cada categoria. Permite identificar jogadores específicos para ações segmentadas. Clique para expandir cada cluster.</span></span></h3>'
)

# Tooltips para cada cluster card
content = content.replace(
    '<span class="cluster-name">Elite</span>',
    '<span class="cluster-name">Elite <span class="info-tooltip"><span class="tooltip-text">Top 50 jogadores com Score Geral mais alto (≥ 80). Clientes mais valiosos da base.</span></span></span>'
)

content = content.replace(
    '<span class="cluster-name">Muito Bom</span>',
    '<span class="cluster-name">Muito Bom <span class="info-tooltip"><span class="tooltip-text">Top 50 jogadores com Score 65-79. Alto potencial de se tornarem Elite.</span></span></span>'
)

content = content.replace(
    '<span class="cluster-name">Estável</span>',
    '<span class="cluster-name">Estável <span class="info-tooltip"><span class="tooltip-text">Top 50 jogadores com Score 50-64. Base consistente com potencial de crescimento.</span></span></span>'
)

content = content.replace(
    '<span class="cluster-name">Baixo</span>',
    '<span class="cluster-name">Baixo <span class="info-tooltip"><span class="tooltip-text">Top 50 jogadores com Score 35-49. Requerem atenção para evitar perda.</span></span></span>'
)

content = content.replace(
    '<span class="cluster-name">Risco: Queda em Receita</span>',
    '<span class="cluster-name">Risco: Queda em Receita <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Top 50 jogadores em risco de queda de receita. Engajados mas com baixa conversão. Prioridade para ofertas e incentivos de compra.</span></span></span>'
)

content = content.replace(
    '<span class="cluster-name">Risco: Queda em Engajamento</span>',
    '<span class="cluster-name">Risco: Queda em Engajamento <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Top 50 jogadores em risco de churn total. Baixo engajamento e compras. Última chance de retenção.</span></span></span>'
)

# Tooltips para Benchmarks
content = content.replace(
    '<h3><i class="fas fa-cogs"></i> Parâmetros e Benchmarks</h3>',
    '<h3><i class="fas fa-cogs"></i> Parâmetros e Benchmarks <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Parâmetros calculados dinamicamente a partir da base de jogadores. Mostra médias, medianas e desvios padrão das principais métricas. Esses valores são usados como benchmarks para calcular os scores.</span></span></h3>'
)

content = content.replace(
    '<h4><i class="fas fa-chart-bar"></i> Médias por Métrica (3 dias)</h4>',
    '<h4><i class="fas fa-chart-bar"></i> Médias por Métrica (3 dias) <span class="info-tooltip tooltip-wide"><span class="tooltip-text">Comparação das médias de cada métrica (torneios, maratonas, missões, promoções, logins) considerando apenas jogadores que participaram de cada atividade (média sem zeros).</span></span></h4>'
)

# Tooltips para Exportar
content = content.replace(
    '<h3><i class="fas fa-download"></i> Exportar Resultados</h3>',
    '<h3><i class="fas fa-download"></i> Exportar Resultados <span class="info-tooltip"><span class="tooltip-text">Exporte os dados completos da análise em formato CSV ou Excel para análises externas.</span></span></h3>'
)

# Salvar o arquivo atualizado
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Tooltips adicionados com sucesso!")
print("\nResumo das alterações:")
print("- 6 KPIs com tooltips")
print("- 2 Score Cards com tooltips")
print("- 2 Gráficos (Visão Geral) com tooltips")
print("- 6 Categorias com tooltips")
print("- 5 KPIs (Executivo) com tooltips")
print("- 3 Gráficos (Executivo) com tooltips")
print("- 2 Gráficos (VIP) com tooltips")
print("- 3 Seções (Jogadores) com tooltips")
print("- 6 Clusters com tooltips")
print("- 1 Gráfico (Benchmarks) com tooltips")
print("- 1 Seção (Exportar) com tooltips")
