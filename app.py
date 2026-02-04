"""
Health Score Dashboard - Backend API
Processa dados de jogadores e calcula métricas de saúde/engajamento
Parâmetros dinâmicos calculados a partir dos dados carregados
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import json
import sqlite3
import os
from typing import List, Dict, Any, Optional
import uvicorn
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

app = FastAPI(title="Health Score Dashboard", version="2.2.0")

# Configuração do banco de dados SQLite
DB_PATH = "historico.db"

def init_db():
    """Inicializa o banco de dados SQLite para histórico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de snapshots do dia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            data_timestamp TEXT NOT NULL,
            total_jogadores INTEGER,
            percentual_ativos REAL,
            media_score_geral REAL,
            media_score_login REAL,
            media_score_engajamento REAL,
            media_score_compras REAL,
            cluster_elite INTEGER,
            cluster_muito_bom INTEGER,
            cluster_estavel INTEGER,
            cluster_baixo INTEGER,
            cluster_risco_receita INTEGER,
            cluster_risco_engajamento INTEGER,
            filtro_regiao TEXT DEFAULT 'all',
            filtro_vip TEXT DEFAULT 'all'
        )
    ''')
    
    # Tabela de clusters por dia (para detalhamento)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clusters_dia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            cluster_nome TEXT,
            quantidade INTEGER,
            percentual REAL,
            score_compras_medio REAL,
            score_engajamento_medio REAL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializa o banco na startup
init_db()

# CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache temporário dos dados processados
cached_data = {}

# ========== PARÂMETROS PADRÃO (fallback) ==========
DEFAULT_PARAMS = {
    'torneios_por_dia': 40,
    'maratonas_por_dia': 11,
    'missoes_por_dia': 3,
    'promos_por_dia': 9,
    'janela_logins_dias': 3,
}

# ========== MAPEAMENTO NÍVEIS VIP ==========
VIP_MAPPING = {
    1: {'nome': 'Ametista', 'cor': '#9B59B6', 'icone': '💎'},
    2: {'nome': 'Topázio', 'cor': '#F39C12', 'icone': '💠'},
    3: {'nome': 'Esmeralda', 'cor': '#27AE60', 'icone': '🔷'},
    4: {'nome': 'Opala', 'cor': '#E74C3C', 'icone': '🔶'},
    5: {'nome': 'Berilo', 'cor': '#3498DB', 'icone': '👑'},
}

def get_vip_info(nivel: int) -> Dict:
    """Retorna informações do nível VIP"""
    return VIP_MAPPING.get(nivel, {'nome': 'Desconhecido', 'cor': '#95A5A6', 'icone': '❓'})


def get_regiao(translation: str) -> str:
    """
    Identifica a região do jogador baseado na tradução.
    Retorna: 'es' (Espanhol), 'br' (Brasil), 'int' (Internacional)
    """
    if pd.isna(translation):
        return 'int'
    
    translation = str(translation).lower().strip()
    
    # Espanhol
    if translation in ['es_ar', 'es_es', 'es_la', 'es_mx', 'es']:
        return 'es'
    
    # Brasil
    if translation in ['pt_br', 'pt-br', 'pt']:
        return 'br'
    
    # Internacional (todos os outros)
    return 'int'


def get_regiao_nome(regiao: str) -> str:
    """Retorna o nome amigável da região"""
    nomes = {
        'es': 'Espanhol',
        'br': 'Brasil',
        'int': 'Internacional',
        'all': 'Todos'
    }
    return nomes.get(regiao, 'Desconhecido')


class HealthScoreCalculator:
    """Calcula scores de saúde para jogadores com parâmetros dinâmicos"""
    
    def __init__(self, params: Dict[str, float] = None):
        self.params = params or self._calcular_params_padrao()
    
    @staticmethod
    def calcular_params_dinamicos(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula parâmetros dinâmicos baseados nas médias do dataset:
        - Média de torneios_3d / 3
        - Média de maratonas_3d / 3
        - Média de missões_3d / 3
        - Média de promoções_3d / 3
        """
        params = {
            'janela_logins_dias': 3,
            'fonte': 'dinamico'  # Marca que são parâmetros calculados
        }
        
        # Normaliza nomes de colunas
        df_cols = df.columns.str.lower().str.strip()
        
        # Mapeia colunas possíveis
        col_mapping = {
            'torneios': ['qtd_torneios_3d', 'torneios_3d', 'qtd_torneios'],
            'maratonas': ['qtd_maratonas_3d', 'maratonas_3d', 'qtd_maratonas'],
            'missoes': ['qtd_missoes_3d', 'missoes_3d', 'qtd_missoes', 'qtd_missões_3d'],
            'promos': ['qtd_promos_3d', 'promos_3d', 'qtd_promos'],
        }
        
        def encontrar_coluna(possiveis):
            for col in possiveis:
                if col in df_cols:
                    return col
            return None
        
        # Calcula médias e converte para "por dia"
        # Fórmula: MÉDIA(qtd_xxx_3d) / 3 = média por dia
        
        # Torneios
        col_torneios = encontrar_coluna(col_mapping['torneios'])
        if col_torneios:
            media_torneios_3d = df[col_torneios].mean()
            params['torneios_por_dia'] = media_torneios_3d / 3
            params['media_torneios_3d'] = media_torneios_3d
            # Desvio padrão (DESVPAD.P no Excel)
            params['desvpad_torneios_3d'] = df[col_torneios].std()
            # Mediana (MED no Excel)
            params['mediana_torneios_3d'] = df[col_torneios].median()
        else:
            params['torneios_por_dia'] = DEFAULT_PARAMS['torneios_por_dia']
        
        # Maratonas
        col_maratonas = encontrar_coluna(col_mapping['maratonas'])
        if col_maratonas:
            media_maratonas_3d = df[col_maratonas].mean()
            params['maratonas_por_dia'] = media_maratonas_3d / 3
            params['media_maratonas_3d'] = media_maratonas_3d
            params['desvpad_maratonas_3d'] = df[col_maratonas].std()
            params['mediana_maratonas_3d'] = df[col_maratonas].median()
        else:
            params['maratonas_por_dia'] = DEFAULT_PARAMS['maratonas_por_dia']
        
        # Missões
        col_missoes = encontrar_coluna(col_mapping['missoes'])
        if col_missoes:
            media_missoes_3d = df[col_missoes].mean()
            params['missoes_por_dia'] = media_missoes_3d / 3
            params['media_missoes_3d'] = media_missoes_3d
            params['desvpad_missoes_3d'] = df[col_missoes].std()
            params['mediana_missoes_3d'] = df[col_missoes].median()
        else:
            params['missoes_por_dia'] = DEFAULT_PARAMS['missoes_por_dia']
        
        # Promoções
        col_promos = encontrar_coluna(col_mapping['promos'])
        if col_promos:
            media_promos_3d = df[col_promos].mean()
            params['promos_por_dia'] = media_promos_3d / 3
            params['media_promos_3d'] = media_promos_3d
            params['desvpad_promos_3d'] = df[col_promos].std()
            params['mediana_promos_3d'] = df[col_promos].median()
        else:
            params['promos_por_dia'] = DEFAULT_PARAMS['promos_por_dia']
        
        # Logins
        col_logins = encontrar_coluna(['qtd_logins_3d', 'logins_3d'])
        if col_logins:
            params['media_logins_3d'] = df[col_logins].mean()
            params['desvpad_logins_3d'] = df[col_logins].std()
            params['mediana_logins_3d'] = df[col_logins].median()
        
        # Calcula os fatores de conversão
        # Fórmula: 100 / (média_3d * 1.5) - jogador acima da média ganha mais pontos
        # Multiplicamos por 1.5 para que quem está na média ganhe ~67 pontos
        # e quem está 50% acima da média ganhe 100 pontos
        
        for metrica in ['torneios', 'maratonas', 'missoes', 'promos']:
            media_3d = params.get(f'media_{metrica}_3d', 0)
            if media_3d > 0:
                # Fator: 100 pontos = 1.5x a média (desempenho acima da média)
                params[f'{metrica}_factor'] = 100 / (media_3d * 1.5)
            else:
                params[f'{metrica}_factor'] = 1.0
        
        # Fator para logins (benchmark: média dos jogadores)
        media_logins = params.get('media_logins_3d', 3)
        if media_logins > 0:
            params['logins_factor'] = 100 / (media_logins * 1.5)
        else:
            params['logins_factor'] = 33.33
        
        return params
    
    @staticmethod
    def _calcular_params_padrao() -> Dict[str, float]:
        """Retorna parâmetros padrão do Dashboard_2"""
        params = DEFAULT_PARAMS.copy()
        params['fonte'] = 'padrao'
        
        # Calcula fatores baseados nos valores padrão
        params['torneios_factor'] = 100 / (params['torneios_por_dia'] * 3)
        params['maratonas_factor'] = 100 / (params['maratonas_por_dia'] * 3)
        params['missoes_factor'] = 100 / (params['missoes_por_dia'] * 3)
        params['promos_factor'] = 100 / (params['promos_por_dia'] * 3)
        params['logins_factor'] = 100 / 3
        
        return params
    
    def calcular_score_login(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de login baseado em:
        - Dias desde último login (decaimento exponencial)
        - Quantidade de logins na janela de 3 dias
        """
        hoje = datetime.now()
        scores = []
        
        for _, row in df.iterrows():
            pontuacoes = []
            
            # Recência do último login
            if 'lastlogin' in df.columns and pd.notna(row.get('lastlogin')):
                try:
                    last_login = pd.to_datetime(row['lastlogin'])
                    dias_desde_login = (hoje - last_login).days
                    login_score = 100 * np.exp(-max(0, dias_desde_login) / 7)
                    pontuacoes.append(login_score)
                except:
                    pass
            
            # Frequência de logins na janela de 3 dias
            if 'qtd_logins_3d' in df.columns:
                qtd = row.get('qtd_logins_3d', 0)
                if pd.notna(qtd):
                    freq_score = min(qtd * self.params['logins_factor'], 100)
                    pontuacoes.append(freq_score)
            
            if pontuacoes:
                scores.append(np.mean(pontuacoes))
            else:
                scores.append(50)
        
        return pd.Series(scores)
    
    def calcular_score_engajamento(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de engajamento com parâmetros dinâmicos:
        - Nível VIP
        - Torneios (média dinâmica)
        - Maratonas (média dinâmica)
        - Missões (média dinâmica)
        - Promoções (média dinâmica)
        """
        scores = []
        
        for _, row in df.iterrows():
            pontuacoes = []
            
            # Nível VIP
            if 'nivel_vip' in df.columns and pd.notna(row.get('nivel_vip')):
                vip = row['nivel_vip']
                vip_score = min((vip / 5) * 100, 100)
                pontuacoes.append(vip_score)
            
            # Torneios
            if 'qtd_torneios_3d' in df.columns:
                torneios = row.get('qtd_torneios_3d', 0)
                if pd.notna(torneios):
                    torneios_score = min(torneios * self.params['torneios_factor'], 100)
                    pontuacoes.append(torneios_score)
            
            # Maratonas
            if 'qtd_maratonas_3d' in df.columns:
                maratonas = row.get('qtd_maratonas_3d', 0)
                if pd.notna(maratonas):
                    maratonas_score = min(maratonas * self.params['maratonas_factor'], 100)
                    pontuacoes.append(maratonas_score)
            
            # Missões
            if 'qtd_missoes_3d' in df.columns:
                missoes = row.get('qtd_missoes_3d', 0)
                if pd.notna(missoes):
                    missoes_score = min(missoes * self.params['missoes_factor'], 100)
                    pontuacoes.append(missoes_score)
            
            # Promoções
            if 'qtd_promos_3d' in df.columns:
                promos = row.get('qtd_promos_3d', 0)
                if pd.notna(promos):
                    promos_score = min(promos * self.params['promos_factor'], 100)
                    pontuacoes.append(promos_score)
            
            if pontuacoes:
                scores.append(np.mean(pontuacoes))
            else:
                scores.append(50)
        
        return pd.Series(scores)
    
    def calcular_score_compras(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de compras baseado em:
        - Quantidade de compras nos últimos 7 dias
        - Recência da última compra
        - Ticket médio (se disponível)
        """
        scores = []
        hoje = datetime.now()
        
        for _, row in df.iterrows():  
            pontuacoes = []
            
            # Quantidade de compras nos últimos 7 dias
            if 'qtd_compras_7d' in df.columns:
                qtd = row.get('qtd_compras_7d', 0)
                if pd.notna(qtd):
                    # Calcula média dinâmica se possível
                    media_compras = df['qtd_compras_7d'].mean()
                    if media_compras > 0:
                        factor = 100 / (media_compras * 1.5)
                    else:
                        factor = 33.33
                    qtd_score = min(qtd * factor, 100)
                    pontuacoes.append(qtd_score)
            
            # Ticket médio
            if 'ticket_medio_7d' in df.columns:
                ticket = row.get('ticket_medio_7d', 0)
                if pd.notna(ticket) and ticket > 0:
                    media_ticket = df['ticket_medio_7d'].mean()
                    if media_ticket > 0:
                        ticket_score = min(ticket / (media_ticket * 1.5) * 100, 100)
                    else:
                        ticket_score = min(ticket / 50 * 100, 100)
                    pontuacoes.append(ticket_score)
            
            # Recência da última compra
            if 'ultima_compra' in df.columns and pd.notna(row.get('ultima_compra')):
                try:
                    ultima = pd.to_datetime(row['ultima_compra'])
                    dias_ultima = (hoje - ultima).days
                    recencia_score = 100 * np.exp(-max(0, dias_ultima) / 30)
                    pontuacoes.append(recencia_score)
                except:
                    pass
            
            if pontuacoes:
                scores.append(np.mean(pontuacoes))
            else:
                scores.append(30)
        
        return pd.Series(scores)
    
    def calcular_score_geral(self, row: pd.Series) -> float:
        """Calcula score geral ponderado"""
        engajamento = row.get('score_engajamento', 50)
        compras = row.get('score_compras', 30)
        
        # Ponderação: Engajamento 30%, Compras 70%
        return engajamento * 0.3 + compras * 0.7
    
    def categorizar_jogador(self, row: pd.Series) -> str:
        """Categoriza jogador baseado no score geral"""
        score = row.get('score_geral', 50)
        
        if score >= 80:
            return "Elite"
        elif score >= 65:
            return "Muito bom"
        elif score >= 50:
            return "Estável"
        elif score >= 35:
            return "Baixo"
        else:
            # Risco - identifica a causa
            score_compras = row.get('score_compras', 0)
            score_engajamento = row.get('score_engajamento', 0)
            
            if score_compras < score_engajamento:
                return "Risco: Queda em Receita"
            else:
                return "Risco: Queda em Engajamento"


def detectar_tipo_arquivo(filename: str) -> str:
    """Detecta o tipo de arquivo baseado na extensão"""
    if filename.lower().endswith('.csv'):
        return 'csv'
    elif filename.lower().endswith(('.xlsx', '.xls')):
        return 'excel'
    else:
        return 'unknown'


def processar_dados_jogadores(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict]:
    """Processa DataFrame e adiciona scores calculados com parâmetros dinâmicos"""
    
    # Calcula parâmetros dinâmicos a partir dos dados
    params = HealthScoreCalculator.calcular_params_dinamicos(df)
    
    # Inicializa calculador com parâmetros dinâmicos
    calc = HealthScoreCalculator(params)
    
    # Normaliza nomes de colunas
    df.columns = df.columns.str.lower().str.strip()
    
    # Renomeia colunas comuns do CRM para padrão
    if 'pid' in df.columns and 'player_id' not in df.columns:
        df = df.rename(columns={'pid': 'player_id'})
    
    # Calcula scores individuais
    df['score_login'] = calc.calcular_score_login(df)
    df['score_engajamento'] = calc.calcular_score_engajamento(df)
    df['score_compras'] = calc.calcular_score_compras(df)
    
    # Calcula score geral
    df['score_geral'] = df.apply(calc.calcular_score_geral, axis=1)
    
    # Categoriza jogadores
    df['categoria'] = df.apply(calc.categorizar_jogador, axis=1)
    
    # Status de atividade
    df['ativo'] = df['score_login'] >= 50
    
    # Identifica região do jogador
    if 'translation' in df.columns:
        df['regiao'] = df['translation'].apply(get_regiao)
    else:
        df['regiao'] = 'int'  # Default: Internacional
    
    # Define ação sugerida baseada na categoria
    df['acao_sugerida'] = df['categoria'].map({
        'Elite': 'Manter engajamento',
        'Muito bom': 'Incentivar compras',
        'Estável': 'Aumentar frequência',
        'Baixo': 'Reengajamento',
        'Risco alto + Crítico': 'Ação imediata!',
        'Risco: Queda em Receita': 'Foco em compras',
        'Risco: Queda em Engajamento': 'Foco em engajamento'
    })
    
    # Adiciona informações de VIP
    if 'nivel_vip' in df.columns:
        df['vip_nome'] = df['nivel_vip'].apply(lambda x: get_vip_info(int(x) if pd.notna(x) else 0)['nome'])
        df['vip_cor'] = df['nivel_vip'].apply(lambda x: get_vip_info(int(x) if pd.notna(x) else 0)['cor'])
        df['vip_icone'] = df['nivel_vip'].apply(lambda x: get_vip_info(int(x) if pd.notna(x) else 0)['icone'])
    
    return df, params


def salvar_snapshot(resumo: Dict, filtros: Dict = None, data_custom: str = None) -> int:
    """Salva um snapshot do dia no banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Usa data customizada (do arquivo) ou data atual
    if data_custom:
        data_snapshot = data_custom
    else:
        data_snapshot = datetime.now().strftime("%Y-%m-%d")
    
    agora = datetime.now().isoformat()
    
    filtros = filtros or {}
    filtro_regiao = filtros.get('regiao', 'all')
    filtro_vip = filtros.get('vip', 'all')
    
    # Insere snapshot principal
    cursor.execute('''
        INSERT INTO snapshots (
            data, data_timestamp, total_jogadores, percentual_ativos,
            media_score_geral, media_score_login, media_score_engajamento, media_score_compras,
            cluster_elite, cluster_muito_bom, cluster_estavel, cluster_baixo,
            cluster_risco_receita, cluster_risco_engajamento,
            filtro_regiao, filtro_vip
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_snapshot, agora,
        resumo.get('total_jogadores', 0),
        resumo.get('percentual_ativos', 0),
        resumo.get('media_pontuacao_geral', 0),
        resumo.get('media_saude_login', 0),
        resumo.get('media_saude_engajamento', 0),
        resumo.get('media_saude_compras', 0),
        resumo.get('contagem_por_categoria', {}).get('Elite', 0),
        resumo.get('contagem_por_categoria', {}).get('Muito bom', 0),
        resumo.get('contagem_por_categoria', {}).get('Estável', 0),
        resumo.get('contagem_por_categoria', {}).get('Baixo', 0),
        resumo.get('contagem_por_categoria', {}).get('Risco: Queda em Receita', 0),
        resumo.get('contagem_por_categoria', {}).get('Risco: Queda em Engajamento', 0),
        filtro_regiao, filtro_vip
    ))
    
    snapshot_id = cursor.lastrowid
    
    # Insere detalhes dos clusters
    contagem = resumo.get('contagem_por_categoria', {})
    total = resumo.get('total_jogadores', 1)
    
    clusters_info = [
        ('Elite', contagem.get('Elite', 0)),
        ('Muito bom', contagem.get('Muito bom', 0)),
        ('Estável', contagem.get('Estável', 0)),
        ('Baixo', contagem.get('Baixo', 0)),
        ('Risco: Queda em Receita', contagem.get('Risco: Queda em Receita', 0)),
        ('Risco: Queda em Engajamento', contagem.get('Risco: Queda em Engajamento', 0)),
    ]
    
    for nome, qtd in clusters_info:
        cursor.execute('''
            INSERT INTO clusters_dia (snapshot_id, cluster_nome, quantidade, percentual, score_compras_medio, score_engajamento_medio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (snapshot_id, nome, qtd, round(qtd/total*100, 2) if total > 0 else 0, 0, 0))
    
    conn.commit()
    conn.close()
    return snapshot_id


def listar_historico(regiao: str = None, vip: str = None, dias: int = 30) -> List[Dict]:
    """Lista histórico de snapshots com filtros opcionais"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM snapshots WHERE 1=1"
    params = []
    
    if regiao and regiao != 'all':
        query += " AND filtro_regiao = ?"
        params.append(regiao)
    if vip and vip != 'all':
        query += " AND filtro_vip = ?"
        params.append(vip)
    
    query += " ORDER BY data_timestamp DESC LIMIT ?"
    params.append(dias)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    historico = []
    for row in rows:
        historico.append({
            'id': row['id'],
            'data': row['data'],
            'data_timestamp': row['data_timestamp'],
            'total_jogadores': row['total_jogadores'],
            'percentual_ativos': row['percentual_ativos'],
            'media_score_geral': row['media_score_geral'],
            'media_score_login': row['media_score_login'],
            'media_score_engajamento': row['media_score_engajamento'],
            'media_score_compras': row['media_score_compras'],
            'clusters': {
                'Elite': row['cluster_elite'],
                'Muito bom': row['cluster_muito_bom'],
                'Estável': row['cluster_estavel'],
                'Baixo': row['cluster_baixo'],
                'Risco: Queda em Receita': row['cluster_risco_receita'],
                'Risco: Queda em Engajamento': row['cluster_risco_engajamento'],
            },
            'filtro_regiao': row['filtro_regiao'],
            'filtro_vip': row['filtro_vip'],
        })
    
    conn.close()
    return historico


def deletar_snapshot(snapshot_id: int = None, data: str = None) -> bool:
    """Deleta um snapshot por ID ou por data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if snapshot_id:
            # Deleta clusters primeiro (foreign key)
            cursor.execute('DELETE FROM clusters_dia WHERE snapshot_id = ?', (snapshot_id,))
            # Deleta snapshot
            cursor.execute('DELETE FROM snapshots WHERE id = ?', (snapshot_id,))
        elif data:
            # Busca IDs dos snapshots da data
            cursor.execute('SELECT id FROM snapshots WHERE data = ?', (data,))
            ids = cursor.fetchall()
            for (sid,) in ids:
                cursor.execute('DELETE FROM clusters_dia WHERE snapshot_id = ?', (sid,))
            cursor.execute('DELETE FROM snapshots WHERE data = ?', (data,))
        else:
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erro ao deletar snapshot: {e}")
        conn.close()
        return False


def comparar_periodos(data_inicio: str, data_fim: str) -> Dict:
    """Compara dados entre dois períodos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM snapshots 
        WHERE data BETWEEN ? AND ?
        ORDER BY data
    ''', (data_inicio, data_fim))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {'mensagem': 'Nenhum dado encontrado para o período'}
    
    # Calcula médias e tendências
    total_dias = len(rows)
    media_jogadores = sum(r[3] for r in rows) / total_dias
    media_ativos = sum(r[4] for r in rows) / total_dias
    media_score = sum(r[5] for r in rows) / total_dias
    
    # Tendência (último vs primeiro dia)
    primeira_data = rows[0]
    ultima_data = rows[-1]
    
    return {
        'periodo': {'inicio': data_inicio, 'fim': data_fim, 'dias': total_dias},
        'medias': {
            'total_jogadores': round(media_jogadores, 0),
            'percentual_ativos': round(media_ativos, 2),
            'score_geral': round(media_score, 2),
        },
        'tendencia': {
            'total_jogadores': ultima_data[3] - primeira_data[3],
            'percentual_ativos': round(ultima_data[4] - primeira_data[4], 2),
            'score_geral': round(ultima_data[5] - primeira_data[5], 2),
        },
        'evolucao_diaria': [
            {
                'data': r[1],
                'total_jogadores': r[3],
                'percentual_ativos': r[4],
                'score_geral': r[5],
            } for r in rows
        ]
    }


def clean_for_json(obj):
    """Limpa valores NaN, Infinity para serialização JSON"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if pd.isna(obj):
            return 0.0
        elif np.isinf(obj):
            return 999999.99 if obj > 0 else -999999.99
        return round(obj, 2)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj) if not (pd.isna(obj) or np.isinf(obj)) else 0.0
    else:
        return obj


def gerar_resumo_dashboard(df: pd.DataFrame, params: Dict) -> Dict[str, Any]:
    """Gera resumo estatístico para o dashboard"""
    total = len(df)
    ativos = df['ativo'].sum()
    
    # Identifica coluna de ID
    id_col = 'player_id' if 'player_id' in df.columns else df.columns[0]
    
    # Calcula contagem por categoria
    contagem_categorias = df['categoria'].value_counts()
    
    resumo = {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "total_jogadores": total,
        "percentual_ativos": round(ativos / total * 100, 2) if total > 0 else 0,
        "media_saude_login": round(df['score_login'].mean(), 2),
        "media_saude_engajamento": round(df['score_engajamento'].mean(), 2),
        "media_saude_compras": round(df['score_compras'].mean(), 2),
        "media_pontuacao_geral": round(df['score_geral'].mean(), 2),
        "distribuicao_categorias": {
            "elite": round((df['categoria'] == 'Elite').sum() / total * 100, 2) if total > 0 else 0,
            "muito_bom": round((df['categoria'] == 'Muito bom').sum() / total * 100, 2) if total > 0 else 0,
            "estavel": round((df['categoria'] == 'Estável').sum() / total * 100, 2) if total > 0 else 0,
            "baixo": round((df['categoria'] == 'Baixo').sum() / total * 100, 2) if total > 0 else 0,
            "risco_receita": round((df['categoria'] == 'Risco: Queda em Receita').sum() / total * 100, 2) if total > 0 else 0,
            "risco_engajamento": round((df['categoria'] == 'Risco: Queda em Engajamento').sum() / total * 100, 2) if total > 0 else 0,
        },
        "contagem_por_categoria": contagem_categorias.to_dict(),
        "parametros_calculados": params,
        "benchmarks": {
            "torneios_por_dia": round(params.get('torneios_por_dia', 0), 2),
            "maratonas_por_dia": round(params.get('maratonas_por_dia', 0), 2),
            "missoes_por_dia": round(params.get('missoes_por_dia', 0), 2),
            "promos_por_dia": round(params.get('promos_por_dia', 0), 2),
            "logins_3d": round(params.get('media_logins_3d', 0), 2),
        },
        "estatisticas": {
            # Médias (MÉDIA no Excel)
            "media_torneios_3d": round(params.get('media_torneios_3d', 0), 2),
            "media_maratonas_3d": round(params.get('media_maratonas_3d', 0), 2),
            "media_missoes_3d": round(params.get('media_missoes_3d', 0), 2),
            "media_promos_3d": round(params.get('media_promos_3d', 0), 2),
            "media_logins_3d": round(params.get('media_logins_3d', 0), 2),
            # Desvios Padrão (DESVPAD.P no Excel)
            "desvpad_torneios_3d": round(params.get('desvpad_torneios_3d', 0), 2),
            "desvpad_maratonas_3d": round(params.get('desvpad_maratonas_3d', 0), 2),
            "desvpad_missoes_3d": round(params.get('desvpad_missoes_3d', 0), 2),
            "desvpad_promos_3d": round(params.get('desvpad_promos_3d', 0), 2),
            "desvpad_logins_3d": round(params.get('desvpad_logins_3d', 0), 2),
            # Medianas (MED no Excel)
            "mediana_torneios_3d": round(params.get('mediana_torneios_3d', 0), 2),
            "mediana_maratonas_3d": round(params.get('mediana_maratonas_3d', 0), 2),
            "mediana_missoes_3d": round(params.get('mediana_missoes_3d', 0), 2),
            "mediana_promos_3d": round(params.get('mediana_promos_3d', 0), 2),
            "mediana_logins_3d": round(params.get('mediana_logins_3d', 0), 2),
        },
        "top_jogadores": df.nlargest(10, 'score_geral')[[id_col, 
                                                          'score_login', 'score_engajamento', 
                                                          'score_compras', 'score_geral', 
                                                          'categoria', 'acao_sugerida']].to_dict('records'),
        "jogadores_risco_receita": df[df['categoria'] == 'Risco: Queda em Receita'][[id_col, 
                                                                          'score_geral', 'score_engajamento', 'score_compras',
                                                                          'categoria', 'acao_sugerida']].head(50).to_dict('records'),
        "jogadores_risco_engajamento": df[df['categoria'] == 'Risco: Queda em Engajamento'][[id_col, 
                                                                          'score_geral', 'score_engajamento', 'score_compras',
                                                                          'categoria', 'acao_sugerida']].head(50).to_dict('records'),
    }
    
    # Adiciona análise por região
    if 'regiao' in df.columns:
        resumo["analise_regiao"] = {}
        resumo["distribuicao_regiao"] = {}
        
        for regiao in ['es', 'br', 'int']:
            df_regiao = df[df['regiao'] == regiao]
            if len(df_regiao) > 0:
                resumo["analise_regiao"][regiao] = {
                    "codigo": regiao,
                    "nome": get_regiao_nome(regiao),
                    "quantidade": len(df_regiao),
                    "percentual": round(len(df_regiao) / total * 100, 2),
                    "score_geral_medio": round(df_regiao['score_geral'].mean(), 2),
                    "score_login_medio": round(df_regiao['score_login'].mean(), 2),
                    "score_engajamento_medio": round(df_regiao['score_engajamento'].mean(), 2),
                    "score_compras_medio": round(df_regiao['score_compras'].mean(), 2),
                    "percentual_ativos": round((df_regiao['ativo'].sum() / len(df_regiao) * 100), 2),
                    "distribuicao_categorias": {
                        "elite": round((df_regiao['categoria'] == 'Elite').sum() / len(df_regiao) * 100, 2),
                        "muito_bom": round((df_regiao['categoria'] == 'Muito bom').sum() / len(df_regiao) * 100, 2),
                        "estavel": round((df_regiao['categoria'] == 'Estável').sum() / len(df_regiao) * 100, 2),
                        "baixo": round((df_regiao['categoria'] == 'Baixo').sum() / len(df_regiao) * 100, 2),
                        "risco_receita": round((df_regiao['categoria'] == 'Risco: Queda em Receita').sum() / len(df_regiao) * 100, 2),
                "risco_engajamento": round((df_regiao['categoria'] == 'Risco: Queda em Engajamento').sum() / len(df_regiao) * 100, 2),
                    },
                    "top_3": df_regiao.nlargest(3, 'score_geral')[[id_col, 'score_geral', 'categoria', 'regiao']].to_dict('records')
                }
                resumo["distribuicao_regiao"][regiao] = len(df_regiao)
    
    # Adiciona análise por nível VIP
    if 'nivel_vip' in df.columns:
        resumo["analise_vip"] = {}
        resumo["distribuicao_vip"] = {}
        
        for nivel in sorted(df['nivel_vip'].dropna().unique()):
            nivel_int = int(nivel)
            df_vip = df[df['nivel_vip'] == nivel]
            vip_info = get_vip_info(nivel_int)
            
            resumo["analise_vip"][f"vip_{nivel_int}"] = {
                "nivel": nivel_int,
                "nome": vip_info['nome'],
                "cor": vip_info['cor'],
                "icone": vip_info['icone'],
                "quantidade": len(df_vip),
                "percentual": round(len(df_vip) / total * 100, 2),
                "score_geral_medio": round(df_vip['score_geral'].mean(), 2),
                "score_login_medio": round(df_vip['score_login'].mean(), 2),
                "score_engajamento_medio": round(df_vip['score_engajamento'].mean(), 2),
                "score_compras_medio": round(df_vip['score_compras'].mean(), 2),
                "percentual_ativos": round((df_vip['ativo'].sum() / len(df_vip) * 100), 2) if len(df_vip) > 0 else 0,
                "distribuicao_categorias": {
                    "elite": round((df_vip['categoria'] == 'Elite').sum() / len(df_vip) * 100, 2),
                    "muito_bom": round((df_vip['categoria'] == 'Muito bom').sum() / len(df_vip) * 100, 2),
                    "estavel": round((df_vip['categoria'] == 'Estável').sum() / len(df_vip) * 100, 2),
                    "baixo": round((df_vip['categoria'] == 'Baixo').sum() / len(df_vip) * 100, 2),
                    "risco_receita": round((df_vip['categoria'] == 'Risco: Queda em Receita').sum() / len(df_vip) * 100, 2),
                "risco_engajamento": round((df_vip['categoria'] == 'Risco: Queda em Engajamento').sum() / len(df_vip) * 100, 2),
                },
                "top_3": df_vip.nlargest(3, 'score_geral')[[id_col, 'score_geral', 'categoria']].to_dict('records')
            }
            
            resumo["distribuicao_vip"][vip_info['nome']] = len(df_vip)
    
    return resumo


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve a página principal"""
    return FileResponse("templates/index.html")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Recebe upload de CSV ou Excel e processa os dados com parâmetros dinâmicos"""
    global cached_data
    
    file_type = detectar_tipo_arquivo(file.filename)
    
    if file_type == 'unknown':
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV ou Excel (.xlsx/.xls)")
    
    try:
        contents = await file.read()
        
        if file_type == 'csv':
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')), sep=None, engine='python')
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Processa dados com parâmetros dinâmicos
        df_processado, params = processar_dados_jogadores(df)
        
        # Gera resumo
        resumo = gerar_resumo_dashboard(df_processado, params)
        
        # Armazena em cache
        cached_data = {
            'df': df_processado,
            'resumo': resumo,
            'params': params,
            'timestamp': datetime.now()
        }
        
        # Limpa valores para JSON
        resumo_clean = clean_for_json(resumo)
        
        return {
            "success": True,
            "message": f"Processados {len(df)} jogadores com parâmetros dinâmicos",
            "resumo": resumo_clean
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Erro ao processar arquivo: {str(e)}"
        print(f"\n{'='*60}")
        print("ERRO NO UPLOAD:")
        print(f"{'='*60}")
        print(error_msg)
        print("\nTraceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/dados")
async def get_dados():
    """Retorna dados processados em cache"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    # Converte DataFrame para dict limpando NaN
    df = cached_data['df']
    dados_dict = df.astype(object).where(pd.notnull(df), None).to_dict('records')
    
    return {
        "resumo": cached_data['resumo'],
        "dados_completos": clean_for_json(dados_dict)
    }


@app.get("/api/regiao/{regiao}")
async def get_dados_regiao(regiao: str):
    """Retorna dados filtrados por região (es, br, int)"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    df = cached_data['df']
    
    if 'regiao' not in df.columns:
        raise HTTPException(status_code=400, detail="Dados não possuem informação de região")
    
    if regiao not in ['es', 'br', 'int']:
        raise HTTPException(status_code=400, detail="Região inválida. Use: es, br, int")
    
    df_regiao = df[df['regiao'] == regiao]
    
    # Recalcula o resumo para esta região
    from copy import deepcopy
    resumo_base = deepcopy(cached_data['resumo'])
    
    # Substitui com dados da região específica
    if 'analise_regiao' in resumo_base and regiao in resumo_base['analise_regiao']:
        resumo_regiao = resumo_base['analise_regiao'][regiao]
        # Atualiza campos principais
        resumo_base['total_jogadores'] = resumo_regiao['quantidade']
        resumo_base['percentual_ativos'] = resumo_regiao['percentual_ativos']
        resumo_base['media_saude_login'] = resumo_regiao['score_login_medio']
        resumo_base['media_saude_engajamento'] = resumo_regiao['score_engajamento_medio']
        resumo_base['media_saude_compras'] = resumo_regiao['score_compras_medio']
        resumo_base['media_pontuacao_geral'] = resumo_regiao['score_geral_medio']
        resumo_base['distribuicao_categorias'] = resumo_regiao['distribuicao_categorias']
        resumo_base['regiao_atual'] = regiao
        resumo_base['regiao_nome'] = resumo_regiao['nome']
    
    return {
        "regiao": regiao,
        "nome": get_regiao_nome(regiao),
        "quantidade": len(df_regiao),
        "resumo": resumo_base,
        "jogadores": df_regiao.to_dict('records')
    }


@app.get("/api/vip/{nivel}")
async def get_dados_vip(nivel: int):
    """Retorna dados filtrados por nível VIP"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    df = cached_data['df']
    
    if 'nivel_vip' not in df.columns:
        raise HTTPException(status_code=400, detail="Dados não possuem informação de nível VIP")
    
    df_vip = df[df['nivel_vip'] == nivel]
    vip_info = get_vip_info(nivel)
    
    return {
        "nivel": nivel,
        "nome": vip_info['nome'],
        "cor": vip_info['cor'],
        "icone": vip_info['icone'],
        "quantidade": len(df_vip),
        "jogadores": df_vip.to_dict('records')
    }


@app.get("/api/vip")
async def get_resumo_vip():
    """Retorna resumo estatístico por nível VIP"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    resumo = cached_data['resumo']
    
    if 'analise_vip' not in resumo:
        raise HTTPException(status_code=400, detail="Dados não possuem análise por VIP")
    
    return resumo['analise_vip']


@app.get("/api/export/csv")
async def export_csv():
    """Exporta dados processados como CSV"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado para exportar")
    
    df = cached_data['df']
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=health_score_resultado.csv"}
    )


@app.get("/api/export/excel")
async def export_excel():
    """Exporta dados processados como Excel com parâmetros dinâmicos"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado para exportar")
    
    df = cached_data['df']
    resumo = cached_data['resumo']
    params = cached_data['params']
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba com dados completos
        df.to_excel(writer, sheet_name='Jogadores', index=False)
        
        # Aba com resumo
        resumo_df = pd.DataFrame([{
            'Data': resumo['data'],
            'Total Jogadores': resumo['total_jogadores'],
            '% Ativos': resumo['percentual_ativos'],
            'Média Saúde Login': resumo['media_saude_login'],
            'Média Saúde Engajamento': resumo['media_saude_engajamento'],
            'Média Saúde Compras': resumo['media_saude_compras'],
            'Média Pontuação Geral': resumo['media_pontuacao_geral'],
            '% Elite': resumo['distribuicao_categorias']['elite'],
            '% Muito Bom': resumo['distribuicao_categorias']['muito_bom'],
            '% Estável': resumo['distribuicao_categorias']['estavel'],
            '% Baixo': resumo['distribuicao_categorias']['baixo'],
            '% Risco Queda Receita': resumo['distribuicao_categorias']['risco_receita'],
            '% Risco Queda Engajamento': resumo['distribuicao_categorias']['risco_engajamento'],
        }])
        resumo_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Aba com parâmetros dinâmicos calculados
        params_data = []
        for k, v in params.items():
            if isinstance(v, (int, float)):
                params_data.append({'Parametro': k, 'Valor': round(v, 4)})
            else:
                params_data.append({'Parametro': k, 'Valor': v})
        params_df = pd.DataFrame(params_data)
        params_df.to_excel(writer, sheet_name='Parametros_Dinamicos', index=False)
        
        # Aba com benchmarks comparativos (igual ao Excel)
        benchmarks_data = [
            {'Métrica': 'Torneios', 'Média 3d': resumo['estatisticas']['media_torneios_3d'], 
             'Mediana': resumo['estatisticas']['mediana_torneios_3d'],
             'DesvPad': resumo['estatisticas']['desvpad_torneios_3d'], 
             'Por Dia': resumo['benchmarks']['torneios_por_dia']},
            {'Métrica': 'Maratonas', 'Média 3d': resumo['estatisticas']['media_maratonas_3d'],
             'Mediana': resumo['estatisticas']['mediana_maratonas_3d'],
             'DesvPad': resumo['estatisticas']['desvpad_maratonas_3d'], 
             'Por Dia': resumo['benchmarks']['maratonas_por_dia']},
            {'Métrica': 'Missões', 'Média 3d': resumo['estatisticas']['media_missoes_3d'],
             'Mediana': resumo['estatisticas']['mediana_missoes_3d'],
             'DesvPad': resumo['estatisticas']['desvpad_missoes_3d'], 
             'Por Dia': resumo['benchmarks']['missoes_por_dia']},
            {'Métrica': 'Promos', 'Média 3d': resumo['estatisticas']['media_promos_3d'],
             'Mediana': resumo['estatisticas']['mediana_promos_3d'],
             'DesvPad': resumo['estatisticas']['desvpad_promos_3d'], 
             'Por Dia': resumo['benchmarks']['promos_por_dia']},
        ]
        benchmarks_df = pd.DataFrame(benchmarks_data)
        benchmarks_df.to_excel(writer, sheet_name='Benchmarks', index=False)
        
        # Aba com análise por nível VIP
        if 'analise_vip' in resumo:
            vip_data = []
            for vip_key, vip_stats in resumo['analise_vip'].items():
                vip_data.append({
                    'Nível': vip_stats['nivel'],
                    'Nome': vip_stats['nome'],
                    'Quantidade': vip_stats['quantidade'],
                    '% do Total': vip_stats['percentual'],
                    'Score Geral Médio': vip_stats['score_geral_medio'],
                    'Score Login Médio': vip_stats['score_login_medio'],
                    'Score Engajamento Médio': vip_stats['score_engajamento_medio'],
                    'Score Compras Médio': vip_stats['score_compras_medio'],
                    '% Ativos': vip_stats['percentual_ativos'],
                    '% Elite': vip_stats['distribuicao_categorias']['elite'],
                    '% Muito Bom': vip_stats['distribuicao_categorias']['muito_bom'],
                    '% Estável': vip_stats['distribuicao_categorias']['estavel'],
                    '% Baixo': vip_stats['distribuicao_categorias']['baixo'],
                    '% Risco Queda Receita': vip_stats['distribuicao_categorias']['risco_receita'],
                    '% Risco Queda Engajamento': vip_stats['distribuicao_categorias']['risco_engajamento'],
                })
            vip_df = pd.DataFrame(vip_data)
            vip_df.to_excel(writer, sheet_name='Analise_VIP', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=health_score_resultado.xlsx"}
    )


# ========== ENDPOINTS DE HISTÓRICO ==========

@app.post("/api/historico/salvar")
async def salvar_historico(request: Dict[str, Any]):
    """Salva o estado atual como snapshot do dia"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    resumo = cached_data['resumo']
    filtros = request.get('filtros', {})
    data_custom = request.get('data')  # Data do arquivo, se informada
    
    snapshot_id = salvar_snapshot(resumo, filtros, data_custom)
    
    return {
        "success": True,
        "message": "Dados do dia salvos com sucesso",
        "snapshot_id": snapshot_id,
        "data": data_custom or datetime.now().strftime("%Y-%m-%d")
    }


@app.delete("/api/historico/{snapshot_id}")
async def deletar_historico(snapshot_id: int):
    """Deleta um snapshot específico pelo ID"""
    sucesso = deletar_snapshot(snapshot_id=snapshot_id)
    
    if sucesso:
        return {
            "success": True,
            "message": f"Snapshot {snapshot_id} deletado com sucesso"
        }
    else:
        raise HTTPException(status_code=404, detail="Snapshot não encontrado")


@app.delete("/api/historico/data/{data}")
async def deletar_historico_por_data(data: str):
    """Deleta todos os snapshots de uma data específica (YYYY-MM-DD)"""
    sucesso = deletar_snapshot(data=data)
    
    if sucesso:
        return {
            "success": True,
            "message": f"Snapshots de {data} deletados com sucesso"
        }
    else:
        raise HTTPException(status_code=404, detail="Nenhum snapshot encontrado para esta data")


@app.get("/api/historico")
async def get_historico(
    regiao: str = Query(None, description="Filtro por região (es, br, int, all)"),
    vip: str = Query(None, description="Filtro por VIP (1-5, all)"),
    dias: int = Query(30, description="Número de dias no histórico")
):
    """Retorna histórico de snapshots com filtros"""
    historico = listar_historico(regiao, vip, dias)
    return {
        "success": True,
        "quantidade": len(historico),
        "historico": historico
    }


@app.get("/api/historico/comparar")
async def comparar_historico(
    inicio: str = Query(..., description="Data início (YYYY-MM-DD)"),
    fim: str = Query(..., description="Data fim (YYYY-MM-DD)")
):
    """Compara dados entre dois períodos"""
    comparacao = comparar_periodos(inicio, fim)
    return {
        "success": True,
        "comparacao": comparacao
    }


@app.get("/api/historico/executivo")
async def get_resumo_executivo(
    dias: int = Query(7, description="Dias para análise")
):
    """Retorna resumo executivo para apresentações"""
    historico = listar_historico(dias=dias)
    
    if not historico:
        return {
            "success": False,
            "message": "Nenhum histórico encontrado"
        }
    
    # Último dia disponível
    ultimo = historico[0]
    
    # Calcular variações se houver histórico anterior
    variacoes = {}
    if len(historico) > 1:
        anterior = historico[1]
        variacoes = {
            'total_jogadores': round(ultimo['total_jogadores'] - anterior['total_jogadores'], 0),
            'percentual_ativos': round(ultimo['percentual_ativos'] - anterior['percentual_ativos'], 2),
            'score_geral': round(ultimo['media_score_geral'] - anterior['media_score_geral'], 2),
        }
    
    # Totais por cluster (último dia)
    clusters = ultimo['clusters']
    total_jogadores = ultimo['total_jogadores']
    
    return {
        "success": True,
        "data_referencia": ultimo['data'],
        "indicadores_principais": {
            "total_jogadores": ultimo['total_jogadores'],
            "percentual_ativos": ultimo['percentual_ativos'],
            "score_geral_medio": ultimo['media_score_geral'],
            "score_engajamento_medio": ultimo['media_score_engajamento'],
            "score_compras_medio": ultimo['media_score_compras'],
        },
        "variacoes_dia": variacoes,
        "distribuicao_clusters": {
            "Elite": {"qtd": clusters['Elite'], "pct": round(clusters['Elite']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "Muito bom": {"qtd": clusters['Muito bom'], "pct": round(clusters['Muito bom']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "Estável": {"qtd": clusters['Estável'], "pct": round(clusters['Estável']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "Baixo": {"qtd": clusters['Baixo'], "pct": round(clusters['Baixo']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "Risco Receita": {"qtd": clusters['Risco: Queda em Receita'], "pct": round(clusters['Risco: Queda em Receita']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "Risco Engajamento": {"qtd": clusters['Risco: Queda em Engajamento'], "pct": round(clusters['Risco: Queda em Engajamento']/total_jogadores*100, 1) if total_jogadores > 0 else 0},
        },
        "evolucao": [
            {
                "data": h['data'],
                "total_jogadores": h['total_jogadores'],
                "percentual_ativos": h['percentual_ativos'],
                "score_geral": h['media_score_geral'],
            } for h in historico[:7]  # Últimos 7 dias
        ]
    }


@app.get("/api/sample")
async def generate_sample():
    """Gera dados de exemplo para teste com distribuição por região"""
    np.random.seed(42)
    n = 100
    
    # Distribuição de traduções: 40% BR, 35% ES, 25% INT
    traducoes = (['pt_BR'] * 40) + (['es_AR'] * 15) + (['es_ES'] * 10) + (['es_LA'] * 5) + (['es_MX'] * 5) + (['en_US'] * 10) + (['fr_FR'] * 5) + (['de_DE'] * 5) + (['it_IT'] * 5)
    
    sample_data = pd.DataFrame({
        'player_id': [f'PLAYER_{i:04d}' for i in range(1, n+1)],
        'nivel_vip': np.random.choice([1, 2, 3, 4, 5], n, p=[0.3, 0.3, 0.2, 0.15, 0.05]),
        'lastLogin': [(datetime.now() - timedelta(days=np.random.exponential(5))).strftime('%Y-%m-%d') for _ in range(n)],
        'translation': np.random.choice(traducoes, n),
        'qtd_logins_3d': np.random.poisson(2, n),
        'qtd_compras_7d': np.random.poisson(1, n),
        'qtd_torneios_3d': np.random.poisson(15, n),
        'qtd_maratonas_3d': np.random.poisson(5, n),
        'qtd_missoes_3d': np.random.poisson(8, n),
        'qtd_promos_3d': np.random.poisson(6, n),
        'ticket_medio_7d': np.random.exponential(30, n),
    })
    
    # Processa os dados de exemplo
    df_processado, params = processar_dados_jogadores(sample_data)
    resumo = gerar_resumo_dashboard(df_processado, params)
    
    # Atualiza cache
    cached_data = {
        'df': df_processado,
        'resumo': resumo,
        'params': params,
        'timestamp': datetime.now()
    }
    
    return {
        "success": True,
        "message": "Dados de exemplo gerados com parâmetros dinâmicos",
        "resumo": resumo
    }


if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("  Health Score Dashboard - Iniciando servidor...")
    print("=" * 60)
    print()
    print("  Acesse no navegador:")
    print("  http://localhost:8080")
    print()
    print("  Pressione CTRL+C para parar")
    print("=" * 60)
    print()
    uvicorn.run(app, host="127.0.0.1", port=8080)
