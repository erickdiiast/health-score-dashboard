/**
 * Health Score Dashboard - Frontend JavaScript
 */

// Variáveis globais
let categoriaChart = null;
let scoresChart = null;
let vipChart = null;
let vipScoresChart = null;
let benchmarksChart = null;

// Dados em cache
let cachedResumo = null;
let cachedResumoAtual = null;  // Resumo da região atual
let cachedDataCompleto = null;
let cachedDadosAtual = null;   // Dados da região atual
let regiaoAtual = 'all';  // 'all', 'es', 'br', 'int'
let vipAtual = 'all';     // 'all', '1', '2', '3', '4', '5'

// Configuração padrão do Chart.js
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';
Chart.defaults.font.family = 'Inter, sans-serif';

/**
 * Gerenciamento de Regiões
 */
function showRegion(regiao) {
    regiaoAtual = regiao;
    
    // Atualiza botões
    document.querySelectorAll('.region-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('region-btn-' + regiao).classList.add('active');
    
    // Filtra dados e atualiza dashboard
    if (cachedDataCompleto) {
        const dadosFiltrados = filtrarDados(cachedDataCompleto, regiao, vipAtual);
        const resumoFiltrado = gerarResumoFiltrado(dadosFiltrados, cachedResumo, regiao);
        
        // Atualiza dashboard com dados filtrados
        updateDashboardWithData(resumoFiltrado, dadosFiltrados);
        
        // Se estiver nas abas VIP ou Benchmarks, força re-renderização
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && (activeTab.id === 'tab-vip' || activeTab.id === 'tab-benchmarks')) {
            renderTabContent(activeTab.id, resumoFiltrado);
        }
    }
}

/**
 * Filtra dados por região
 */
function filtrarPorRegiao(dados, regiao) {
    if (regiao === 'all') return dados;
    return dados.filter(j => j.regiao === regiao);
}

/**
 * Gerenciamento de Nível VIP
 */
function showVIP(nivel) {
    vipAtual = nivel;
    
    // Atualiza botões
    document.querySelectorAll('.vip-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('vip-btn-' + nivel).classList.add('active');
    
    // Filtra dados e atualiza dashboard
    if (cachedDataCompleto) {
        const dadosFiltrados = filtrarDados(cachedDataCompleto, regiaoAtual, vipAtual);
        const resumoFiltrado = gerarResumoFiltrado(dadosFiltrados, cachedResumo, regiaoAtual);
        
        // Atualiza dashboard com dados filtrados
        updateDashboardWithData(resumoFiltrado, dadosFiltrados);
        
        // Se estiver nas abas VIP ou Benchmarks, força re-renderização
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && (activeTab.id === 'tab-vip' || activeTab.id === 'tab-benchmarks')) {
            renderTabContent(activeTab.id, resumoFiltrado);
        }
    }
}

/**
 * Filtra dados por nível VIP
 */
function filtrarPorVIP(dados, nivel) {
    if (nivel === 'all') return dados;
    return dados.filter(j => String(j.vip_level) === nivel || String(j.nivel_vip) === nivel);
}

/**
 * Filtra dados por região e VIP combinados
 */
function filtrarDados(dados, regiao, vip) {
    let resultado = dados;
    if (regiao !== 'all') {
        resultado = resultado.filter(j => j.regiao === regiao);
    }
    if (vip !== 'all') {
        resultado = resultado.filter(j => String(j.vip_level) === vip || String(j.nivel_vip) === vip);
    }
    return resultado;
}

/**
 * Gera resumo filtrado por região e/ou VIP
 */
function gerarResumoFiltrado(dados, resumoOriginal, regiao) {
    // Se região for 'all' e não houver filtro VIP, retorna original
    if (regiao === 'all' && vipAtual === 'all') return resumoOriginal;
    
    // Se temos análise pré-calculada no backend E não há filtro VIP ativo, usa ela
    if (vipAtual === 'all' && resumoOriginal.analise_regiao && resumoOriginal.analise_regiao[regiao]) {
        const analise = resumoOriginal.analise_regiao[regiao];
        return {
            ...resumoOriginal,
            total_jogadores: analise.quantidade,
            percentual_ativos: analise.percentual_ativos,
            media_saude_login: analise.score_login_medio,
            media_saude_engajamento: analise.score_engajamento_medio,
            media_saude_compras: analise.score_compras_medio,
            media_pontuacao_geral: analise.score_geral_medio,
            distribuicao_categorias: analise.distribuicao_categorias,
            top_jogadores: dados.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10),
            jogadores_risco_receita: dados.filter(j => j.categoria === '🚨 Risco: Queda Receita').slice(0, 50),
            jogadores_risco_engajamento: dados.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').slice(0, 50),
            regiao_atual: regiao,
            regiao_nome: analise.nome
        };
    }
    
    // Caso contrário, calcula do lado do cliente
    const total = dados.length;
    if (total === 0) return resumoOriginal;
    
    const ativos = dados.filter(j => j.ativo).length;
    
    // Calcula distribuição de categorias (todas as novas categorias)
    const elite = dados.filter(j => j.categoria === '⭐ Elite').length;
    const vipAtivo = dados.filter(j => j.categoria === '🏆 VIP Ativo').length;
    const bom = dados.filter(j => j.categoria === '📈 Bom').length;
    const estavel = dados.filter(j => j.categoria === '📊 Estável').length;
    const atencao = dados.filter(j => j.categoria === '⚠️ Atenção').length;
    const riscoAlto = dados.filter(j => j.categoria === '🚨 Risco Alto').length;
    const churn = dados.filter(j => j.categoria === '💎 Churn Iminente').length;
    const oportunidade = dados.filter(j => j.categoria === '💰 Oportunidade').length;
    const oportunidadeVip = dados.filter(j => j.categoria === '💰 Oportunidade VIP').length;
    const potencial = dados.filter(j => j.categoria === '🎯 Potencial').length;
    const riscoReceita = dados.filter(j => j.categoria === '🚨 Risco: Queda Receita').length;
    const riscoEngajamento = dados.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').length;
    
    return {
        ...resumoOriginal,
        total_jogadores: total,
        percentual_ativos: ativos / total * 100,
        media_saude_login: dados.reduce((a, b) => a + b.score_login, 0) / total,
        media_saude_engajamento: dados.reduce((a, b) => a + b.score_engajamento, 0) / total,
        media_saude_compras: dados.reduce((a, b) => a + b.score_compras, 0) / total,
        media_pontuacao_geral: dados.reduce((a, b) => a + b.score_geral, 0) / total,
        distribuicao_categorias: {
            elite: parseFloat((elite / total * 100).toFixed(2)),
            vip_ativo: parseFloat((vipAtivo / total * 100).toFixed(2)),
            bom: parseFloat((bom / total * 100).toFixed(2)),
            estavel: parseFloat((estavel / total * 100).toFixed(2)),
            atencao: parseFloat((atencao / total * 100).toFixed(2)),
            risco_alto: parseFloat((riscoAlto / total * 100).toFixed(2)),
            churn_iminente: parseFloat((churn / total * 100).toFixed(2)),
            oportunidade: parseFloat((oportunidade / total * 100).toFixed(2)),
            oportunidade_vip: parseFloat((oportunidadeVip / total * 100).toFixed(2)),
            potencial: parseFloat((potencial / total * 100).toFixed(2)),
            risco_receita: parseFloat((riscoReceita / total * 100).toFixed(2)),
            risco_engajamento: parseFloat((riscoEngajamento / total * 100).toFixed(2))
        },
        top_jogadores: dados.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10),
        jogadores_risco_receita: dados.filter(j => j.categoria === '🚨 Risco: Queda Receita').slice(0, 50),
        jogadores_risco_engajamento: dados.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').slice(0, 50),
        regiao_atual: regiao,
        regiao_nome: regiao === 'es' ? 'Espanhol' : regiao === 'br' ? 'Brasil' : 'Internacional'
    };
}

/**
 * Calcula estatísticas para benchmarks baseado nos dados
 */
function calcularEstatisticas(dados) {
    const calcularMedia = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length || 0;
    const calcularMediana = (arr) => {
        if (arr.length === 0) return 0;
        const sorted = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    };
    
    const torneios = dados.map(d => d.qtd_torneios_3d || 0);
    const maratonas = dados.map(d => d.qtd_maratonas_3d || 0);
    const missoes = dados.map(d => d.qtd_missoes_3d || 0);
    const promos = dados.map(d => d.qtd_promos_3d || 0);
    const logins = dados.map(d => d.qtd_logins_3d || 0);
    
    return {
        media_torneios_3d: calcularMedia(torneios),
        media_maratonas_3d: calcularMedia(maratonas),
        media_missoes_3d: calcularMedia(missoes),
        media_promos_3d: calcularMedia(promos),
        media_logins_3d: calcularMedia(logins),
        mediana_torneios_3d: calcularMediana(torneios),
        mediana_maratonas_3d: calcularMediana(maratonas),
        mediana_missoes_3d: calcularMediana(missoes),
        mediana_promos_3d: calcularMediana(promos),
        mediana_logins_3d: calcularMediana(logins),
    };
}

/**
 * Calcula análise VIP baseada nos dados
 */
function calcularAnaliseVIP(dados) {
    const niveis = [1, 2, 3, 4, 5];
    const nomesVIP = {
        1: { nome: 'Ametista', cor: '#9B59B6', icone: '💎' },
        2: { nome: 'Topázio', cor: '#F39C12', icone: '💠' },
        3: { nome: 'Esmeralda', cor: '#27AE60', icone: '🔷' },
        4: { nome: 'Opala', cor: '#E74C3C', icone: '🔶' },
        5: { nome: 'Berilo', cor: '#3498DB', icone: '👑' }
    };
    
    const calcularMedia = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length || 0;
    const calcularMediana = (arr) => {
        if (arr.length === 0) return 0;
        const sorted = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    };
    
    const analise = {};
    const total = dados.length;
    
    niveis.forEach(nivel => {
        const jogadoresNivel = dados.filter(j => j.nivel_vip === nivel || j.vip_level === nivel);
        if (jogadoresNivel.length > 0) {
            const count = jogadoresNivel.length;
            
            // Calcula estatísticas de benchmarks para este nível VIP
            const torneios = jogadoresNivel.map(d => d.qtd_torneios_3d || 0);
            const maratonas = jogadoresNivel.map(d => d.qtd_maratonas_3d || 0);
            const missoes = jogadoresNivel.map(d => d.qtd_missoes_3d || 0);
            const promos = jogadoresNivel.map(d => d.qtd_promos_3d || 0);
            
            // Calcula percentual de ativos (login >= 50)
            const ativos = jogadoresNivel.filter(j => j.score_login >= 50).length;
            const percentualAtivos = (ativos / count * 100).toFixed(2);
            
            analise[`vip_${nivel}`] = {
                nivel: nivel,
                nome: nomesVIP[nivel].nome,
                cor: nomesVIP[nivel].cor,
                icone: nomesVIP[nivel].icone,
                quantidade: count,
                percentual: ((count / total) * 100).toFixed(2),
                percentual_ativos: percentualAtivos,
                score_geral_medio: (jogadoresNivel.reduce((a, b) => a + b.score_geral, 0) / count).toFixed(2),
                score_login_medio: (jogadoresNivel.reduce((a, b) => a + b.score_login, 0) / count).toFixed(2),
                score_engajamento_medio: (jogadoresNivel.reduce((a, b) => a + b.score_engajamento, 0) / count).toFixed(2),
                score_compras_medio: (jogadoresNivel.reduce((a, b) => a + b.score_compras, 0) / count).toFixed(2),
                // Estatísticas de benchmarks
                estatisticas: {
                    media_torneios_3d: calcularMedia(torneios),
                    media_maratonas_3d: calcularMedia(maratonas),
                    media_missoes_3d: calcularMedia(missoes),
                    media_promos_3d: calcularMedia(promos),
                    mediana_torneios_3d: calcularMediana(torneios),
                    mediana_maratonas_3d: calcularMediana(maratonas),
                    mediana_missoes_3d: calcularMediana(missoes),
                    mediana_promos_3d: calcularMediana(promos),
                }
            };
        }
    });
    
    return analise;
}

/**
 * Atualiza dashboard com dados específicos
 */
function updateDashboardWithData(resumo, dados) {
    // Limpa gráficos anteriores
    if (categoriaChart) { categoriaChart.destroy(); categoriaChart = null; }
    if (scoresChart) { scoresChart.destroy(); scoresChart = null; }
    if (vipChart) { vipChart.destroy(); vipChart = null; }
    if (vipScoresChart) { vipScoresChart.destroy(); vipScoresChart = null; }
    if (benchmarksChart) { benchmarksChart.destroy(); benchmarksChart = null; }
    
    // Calcula estatísticas e VIP específicos da região atual
    const estatisticas = calcularEstatisticas(dados);
    const analiseVIP = calcularAnaliseVIP(dados);
    
    // Adiciona ao resumo
    resumo.estatisticas = estatisticas;
    resumo.analise_vip = analiseVIP;
    
    // Salva resumo e dados atuais da região
    cachedResumoAtual = resumo;
    cachedDadosAtual = dados;
    
    // Atualiza visualizações
    updateKPIs(resumo);
    updateScores(resumo);
    updateCategorias(resumo.distribuicao_categorias);
    
    // Renderiza gráficos da aba ativa
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        renderTabContent(activeTab.id, resumo);
    }
    
    // Atualiza tabelas - calcula a partir dos dados filtrados
    const topJogadores = dados.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10);
    const jogadoresRiscoReceita = dados.filter(j => j.categoria === '🚨 Risco: Queda Receita').slice(0, 50);
    const jogadoresRiscoEngajamento = dados.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').slice(0, 50);
    
    updateTopJogadores(topJogadores);
    updateJogadoresRiscoReceita(jogadoresRiscoReceita);
    updateJogadoresRiscoEngajamento(jogadoresRiscoEngajamento);
    
    // Atualiza seção de clusters
    updateClustersSection(dados);
}

/**
 * Gerenciamento de Abas
 */
function showTab(tabId) {
    // Esconde todas as abas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active de todos os botões
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostra a aba selecionada
    document.getElementById(tabId).classList.add('active');
    
    // Ativa o botão
    document.getElementById('tab-btn-' + tabId.replace('tab-', '')).classList.add('active');
    
    // Renderiza gráficos específicos da aba (usando resumo atual da região)
    const resumoParaUsar = cachedResumoAtual || cachedResumo;
    if (resumoParaUsar) {
        renderTabContent(tabId, resumoParaUsar);
    }
}

/**
 * Renderiza conteúdo específico da aba
 */
function renderTabContent(tabId, resumo) {
    switch(tabId) {
        case 'tab-overview':
            if (resumo.distribuicao_categorias) {
                renderCategoriaChart(resumo.distribuicao_categorias);
                renderScoresChart(resumo);
            }
            break;
        case 'tab-executivo':
            renderResumoExecutivo();
            break;
        case 'tab-vip':
            if (resumo.analise_vip) {
                updateVIPSection(resumo.analise_vip);
            }
            break;
        case 'tab-players':
            // Tabelas já foram renderizadas
            break;
        case 'tab-clusters':
            // Clusters são atualizados via updateDashboardWithData
            break;
        case 'tab-benchmarks':
            if (resumo.estatisticas) {
                renderBenchmarksSection(resumo);
            }
            break;
    }
}

/**
 * Mostra/esconde elementos
 */
function showElement(id) {
    document.getElementById(id).classList.remove('hidden');
}

function hideElement(id) {
    document.getElementById(id).classList.add('hidden');
}

/**
 * Mostra loading
 */
function showLoading() {
    hideElement('empty-state');
    hideElement('dashboard');
    showElement('loading');
}

/**
 * Mostra dashboard
 */
function showDashboard() {
    const emptyState = document.getElementById('empty-state');
    const loading = document.getElementById('loading');
    const dashboard = document.getElementById('dashboard');
    
    hideElement('empty-state');
    hideElement('loading');
    
    // Mostra o dashboard removendo hidden e adicionando active
    dashboard.classList.remove('hidden');
    dashboard.classList.add('active');
    
    // Ativa a primeira aba (overview) se nenhuma estiver ativa
    const activeTab = document.querySelector('.tab-content.active');
    
    if (!activeTab) {
        showTab('tab-overview');
    }
}

/**
 * Formata número com 2 casas decimais
 */
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0,00';
    return parseFloat(num).toFixed(2).replace('.', ',');
}

/**
 * Atualiza KPI cards
 */
function updateKPIs(resumo) {
    document.getElementById('total-jogadores').textContent = resumo.total_jogadores;
    document.getElementById('percentual-ativos').textContent = formatNumber(resumo.percentual_ativos) + '%';
    document.getElementById('pontuacao-geral').textContent = formatNumber(resumo.media_pontuacao_geral);
    document.getElementById('percentual-elite').textContent = resumo.distribuicao_categorias.elite + '%';
}

/**
 * Atualiza cards de scores
 */
function updateScores(resumo) {
    // Atualiza valores (apenas Engajamento e Compras)
    document.getElementById('score-engajamento').textContent = formatNumber(resumo.media_saude_engajamento);
    document.getElementById('score-compras').textContent = formatNumber(resumo.media_saude_compras);
    
    // Atualiza barras de progresso
    document.getElementById('bar-engajamento').style.width = resumo.media_saude_engajamento + '%';
    document.getElementById('bar-compras').style.width = resumo.media_saude_compras + '%';
}

/**
 * Atualiza distribuição de categorias
 */
function updateCategorias(distribuicao) {
    // Mapeia TODAS as categorias novas para os 6 grupos do HTML
    const valores = {
        'elite': (distribuicao.elite || 0) + (distribuicao.oportunidade_vip || 0), // Elite + Oportunidade VIP
        'muito_bom': (distribuicao.vip_ativo || 0) + (distribuicao.bom || 0) + (distribuicao.oportunidade || 0) + (distribuicao.potencial || 0), // VIP Ativo + Bom + Oportunidade + Potencial
        'estavel': distribuicao.estavel || 0,
        'baixo': (distribuicao.atencao || 0) + (distribuicao.risco_alto || 0) + (distribuicao.churn_iminente || 0), // Atenção + Risco Alto + Churn
        'risco_receita': distribuicao.risco_receita || 0,
        'risco_engajamento': distribuicao.risco_engajamento || 0
    };
    
    // Calcula total para verificar
    const total = Object.values(valores).reduce((a, b) => a + b, 0);
    
    document.getElementById('cat-elite').textContent = valores.elite.toFixed(2) + '%';
    document.getElementById('cat-muito-bom').textContent = valores.muito_bom.toFixed(2) + '%';
    document.getElementById('cat-estavel').textContent = valores.estavel.toFixed(2) + '%';
    document.getElementById('cat-baixo').textContent = valores.baixo.toFixed(2) + '%';
    document.getElementById('cat-risco-receita').textContent = valores.risco_receita.toFixed(2) + '%';
    document.getElementById('cat-risco-engajamento').textContent = valores.risco_engajamento.toFixed(2) + '%';
    
    // Atualiza barras de progresso
    document.getElementById('progress-elite').style.width = valores.elite + '%';
    document.getElementById('progress-muito-bom').style.width = valores.muito_bom + '%';
    document.getElementById('progress-estavel').style.width = valores.estavel + '%';
    document.getElementById('progress-baixo').style.width = valores.baixo + '%';
    document.getElementById('progress-risco-receita').style.width = valores.risco_receita + '%';
    document.getElementById('progress-risco-engajamento').style.width = valores.risco_engajamento + '%';
}

/**
 * Renderiza gráfico de categorias (doughnut)
 */
function renderCategoriaChart(distribuicao) {
    const canvas = document.getElementById('categoriaChart');
    if (!canvas) return;
    
    // Verificação de segurança para distribuição
    if (!distribuicao) {
        distribuicao = {};
    }
    
    const ctx = canvas.getContext('2d');
    
    if (categoriaChart) {
        categoriaChart.destroy();
    }
    
    // Agrupa categorias para manter compatibilidade com o gráfico
    const valores = {
        elite: distribuicao.elite || 0,
        vip_ativo: (distribuicao.vip_ativo || 0) + (distribuicao.bom || 0),
        estavel: distribuicao.estavel || 0,
        atencao: (distribuicao.atencao || 0) + (distribuicao.risco_alto || 0) + (distribuicao.churn_iminente || 0),
        risco_receita: distribuicao.risco_receita || 0,
        risco_engajamento: distribuicao.risco_engajamento || 0
    };
    
    categoriaChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['⭐ Elite', '🏆 VIP Ativo/Bom', '📊 Estável', '⚠️ Atenção/Risco', '🚨 Risco: Queda Receita', '🚨 Risco: Queda Engajamento'],
            datasets: [{
                data: [
                    valores.elite,
                    valores.vip_ativo,
                    valores.estavel,
                    valores.atencao,
                    valores.risco_receita,
                    valores.risco_engajamento
                ],
                backgroundColor: [
                    '#fbbf24',
                    '#34d399',
                    '#60a5fa',
                    '#fb923c',
                    '#ef4444',
                    '#f97316'
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Renderiza gráfico de scores (bar)
 */
function renderScoresChart(resumo) {
    const canvas = document.getElementById('scoresChart');
    if (!canvas) return;
    
    // Verificação de segurança para resumo
    if (!resumo) {
        resumo = {};
    }
    
    const ctx = canvas.getContext('2d');
    
    if (scoresChart) {
        scoresChart.destroy();
    }
    
    scoresChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Engajamento (30%)', 'Compras (70%)', 'Score Geral'],
            datasets: [{
                label: 'Média de Saúde',
                data: [
                    resumo.media_saude_engajamento,
                    resumo.media_saude_compras,
                    resumo.media_pontuacao_geral
                ],
                backgroundColor: [
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(99, 102, 241, 0.8)'
                ],
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Score: ' + formatNumber(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Retorna classe do badge baseado na categoria
 */
function getBadgeClass(categoria) {
    const map = {
        '⭐ Elite': 'badge-elite',
        '🏆 VIP Ativo': 'badge-muito-bom',
        '📈 Bom': 'badge-muito-bom',
        '📊 Estável': 'badge-estavel',
        '⚠️ Atenção': 'badge-baixo',
        '🚨 Risco Alto': 'badge-risco',
        '💎 Churn Iminente': 'badge-risco',
        '🚨 Risco: Queda Receita': 'badge-risco-receita',
        '🚨 Risco: Queda Engajamento': 'badge-risco-engajamento',
        '💰 Oportunidade': 'badge-muito-bom',
        '💰 Oportunidade VIP': 'badge-elite',
        '🎯 Potencial': 'badge-estavel'
    };
    return map[categoria] || 'badge-estavel';
}

/**
 * Atualiza tabela de top jogadores
 */
function updateTopJogadores(topJogadores) {
    const tbody = document.getElementById('top-jogadores-body');
    tbody.innerHTML = '';
    
    topJogadores.forEach((jogador, index) => {
        const row = document.createElement('tr');
        const playerId = jogador.player_id || jogador[jogador.columns?.[0] || Object.keys(jogador)[0]];
        
        // Monta badge VIP se existir
        let vipBadge = '';
        if (jogador.vip_nome) {
            vipBadge = `<span class="badge" style="background: ${jogador.vip_cor}20; color: ${jogador.vip_cor};">${jogador.vip_icone} ${jogador.vip_nome}</span>`;
        } else if (jogador.nivel_vip) {
            vipBadge = `<span class="badge">VIP ${jogador.nivel_vip}</span>`;
        }
        
        row.innerHTML = `
            <td><strong>#${index + 1}</strong></td>
            <td>${playerId} ${vipBadge}</td>
            <td>${formatNumber(jogador.score_login || 0)}</td>
            <td>${formatNumber(jogador.score_engajamento || 0)}</td>
            <td>${formatNumber(jogador.score_compras || 0)}</td>
            <td><strong>${formatNumber(jogador.score_geral || 0)}</strong></td>
            <td><span class="badge ${getBadgeClass(jogador.categoria)}">${jogador.categoria}</span></td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Atualiza tabela de jogadores em risco - Queda em Receita
 */
function updateJogadoresRiscoReceita(jogadores) {
    const tbody = document.getElementById('risco-receita-body');
    tbody.innerHTML = '';
    
    if (!jogadores || jogadores.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" style="text-align: center; color: #64748b;">Nenhum jogador em risco de queda em receita</td>';
        tbody.appendChild(row);
        return;
    }
    
    jogadores.forEach(jogador => {
        const row = document.createElement('tr');
        const playerId = jogador.player_id || Object.values(jogador)[0];
        
        row.innerHTML = `
            <td>${playerId}</td>
            <td>${formatNumber(jogador.score_geral || 0)}</td>
            <td>${formatNumber(jogador.score_engajamento || 0)}</td>
            <td>${formatNumber(jogador.score_compras || 0)}</td>
            <td><span class="badge badge-risco-receita">Oferta personalizada</span></td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Atualiza tabela de jogadores em risco - Queda em Engajamento
 */
function updateJogadoresRiscoEngajamento(jogadores) {
    const tbody = document.getElementById('risco-engajamento-body');
    tbody.innerHTML = '';
    
    if (!jogadores || jogadores.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" style="text-align: center; color: #64748b;">Nenhum jogador em risco de queda em engajamento</td>';
        tbody.appendChild(row);
        return;
    }
    
    jogadores.forEach(jogador => {
        const row = document.createElement('tr');
        const playerId = jogador.player_id || Object.values(jogador)[0];
        
        row.innerHTML = `
            <td>${playerId}</td>
            <td>${formatNumber(jogador.score_geral || 0)}</td>
            <td>${formatNumber(jogador.score_engajamento || 0)}</td>
            <td>${formatNumber(jogador.score_compras || 0)}</td>
            <td><span class="badge badge-risco-engajamento">Campanha de reengajamento</span></td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Toggle expand/colapsar cluster
 */
function toggleCluster(clusterId) {
    const content = document.getElementById(`cluster-${clusterId}-content`);
    const toggle = document.getElementById(`cluster-${clusterId}-toggle`);
    
    if (content.classList.contains('open')) {
        content.classList.remove('open');
        toggle.classList.remove('open');
    } else {
        content.classList.add('open');
        toggle.classList.add('open');
    }
}

/**
 * Toggle da seção de pontuação
 */
function togglePontuacao() {
    const content = document.getElementById('pontuacao-content');
    const toggle = document.getElementById('pontuacao-toggle');
    
    if (content.classList.contains('open')) {
        content.classList.remove('open');
        toggle.classList.remove('open');
    } else {
        content.classList.add('open');
        toggle.classList.add('open');
    }
}

/**
 * Atualiza tabela de cluster com jogadores
 */
// Cache para tendências de jogadores (evita múltiplas requisições)
const playerTendenciaCache = {};

/**
 * Busca a tendência do jogador (subiu, desceu, manteve, novo)
 * Agora considera TODO o histórico (90 dias) para determinar se é novo
 */
async function getPlayerTendencia(playerId) {
    // Verifica cache
    if (playerTendenciaCache[playerId] !== undefined) {
        return playerTendenciaCache[playerId];
    }
    
    try {
        // Busca 90 dias de histórico para ter certeza se é novo ou não
        const response = await fetch(`/api/player/${playerId}/evolucao?dias=90`);
        const data = await response.json();
        
        if (!data.success || !data.evolucao || !data.evolucao.evolucao) {
            playerTendenciaCache[playerId] = null;
            return null;
        }
        
        const evolucao = data.evolucao.evolucao;
        const totalRegistros = data.evolucao.total_registros || evolucao.length;
        
        console.log(`[DEBUG] Jogador ${playerId}: ${totalRegistros} registros no histórico`);
        
        // Se só tem 1 registro em TODO o histórico, é novo
        if (totalRegistros <= 1) {
            console.log(`[DEBUG] Jogador ${playerId}: NOVO (apenas 1 registro)`);
            playerTendenciaCache[playerId] = 'novo';
            return 'novo';
        }
        
        // Pega primeiro e último registro para comparar
        const primeiro = evolucao[0];  // Mais antigo
        const ultimo = evolucao[evolucao.length - 1];  // Mais recente
        
        console.log(`[DEBUG] Jogador ${playerId}: Primeiro=${primeiro.categoria}, Último=${ultimo.categoria}`);
        
        // Determina a ordem dos clusters (do melhor para o pior)
        const ordemClusters = [
            '⭐ Elite', '🏆 VIP Ativo', '📈 Bom', '📊 Estável', 
            '⚠️ Atenção', '🚨 Risco Alto', '🚨 Risco: Queda Receita', 
            '🚨 Risco: Queda Engajamento', '💎 Churn Iminente',
            '💰 Oportunidade VIP', '💰 Oportunidade', '🎯 Potencial'
        ];
        
        const idxPrimeiro = ordemClusters.indexOf(primeiro.categoria);
        const idxUltimo = ordemClusters.indexOf(ultimo.categoria);
        
        let tendencia = 'manteve';
        if (idxUltimo < idxPrimeiro) {
            tendencia = 'subiu';
            console.log(`[DEBUG] Jogador ${playerId}: SUBIU de ${primeiro.categoria} para ${ultimo.categoria}`);
        } else if (idxUltimo > idxPrimeiro) {
            tendencia = 'desceu';
            console.log(`[DEBUG] Jogador ${playerId}: DESCEU de ${primeiro.categoria} para ${ultimo.categoria}`);
        } else {
            console.log(`[DEBUG] Jogador ${playerId}: MANTEVE em ${ultimo.categoria}`);
        }
        
        playerTendenciaCache[playerId] = tendencia;
        return tendencia;
        
    } catch (error) {
        console.error('Erro ao buscar tendência:', error);
        playerTendenciaCache[playerId] = null;
        return null;
    }
}

/**
 * Retorna o HTML da tag de tendência
 */
function getTendenciaTag(tendencia) {
    const tags = {
        'subiu': '<span class="tendencia-tag subiu" title="Subiu de cluster">▲</span>',
        'desceu': '<span class="tendencia-tag desceu" title="Desceu de cluster">▼</span>',
        'manteve': '<span class="tendencia-tag manteve" title="Manteve o cluster">~</span>',
        'novo': '<span class="tendencia-tag novo" title="Jogador novo">*</span>'
    };
    return tags[tendencia] || '';
}

function updateClusterTable(clusterId, jogadores) {
    const tbody = document.getElementById(`cluster-${clusterId}-body`);
    const countEl = document.getElementById(`cluster-${clusterId}-count`);
    
    // Atualiza contador
    const total = jogadores ? jogadores.length : 0;
    countEl.textContent = `${total} jogador${total !== 1 ? 'es' : ''}`;
    
    tbody.innerHTML = '';
    
    if (!jogadores || jogadores.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" style="text-align: center; color: #64748b; padding: 20px;">Nenhum jogador nesta categoria</td>`;
        tbody.appendChild(row);
        return;
    }
    
    // Processa jogadores de forma assíncrona para buscar tendências
    jogadores.forEach(async (jogador, index) => {
        const row = document.createElement('tr');
        const playerId = jogador.player_id || jogador.id || Object.values(jogador)[0];
        
        // Busca tendência
        const tendencia = await getPlayerTendencia(playerId);
        const tendenciaTag = getTendenciaTag(tendencia);
        
        // Determina o nível VIP
        let vipLevel = jogador.nivel_vip || jogador.vip_level || '-';
        let vipBadge = '';
        if (vipLevel !== '-') {
            const coresVIP = {
                1: '#9B59B6', 2: '#F39C12', 3: '#27AE60', 4: '#E74C3C', 5: '#3498DB'
            };
            const nomesVIP = {
                1: 'Ametista', 2: 'Topázio', 3: 'Esmeralda', 4: 'Opala', 5: 'Berilo'
            };
            const cor = coresVIP[vipLevel] || '#64748b';
            const nome = nomesVIP[vipLevel] || `VIP ${vipLevel}`;
            vipBadge = `<span class="badge" style="background: ${cor}20; color: ${cor}; border: 1px solid ${cor}40;">${nome}</span>`;
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${playerId} ${tendenciaTag}</td>
            <td>${formatNumber(jogador.score_geral || 0)}</td>
            <td>${formatNumber(jogador.score_engajamento || 0)}</td>
            <td>${formatNumber(jogador.score_compras || 0)}</td>
            <td>${vipBadge}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Carrega todos os jogadores do histórico (incluindo ausentes no dia atual)
 * e atualiza as tabelas de clusters
 */
async function carregarClustersComHistorico() {
    try {
        console.log('[DEBUG] Carregando clusters com histórico acumulado...');
        
        // Busca todos os jogadores com seu registro mais recente (até 90 dias)
        const response = await fetch('/api/players/ultimos?dias=90');
        const data = await response.json();
        
        if (!data.success) {
            console.error('[DEBUG] Erro ao carregar histórico:', data.message);
            return;
        }
        
        console.log(`[DEBUG] Total de jogadores únicos: ${data.total}`);
        
        const jogadores = data.jogadores || [];
        
        // Filtra top 50 de cada categoria
        const elite = jogadores.filter(j => j.categoria === '⭐ Elite').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        const vipAtivo = jogadores.filter(j => j.categoria === '🏆 VIP Ativo').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        const estavel = jogadores.filter(j => j.categoria === '📊 Estável').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        const atencao = jogadores.filter(j => j.categoria === '⚠️ Atenção').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        const riscoReceita = jogadores.filter(j => j.categoria === '🚨 Risco: Queda Receita').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        const riscoEngajamento = jogadores.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
        
        // Atualiza tabelas
        updateClusterTable('elite', elite);
        updateClusterTable('muito-bom', vipAtivo);
        updateClusterTable('estavel', estavel);
        updateClusterTable('baixo', atencao);
        updateClusterTable('risco-receita', riscoReceita);
        updateClusterTable('risco-engajamento', riscoEngajamento);
        
    } catch (error) {
        console.error('[DEBUG] Erro ao carregar clusters:', error);
    }
}

/**
 * Atualiza todas as tabelas de clusters
 */
function updateClustersSection(dados) {
    // Agora usa a função que carrega do histórico acumulado
    carregarClustersComHistorico();
}

/**
 * Atualiza todo o dashboard com os dados
 */
function updateDashboard(resumo, dadosCompletos) {
    // Guarda em cache
    cachedResumo = resumo;
    if (dadosCompletos) {
        cachedDataCompleto = dadosCompletos;
    }
    
    // Se temos dados completos e filtros selecionados, aplica-os
    let dadosParaMostrar = dadosCompletos;
    let resumoParaMostrar = resumo;
    
    if (cachedDataCompleto && (regiaoAtual !== 'all' || vipAtual !== 'all')) {
        dadosParaMostrar = filtrarDados(cachedDataCompleto, regiaoAtual, vipAtual);
        resumoParaMostrar = gerarResumoFiltrado(dadosParaMostrar, resumo, regiaoAtual);
    }
    
    // Calcula estatísticas e VIP específicos
    if (dadosParaMostrar) {
        resumoParaMostrar.estatisticas = calcularEstatisticas(dadosParaMostrar);
        resumoParaMostrar.analise_vip = calcularAnaliseVIP(dadosParaMostrar);
    }
    
    // Salva resumo e dados atuais
    cachedResumoAtual = resumoParaMostrar;
    cachedDadosAtual = dadosParaMostrar;
    
    // Atualiza Visão Geral
    updateKPIs(resumoParaMostrar);
    updateScores(resumoParaMostrar);
    updateCategorias(resumoParaMostrar.distribuicao_categorias);
    
    // Renderiza gráficos da aba ativa (com delay para garantir visibilidade do dashboard)
    const activeTab = document.querySelector('.tab-content.active');
    setTimeout(() => {
        if (activeTab) {
            renderTabContent(activeTab.id, resumoParaMostrar);
        } else {
            renderCategoriaChart(resumoParaMostrar.distribuicao_categorias);
            renderScoresChart(resumoParaMostrar);
        }
    }, 100);
    
    // Atualiza tabelas - calcula a partir dos dados filtrados (com verificação de segurança)
    if (dadosParaMostrar && Array.isArray(dadosParaMostrar)) {
        const topJogadores = dadosParaMostrar.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10);
        const jogadoresRiscoReceita = dadosParaMostrar.filter(j => j.categoria === '🚨 Risco: Queda Receita').slice(0, 50);
        const jogadoresRiscoEngajamento = dadosParaMostrar.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').slice(0, 50);
        
        updateTopJogadores(topJogadores);
        updateJogadoresRiscoReceita(jogadoresRiscoReceita);
        updateJogadoresRiscoEngajamento(jogadoresRiscoEngajamento);
        
        // Atualiza seção de clusters
        updateClustersSection(dadosParaMostrar);
    }
    
    if (resumoParaMostrar.analise_vip) {
        updateVIPSection(resumoParaMostrar.analise_vip);
    }
}

/**
 * Handle file upload
 */
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) {
        return;
    }
    
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const isValid = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!isValid) {
        alert('Por favor, selecione um arquivo CSV ou Excel válido (.csv, .xlsx, .xls)');
        return;
    }
    
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao processar arquivo');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Busca dados completos
            try {
                const dadosResponse = await fetch('/api/dados');
                if (!dadosResponse.ok) {
                    throw new Error('Falha ao buscar dados completos');
                }
                const dadosData = await dadosResponse.json();
                
                updateDashboard(data.resumo, dadosData.dados_completos);
            } catch (dadosError) {
                // Mesmo sem dados completos, mostra o dashboard com o resumo
                updateDashboard(data.resumo, []);
            }
            showDashboard();
        } else {
            throw new Error(data.message || 'Erro desconhecido');
        }
        
    } catch (error) {
        alert('Erro: ' + error.message);
        hideElement('loading');
        showElement('empty-state');
    }
    
    // Limpa o input
    event.target.value = '';
}

/**
 * Carrega dados de exemplo
 */
async function loadSampleData() {
    showLoading();
    
    try {
        const response = await fetch('/api/sample');
        
        if (!response.ok) {
            throw new Error('Erro ao carregar dados de exemplo');
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateDashboard(data.resumo);
            showDashboard();
        } else {
            throw new Error(data.message || 'Erro desconhecido');
        }
        
    } catch (error) {
        alert('Erro: ' + error.message);
        hideElement('loading');
        showElement('empty-state');
    }
}

/**
 * Exporta para CSV
 */
async function exportCSV() {
    try {
        const response = await fetch('/api/export/csv');
        
        if (!response.ok) {
            throw new Error('Nenhum dado para exportar');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'health_score_resultado.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

/**
 * Exporta para Excel
 */
async function exportExcel() {
    try {
        const response = await fetch('/api/export/excel');
        
        if (!response.ok) {
            throw new Error('Nenhum dado para exportar');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'health_score_resultado.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

/**
 * Atualiza a seção de análise VIP
 */
function updateVIPSection(analiseVip) {
    const vipGrid = document.getElementById('vip-grid');
    if (!vipGrid) return;
    
    // Limpa conteúdo anterior
    vipGrid.innerHTML = '';
    
    // Ordena por nível VIP (1 a 5)
    const vips = Object.values(analiseVip).sort((a, b) => a.nivel - b.nivel);
    
    vips.forEach(vip => {
        const card = document.createElement('div');
        card.className = `vip-card vip-${vip.nivel}`;
        card.innerHTML = `
            <div class="vip-header">
                <span class="vip-icon">${vip.icone}</span>
                <span class="vip-nome">${vip.nome}</span>
            </div>
            <div class="vip-quantidade">${vip.quantidade} <small style="font-size: 12px; color: #64748b;">(${vip.percentual}%)</small></div>
            <div class="vip-stats">
                <div class="vip-stat">
                    <span class="vip-stat-label">Score Geral:</span>
                    <span class="vip-stat-value">${formatNumber(vip.score_geral_medio)}</span>
                </div>
                <div class="vip-stat">
                    <span class="vip-stat-label">Login:</span>
                    <span class="vip-stat-value">${formatNumber(vip.score_login_medio)}</span>
                </div>
                <div class="vip-stat">
                    <span class="vip-stat-label">Engajamento:</span>
                    <span class="vip-stat-value">${formatNumber(vip.score_engajamento_medio)}</span>
                </div>
                <div class="vip-stat">
                    <span class="vip-stat-label">Compras:</span>
                    <span class="vip-stat-value">${formatNumber(vip.score_compras_medio)}</span>
                </div>
                <div class="vip-stat">
                    <span class="vip-stat-label">% Ativos:</span>
                    <span class="vip-stat-value">${formatNumber(vip.percentual_ativos)}%</span>
                </div>
            </div>
        `;
        vipGrid.appendChild(card);
    });
    
    // Renderiza gráficos apenas se estiverem visíveis
    if (document.getElementById('tab-vip').classList.contains('active')) {
        setTimeout(() => {
            renderVIPChart(vips);
            renderVIPScoresChart(vips);
        }, 100);
    }
}

/**
 * Renderiza gráfico de distribuição VIP
 */
function renderVIPChart(vips) {
    const ctx = document.getElementById('vipChart');
    if (!ctx) return;
    
    if (vipChart) {
        vipChart.destroy();
    }
    
    vipChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: vips.map(v => `${v.icone} ${v.nome}`),
            datasets: [{
                data: vips.map(v => v.quantidade),
                backgroundColor: vips.map(v => v.cor),
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Renderiza gráfico de scores médios por VIP
 */
function renderVIPScoresChart(vips) {
    const ctx = document.getElementById('vipScoresChart');
    if (!ctx) return;
    
    if (vipScoresChart) {
        vipScoresChart.destroy();
    }
    
    vipScoresChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: vips.map(v => v.nome),
            datasets: [
                {
                    label: 'Score Geral',
                    data: vips.map(v => v.score_geral_medio),
                    backgroundColor: vips.map(v => v.cor),
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Renderiza seção de Benchmarks
 */
function renderBenchmarksSection(resumo) {
    const grid = document.getElementById('benchmarks-grid');
    if (!grid) return;
    
    const stats = resumo.estatisticas;
    const params = resumo.parametros_calculados || {};
    
    const benchmarks = [
        { icon: '🎯', title: 'Torneios/dia', value: (stats.media_torneios_3d / 3).toFixed(2), subtitle: `Média 3d: ${stats.media_torneios_3d}` },
        { icon: '🏃', title: 'Maratonas/dia', value: (stats.media_maratonas_3d / 3).toFixed(2), subtitle: `Média 3d: ${stats.media_maratonas_3d}` },
        { icon: '✅', title: 'Missões/dia', value: (stats.media_missoes_3d / 3).toFixed(2), subtitle: `Média 3d: ${stats.media_missoes_3d}` },
        { icon: '🎁', title: 'Promos/dia', value: (stats.media_promos_3d / 3).toFixed(2), subtitle: `Média 3d: ${stats.media_promos_3d}` },
    ];
    
    grid.innerHTML = benchmarks.map(b => `
        <div class="benchmark-card">
            <div class="benchmark-header">
                <div class="benchmark-icon">${b.icon}</div>
                <span class="benchmark-title">${b.title}</span>
            </div>
            <div class="benchmark-value">${b.value}</div>
            <div class="benchmark-subtitle">${b.subtitle}</div>
        </div>
    `).join('');
    
    // Renderiza gráfico de benchmarks
    const ctx = document.getElementById('benchmarksChart');
    if (ctx) {
        if (benchmarksChart) benchmarksChart.destroy();
        
        benchmarksChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Torneios', 'Maratonas', 'Missões', 'Promos'],
                datasets: [
                    {
                        label: 'Média 3d',
                        data: [stats.media_torneios_3d, stats.media_maratonas_3d, stats.media_missoes_3d, stats.media_promos_3d],
                        backgroundColor: 'rgba(99, 102, 241, 0.8)',
                        borderRadius: 6
                    },
                    {
                        label: 'Mediana',
                        data: [stats.mediana_torneios_3d, stats.mediana_maratonas_3d, stats.mediana_missoes_3d, stats.mediana_promos_3d],
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('Health Score Dashboard v2.3 - Inicializado');
    
    // Adiciona listener para teclas de navegação
    document.addEventListener('keydown', function(e) {
        // Regiões (Ctrl + letra)
        if (e.ctrlKey && !e.altKey) {
            if (e.key === 'a' || e.key === '0') showRegion('all');
            if (e.key === 'e') showRegion('es');
            if (e.key === 'b') showRegion('br');
            if (e.key === 'i') showRegion('int');
            
            // VIP (Ctrl + Alt + número)
            if (e.key === 'v') showVIP('all');
        }
        // VIP (Alt + número 1-5)
        else if (e.altKey) {
            if (e.key === '1') showVIP('1');
            if (e.key === '2') showVIP('2');
            if (e.key === '3') showVIP('3');
            if (e.key === '4') showVIP('4');
            if (e.key === '5') showVIP('5');
            if (e.key === '0' || e.key === 'v') showVIP('all');
        }
        // Abas (1-5)
        else {
            if (e.key === '1') showTab('tab-overview');
            if (e.key === '2') showTab('tab-vip');
            if (e.key === '3') showTab('tab-players');
            if (e.key === '4') showTab('tab-clusters');
            if (e.key === '5') showTab('tab-benchmarks');
        }
    });
});


/* ========================================
   RESUMO EXECUTIVO - FUNÇÕES
   ======================================== */

let execClustersChart = null;
let execEvolucaoChart = null;

/**
 * Salva snapshot do dia no histórico
 */
async function salvarSnapshot() {
    try {
        const dataInput = document.getElementById('snapshot-data');
        let dataSnapshot = dataInput.value; // Data no formato YYYY-MM-DD
        
        // Se não houver data selecionada, usa a data atual no formato YYYY-MM-DD
        if (!dataSnapshot) {
            const hoje = new Date();
            const ano = hoje.getFullYear();
            const mes = String(hoje.getMonth() + 1).padStart(2, '0');
            const dia = String(hoje.getDate()).padStart(2, '0');
            dataSnapshot = `${ano}-${mes}-${dia}`;
        }
        
        const response = await fetch('/api/historico/salvar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filtros: {
                    regiao: regiaoAtual,
                    vip: vipAtual
                },
                data: dataSnapshot || null // Se vazio, backend usa data atual
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Dados salvos! Data: ' + data.data, 'success');
            carregarHistorico();
            dataInput.value = ''; // Limpa o campo
        } else {
            showToast('Erro ao salvar: ' + data.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao salvar dados', 'error');
    }
}

/**
 * Deleta um snapshot pelo ID
 */
async function deletarSnapshot(snapshotId) {
    if (!confirm('Tem certeza que deseja excluir este registro?')) {
        return;
    }
    
    console.log(`%c[DEBUG] Iniciando delete - snapshot ID: ${snapshotId}`, 'color: #3b82f6; font-weight: bold');
    
    try {
        const url = `/api/historico/${snapshotId}`;
        console.log(`[DEBUG] URL: ${url}`);
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log(`[DEBUG] Response status: ${response.status} ${response.statusText}`);
        console.log(`[DEBUG] Response headers:`, [...response.headers.entries()]);
        
        let data;
        try {
            data = await response.json();
            console.log(`[DEBUG] Response data:`, data);
        } catch (jsonError) {
            console.error(`[DEBUG] Erro ao parsear JSON:`, jsonError);
            const text = await response.text();
            console.log(`[DEBUG] Response text:`, text);
            throw new Error('Resposta inválida do servidor');
        }
        
        if (response.ok && data.success) {
            console.log(`%c[DEBUG] Delete bem-sucedido!`, 'color: #10b981; font-weight: bold');
            showToast('Registro excluído com sucesso!', 'success');
            carregarHistorico();
        } else {
            console.error(`%c[DEBUG] Erro na resposta:`, 'color: #ef4444;', data);
            showToast('Erro ao excluir: ' + (data.message || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error(`%c[DEBUG] Erro catch:`, 'color: #ef4444; font-weight: bold', error);
        showToast('Erro ao excluir registro: ' + error.message, 'error');
    }
}

/**
 * Carrega histórico com filtros
 */
async function carregarHistorico() {
    try {
        const regiao = document.getElementById('filtro-hist-regiao').value;
        const vip = document.getElementById('filtro-hist-vip').value;
        const dias = document.getElementById('filtro-hist-dias').value;
        
        const response = await fetch(`/api/historico?regiao=${regiao}&vip=${vip}&dias=${dias}`);
        const data = await response.json();
        
        if (data.success) {
            atualizarTabelaHistorico(data.historico);
            
            // Se tiver dados, atualiza os gráficos
            if (data.historico.length > 0) {
                atualizarKPIsExecutivo(data.historico);
                atualizarGraficoEvolucao(data.historico);
                const ultimoDia = data.historico[data.historico.length - 1];
                const penultimoDia = data.historico.length > 1 ? data.historico[data.historico.length - 2] : null;
                atualizarTabelaClusters(ultimoDia, penultimoDia);
                
                // Sempre renderiza o gráfico de clusters
                atualizarGraficoClusters(ultimoDia);
            }
        }
    } catch (error) {
    }
}

/**
 * Atualiza KPIs do Resumo Executivo
 */
function atualizarKPIsExecutivo(historico) {
    if (historico.length === 0) return;
    
    // Pega o último (mais recente) e o penúltimo
    const atual = historico[historico.length - 1];
    const anterior = historico.length > 1 ? historico[historico.length - 2] : null;
    
    // Atualiza valores
    document.getElementById('exec-total-jogadores').textContent = atual.total_jogadores.toLocaleString();
    document.getElementById('exec-percentual-ativos').textContent = atual.percentual_ativos.toFixed(1) + '%';
    document.getElementById('exec-score-geral').textContent = atual.media_score_geral.toFixed(1);
    document.getElementById('exec-score-compras').textContent = atual.media_score_compras.toFixed(1);
    document.getElementById('exec-score-engajamento').textContent = atual.media_score_engajamento.toFixed(1);
    
    // Atualiza variações
    if (anterior) {
        atualizarVariacao('exec-var-total', atual.total_jogadores - anterior.total_jogadores, 0);
        atualizarVariacao('exec-var-ativos', atual.percentual_ativos - anterior.percentual_ativos, 1);
        atualizarVariacao('exec-var-score', atual.media_score_geral - anterior.media_score_geral, 1);
        atualizarVariacao('exec-var-compras', atual.media_score_compras - anterior.media_score_compras, 1);
        atualizarVariacao('exec-var-engajamento', atual.media_score_engajamento - anterior.media_score_engajamento, 1);
    }
}

/**
 * Atualiza elemento de variação
 */
function atualizarVariacao(elementId, valor, decimais) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    const sinal = valor > 0 ? '+' : '';
    const cor = valor > 0 ? 'positivo' : (valor < 0 ? 'negativo' : 'neutro');
    const icone = valor > 0 ? '▲' : (valor < 0 ? '▼' : '–');
    
    el.className = 'kpi-variacao ' + cor;
    el.innerHTML = `${icone} ${sinal}${valor.toFixed(decimais)}`;
}

/**
 * Atualiza tabela de clusters com tendência
 */
function atualizarTabelaClusters(ultimoDia, penultimoDia) {
    const tbody = document.getElementById('exec-clusters-body');
    if (!tbody) return;
    
    const clusters = ultimoDia.clusters || {};
    const total = ultimoDia.total_jogadores || 0;
    
    // Clusters do dia anterior (para tendência)
    const clustersAnterior = penultimoDia ? (penultimoDia.clusters || {}) : null;
    
    // Agrupa as categorias nos 6 grupos da tabela
    const grupos = {
        'Elite': (clusters['⭐ Elite'] || 0),
        'Muito bom': (clusters['🏆 VIP Ativo'] || 0),
        'Estável': clusters['📊 Estável'] || 0,
        'Baixo': (clusters['⚠️ Atenção'] || 0),
        'Risco: Queda em Receita': clusters['🚨 Risco: Queda Receita'] || 0,
        'Risco: Queda em Engajamento': clusters['🚨 Risco: Queda Engajamento'] || 0
    };
    
    // Grupos do dia anterior
    const gruposAnterior = clustersAnterior ? {
        'Elite': (clustersAnterior['⭐ Elite'] || 0),
        'Muito bom': (clustersAnterior['🏆 VIP Ativo'] || 0),
        'Estável': clustersAnterior['📊 Estável'] || 0,
        'Baixo': (clustersAnterior['⚠️ Atenção'] || 0),
        'Risco: Queda em Receita': clustersAnterior['🚨 Risco: Queda Receita'] || 0,
        'Risco: Queda em Engajamento': clustersAnterior['🚨 Risco: Queda Engajamento'] || 0
    } : null;
    
    const grupoInfo = {
        'Elite': { icone: '⭐', cor: '#fbbf24' },
        'Muito bom': { icone: '📈', cor: '#34d399' },
        'Estável': { icone: '📊', cor: '#60a5fa' },
        'Baixo': { icone: '⚠️', cor: '#fb923c' },
        'Risco: Queda em Receita': { icone: '🚨', cor: '#ef4444' },
        'Risco: Queda em Engajamento': { icone: '📉', cor: '#f59e0b' }
    };
    
    let html = '';
    for (const [nome, qtd] of Object.entries(grupos)) {
        const info = grupoInfo[nome];
        const pct = total > 0 ? (qtd / total * 100).toFixed(1) : 0;
        
        // Calcula tendência
        let tendencia = '-';
        if (gruposAnterior) {
            const qtdAnterior = gruposAnterior[nome] || 0;
            const diff = qtd - qtdAnterior;
            if (diff > 0) {
                tendencia = `<span style="color: #10b981">▲ +${diff}</span>`;
            } else if (diff < 0) {
                tendencia = `<span style="color: #ef4444">▼ ${diff}</span>`;
            } else {
                tendencia = `<span style="color: #64748b">– 0</span>`;
            }
        }
        
        html += `
            <tr>
                <td><span style="color: ${info.cor}">${info.icone}</span> ${nome}</td>
                <td>${qtd.toLocaleString()}</td>
                <td>${pct}%</td>
                <td>${tendencia}</td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
}

/**
 * Atualiza tabela de histórico
 */
function atualizarTabelaHistorico(historico) {
    const tbody = document.getElementById('historico-body');
    if (!tbody) return;
    
    // Inverte para mostrar do mais novo para o mais antigo
    const historicoInvertido = [...historico].reverse();
    
    let html = '';
    for (const dia of historicoInvertido.slice(0, 10)) {
        const clusters = dia.clusters;
        const riscos = (clusters['🚨 Risco: Queda Receita'] || 0) + (clusters['🚨 Risco: Queda Engajamento'] || 0);
        
        html += `
            <tr>
                <td>#${dia.id}</td>
                <td>${formatarDataCompleta(dia.data)}</td>
                <td>${dia.total_jogadores.toLocaleString()}</td>
                <td>${dia.percentual_ativos.toFixed(1)}%</td>
                <td>${dia.media_score_geral.toFixed(1)}</td>
                <td>${(clusters['⭐ Elite'] || 0).toLocaleString()}</td>
                <td>${riscos.toLocaleString()}</td>
                <td>
                    <button class="btn-delete" onclick="deletarSnapshot(${dia.id})" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html || '<tr><td colspan="8" style="text-align:center">Nenhum histórico encontrado</td></tr>';
}

/**
 * Atualiza gráfico de evolução
 */
function atualizarGraficoEvolucao(historico) {
    const ctx = document.getElementById('execEvolucaoChart');
    if (!ctx) return;
    
    if (execEvolucaoChart) {
        execEvolucaoChart.destroy();
    }
    
    // Dados já vêm ordenados do mais antigo para o mais novo (do backend)
    const dados = historico.slice(-15); // Pega os últimos 15 registros
    const labels = dados.map(d => {
        const [ano, mes, dia] = d.data.split('-');
        return `${dia}/${mes}`;
    });
    
    execEvolucaoChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Score Geral',
                    data: dados.map(d => d.media_score_geral),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '% Ativos',
                    data: dados.map(d => d.percentual_ativos),
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                },
                y1: {
                    position: 'right',
                    grid: { drawOnChartArea: false }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Atualiza gráfico de clusters
 */
function atualizarGraficoClusters(ultimoDia) {
    const ctx = document.getElementById('execClustersChart');
    if (!ctx) return;
    
    // Verifica se o canvas está visível
    if (ctx.offsetParent === null) {
        // Canvas não está visível, agenda para atualizar quando estiver
        setTimeout(() => atualizarGraficoClusters(ultimoDia), 500);
        return;
    }
    
    if (execClustersChart) {
        execClustersChart.destroy();
        execClustersChart = null;
    }
    
    const clusters = ultimoDia.clusters || {};
    const total = ultimoDia.total_jogadores || 0;
    
    // Dados do histórico já vêm agrupados em 6 categorias
    const dadosAgrupados = [
        clusters['⭐ Elite'] || 0,
        clusters['🏆 VIP Ativo'] || 0,
        clusters['📊 Estável'] || 0,
        clusters['⚠️ Atenção'] || 0,
        clusters['🚨 Risco: Queda Receita'] || 0,
        clusters['🚨 Risco: Queda Engajamento'] || 0
    ];
    
    execClustersChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['⭐ Elite', '🏆 VIP Ativo/Bom', '📊 Estável', '⚠️ Atenção/Risco', '🚨 Risco Receita', '🚨 Risco Engajamento'],
            datasets: [{
                data: dadosAgrupados,
                backgroundColor: [
                    '#fbbf24',
                    '#34d399',
                    '#60a5fa',
                    '#fb923c',
                    '#ef4444',
                    '#f59e0b'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const pct = total > 0 ? (val / total * 100).toFixed(1) : 0;
                            return `${context.label}: ${val.toLocaleString()} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Mostra toast notification
 */
function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    
    const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
    toast.innerHTML = `<span>${icon}</span> ${message}`;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Renderiza conteúdo da aba Resumo Executivo quando ativada
 */
function renderResumoExecutivo() {
    carregarHistorico();
}


/**
 * ============================================
 * JORNADA DO JOGADOR - Acompanhamento Individual
 * ============================================
 */

let jornadaChart = null;

/**
 * Busca a jornada de um jogador específico
 */
async function buscarJornadaJogador() {
    const pid = document.getElementById('jornada-pid').value.trim();
    const dias = document.getElementById('jornada-dias').value;
    
    if (!pid) {
        showToast('Digite um Player ID', 'error');
        return;
    }
    
    // Mostra loading
    const resultadoDiv = document.getElementById('jornada-resultado');
    const emptyDiv = document.getElementById('jornada-empty');
    
    resultadoDiv.classList.add('hidden');
    emptyDiv.innerHTML = '<div class="spinner"></div><p>Buscando dados...</p>';
    
    try {
        const response = await fetch(`/api/player/${pid}/evolucao?dias=${dias}`);
        const data = await response.json();
        
        if (!data.success) {
            emptyDiv.innerHTML = `
                <i class="fas fa-exclamation-circle" style="color: #ef4444;"></i>
                <p>${data.message || 'Jogador não encontrado no histórico'}</p>
                <p class="subtext">Tente fazer upload de dados mais recentes ou verifique o Player ID</p>
            `;
            return;
        }
        
        // Renderiza os dados
        renderizarJornada(data.evolucao);
        
        // Mostra resultado
        emptyDiv.classList.add('hidden');
        resultadoDiv.classList.remove('hidden');
        
    } catch (error) {
        console.error('Erro ao buscar jornada:', error);
        emptyDiv.innerHTML = `
            <i class="fas fa-exclamation-circle" style="color: #ef4444;"></i>
            <p>Erro ao buscar dados</p>
            <p class="subtext">${error.message}</p>
        `;
    }
}

/**
 * Renderiza a jornada do jogador na interface
 */
function renderizarJornada(dados) {
    // Header
    document.getElementById('jornada-pid-display').textContent = dados.player_id;
    document.getElementById('jornada-cluster-atual').textContent = dados.cluster_atual;
    document.getElementById('jornada-cluster-atual').className = `player-cluster ${getClusterClass(dados.cluster_atual)}`;
    
    // Resumo
    const ultimoRegistro = dados.evolucao[dados.evolucao.length - 1];
    document.getElementById('jornada-score-atual').textContent = ultimoRegistro.score_geral.toFixed(1);
    document.getElementById('jornada-mudancas').textContent = dados.resumo.mudancas_cluster;
    document.getElementById('jornada-dias-cluster').textContent = `${dados.dias_no_cluster_atual} dias`;
    
    // Tendência
    const tendencia = dados.resumo.variacao_total_geral;
    const tendenciaEl = document.getElementById('jornada-tendencia');
    if (tendencia > 5) {
        tendenciaEl.innerHTML = '<i class="fas fa-arrow-up" style="color: #10b981;"></i> Crescente';
    } else if (tendencia < -5) {
        tendenciaEl.innerHTML = '<i class="fas fa-arrow-down" style="color: #ef4444;"></i> Decrescente';
    } else {
        tendenciaEl.innerHTML = '<i class="fas fa-minus" style="color: #64748b;"></i> Estável';
    }
    
    // Gráfico
    renderizarGraficoJornada(dados.evolucao);
    
    // Timeline
    renderizarTimeline(dados.evolucao);
    
    // Métricas
    renderizarMetricas(dados);
    
    // Tabela
    renderizarTabelaHistorico(dados.evolucao, dados.variacoes);
}

/**
 * Retorna a classe CSS para um cluster
 */
function getClusterClass(cluster) {
    const map = {
        '⭐ Elite': 'cluster-elite',
        '🏆 VIP Ativo': 'cluster-vip-ativo',
        '📈 Bom': 'cluster-bom',
        '📊 Estável': 'cluster-estavel',
        '⚠️ Atenção': 'cluster-atencao',
        '🚨 Risco Alto': 'cluster-risco',
        '🚨 Risco: Queda Receita': 'cluster-risco-receita',
        '🚨 Risco: Queda Engajamento': 'cluster-risco-engajamento',
        '💎 Churn Iminente': 'cluster-churn',
        '💰 Oportunidade VIP': 'cluster-oportunidade-vip',
        '💰 Oportunidade': 'cluster-oportunidade',
        '🎯 Potencial': 'cluster-potencial'
    };
    return map[cluster] || 'cluster-default';
}

/**
 * Renderiza o gráfico de evolução
 */
function renderizarGraficoJornada(evolucao) {
    const ctx = document.getElementById('jornadaChart');
    if (!ctx) return;
    
    if (jornadaChart) {
        jornadaChart.destroy();
    }
    
    const labels = evolucao.map(e => formatarData(e.data));
    
    const scoresGeral = evolucao.map(e => e.score_geral);
    const scoresCompras = evolucao.map(e => e.score_compras);
    const scoresEngajamento = evolucao.map(e => e.score_engajamento);
    
    jornadaChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Score Geral',
                    data: scoresGeral,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Score Compras',
                    data: scoresCompras,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Score Engajamento',
                    data: scoresEngajamento,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toFixed(1)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: '#334155'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Renderiza a timeline de clusters
 */
function renderizarTimeline(evolucao) {
    const container = document.getElementById('jornada-timeline');
    if (!container) return;
    
    // Agrupa por cluster consecutivo
    const grupos = [];
    let clusterAtual = null;
    let grupoAtual = null;
    
    evolucao.forEach((reg, idx) => {
        if (reg.categoria !== clusterAtual) {
            if (grupoAtual) {
                grupoAtual.dataFim = reg.data;
            }
            clusterAtual = reg.categoria;
            grupoAtual = {
                cluster: reg.categoria,
                dataInicio: reg.data,
                dataFim: reg.data,
                dias: 1
            };
            grupos.push(grupoAtual);
        } else {
            grupoAtual.dias++;
            grupoAtual.dataFim = reg.data;
        }
    });
    
    // Gera HTML
    let html = '<div class="timeline-line">';
    
    grupos.forEach((grupo, idx) => {
        const clusterClass = getClusterClass(grupo.cluster);
        const isFirst = idx === 0;
        const isLast = idx === grupos.length - 1;
        
        html += `
            <div class="timeline-item ${clusterClass}">
                <div class="timeline-dot ${isFirst ? 'first' : ''} ${isLast ? 'last' : ''}"></div>
                <div class="timeline-content">
                    <span class="timeline-cluster">${grupo.cluster}</span>
                    <span class="timeline-period">${formatarData(grupo.dataInicio)} - ${formatarData(grupo.dataFim)}</span>
                    <span class="timeline-dias">${grupo.dias} dia${grupo.dias > 1 ? 's' : ''}</span>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Formata data para exibição (corrigido para evitar problemas de timezone)
 * Recebe data no formato YYYY-MM-DD e retorna DD/MM/YYYY
 */
function formatarData(dataStr) {
    if (!dataStr) return '-';
    // Extrai componentes diretamente do string para evitar conversão de timezone
    // Formato esperado: YYYY-MM-DD
    const [ano, mes, dia] = dataStr.split('-');
    if (ano && mes && dia) {
        return `${dia}/${mes}`;
    }
    return dataStr;
}

/**
 * Formata data completa para exibição (DD/MM/YYYY)
 */
function formatarDataCompleta(dataStr) {
    if (!dataStr) return '-';
    const [ano, mes, dia] = dataStr.split('-');
    if (ano && mes && dia) {
        return `${dia}/${mes}/${ano}`;
    }
    return dataStr;
}

/**
 * Renderiza as métricas de compras e engajamento
 */
function renderizarMetricas(dados) {
    // Métricas de compras
    const metricasCompras = dados.metricas_compras;
    const comprasEl = document.getElementById('jornada-metricas-compras');
    comprasEl.innerHTML = `
        <div class="metrica-card">
            <span class="metrica-label">Maior Score</span>
            <span class="metrica-valor" style="color: #10b981;">${metricasCompras.maior_score}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Menor Score</span>
            <span class="metrica-valor" style="color: #ef4444;">${metricasCompras.menor_score}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Média</span>
            <span class="metrica-valor" style="color: #8b5cf6;">${metricasCompras.media}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Tendência</span>
            <span class="metrica-valor ${metricasCompras.tendencia === 'crescente' ? 'tendencia-up' : 'tendencia-down'}">
                <i class="fas fa-${metricasCompras.tendencia === 'crescente' ? 'arrow-up' : 'arrow-down'}"></i>
                ${metricasCompras.tendencia === 'crescente' ? 'Crescente' : 'Decrescente'}
            </span>
        </div>
    `;
    
    // Métricas de engajamento
    const metricasEngajamento = dados.metricas_engajamento;
    const engajamentoEl = document.getElementById('jornada-metricas-engajamento');
    engajamentoEl.innerHTML = `
        <div class="metrica-card">
            <span class="metrica-label">Maior Score</span>
            <span class="metrica-valor" style="color: #10b981;">${metricasEngajamento.maior_score}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Menor Score</span>
            <span class="metrica-valor" style="color: #ef4444;">${metricasEngajamento.menor_score}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Média</span>
            <span class="metrica-valor" style="color: #8b5cf6;">${metricasEngajamento.media}</span>
        </div>
        <div class="metrica-card">
            <span class="metrica-label">Tendência</span>
            <span class="metrica-valor ${metricasEngajamento.tendencia === 'crescente' ? 'tendencia-up' : 'tendencia-down'}">
                <i class="fas fa-${metricasEngajamento.tendencia === 'crescente' ? 'arrow-up' : 'arrow-down'}"></i>
                ${metricasEngajamento.tendencia === 'crescente' ? 'Crescente' : 'Decrescente'}
            </span>
        </div>
    `;
}

/**
 * Renderiza a tabela de histórico
 */
function renderizarTabelaHistorico(evolucao, variacoes) {
    const tbody = document.getElementById('jornada-historico-body');
    if (!tbody) return;
    
    // Cria um mapa de variações por data
    const varMap = {};
    variacoes.forEach(v => {
        varMap[v.data] = v;
    });
    
    // Gera linhas (ordem reversa - mais recente primeiro)
    const html = [...evolucao].reverse().map(reg => {
        const variacao = varMap[reg.data];
        let varHtml = '-';
        
        if (variacao) {
            const varClass = variacao.variacao_geral > 0 ? 'var-up' : (variacao.variacao_geral < 0 ? 'var-down' : 'var-stable');
            const varIcon = variacao.variacao_geral > 0 ? '▲' : (variacao.variacao_geral < 0 ? '▼' : '~');
            varHtml = `<span class="${varClass}">${varIcon} ${Math.abs(variacao.variacao_geral).toFixed(1)}</span>`;
        }
        
        return `
            <tr>
                <td>${formatarData(reg.data)}</td>
                <td><span class="cluster-badge-timeline ${getClusterClass(reg.categoria)}">${reg.categoria}</span></td>
                <td><strong>${reg.score_geral.toFixed(1)}</strong></td>
                <td>${reg.score_compras.toFixed(1)}</td>
                <td>${reg.score_engajamento.toFixed(1)}</td>
                <td>${varHtml}</td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = html;
}

/**
 * Busca jornada ao pressionar Enter no input
 */
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('jornada-pid');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                buscarJornadaJogador();
            }
        });
    }
});
