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
    console.log('Trocando região para:', regiao);
    regiaoAtual = regiao;
    
    // Atualiza botões
    document.querySelectorAll('.region-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('region-btn-' + regiao).classList.add('active');
    
    // Filtra dados e atualiza dashboard
    if (cachedDataCompleto) {
        console.log('Filtrando', cachedDataCompleto.length, 'jogadores');
        const dadosFiltrados = filtrarDados(cachedDataCompleto, regiao, vipAtual);
        console.log('Filtrado para', dadosFiltrados.length, 'jogadores (região:', regiao, ', VIP:', vipAtual, ')');
        const resumoFiltrado = gerarResumoFiltrado(dadosFiltrados, cachedResumo, regiao);
        console.log('Resumo calculado:', resumoFiltrado.total_jogadores, 'jogadores');
        
        // Atualiza dashboard com dados filtrados
        updateDashboardWithData(resumoFiltrado, dadosFiltrados);
        
        // Se estiver nas abas VIP ou Benchmarks, força re-renderização
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && (activeTab.id === 'tab-vip' || activeTab.id === 'tab-benchmarks')) {
            renderTabContent(activeTab.id, resumoFiltrado);
        }
    } else {
        console.log('Sem dados em cache para filtrar');
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
    console.log('Trocando nível VIP para:', nivel);
    vipAtual = nivel;
    
    // Atualiza botões
    document.querySelectorAll('.vip-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('vip-btn-' + nivel).classList.add('active');
    
    // Filtra dados e atualiza dashboard
    if (cachedDataCompleto) {
        const dadosFiltrados = filtrarDados(cachedDataCompleto, regiaoAtual, vipAtual);
        console.log('Filtrado para', dadosFiltrados.length, 'jogadores (região:', regiaoAtual, ', VIP:', vipAtual, ')');
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
            
            analise[`vip_${nivel}`] = {
                nivel: nivel,
                nome: nomesVIP[nivel].nome,
                cor: nomesVIP[nivel].cor,
                icone: nomesVIP[nivel].icone,
                quantidade: count,
                percentual: ((count / total) * 100).toFixed(2),
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
    hideElement('empty-state');
    hideElement('loading');
    showElement('dashboard');
    
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
    console.log('updateCategorias - distribuicao recebida:', distribuicao);
    
    // Mapeia novas chaves para os IDs do HTML (mantendo compatibilidade com layout antigo)
    const valores = {
        'elite': distribuicao.elite || 0,
        'muito_bom': (distribuicao.vip_ativo || 0) + (distribuicao.bom || 0), // Agrupa VIP Ativo + Bom
        'estavel': distribuicao.estavel || 0,
        'baixo': (distribuicao.atencao || 0) + (distribuicao.risco_alto || 0), // Agrupa Atenção + Risco Alto
        'risco_receita': distribuicao.risco_receita || 0,
        'risco_engajamento': distribuicao.risco_engajamento || 0
    };
    
    console.log('updateCategorias - valores calculados:', valores);
    
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
            maintainAspectRatio: false,
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
            maintainAspectRatio: false,
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
    
    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        toggle.classList.remove('expanded');
    } else {
        content.classList.add('expanded');
        toggle.classList.add('expanded');
    }
}

/**
 * Atualiza tabela de cluster com jogadores
 */
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
    
    jogadores.forEach((jogador, index) => {
        const row = document.createElement('tr');
        const playerId = jogador.player_id || jogador.id || Object.values(jogador)[0];
        
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
            <td>${playerId}</td>
            <td>${formatNumber(jogador.score_geral || 0)}</td>
            <td>${formatNumber(jogador.score_engajamento || 0)}</td>
            <td>${formatNumber(jogador.score_compras || 0)}</td>
            <td>${vipBadge}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Atualiza todas as tabelas de clusters
 */
function updateClustersSection(dados) {
    if (!dados) {
        console.log('updateClustersSection: dados vazios');
        return;
    }
    
    // Debug: mostra categorias únicas
    const categoriasUnicas = [...new Set(dados.map(j => j.categoria))];
    console.log('Categorias encontradas:', categoriasUnicas);
    console.log('Total jogadores:', dados.length);
    
    // Filtra top 50 de cada categoria (mapeando para IDs existentes no HTML)
    const elite = dados.filter(j => j.categoria === '⭐ Elite').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const vipAtivo = dados.filter(j => j.categoria === '🏆 VIP Ativo').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const bom = dados.filter(j => j.categoria === '📈 Bom').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const estavel = dados.filter(j => j.categoria === '📊 Estável').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const atencao = dados.filter(j => j.categoria === '⚠️ Atenção').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const riscoAlto = dados.filter(j => j.categoria === '🚨 Risco Alto').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const churn = dados.filter(j => j.categoria === '💎 Churn Iminente').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const oportunidade = dados.filter(j => j.categoria === '💰 Oportunidade').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const oportunidadeVip = dados.filter(j => j.categoria === '💰 Oportunidade VIP').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const potencial = dados.filter(j => j.categoria === '🎯 Potencial').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const riscoReceita = dados.filter(j => j.categoria === '🚨 Risco: Queda Receita').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    const riscoEngajamento = dados.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').sort((a, b) => b.score_geral - a.score_geral).slice(0, 50);
    
    console.log('Contagem - Elite:', elite.length, 'VIP Ativo:', vipAtivo.length, 'Estável:', estavel.length, 'Atenção:', atencao.length);
    
    // Atualiza tabelas existentes
    updateClusterTable('elite', elite);
    updateClusterTable('muito-bom', vipAtivo);  // VIP Ativo vai para Muito Bom
    updateClusterTable('estavel', estavel);
    updateClusterTable('baixo', atencao);  // Atenção vai para Baixo
    updateClusterTable('risco-receita', riscoReceita);
    updateClusterTable('risco-engajamento', riscoEngajamento);
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
    
    // Renderiza gráficos da aba ativa
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        renderTabContent(activeTab.id, resumoParaMostrar);
    } else {
        renderCategoriaChart(resumoParaMostrar.distribuicao_categorias);
        renderScoresChart(resumoParaMostrar);
    }
    
    // Atualiza tabelas - calcula a partir dos dados filtrados
    const topJogadores = dadosParaMostrar.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10);
    const jogadoresRiscoReceita = dadosParaMostrar.filter(j => j.categoria === '🚨 Risco: Queda Receita').slice(0, 50);
    const jogadoresRiscoEngajamento = dadosParaMostrar.filter(j => j.categoria === '🚨 Risco: Queda Engajamento').slice(0, 50);
    
    updateTopJogadores(topJogadores);
    updateJogadoresRiscoReceita(jogadoresRiscoReceita);
    updateJogadoresRiscoEngajamento(jogadoresRiscoEngajamento);
    
    // Atualiza seção de clusters
    updateClustersSection(dadosParaMostrar);
    
    if (resumoParaMostrar.analise_vip) {
        updateVIPSection(resumoParaMostrar.analise_vip);
    }
}

/**
 * Handle file upload
 */
async function handleFileUpload(event) {
    console.log('Upload iniciado...');
    const file = event.target.files[0];
    if (!file) {
        console.log('Nenhum arquivo selecionado');
        return;
    }
    
    console.log('Arquivo:', file.name);
    
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
        console.log('Enviando para /api/upload...');
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        console.log('Resposta recebida:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao processar arquivo');
        }
        
        const data = await response.json();
        console.log('Dados recebidos:', data);
        
        if (data.success) {
            console.log('Atualizando dashboard...');
            // Busca dados completos
            const dadosResponse = await fetch('/api/dados');
            const dadosData = await dadosResponse.json();
            
            updateDashboard(data.resumo, dadosData.dados_completos);
            showDashboard();
            console.log('Dashboard atualizado!');
        } else {
            throw new Error(data.message || 'Erro desconhecido');
        }
        
    } catch (error) {
        console.error('Erro:', error);
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
        console.error('Erro:', error);
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
            maintainAspectRatio: false,
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
            maintainAspectRatio: false,
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
                maintainAspectRatio: false,
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
    console.log('Health Score Dashboard - Inicializado');
    
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
        const dataSnapshot = dataInput.value; // Data no formato YYYY-MM-DD
        
        console.log('salvarSnapshot - dataInput.value:', dataSnapshot);
        console.log('salvarSnapshot - dataInput.value tipo:', typeof dataSnapshot);
        
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
        console.log('salvarSnapshot - resposta do servidor:', data);
        
        if (data.success) {
            showToast('Dados salvos com sucesso! Data: ' + data.data, 'success');
            carregarHistorico();
            dataInput.value = ''; // Limpa o campo
        } else {
            showToast('Erro ao salvar: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar snapshot:', error);
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
    
    try {
        const response = await fetch(`/api/historico/${snapshotId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Registro excluído com sucesso!', 'success');
            carregarHistorico();
        } else {
            showToast('Erro ao excluir: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Erro ao deletar snapshot:', error);
        showToast('Erro ao excluir registro', 'error');
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
                atualizarTabelaClusters(data.historico[0]);
                
                if (execClustersChart) {
                    atualizarGraficoClusters(data.historico[0]);
                }
            }
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    }
}

/**
 * Atualiza KPIs do Resumo Executivo
 */
function atualizarKPIsExecutivo(historico) {
    if (historico.length === 0) return;
    
    const atual = historico[0];
    const anterior = historico[1];
    
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
 * Atualiza tabela de clusters
 */
function atualizarTabelaClusters(ultimoDia) {
    const tbody = document.getElementById('exec-clusters-body');
    if (!tbody) return;
    
    const clusters = ultimoDia.clusters;
    const total = ultimoDia.total_jogadores;
    
    const clusterNomes = {
        '⭐ Elite': { icone: '⭐', cor: '#fbbf24' },
        '🏆 VIP Ativo': { icone: '🏆', cor: '#34d399' },
        '📈 Bom': { icone: '📈', cor: '#34d399' },
        '📊 Estável': { icone: '📊', cor: '#60a5fa' },
        '⚠️ Atenção': { icone: '⚠️', cor: '#fb923c' },
        '🚨 Risco Alto': { icone: '🚨', cor: '#ef4444' },
        '💎 Churn Iminente': { icone: '💎', cor: '#ef4444' },
        '🚨 Risco: Queda Receita': { icone: '🚨', cor: '#ef4444' },
        '🚨 Risco: Queda Engajamento': { icone: '📉', cor: '#f59e0b' },
        '💰 Oportunidade': { icone: '💰', cor: '#a78bfa' },
        '💰 Oportunidade VIP': { icone: '💎', cor: '#a78bfa' },
        '🎯 Potencial': { icone: '🎯', cor: '#60a5fa' }
    };
    
    let html = '';
    for (const [nome, qtd] of Object.entries(clusters)) {
        const info = clusterNomes[nome] || { icone: '●', cor: '#94a3b8' };
        const pct = total > 0 ? (qtd / total * 100).toFixed(1) : 0;
        
        html += `
            <tr>
                <td><span style="color: ${info.cor}">${info.icone}</span> ${nome}</td>
                <td>${qtd.toLocaleString()}</td>
                <td>${pct}%</td>
                <td>-</td>
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
    
    let html = '';
    for (const dia of historico.slice(0, 10)) {
        const clusters = dia.clusters;
        const riscos = (clusters['Risco: Queda em Receita'] || 0) + (clusters['Risco: Queda em Engajamento'] || 0);
        
        html += `
            <tr>
                <td>#${dia.id}</td>
                <td>${new Date(dia.data).toLocaleDateString('pt-BR')}</td>
                <td>${dia.total_jogadores.toLocaleString()}</td>
                <td>${dia.percentual_ativos.toFixed(1)}%</td>
                <td>${dia.media_score_geral.toFixed(1)}</td>
                <td>${(clusters['Elite'] || 0).toLocaleString()}</td>
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
    
    const dados = historico.slice(0, 15).reverse();
    const labels = dados.map(d => new Date(d.data).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }));
    
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
    
    if (execClustersChart) {
        execClustersChart.destroy();
    }
    
    const clusters = ultimoDia.clusters;
    const total = ultimoDia.total_jogadores;
    
    execClustersChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['⭐ Elite', '🏆 VIP Ativo', '📊 Estável', '⚠️ Atenção', '🚨 Risco Receita', '🚨 Risco Engajamento'],
            datasets: [{
                data: [
                    clusters['elite'] || 0,
                    clusters['vip_ativo'] || 0,
                    clusters['estavel'] || 0,
                    clusters['atencao'] || 0,
                    clusters['risco_receita'] || 0,
                    clusters['risco_engajamento'] || 0
                ],
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
