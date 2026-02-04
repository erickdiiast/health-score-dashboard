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
        const dadosFiltrados = filtrarPorRegiao(cachedDataCompleto, regiao);
        console.log('Filtrado para', dadosFiltrados.length, 'jogadores na região', regiao);
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
 * Gera resumo filtrado por região
 */
function gerarResumoFiltrado(dados, resumoOriginal, regiao) {
    if (regiao === 'all') return resumoOriginal;
    
    // Se temos análise pré-calculada no backend, usa ela
    if (resumoOriginal.analise_regiao && resumoOriginal.analise_regiao[regiao]) {
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
            jogadores_risco_receita: dados.filter(j => j.categoria === 'Risco: Queda em Receita').slice(0, 50),
            jogadores_risco_engajamento: dados.filter(j => j.categoria === 'Risco: Queda em Engajamento').slice(0, 50),
            regiao_atual: regiao,
            regiao_nome: analise.nome
        };
    }
    
    // Caso contrário, calcula do lado do cliente
    const total = dados.length;
    if (total === 0) return resumoOriginal;
    
    const ativos = dados.filter(j => j.ativo).length;
    
    // Calcula distribuição de categorias
    const elite = dados.filter(j => j.categoria === 'Elite').length;
    const muitoBom = dados.filter(j => j.categoria === 'Muito bom').length;
    const estavel = dados.filter(j => j.categoria === 'Estável').length;
    const baixo = dados.filter(j => j.categoria === 'Baixo').length;
    const riscoReceita = dados.filter(j => j.categoria === 'Risco: Queda em Receita').length;
    const riscoEngajamento = dados.filter(j => j.categoria === 'Risco: Queda em Engajamento').length;
    
    return {
        ...resumoOriginal,
        total_jogadores: total,
        percentual_ativos: ativos / total * 100,
        media_saude_login: dados.reduce((a, b) => a + b.score_login, 0) / total,
        media_saude_engajamento: dados.reduce((a, b) => a + b.score_engajamento, 0) / total,
        media_saude_compras: dados.reduce((a, b) => a + b.score_compras, 0) / total,
        media_pontuacao_geral: dados.reduce((a, b) => a + b.score_geral, 0) / total,
        distribuicao_categorias: {
            elite: (elite / total * 100).toFixed(2),
            muito_bom: (muitoBom / total * 100).toFixed(2),
            estavel: (estavel / total * 100).toFixed(2),
            baixo: (baixo / total * 100).toFixed(2),
            risco_receita: (riscoReceita / total * 100).toFixed(2),
            risco_engajamento: (riscoEngajamento / total * 100).toFixed(2)
        },
        top_jogadores: dados.sort((a, b) => b.score_geral - a.score_geral).slice(0, 10),
        jogadores_risco_receita: dados.filter(j => j.categoria === 'Risco: Queda em Receita').slice(0, 50),
        jogadores_risco_engajamento: dados.filter(j => j.categoria === 'Risco: Queda em Engajamento').slice(0, 50),
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
    
    const analise = {};
    const total = dados.length;
    
    niveis.forEach(nivel => {
        const jogadoresNivel = dados.filter(j => j.nivel_vip === nivel);
        if (jogadoresNivel.length > 0) {
            const count = jogadoresNivel.length;
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
    
    // Atualiza tabelas
    updateTopJogadores(resumo.top_jogadores);
    updateJogadoresRiscoReceita(resumo.jogadores_risco_receita);
    updateJogadoresRiscoEngajamento(resumo.jogadores_risco_engajamento);
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
        case 'tab-vip':
            if (resumo.analise_vip) {
                updateVIPSection(resumo.analise_vip);
            }
            break;
        case 'tab-players':
            // Tabelas já foram renderizadas
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
    document.getElementById('cat-elite').textContent = distribuicao.elite + '%';
    document.getElementById('cat-muito-bom').textContent = distribuicao.muito_bom + '%';
    document.getElementById('cat-estavel').textContent = distribuicao.estavel + '%';
    document.getElementById('cat-baixo').textContent = distribuicao.baixo + '%';
    document.getElementById('cat-risco-receita').textContent = distribuicao.risco_receita + '%';
    document.getElementById('cat-risco-engajamento').textContent = distribuicao.risco_engajamento + '%';
    
    // Atualiza barras de progresso
    document.getElementById('progress-elite').style.width = distribuicao.elite + '%';
    document.getElementById('progress-muito-bom').style.width = distribuicao.muito_bom + '%';
    document.getElementById('progress-estavel').style.width = distribuicao.estavel + '%';
    document.getElementById('progress-baixo').style.width = distribuicao.baixo + '%';
    document.getElementById('progress-risco-receita').style.width = distribuicao.risco_receita + '%';
    document.getElementById('progress-risco-engajamento').style.width = distribuicao.risco_engajamento + '%';
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
    
    categoriaChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Elite', 'Muito Bom', 'Estável', 'Baixo', 'Risco: Queda em Receita', 'Risco: Queda em Engajamento'],
            datasets: [{
                data: [
                    distribuicao.elite,
                    distribuicao.muito_bom,
                    distribuicao.estavel,
                    distribuicao.baixo,
                    distribuicao.risco_receita,
                    distribuicao.risco_engajamento
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
        'Elite': 'badge-elite',
        'Muito bom': 'badge-muito-bom',
        'Estável': 'badge-estavel',
        'Baixo': 'badge-baixo',
        'Risco alto + Crítico': 'badge-risco',
        'Risco: Queda em Receita': 'badge-risco-receita',
        'Risco: Queda em Engajamento': 'badge-risco-engajamento'
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
 * Atualiza todo o dashboard com os dados
 */
function updateDashboard(resumo, dadosCompletos) {
    // Guarda em cache
    cachedResumo = resumo;
    if (dadosCompletos) {
        cachedDataCompleto = dadosCompletos;
    }
    
    // Se temos dados completos e uma região selecionada, filtra
    let dadosParaMostrar = dadosCompletos;
    let resumoParaMostrar = resumo;
    
    if (cachedDataCompleto && regiaoAtual !== 'all') {
        dadosParaMostrar = filtrarPorRegiao(cachedDataCompleto, regiaoAtual);
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
    
    // Atualiza tabelas
    updateTopJogadores(resumoParaMostrar.top_jogadores);
    updateJogadoresRiscoReceita(resumoParaMostrar.jogadores_risco_receita);
    updateJogadoresRiscoEngajamento(resumoParaMostrar.jogadores_risco_engajamento);
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
        // Regiões (Ctrl + tecla)
        if (e.ctrlKey) {
            if (e.key === 'a' || e.key === '0') showRegion('all');
            if (e.key === 'e') showRegion('es');
            if (e.key === 'b') showRegion('br');
            if (e.key === 'i') showRegion('int');
        }
        // Abas (1-4)
        else {
            if (e.key === '1') showTab('tab-overview');
            if (e.key === '2') showTab('tab-vip');
            if (e.key === '3') showTab('tab-players');
            if (e.key === '4') showTab('tab-benchmarks');
        }
    });
});
