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
import sys
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Detecta ambiente
def get_base_dir():
    """Retorna o diretório base do aplicativo"""
    if getattr(sys, 'frozen', False):
        # Rodando como executável PyInstaller
        # No modo onefile, sys._MEIPASS aponta para a pasta temporária
        # onde os arquivos são extraídos
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            # Fallback para o diretório do executável
            return os.path.dirname(sys.executable)
    elif 'PYTHONANYWHERE_DOMAIN' in os.environ:
        # PythonAnywhere
        return os.path.dirname(os.path.abspath(__file__))
    else:
        # Desenvolvimento local
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ
IS_FROZEN = getattr(sys, 'frozen', False)

app = FastAPI(title="Health Score Dashboard", version="2.8.0")

# Configuração do banco de dados SQLite
DB_PATH = os.path.join(BASE_DIR, "historico.db")

print(f"[INFO] Base dir: {BASE_DIR}")
print(f"[INFO] DB path: {DB_PATH}")
print(f"[INFO] Frozen: {IS_FROZEN}")
print(f"[INFO] PythonAnywhere: {IS_PYTHONANYWHERE}")

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
    
    # NOVA TABELA: Acompanhamento individual de jogadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            data TEXT NOT NULL,
            data_timestamp TEXT NOT NULL,
            
            -- Scores calculados
            score_geral REAL,
            score_engajamento REAL,
            score_compras REAL,
            score_login REAL,
            
            -- Métricas brutas de compras
            qtd_compras_7d INTEGER,
            ticket_medio_7d REAL,
            
            -- Métricas brutas de engajamento
            qtd_torneios_3d INTEGER,
            qtd_maratonas_3d INTEGER,
            qtd_missoes_3d INTEGER,
            qtd_promos_3d INTEGER,
            qtd_logins_3d INTEGER,
            
            -- Classificação
            categoria TEXT,
            nivel_vip INTEGER,
            regiao TEXT,
            
            -- Campanhas (para análise de eficácia)
            campanha_nome TEXT,
            
            -- Índices para consultas rápidas
            FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
        )
    ''')
    
    # Índices para performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_player_date 
        ON player_snapshots(player_id, data)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_date 
        ON player_snapshots(data)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_categoria 
        ON player_snapshots(categoria)
    ''')
    
    # Índice UNIQUE para evitar duplicatas (um registro por jogador por dia)
    # Primeiro, remove duplicatas existentes (mantém o registro com maior id = mais recente)
    try:
        cursor.execute('''
            DELETE FROM player_snapshots 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM player_snapshots 
                GROUP BY player_id, data
            )
        ''')
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"[INFO] {deleted} registros duplicados removidos de player_snapshots")
    except Exception as e:
        print(f"[WARN] Erro ao remover duplicatas: {e}")
    
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_player_snapshots_unique 
        ON player_snapshots(player_id, data)
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

# Configurar caminhos de arquivos estáticos
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Se estiver em _internal (PyInstaller), usa esse caminho
if IS_FROZEN and not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(BASE_DIR, "_internal", "static")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "_internal", "templates")

print(f"[INFO] Static dir: {STATIC_DIR}")
print(f"[INFO] Templates dir: {TEMPLATES_DIR}")

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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


def media_sem_zeros(serie) -> float:
    """
    Calcula média desconsiderando zeros e valores nulos.
    Apenas participantes ativos entram no cálculo.
    """
    if serie is None or len(serie) == 0:
        return 0
    
    # Filtra apenas valores > 0 (participantes ativos)
    valores_validos = serie[serie > 0]
    
    if len(valores_validos) == 0:
        return 0
    
    return valores_validos.mean()


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
        
        # Torneios - média apenas de quem participou (ignora zeros)
        col_torneios = encontrar_coluna(col_mapping['torneios'])
        if col_torneios:
            media_torneios_3d = media_sem_zeros(df[col_torneios])
            params['torneios_por_dia'] = media_torneios_3d / 3
            params['media_torneios_3d'] = media_torneios_3d
            # Desvio padrão e mediana também ignorando zeros
            valores_torneios = df[col_torneios][df[col_torneios] > 0]
            params['desvpad_torneios_3d'] = valores_torneios.std() if len(valores_torneios) > 0 else 0
            params['mediana_torneios_3d'] = valores_torneios.median() if len(valores_torneios) > 0 else 0
        else:
            params['torneios_por_dia'] = DEFAULT_PARAMS['torneios_por_dia']
        
        # Maratonas - média apenas de quem participou (ignora zeros)
        col_maratonas = encontrar_coluna(col_mapping['maratonas'])
        if col_maratonas:
            media_maratonas_3d = media_sem_zeros(df[col_maratonas])
            params['maratonas_por_dia'] = media_maratonas_3d / 3
            params['media_maratonas_3d'] = media_maratonas_3d
            valores_maratonas = df[col_maratonas][df[col_maratonas] > 0]
            params['desvpad_maratonas_3d'] = valores_maratonas.std() if len(valores_maratonas) > 0 else 0
            params['mediana_maratonas_3d'] = valores_maratonas.median() if len(valores_maratonas) > 0 else 0
        else:
            params['maratonas_por_dia'] = DEFAULT_PARAMS['maratonas_por_dia']
        
        # Missões - média apenas de quem participou (ignora zeros)
        col_missoes = encontrar_coluna(col_mapping['missoes'])
        if col_missoes:
            media_missoes_3d = media_sem_zeros(df[col_missoes])
            params['missoes_por_dia'] = media_missoes_3d / 3
            params['media_missoes_3d'] = media_missoes_3d
            valores_missoes = df[col_missoes][df[col_missoes] > 0]
            params['desvpad_missoes_3d'] = valores_missoes.std() if len(valores_missoes) > 0 else 0
            params['mediana_missoes_3d'] = valores_missoes.median() if len(valores_missoes) > 0 else 0
        else:
            params['missoes_por_dia'] = DEFAULT_PARAMS['missoes_por_dia']
        
        # Promoções - média apenas de quem participou (ignora zeros)
        col_promos = encontrar_coluna(col_mapping['promos'])
        if col_promos:
            media_promos_3d = media_sem_zeros(df[col_promos])
            params['promos_por_dia'] = media_promos_3d / 3
            params['media_promos_3d'] = media_promos_3d
            valores_promos = df[col_promos][df[col_promos] > 0]
            params['desvpad_promos_3d'] = valores_promos.std() if len(valores_promos) > 0 else 0
            params['mediana_promos_3d'] = valores_promos.median() if len(valores_promos) > 0 else 0
        else:
            params['promos_por_dia'] = DEFAULT_PARAMS['promos_por_dia']
        
        # Logins - média apenas de quem logou (ignora zeros)
        col_logins = encontrar_coluna(['qtd_logins_3d', 'logins_3d'])
        if col_logins:
            params['media_logins_3d'] = media_sem_zeros(df[col_logins])
            valores_logins = df[col_logins][df[col_logins] > 0]
            params['desvpad_logins_3d'] = valores_logins.std() if len(valores_logins) > 0 else 0
            params['mediana_logins_3d'] = valores_logins.median() if len(valores_logins) > 0 else 0
        
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
    
    def calcular_score_login(self, df: pd.DataFrame, data_referencia: datetime = None) -> pd.Series:
        """
        Calcula score de login baseado em:
        - Dias desde último login (decaimento exponencial)
        - Quantidade de logins na janela de 3 dias
        
        Args:
            df: DataFrame com dados dos jogadores
            data_referencia: Data de referência para cálculo (default: datetime.now())
        """
        hoje = data_referencia if data_referencia else datetime.now()
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
        Calcula score de engajamento usando Z-Score baseado em desvio padrão,
        ajustado para garantir que 0 atividades = score baixo (0-10).
        
        Fórmula ajustada:
        - 0 atividades = 0 pontos
        - Média da amostra = 50 pontos
        - Acima da média = escala Z normal
        """
        scores = []
        
        atividades = {
            'torneios': {'col': 'qtd_torneios_3d', 'peso': 2.0},
            'maratonas': {'col': 'qtd_maratonas_3d', 'peso': 2.5},
            'missoes': {'col': 'qtd_missoes_3d', 'peso': 1.5},
            'promos': {'col': 'qtd_promos_3d', 'peso': 1.0},
            'logins': {'col': 'qtd_logins_3d', 'peso': 1.0}
        }
        
        # Calcula estatísticas para cada atividade
        stats = {}
        for key, config in atividades.items():
            col = config['col']
            if col in df.columns:
                valores = df[col].fillna(0)
                media = valores.mean()
                std = valores.std() if len(valores) > 1 else 1
                max_val = valores.max() if len(valores) > 0 else 1
                if std == 0:
                    std = 1
                stats[key] = {'media': media, 'std': std, 'max': max_val, 'peso': config['peso']}
        
        for _, row in df.iterrows():
            atividades_scores = []
            atividades_pesos = []
            
            for key, stat in stats.items():
                col = atividades[key]['col']
                valor = row.get(col, 0) or 0
                
                if valor == 0:
                    # Zero atividades = score 0 para esta atividade
                    atividade_score = 0
                else:
                    # Normalização: 0->0, média->50, máximo->100
                    # Usa fórmula híbrida: log para valores baixos, linear para altos
                    if valor <= stat['media']:
                        # Entre 0 e média: escala logarítmica suave
                        ratio = valor / stat['media'] if stat['media'] > 0 else 0
                        atividade_score = 50 * (ratio ** 0.5)  # Raiz quadrada para suavizar
                    else:
                        # Acima da média: Z-score normal
                        z_score = (valor - stat['media']) / stat['std']
                        atividade_score = 50 + (z_score * 25)
                    
                    atividade_score = max(0, min(100, atividade_score))
                
                atividades_scores.append(atividade_score * stat['peso'])
                atividades_pesos.append(stat['peso'])
            
            if atividades_scores:
                score_final = sum(atividades_scores) / sum(atividades_pesos)
                scores.append(score_final)
            else:
                scores.append(0)  # Sem dados = 0
        
        return pd.Series(scores)
    
    def calcular_score_compras(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula score de compras ajustado para garantir que 0 compras = score baixo.
        
        Fórmula ajustada:
        - 0 compras/ticket = 0 pontos
        - Média da amostra = 50 pontos
        - Acima da média = escala Z normal
        """
        scores = []
        hoje = datetime.now()
        
        # Calcula estatísticas para quantidade
        if 'qtd_compras_7d' in df.columns:
            valores_qtd = df['qtd_compras_7d'].fillna(0)
            media_qtd = valores_qtd.mean()
            std_qtd = valores_qtd.std() if len(valores_qtd) > 1 else 1
            if std_qtd == 0:
                std_qtd = 1
        else:
            media_qtd = 2
            std_qtd = 1
        
        # Calcula estatísticas para ticket
        if 'ticket_medio_7d' in df.columns:
            valores_ticket = df['ticket_medio_7d'].fillna(0)
            media_ticket = valores_ticket.mean()
            std_ticket = valores_ticket.std() if len(valores_ticket) > 1 else 1
            if std_ticket == 0:
                std_ticket = 1
        else:
            media_ticket = 50
            std_ticket = 10
        
        for _, row in df.iterrows():  
            pontuacoes = []
            pesos = []
            
            # 1. Quantidade de compras (40% de peso)
            if 'qtd_compras_7d' in df.columns:
                qtd = row.get('qtd_compras_7d', 0) or 0
                
                if qtd == 0:
                    qtd_score = 0  # Zero compras = score 0
                else:
                    # Normalização híbrida
                    if qtd <= media_qtd:
                        ratio = qtd / media_qtd if media_qtd > 0 else 0
                        qtd_score = 50 * (ratio ** 0.5)  # Raiz quadrada
                    else:
                        z_score = (qtd - media_qtd) / std_qtd
                        qtd_score = 50 + (z_score * 25)
                    qtd_score = max(0, min(100, qtd_score))
                
                pontuacoes.append(qtd_score * 0.40)
                pesos.append(0.40)
            
            # 2. Ticket médio (35% de peso)
            if 'ticket_medio_7d' in df.columns:
                ticket = row.get('ticket_medio_7d', 0) or 0
                
                if ticket == 0:
                    ticket_score = 0  # Zero ticket = score 0
                else:
                    if ticket <= media_ticket:
                        ratio = ticket / media_ticket if media_ticket > 0 else 0
                        ticket_score = 50 * (ratio ** 0.5)
                    else:
                        z_score = (ticket - media_ticket) / std_ticket
                        ticket_score = 50 + (z_score * 25)
                    ticket_score = max(0, min(100, ticket_score))
                
                pontuacoes.append(ticket_score * 0.35)
                pesos.append(0.35)
            
            # 3. Recência da última compra (25% de peso)
            if 'ultima_compra' in df.columns and pd.notna(row.get('ultima_compra')):
                try:
                    ultima = pd.to_datetime(row['ultima_compra'])
                    dias_ultima = (hoje - ultima).days
                    # Decaimento exponencial
                    recencia_score = 100 * np.exp(-max(0, dias_ultima) / 30)
                    pontuacoes.append(recencia_score * 0.25)
                    pesos.append(0.25)
                except:
                    pass
            
            if pontuacoes:
                score_final = sum(pontuacoes) / sum(pesos) if sum(pesos) > 0 else 0
                scores.append(score_final)
            else:
                scores.append(0)  # Sem dados de compra = 0
        
        return pd.Series(scores)
    
    def calcular_score_geral(self, row: pd.Series) -> float:
        """Calcula score geral ponderado"""
        engajamento = row.get('score_engajamento', 50)
        compras = row.get('score_compras', 30)
        
        # Ponderação: Engajamento 30%, Compras 70%
        return engajamento * 0.3 + compras * 0.7
    
    def categorizar_jogador(self, row: pd.Series) -> str:
        """
        Categoriza jogador com granularidade para ações de CRM:
        
        Hierarquia de categorização:
        1. Primeiro verifica oportunidades (alto engajamento + baixas compras)
        2. Depois categoriza por score geral
        3. Por fim, identifica tipo de risco
        """
        score_geral = row.get('score_geral', 50)
        score_compras = row.get('score_compras', 0)
        score_engajamento = row.get('score_engajamento', 0)
        nivel_vip = row.get('nivel_vip', 1)
        
        # OPORTUNIDADES: Alto engajamento mas compras baixas
        # Estes são prioritários para CRM pois têm potencial
        if score_engajamento >= 60 and score_compras < 40:
            if nivel_vip >= 3:
                return "💰 Oportunidade VIP"
            else:
                return "💰 Oportunidade"
        
        # POTENCIAL: Bom engajamento, compras médias
        if score_engajamento >= 40 and score_compras >= 30 and score_compras < 50:
            return "🎯 Potencial"
        
        # Categorização por score geral (alinhada com os clusters do frontend)
        # Hierarquia clara de 9 categorias principais + 3 de oportunidade
        
        # 1. OPORTUNIDADES (alto engajamento + baixas compras) - verifica primeiro
        if score_engajamento >= 60 and score_compras < 40:
            if nivel_vip >= 3:
                return "💰 Oportunidade VIP"
            else:
                return "💰 Oportunidade"
        
        # 2. POTENCIAL (bom engajamento, compras médias)
        if score_engajamento >= 40 and score_compras >= 30 and score_compras < 50:
            return "🎯 Potencial"
        
        # 3. Categorização principal por Score Geral
        if score_geral >= 80:
            return "⭐ Elite"  # Score >= 80
        elif score_geral >= 65:
            return "🏆 VIP Ativo"  # Score 65-79
        elif score_geral >= 50:
            return "📈 Bom"  # Score 50-64
        elif score_geral >= 40:
            return "📊 Estável"  # Score 40-49
        elif score_geral >= 25:
            return "⚠️ Atenção"  # Score 25-39
        elif score_geral >= 15:
            # Risco: Score 15-24 - distribui entre os dois tipos de risco
            if score_compras < score_engajamento:
                return "🚨 Risco: Queda Receita"
            else:
                return "🚨 Risco: Queda Engajamento"
        else:
            # Score < 15 = Crítico
            if score_compras < 15 and score_engajamento < 20:
                return "💎 Churn Iminente"  # Ambos críticos
            elif score_compras < score_engajamento:
                return "🚨 Risco: Queda Receita"
            else:
                return "🚨 Risco: Queda Engajamento"


def get_expectativa_vip(nivel: int) -> Dict:
    """
    Retorna expectativas de compra por nível VIP
    Usado para comparar performance real vs esperada
    """
    expectativas = {
        1: {'compras_7d': 1, 'ticket_medio': 20, 'label': 'Iniciante'},
        2: {'compras_7d': 2, 'ticket_medio': 35, 'label': 'Regular'},
        3: {'compras_7d': 3, 'ticket_medio': 50, 'label': 'Fiel'},
        4: {'compras_7d': 4, 'ticket_medio': 75, 'label': 'Premium'},
        5: {'compras_7d': 5, 'ticket_medio': 100, 'label': 'Elite'}
    }
    return expectativas.get(int(nivel) if pd.notna(nivel) else 1, expectativas[1])


def calcular_status_vip(row: pd.Series) -> str:
    """
    Compara performance do jogador com a expectativa do seu VIP
    Retorna: acima, na_media, abaixo, critico
    """
    nivel = row.get('nivel_vip', 1)
    expectativa = get_expectativa_vip(nivel)
    
    qtd_real = row.get('qtd_compras_7d', 0) or 0
    ticket_real = row.get('ticket_medio_7d', 0) or 0
    
    qtd_esperada = expectativa['compras_7d']
    ticket_esperado = expectativa['ticket_medio']
    
    # Calcula performance (0 a 200%)
    perf_qtd = (qtd_real / qtd_esperada * 100) if qtd_esperada > 0 else 0
    perf_ticket = (ticket_real / ticket_esperado * 100) if ticket_esperado > 0 else 0
    
    # Média ponderada: quantidade pesa mais
    performance = (perf_qtd * 0.6) + (perf_ticket * 0.4)
    
    if performance >= 120:
        return "🏆 Superando"
    elif performance >= 90:
        return "✅ Dentro da meta"
    elif performance >= 60:
        return "⚠️ Abaixo do esperado"
    else:
        return "🚨 Crítico"


def detectar_tipo_arquivo(filename: str) -> str:
    """Detecta o tipo de arquivo baseado na extensão"""
    if filename.lower().endswith('.csv'):
        return 'csv'
    elif filename.lower().endswith(('.xlsx', '.xls')):
        return 'excel'
    else:
        return 'unknown'


def processar_dados_jogadores(df: pd.DataFrame, data_referencia: datetime = None) -> tuple[pd.DataFrame, Dict]:
    """Processa DataFrame e adiciona scores calculados com parâmetros dinâmicos
    
    Args:
        df: DataFrame com dados dos jogadores
        data_referencia: Data de referência para cálculo de scores (ex: data do snapshot)
                         Se None, usa datetime.now()
    """
    
    # Calcula parâmetros dinâmicos a partir dos dados
    params = HealthScoreCalculator.calcular_params_dinamicos(df)
    
    # Inicializa calculador com parâmetros dinâmicos
    calc = HealthScoreCalculator(params)
    
    # Normaliza nomes de colunas
    df.columns = df.columns.str.lower().str.strip()
    
    # Renomeia colunas comuns do CRM para padrão
    if 'pid' in df.columns and 'player_id' not in df.columns:
        df = df.rename(columns={'pid': 'player_id'})
    
    # Calcula scores individuais (passando data de referência para score_login)
    df['score_login'] = calc.calcular_score_login(df, data_referencia)
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
    # Define ação sugerida baseada na categoria
    acoes_crm = {
        '⭐ Elite': '✨ Benefícios exclusivos + Personalização',
        '🏆 VIP Ativo': '🎁 Recompensas + Upsell',
        '📈 Bom': '💳 Incentivar mais compras',
        '📊 Estável': '📱 Manter ritmo + Notificações',
        '⚠️ Atenção': '🔔 Reengajamento ativo',

        '🚨 Risco: Queda Receita': '🛒 Foco em conversão',
        '🚨 Risco: Queda Engajamento': '🎮 Foco em atividades',
        '💎 Churn Iminente': '📞 Ligação + Oferta última chance',
        '💰 Oportunidade VIP': '💎 Atendimento VIP + Oferta personalizada',
        '💰 Oportunidade': '🎁 Oferta de boas-vindas + Onboarding',
        '🎯 Potencial': '📈 Nutrir + Incentivo gradual'
    }
    
    df['acao_sugerida'] = df['categoria'].map(acoes_crm)
    df['acao_sugerida'] = df['acao_sugerida'].fillna('📊 Acompanhamento geral')
    
    # Adiciona expectativa e status por VIP
    if 'nivel_vip' in df.columns:
        df['vip_expectativa'] = df['nivel_vip'].apply(lambda x: get_expectativa_vip(x)['label'])
        df['vip_status'] = df.apply(calcular_status_vip, axis=1)
    
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
    
    # Agrupa as 12 categorias com emojis nas 6 categorias do banco
    contagem = resumo.get('contagem_por_categoria', {})
    
    # Mapeamento: 12 novas categorias -> 6 grupos do banco
    cluster_elite = contagem.get('⭐ Elite', 0) + contagem.get('💰 Oportunidade VIP', 0)
    cluster_muito_bom = (contagem.get('🏆 VIP Ativo', 0) + contagem.get('📈 Bom', 0) + 
                         contagem.get('💰 Oportunidade', 0) + contagem.get('🎯 Potencial', 0))
    cluster_estavel = contagem.get('📊 Estável', 0)
    cluster_baixo = (contagem.get('⚠️ Atenção', 0) +  
                     contagem.get('💎 Churn Iminente', 0))
    cluster_risco_receita = contagem.get('🚨 Risco: Queda Receita', 0)
    cluster_risco_engajamento = contagem.get('🚨 Risco: Queda Engajamento', 0)
    
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
        cluster_elite,
        cluster_muito_bom,
        cluster_estavel,
        cluster_baixo,
        cluster_risco_receita,
        cluster_risco_engajamento,
        filtro_regiao, filtro_vip
    ))
    
    snapshot_id = cursor.lastrowid
    
    # Insere detalhes dos clusters (já calculados acima)
    total = resumo.get('total_jogadores', 1)
    
    clusters_info = [
        ('Elite', cluster_elite),
        ('Muito bom', cluster_muito_bom),
        ('Estável', cluster_estavel),
        ('Baixo', cluster_baixo),
        ('Risco: Queda em Receita', cluster_risco_receita),
        ('Risco: Queda em Engajamento', cluster_risco_engajamento),
    ]
    
    for nome, qtd in clusters_info:
        cursor.execute('''
            INSERT INTO clusters_dia (snapshot_id, cluster_nome, quantidade, percentual, score_compras_medio, score_engajamento_medio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (snapshot_id, nome, qtd, round(qtd/total*100, 2) if total > 0 else 0, 0, 0))
    
    conn.commit()
    conn.close()
    return snapshot_id


def salvar_player_snapshots(df: pd.DataFrame, data_snapshot: str = None, campanha_nome: str = None):
    """
    Salva os dados individuais de cada jogador para acompanhamento de evolução.
    Permite analisar flutuação entre clusters e impacto de campanhas.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if data_snapshot is None:
        data_snapshot = datetime.now().strftime("%Y-%m-%d")
    
    agora = datetime.now().isoformat()
    
    # Prepara dados para inserção em lote
    player_data = []
    
    for _, row in df.iterrows():
        player_data.append((
            str(row.get('player_id', row.get('pid', ''))),
            data_snapshot,
            agora,
            float(row.get('score_geral', 0)),
            float(row.get('score_engajamento', 0)),
            float(row.get('score_compras', 0)),
            float(row.get('score_login', 0)),
            int(row.get('qtd_compras_7d', 0) or 0),
            float(row.get('ticket_medio_7d', 0) or 0),
            int(row.get('qtd_torneios_3d', 0) or 0),
            int(row.get('qtd_maratonas_3d', 0) or 0),
            int(row.get('qtd_missoes_3d', 0) or 0),
            int(row.get('qtd_promos_3d', 0) or 0),
            int(row.get('qtd_logins_3d', 0) or 0),
            str(row.get('categoria', '')),
            int(row.get('nivel_vip', 1) or 1),
            str(row.get('regiao', 'int')),
            campanha_nome
        ))
    
    # Insere em lote usando INSERT OR REPLACE para evitar duplicatas
    # Se já existir registro para este player_id + data, atualiza os dados
    cursor.executemany('''
        INSERT OR REPLACE INTO player_snapshots (
            player_id, data, data_timestamp,
            score_geral, score_engajamento, score_compras, score_login,
            qtd_compras_7d, ticket_medio_7d,
            qtd_torneios_3d, qtd_maratonas_3d, qtd_missoes_3d, qtd_promos_3d, qtd_logins_3d,
            categoria, nivel_vip, regiao, campanha_nome
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', player_data)
    
    conn.commit()
    conn.close()
    
    return len(player_data)


def get_evolucao_player(player_id: str, dias: int = 30) -> Dict:
    """
    Retorna a evolução histórica de um jogador específico.
    Combina dados do histórico (player_snapshots) com dados do cache atual.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Log para debug
    print(f"[DEBUG] Buscando evolução do jogador {player_id} nos últimos {dias} dias")
    
    # Busca dados do histórico
    cursor.execute('''
        SELECT * FROM player_snapshots 
        WHERE player_id = ? 
        AND data >= date('now', '-{} days')
        ORDER BY data ASC
    '''.format(dias), (player_id,))
    
    rows = cursor.fetchall()
    
    # Também busca no cache atual (dados de upload recente não salvos no histórico)
    dados_cache = []
    if cached_data and 'df' in cached_data:
        df = cached_data['df']
        jogador_cache = df[df['player_id'] == player_id]
        if not jogador_cache.empty:
            row = jogador_cache.iloc[0]
            hoje = datetime.now().strftime('%Y-%m-%d')
            # Verifica se a data de hoje já não está no histórico
            datas_historico = [r['data'] for r in rows] if rows else []
            if hoje not in datas_historico:
                dados_cache.append({
                    'player_id': player_id,
                    'data': hoje,
                    'score_geral': row.get('score_geral', 0),
                    'score_engajamento': row.get('score_engajamento', 0),
                    'score_compras': row.get('score_compras', 0),
                    'categoria': row.get('categoria', 'N/A'),
                    'campanha_nome': None,
                    'nivel_vip': row.get('nivel_vip', 1)
                })
                print(f"[DEBUG] Adicionado dados do cache para hoje ({hoje})")
    
    # Combina dados do histórico com dados do cache
    todos_dados = list(rows) + dados_cache
    
    # Ordena por data
    todos_dados.sort(key=lambda x: x['data'] if isinstance(x, sqlite3.Row) else x['data'])
    
    print(f"[DEBUG] Total de registros (histórico + cache): {len(todos_dados)}")
    for d in todos_dados:
        data = d['data'] if isinstance(d, sqlite3.Row) else d['data']
        cat = d['categoria'] if isinstance(d, sqlite3.Row) else d['categoria']
        print(f"[DEBUG]   - Data: {data}, Categoria: {cat}")
    
    if not todos_dados:
        conn.close()
        return {"error": "Nenhum histórico encontrado para este jogador"}
    
    rows = todos_dados
    
    # Processa evolução
    evolucao = []
    flutuacao_clusters = []
    variacoes = []
    
    for i, row in enumerate(rows):
        evolucao.append({
            "data": row['data'],
            "score_geral": round(row['score_geral'], 2),
            "score_engajamento": round(row['score_engajamento'], 2),
            "score_compras": round(row['score_compras'], 2),
            "categoria": row['categoria'],
            "campanha_nome": row['campanha_nome']
        })
        
        flutuacao_clusters.append(row['categoria'])
        
        # Calcula variação em relação ao dia anterior
        if i > 0:
            var_geral = row['score_geral'] - rows[i-1]['score_geral']
            var_engajamento = row['score_engajamento'] - rows[i-1]['score_engajamento']
            var_compras = row['score_compras'] - rows[i-1]['score_compras']
            
            variacoes.append({
                "data": row['data'],
                "variacao_geral": round(var_geral, 2),
                "variacao_engajamento": round(var_engajamento, 2),
                "variacao_compras": round(var_compras, 2),
                "mudanca_cluster": row['categoria'] != rows[i-1]['categoria']
            })
    
    # Análise de clusters
    cluster_atual = rows[-1]['categoria']
    dias_no_cluster_atual = 0
    for row in reversed(rows):
        if row['categoria'] == cluster_atual:
            dias_no_cluster_atual += 1
        else:
            break
    
    # Métricas de compras e engajamento
    metricas_compras = {
        "tendencia": "crescente" if len(rows) > 1 and rows[-1]['score_compras'] > rows[0]['score_compras'] else "decrescente",
        "maior_score": round(max(r['score_compras'] for r in rows), 2),
        "menor_score": round(min(r['score_compras'] for r in rows), 2),
        "media": round(sum(r['score_compras'] for r in rows) / len(rows), 2)
    }
    
    metricas_engajamento = {
        "tendencia": "crescente" if len(rows) > 1 and rows[-1]['score_engajamento'] > rows[0]['score_engajamento'] else "decrescente",
        "maior_score": round(max(r['score_engajamento'] for r in rows), 2),
        "menor_score": round(min(r['score_engajamento'] for r in rows), 2),
        "media": round(sum(r['score_engajamento'] for r in rows) / len(rows), 2)
    }
    
    conn.close()
    
    return {
        "player_id": player_id,
        "total_registros": len(rows),
        "periodo_dias": dias,
        "cluster_atual": cluster_atual,
        "dias_no_cluster_atual": dias_no_cluster_atual,
        "historico_clusters": list(dict.fromkeys(flutuacao_clusters)),  # Remove duplicatas mantendo ordem
        "evolucao": evolucao,
        "variacoes": variacoes,
        "metricas_compras": metricas_compras,
        "metricas_engajamento": metricas_engajamento,
        "resumo": {
            "mudancas_cluster": sum(1 for v in variacoes if v['mudanca_cluster']),
            "variacao_total_geral": round(rows[-1]['score_geral'] - rows[0]['score_geral'], 2) if len(rows) > 1 else 0,
            "variacao_total_compras": round(rows[-1]['score_compras'] - rows[0]['score_compras'], 2) if len(rows) > 1 else 0,
            "variacao_total_engajamento": round(rows[-1]['score_engajamento'] - rows[0]['score_engajamento'], 2) if len(rows) > 1 else 0
        }
    }


def get_players_com_flutuacao(cluster_origem: str = None, cluster_destino: str = None, 
                               dias: int = 7, tipo_flutuacao: str = 'melhora') -> List[Dict]:
    """
    Identifica jogadores que mudaram de cluster significativamente.
    
    tipo_flutuacao: 'melhora' (ex: Baixo -> Bom), 'piora' (ex: Bom -> Baixo), 'qualquer'
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Busca todos os jogadores com histórico no período
    cursor.execute('''
        SELECT player_id, COUNT(*) as total_registros
        FROM player_snapshots 
        WHERE data >= date('now', '-{} days')
        GROUP BY player_id
        HAVING total_registros >= 2
    '''.format(dias))
    
    players = cursor.fetchall()
    
    resultado = []
    
    for player in players:
        player_id = player['player_id']
        
        # Busca primeiro e último registro do período
        cursor.execute('''
            SELECT * FROM player_snapshots 
            WHERE player_id = ? 
            AND data >= date('now', '-{} days')
            ORDER BY data ASC
            LIMIT 1
        '''.format(dias), (player_id,))
        
        primeiro = cursor.fetchone()
        
        cursor.execute('''
            SELECT * FROM player_snapshots 
            WHERE player_id = ? 
            AND data >= date('now', '-{} days')
            ORDER BY data DESC
            LIMIT 1
        '''.format(dias), (player_id,))
        
        ultimo = cursor.fetchone()
        
        if not primeiro or not ultimo:
            continue
        
        # Verifica filtros de cluster
        if cluster_origem and primeiro['categoria'] != cluster_origem:
            continue
        if cluster_destino and ultimo['categoria'] != cluster_destino:
            continue
        
        # Determina se é melhora ou piora
        # Ordem de "qualidade": Elite > VIP Ativo > Bom > Estável > Atenção > Risco
        ordem_clusters = ['⭐ Elite', '🏆 VIP Ativo', '📈 Bom', '📊 Estável', 
                         '⚠️ Atenção', '🚨 Risco: Queda Receita', 
                         '🚨 Risco: Queda Engajamento', '💎 Churn Iminente']
        
        idx_origem = ordem_clusters.index(primeiro['categoria']) if primeiro['categoria'] in ordem_clusters else 999
        idx_destino = ordem_clusters.index(ultimo['categoria']) if ultimo['categoria'] in ordem_clusters else 999
        
        melhorou = idx_destino < idx_origem
        piorou = idx_destino > idx_origem
        
        if tipo_flutuacao == 'melhora' and not melhorou:
            continue
        if tipo_flutuacao == 'piora' and not piorou:
            continue
        if tipo_flutuacao == 'qualquer' and idx_origem == idx_destino:
            continue
        
        resultado.append({
            "player_id": player_id,
            "cluster_origem": primeiro['categoria'],
            "cluster_destino": ultimo['categoria'],
            "data_inicio": primeiro['data'],
            "data_fim": ultimo['data'],
            "variacao_score": round(ultimo['score_geral'] - primeiro['score_geral'], 2),
            "variacao_compras": round(ultimo['score_compras'] - primeiro['score_compras'], 2),
            "variacao_engajamento": round(ultimo['score_engajamento'] - primeiro['score_engajamento'], 2),
            "melhorou": melhorou,
            "campanha_inicio": primeiro['campanha_nome'],
            "campanha_fim": ultimo['campanha_nome']
        })
    
    conn.close()
    
    # Ordena por maior variação de score
    resultado.sort(key=lambda x: abs(x['variacao_score']), reverse=True)
    
    return resultado


def calcular_distribuicao_categorias(data: str, regiao: str = None, vip: str = None) -> Dict[str, int]:
    """
    Calcula a distribuição de categorias a partir dos dados individuais dos jogadores.
    RECALCULA os scores a partir dos valores brutos usando a nova fórmula.
    """
    from statistics import mean, stdev
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Busca todos os dados brutos necessários
    query = """
        SELECT player_id, nivel_vip, regiao,
               qtd_torneios_3d, qtd_maratonas_3d, qtd_missoes_3d, qtd_promos_3d, qtd_logins_3d,
               qtd_compras_7d, ticket_medio_7d
        FROM player_snapshots 
        WHERE data = ?
    """
    params = [data]
    
    if regiao and regiao != 'all':
        query += " AND regiao = ?"
        params.append(regiao)
    if vip and vip != 'all':
        query += " AND nivel_vip = ?"
        params.append(int(vip))
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {c: 0 for c in ['⭐ Elite', '🏆 VIP Ativo', '📈 Bom', '📊 Estável', '⚠️ Atenção', 
                               '🚨 Risco: Queda Receita', '🚨 Risco: Queda Engajamento', 
                               '💎 Churn Iminente', '💰 Oportunidade VIP', '💰 Oportunidade', '🎯 Potencial']}
    
    # Calcula estatísticas globais
    todos_torneios = [r['qtd_torneios_3d'] or 0 for r in rows]
    todos_maratonas = [r['qtd_maratonas_3d'] or 0 for r in rows]
    todos_missoes = [r['qtd_missoes_3d'] or 0 for r in rows]
    todos_promos = [r['qtd_promos_3d'] or 0 for r in rows]
    todos_logins = [r['qtd_logins_3d'] or 0 for r in rows]
    todos_compras = [r['qtd_compras_7d'] or 0 for r in rows]
    todos_tickets = [r['ticket_medio_7d'] or 0 for r in rows]
    
    def calc_stats(valores):
        m = mean(valores) if valores else 0
        s = stdev(valores) if len(valores) > 1 else 1
        if s == 0:
            s = 1
        return m, s
    
    media_torneios, std_torneios = calc_stats(todos_torneios)
    media_maratonas, std_maratonas = calc_stats(todos_maratonas)
    media_missoes, std_missoes = calc_stats(todos_missoes)
    media_promos, std_promos = calc_stats(todos_promos)
    media_logins, std_logins = calc_stats(todos_logins)
    media_compras, std_compras = calc_stats(todos_compras)
    media_tickets, std_tickets = calc_stats(todos_tickets)
    
    def calcular_score_atividade(valor, media, std):
        """Calcula score de uma atividade (0-100)"""
        if valor == 0:
            return 0
        if valor <= media:
            ratio = valor / media if media > 0 else 0
            return 50 * (ratio ** 0.5)
        else:
            z_score = (valor - media) / std
            return min(100, 50 + (z_score * 25))
    
    # Inicializa contadores
    categorias = {
        '⭐ Elite': 0, '🏆 VIP Ativo': 0, '📈 Bom': 0, '📊 Estável': 0, '⚠️ Atenção': 0,
        '🚨 Risco: Queda Receita': 0, '🚨 Risco: Queda Engajamento': 0,
        '💎 Churn Iminente': 0, '💰 Oportunidade VIP': 0, '💰 Oportunidade': 0, '🎯 Potencial': 0
    }
    
    for row in rows:
        # Recalcula score de engajamento
        s_torneios = calcular_score_atividade(row['qtd_torneios_3d'] or 0, media_torneios, std_torneios) * 2.0
        s_maratonas = calcular_score_atividade(row['qtd_maratonas_3d'] or 0, media_maratonas, std_maratonas) * 2.5
        s_missoes = calcular_score_atividade(row['qtd_missoes_3d'] or 0, media_missoes, std_missoes) * 1.5
        s_promos = calcular_score_atividade(row['qtd_promos_3d'] or 0, media_promos, std_promos) * 1.0
        s_logins = calcular_score_atividade(row['qtd_logins_3d'] or 0, media_logins, std_logins) * 1.0
        
        peso_total_eng = 8.0
        score_engajamento = (s_torneios + s_maratonas + s_missoes + s_promos + s_logins) / peso_total_eng
        
        # Recalcula score de compras
        s_qtd = calcular_score_atividade(row['qtd_compras_7d'] or 0, media_compras, std_compras) * 0.40
        s_ticket = calcular_score_atividade(row['ticket_medio_7d'] or 0, media_tickets, std_tickets) * 0.35
        
        # Recência
        s_recencia = 0
        peso_recencia = 0
        if row['qtd_compras_7d'] and row['qtd_compras_7d'] > 0:
            s_recencia = 100 * 0.25
            peso_recencia = 0.25
        
        peso_total_comp = 0.40 + 0.35 + peso_recencia
        score_compras = (s_qtd + s_ticket + s_recencia) / peso_total_comp if peso_total_comp > 0 else 0
        
        # Score geral
        score_geral = score_engajamento * 0.3 + score_compras * 0.7
        
        nivel_vip = row['nivel_vip'] or 1
        
        # Recalcula categoria
        categoria = recalcular_categoria(score_geral, score_engajamento, score_compras, nivel_vip)
        if categoria in categorias:
            categorias[categoria] += 1
    
    return categorias


def listar_historico(regiao: str = None, vip: str = None, dias: int = 30) -> List[Dict]:
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
    
    query += " ORDER BY data ASC LIMIT ?"  # Ordena por data do snapshot (mais antigo primeiro)
    params.append(dias)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    historico = []
    for row in rows:
        # Calcula distribuição de categorias a partir dos dados individuais
        # Isso garante que tenhamos todas as 9+ categorias separadas, não agrupadas
        distribuicao = calcular_distribuicao_categorias(row['data'], regiao, vip)
        
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
            'clusters': distribuicao,  # Usa distribuição calculada dos dados individuais
            'filtro_regiao': row['filtro_regiao'],
            'filtro_vip': row['filtro_vip'],
        })
    
    conn.close()
    return historico


def deletar_snapshot(snapshot_id: int = None, data: str = None) -> bool:
    """Deleta um snapshot por ID ou por data"""
    print(f"[DEBUG] deletar_snapshot chamado - snapshot_id={snapshot_id}, data={data}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        total_afetado = 0
        data_para_deletar = None
        
        if snapshot_id:
            print(f"[DEBUG] Verificando se snapshot {snapshot_id} existe...")
            cursor.execute('SELECT id, data FROM snapshots WHERE id = ?', (snapshot_id,))
            resultado = cursor.fetchone()
            print(f"[DEBUG] Snapshot existe: {resultado is not None}")
            
            if not resultado:
                conn.close()
                return False
            
            # Guarda a data para deletar player_snapshots depois
            data_para_deletar = resultado[1]
            
            # Deleta clusters primeiro (foreign key)
            print(f"[DEBUG] Deletando clusters do snapshot {snapshot_id}...")
            cursor.execute('DELETE FROM clusters_dia WHERE snapshot_id = ?', (snapshot_id,))
            clusters_deletados = cursor.rowcount
            print(f"[DEBUG] Clusters deletados: {clusters_deletados}")
            total_afetado += clusters_deletados
            
            # Deleta snapshot
            print(f"[DEBUG] Deletando snapshot {snapshot_id}...")
            cursor.execute('DELETE FROM snapshots WHERE id = ?', (snapshot_id,))
            snapshots_deletados = cursor.rowcount
            print(f"[DEBUG] Snapshots deletados: {snapshots_deletados}")
            total_afetado += snapshots_deletados
            
        elif data:
            data_para_deletar = data
            # Busca IDs dos snapshots da data
            cursor.execute('SELECT id FROM snapshots WHERE data = ?', (data,))
            ids = cursor.fetchall()
            print(f"[DEBUG] Encontrados {len(ids)} snapshots para data {data}")
            for (sid,) in ids:
                cursor.execute('DELETE FROM clusters_dia WHERE snapshot_id = ?', (sid,))
                total_afetado += cursor.rowcount
            cursor.execute('DELETE FROM snapshots WHERE data = ?', (data,))
            total_afetado += cursor.rowcount
        else:
            print(f"[DEBUG] Nenhum ID ou data fornecido")
            conn.close()
            return False
        
        # IMPORTANTE: Também deleta os dados individuais dos jogadores (player_snapshots)
        # para a mesma data
        if data_para_deletar:
            print(f"[DEBUG] Deletando player_snapshots para data {data_para_deletar}...")
            cursor.execute('DELETE FROM player_snapshots WHERE data = ?', (data_para_deletar,))
            players_deletados = cursor.rowcount
            print(f"[DEBUG] Player snapshots deletados: {players_deletados}")
            total_afetado += players_deletados
        
        conn.commit()
        conn.close()
        print(f"[DEBUG] Total registros afetados: {total_afetado}")
        return total_afetado > 0
    except Exception as e:
        print(f"[ERROR] Erro ao deletar snapshot: {e}")
        import traceback
        traceback.print_exc()
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
            "elite": round((df['categoria'] == '⭐ Elite').sum() / total * 100, 2) if total > 0 else 0,
            "vip_ativo": round((df['categoria'] == '🏆 VIP Ativo').sum() / total * 100, 2) if total > 0 else 0,
            "bom": round((df['categoria'] == '📈 Bom').sum() / total * 100, 2) if total > 0 else 0,
            "estavel": round((df['categoria'] == '📊 Estável').sum() / total * 100, 2) if total > 0 else 0,
            "atencao": round((df['categoria'] == '⚠️ Atenção').sum() / total * 100, 2) if total > 0 else 0,

            "risco_receita": round((df['categoria'] == '🚨 Risco: Queda Receita').sum() / total * 100, 2) if total > 0 else 0,
            "risco_engajamento": round((df['categoria'] == '🚨 Risco: Queda Engajamento').sum() / total * 100, 2) if total > 0 else 0,
            "churn_iminente": round((df['categoria'] == '💎 Churn Iminente').sum() / total * 100, 2) if total > 0 else 0,
            "oportunidade_vip": round((df['categoria'] == '💰 Oportunidade VIP').sum() / total * 100, 2) if total > 0 else 0,
            "oportunidade": round((df['categoria'] == '💰 Oportunidade').sum() / total * 100, 2) if total > 0 else 0,
            "potencial": round((df['categoria'] == '🎯 Potencial').sum() / total * 100, 2) if total > 0 else 0,
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
                        "elite": round((df_regiao['categoria'] == '⭐ Elite').sum() / len(df_regiao) * 100, 2),
                        "vip_ativo": round((df_regiao['categoria'] == '🏆 VIP Ativo').sum() / len(df_regiao) * 100, 2),
                        "bom": round((df_regiao['categoria'] == '📈 Bom').sum() / len(df_regiao) * 100, 2),
                        "estavel": round((df_regiao['categoria'] == '📊 Estável').sum() / len(df_regiao) * 100, 2),
                        "atencao": round((df_regiao['categoria'] == '⚠️ Atenção').sum() / len(df_regiao) * 100, 2),

                        "risco_receita": round((df_regiao['categoria'] == '🚨 Risco: Queda Receita').sum() / len(df_regiao) * 100, 2),
                        "risco_engajamento": round((df_regiao['categoria'] == '🚨 Risco: Queda Engajamento').sum() / len(df_regiao) * 100, 2),
                        "churn_iminente": round((df_regiao['categoria'] == '💎 Churn Iminente').sum() / len(df_regiao) * 100, 2),
                        "oportunidade_vip": round((df_regiao['categoria'] == '💰 Oportunidade VIP').sum() / len(df_regiao) * 100, 2),
                        "oportunidade": round((df_regiao['categoria'] == '💰 Oportunidade').sum() / len(df_regiao) * 100, 2),
                        "potencial": round((df_regiao['categoria'] == '🎯 Potencial').sum() / len(df_regiao) * 100, 2),
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
                    "elite": round((df_vip['categoria'] == '⭐ Elite').sum() / len(df_vip) * 100, 2),
                    "vip_ativo": round((df_vip['categoria'] == '🏆 VIP Ativo').sum() / len(df_vip) * 100, 2),
                    "bom": round((df_vip['categoria'] == '📈 Bom').sum() / len(df_vip) * 100, 2),
                    "estavel": round((df_vip['categoria'] == '📊 Estável').sum() / len(df_vip) * 100, 2),
                    "atencao": round((df_vip['categoria'] == '⚠️ Atenção').sum() / len(df_vip) * 100, 2),

                    "risco_receita": round((df_vip['categoria'] == '🚨 Risco: Queda Receita').sum() / len(df_vip) * 100, 2),
                    "risco_engajamento": round((df_vip['categoria'] == '🚨 Risco: Queda Engajamento').sum() / len(df_vip) * 100, 2),
                    "churn_iminente": round((df_vip['categoria'] == '💎 Churn Iminente').sum() / len(df_vip) * 100, 2),
                    "oportunidade_vip": round((df_vip['categoria'] == '💰 Oportunidade VIP').sum() / len(df_vip) * 100, 2),
                    "oportunidade": round((df_vip['categoria'] == '💰 Oportunidade').sum() / len(df_vip) * 100, 2),
                    "potencial": round((df_vip['categoria'] == '🎯 Potencial').sum() / len(df_vip) * 100, 2),
                },
                "top_3": df_vip.nlargest(3, 'score_geral')[[id_col, 'score_geral', 'categoria']].to_dict('records')
            }
            
            resumo["distribuicao_vip"][vip_info['nome']] = len(df_vip)
    
    return resumo


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve a página principal"""
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        # Fallback para caminho relativo
        index_path = "templates/index.html"
    return FileResponse(index_path)


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
        
        # Processa dados com parâmetros dinâmicos (sem salvar no histórico ainda)
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
            '% Elite': resumo['distribuicao_categorias'].get('elite', 0),
            '% VIP Ativo': resumo['distribuicao_categorias'].get('vip_ativo', 0),
            '% Bom': resumo['distribuicao_categorias'].get('bom', 0),
            '% Estável': resumo['distribuicao_categorias'].get('estavel', 0),
            '% Atenção': resumo['distribuicao_categorias'].get('atencao', 0),

            '% Risco Queda Receita': resumo['distribuicao_categorias'].get('risco_receita', 0),
            '% Risco Queda Engajamento': resumo['distribuicao_categorias'].get('risco_engajamento', 0),
            '% Churn Iminente': resumo['distribuicao_categorias'].get('churn_iminente', 0),
            '% Oportunidade VIP': resumo['distribuicao_categorias'].get('oportunidade_vip', 0),
            '% Oportunidade': resumo['distribuicao_categorias'].get('oportunidade', 0),
            '% Potencial': resumo['distribuicao_categorias'].get('potencial', 0),
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
                    '% Elite': vip_stats['distribuicao_categorias'].get('elite', 0),
                    '% VIP Ativo': vip_stats['distribuicao_categorias'].get('vip_ativo', 0),
                    '% Bom': vip_stats['distribuicao_categorias'].get('bom', 0),
                    '% Estável': vip_stats['distribuicao_categorias'].get('estavel', 0),
                    '% Atenção': vip_stats['distribuicao_categorias'].get('atencao', 0),

                    '% Risco Queda Receita': vip_stats['distribuicao_categorias'].get('risco_receita', 0),
                    '% Risco Queda Engajamento': vip_stats['distribuicao_categorias'].get('risco_engajamento', 0),
                    '% Churn Iminente': vip_stats['distribuicao_categorias'].get('churn_iminente', 0),
                    '% Oportunidade VIP': vip_stats['distribuicao_categorias'].get('oportunidade_vip', 0),
                    '% Oportunidade': vip_stats['distribuicao_categorias'].get('oportunidade', 0),
                    '% Potencial': vip_stats['distribuicao_categorias'].get('potencial', 0),
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
    """Salva o estado atual como snapshot do dia e dados individuais dos jogadores"""
    if not cached_data:
        raise HTTPException(status_code=404, detail="Nenhum dado processado. Faça upload primeiro.")
    
    resumo = cached_data['resumo']
    df_original = cached_data['df']  # DataFrame completo com dados dos jogadores
    filtros = request.get('filtros', {})
    data_custom = request.get('data')  # Data no formato YYYY-MM-DD
    
    # Usa a data exatamente como recebida do frontend
    if data_custom and isinstance(data_custom, str) and len(data_custom) == 10:
        data_usar = data_custom  # Usa diretamente: YYYY-MM-DD
    else:
        data_usar = datetime.now().strftime("%Y-%m-%d")
    
    print(f"[DEBUG] Data recebida do frontend: {data_custom}")
    print(f"[DEBUG] Data usada para salvar: {data_usar}")
    
    # IMPORTANTE: Se a data do snapshot for diferente de hoje, recalcula os scores
    # usando a data do snapshot como referência (para dados históricos)
    hoje = datetime.now().strftime("%Y-%m-%d")
    if data_usar != hoje:
        print(f"[DEBUG] Recalculando scores para data histórica: {data_usar}")
        try:
            # Converte a data do snapshot para datetime
            data_referencia = datetime.strptime(data_usar, "%Y-%m-%d")
            # Reprocessa os dados com a data de referência correta
            df, params = processar_dados_jogadores(df_original.copy(), data_referencia)
            # Recalcula o resumo com os novos scores
            resumo = gerar_resumo(df, params)
            print(f"[DEBUG] Scores recalculados para data: {data_usar}")
        except Exception as e:
            print(f"[WARN] Erro ao recalcular scores: {e}. Usando dados originais.")
            df = df_original.copy()
    else:
        df = df_original.copy()
    
    # Salva snapshot geral
    snapshot_id = salvar_snapshot(resumo, filtros, data_usar)
    
    # Salva dados individuais de cada jogador com a mesma data
    try:
        total_salvos = salvar_player_snapshots(df, data_usar)
        print(f"[INFO] {total_salvos} jogadores salvos para acompanhamento individual (data: {data_usar})")
    except Exception as e:
        print(f"[WARN] Erro ao salvar player_snapshots: {e}")
        # Não falha o snapshot se der erro ao salvar jogadores individuais
    
    return {
        "success": True,
        "message": "Dados do dia salvos com sucesso",
        "snapshot_id": snapshot_id,
        "data": data_usar
    }


@app.delete("/api/historico/{snapshot_id}")
async def deletar_historico(snapshot_id: int):
    """Deleta um snapshot específico pelo ID"""
    print(f"[DEBUG] DELETE request recebido - snapshot_id: {snapshot_id}")
    
    try:
        sucesso = deletar_snapshot(snapshot_id=snapshot_id)
        
        if sucesso:
            print(f"[DEBUG] Snapshot {snapshot_id} deletado com sucesso")
            return {
                "success": True,
                "message": f"Snapshot {snapshot_id} deletado com sucesso"
            }
        else:
            print(f"[DEBUG] Snapshot {snapshot_id} não encontrado ou erro ao deletar")
            raise HTTPException(status_code=404, detail="Snapshot não encontrado")
    except Exception as e:
        print(f"[ERROR] Erro no endpoint delete: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


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
            "⭐ Elite": {"qtd": clusters.get('⭐ Elite', 0), "pct": round(clusters.get('⭐ Elite', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "🏆 VIP Ativo": {"qtd": clusters.get('🏆 VIP Ativo', 0), "pct": round(clusters.get('🏆 VIP Ativo', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "📈 Bom": {"qtd": clusters.get('📈 Bom', 0), "pct": round(clusters.get('📈 Bom', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "📊 Estável": {"qtd": clusters.get('📊 Estável', 0), "pct": round(clusters.get('📊 Estável', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "⚠️ Atenção": {"qtd": clusters.get('⚠️ Atenção', 0), "pct": round(clusters.get('⚠️ Atenção', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},

            "🚨 Risco: Queda Receita": {"qtd": clusters.get('🚨 Risco: Queda Receita', 0), "pct": round(clusters.get('🚨 Risco: Queda Receita', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "🚨 Risco: Queda Engajamento": {"qtd": clusters.get('🚨 Risco: Queda Engajamento', 0), "pct": round(clusters.get('🚨 Risco: Queda Engajamento', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
            "💎 Churn Iminente": {"qtd": clusters.get('💎 Churn Iminente', 0), "pct": round(clusters.get('💎 Churn Iminente', 0)/total_jogadores*100, 1) if total_jogadores > 0 else 0},
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


# ========== ENDPOINTS DE ACOMPANHAMENTO INDIVIDUAL ==========

def recalcular_categoria(score_geral: float, score_engajamento: float, score_compras: float, nivel_vip: int = 1) -> str:
    """
    Recalcula a categoria com base nos scores.
    Usa a mesma lógica do HealthScoreCalculator.categorizar_jogador
    """
    # Garante que os scores sejam numéricos
    try:
        score_geral = float(score_geral) if score_geral is not None else 0
        score_engajamento = float(score_engajamento) if score_engajamento is not None else 0
        score_compras = float(score_compras) if score_compras is not None else 0
        nivel_vip = int(nivel_vip) if nivel_vip is not None else 1
    except (ValueError, TypeError):
        score_geral = score_engajamento = score_compras = 0
        nivel_vip = 1
    
    # OPORTUNIDADES (alto engajamento + baixas compras)
    if score_engajamento >= 60 and score_compras < 40:
        if nivel_vip >= 3:
            return "💰 Oportunidade VIP"
        else:
            return "💰 Oportunidade"
    
    # POTENCIAL (bom engajamento, compras médias)
    if score_engajamento >= 40 and score_compras >= 30 and score_compras < 50:
        return "🎯 Potencial"
    
    # Categorização principal por Score Geral
    if score_geral >= 80:
        return "⭐ Elite"
    elif score_geral >= 65:
        return "🏆 VIP Ativo"
    elif score_geral >= 50:
        return "📈 Bom"
    elif score_geral >= 40:
        return "📊 Estável"
    elif score_geral >= 25:
        return "⚠️ Atenção"
    elif score_geral >= 15:
        # Risco moderado (Score 15-24) - distribui entre os dois tipos de risco
        if score_compras < score_engajamento:
            return "🚨 Risco: Queda Receita"
        else:
            return "🚨 Risco: Queda Engajamento"
    else:
        # Score < 15 = Crítico
        if score_compras < 15 and score_engajamento < 20:
            return "💎 Churn Iminente"
        elif score_compras < score_engajamento:
            return "🚨 Risco: Queda Receita"
        else:
            return "🚨 Risco: Queda Engajamento"


def get_ultimo_registro_todos_jogadores(dias: int = 90, regiao: str = None, nivel_vip: int = None) -> List[Dict]:
    """
    Retorna o registro mais recente de TODOS os jogadores que já apareceram no histórico.
    Mesmo que o jogador não tenha dados no dia atual, retorna seu último registro.
    Pode filtrar por região e nível VIP.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Constrói a query base
    query = '''
        SELECT 
            ps.player_id,
            ps.data,
            ps.score_geral,
            ps.score_engajamento,
            ps.score_compras,
            ps.score_login,
            ps.categoria,
            ps.nivel_vip,
            ps.regiao,
            ps.qtd_compras_7d,
            ps.ticket_medio_7d,
            ps.qtd_torneios_3d,
            ps.qtd_maratonas_3d,
            ps.qtd_missoes_3d,
            ps.qtd_promos_3d,
            ps.qtd_logins_3d
        FROM player_snapshots ps
        INNER JOIN (
            SELECT player_id, MAX(data) as max_data
            FROM player_snapshots
            WHERE data >= date('now', '-{} days')
            GROUP BY player_id
        ) latest ON ps.player_id = latest.player_id AND ps.data = latest.max_data
        WHERE ps.data >= date('now', '-{} days')
    '''.format(dias, dias)
    
    # Adiciona filtros se fornecidos
    params = []
    filtros_where = []
    
    if regiao and regiao != 'all':
        filtros_where.append("ps.regiao = ?")
        params.append(regiao)
    
    if nivel_vip and nivel_vip != 'all':
        try:
            vip_int = int(nivel_vip)
            filtros_where.append("ps.nivel_vip = ?")
            params.append(vip_int)
        except (ValueError, TypeError):
            pass  # Ignora se não for um número válido
    
    # Adiciona os filtros à query
    if filtros_where:
        # Substitui o WHERE inicial pelos filtros + condição original de data
        query = query.replace(
            "WHERE ps.data >= date('now',",
            "WHERE " + " AND ".join(filtros_where) + " AND ps.data >= date('now',"
        )
    
    if params:
        cursor.execute(query, tuple(params))
    else:
        cursor.execute(query)
    
    rows = cursor.fetchall()
    
    # Converte para lista de dicionários
    jogadores_unicos = {}
    contagem_categorias = {}
    contagem_scores = {'<15': 0, '15-24': 0, '25-39': 0, '>=40': 0}
    
    # Calcula estatísticas globais para recalcular scores
    from statistics import mean, stdev
    
    # Coleta todos os valores para calcular estatísticas
    todos_torneios = [r['qtd_torneios_3d'] or 0 for r in rows]
    todos_maratonas = [r['qtd_maratonas_3d'] or 0 for r in rows]
    todos_missoes = [r['qtd_missoes_3d'] or 0 for r in rows]
    todos_promos = [r['qtd_promos_3d'] or 0 for r in rows]
    todos_logins = [r['qtd_logins_3d'] or 0 for r in rows]
    todos_compras = [r['qtd_compras_7d'] or 0 for r in rows]
    todos_tickets = [r['ticket_medio_7d'] or 0 for r in rows]
    
    # Calcula médias e desvios
    def calc_stats(valores):
        m = mean(valores) if valores else 0
        s = stdev(valores) if len(valores) > 1 else 1
        if s == 0:
            s = 1
        return m, s
    
    media_torneios, std_torneios = calc_stats(todos_torneios)
    media_maratonas, std_maratonas = calc_stats(todos_maratonas)
    media_missoes, std_missoes = calc_stats(todos_missoes)
    media_promos, std_promos = calc_stats(todos_promos)
    media_logins, std_logins = calc_stats(todos_logins)
    media_compras, std_compras = calc_stats(todos_compras)
    media_tickets, std_tickets = calc_stats(todos_tickets)
    
    def calcular_score_atividade(valor, media, std):
        """Calcula score de uma atividade (0-100)"""
        if valor == 0:
            return 0
        if valor <= media:
            ratio = valor / media if media > 0 else 0
            return 50 * (ratio ** 0.5)
        else:
            z_score = (valor - media) / std
            return min(100, 50 + (z_score * 25))
    
    for row in rows:
        pid = row['player_id']
        
        # Recalcula scores a partir dos valores brutos
        # Score de engajamento (média ponderada das atividades)
        s_torneios = calcular_score_atividade(row['qtd_torneios_3d'] or 0, media_torneios, std_torneios) * 2.0
        s_maratonas = calcular_score_atividade(row['qtd_maratonas_3d'] or 0, media_maratonas, std_maratonas) * 2.5
        s_missoes = calcular_score_atividade(row['qtd_missoes_3d'] or 0, media_missoes, std_missoes) * 1.5
        s_promos = calcular_score_atividade(row['qtd_promos_3d'] or 0, media_promos, std_promos) * 1.0
        s_logins = calcular_score_atividade(row['qtd_logins_3d'] or 0, media_logins, std_logins) * 1.0
        
        peso_total_eng = 2.0 + 2.5 + 1.5 + 1.0 + 1.0
        score_engajamento = (s_torneios + s_maratonas + s_missoes + s_promos + s_logins) / peso_total_eng
        
        # Score de compras (média ponderada)
        s_qtd = calcular_score_atividade(row['qtd_compras_7d'] or 0, media_compras, std_compras) * 0.40
        s_ticket = calcular_score_atividade(row['ticket_medio_7d'] or 0, media_tickets, std_tickets) * 0.35
        
        # Recência (se disponível)
        s_recencia = 0
        peso_recencia = 0
        if row['qtd_compras_7d'] and row['qtd_compras_7d'] > 0:
            # Se comprou nos últimos 7 dias, recência = 100
            s_recencia = 100 * 0.25
            peso_recencia = 0.25
        
        peso_total_comp = 0.40 + 0.35 + peso_recencia
        if peso_total_comp > 0:
            score_compras = (s_qtd + s_ticket + s_recencia) / peso_total_comp
        else:
            score_compras = 0
        
        # Score geral (ponderação: engajamento 30%, compras 70%)
        score_geral = score_engajamento * 0.3 + score_compras * 0.7
        
        nivel_vip = row['nivel_vip'] or 1
        
        # Debug: contagem de scores
        if score_geral < 15:
            contagem_scores['<15'] += 1
        elif score_geral < 25:
            contagem_scores['15-24'] += 1
        elif score_geral < 40:
            contagem_scores['25-39'] += 1
        else:
            contagem_scores['>=40'] += 1
        
        categoria_recalculada = recalcular_categoria(score_geral, score_engajamento, score_compras, nivel_vip)
        
        # Debug: contagem de categorias
        contagem_categorias[categoria_recalculada] = contagem_categorias.get(categoria_recalculada, 0) + 1
        
        jogadores_unicos[pid] = {
            'player_id': pid,
            'data': row['data'],
            'score_geral': round(score_geral, 2),
            'score_engajamento': round(score_engajamento, 2),
            'score_compras': round(score_compras, 2),
            'score_login': row['score_login'],
            'categoria': categoria_recalculada,  # Usa a categoria recalculada
            'nivel_vip': nivel_vip,
            'regiao': row['regiao'],
            'qtd_compras_7d': row['qtd_compras_7d'],
            'ticket_medio_7d': row['ticket_medio_7d'],
            'qtd_torneios_3d': row['qtd_torneios_3d'],
            'qtd_maratonas_3d': row['qtd_maratonas_3d'],
            'qtd_missoes_3d': row['qtd_missoes_3d'],
            'qtd_promos_3d': row['qtd_promos_3d'],
            'qtd_logins_3d': row['qtd_logins_3d']
        }
    
    # Debug: imprime distribuição
    print(f"[DEBUG] Distribuição de scores: {contagem_scores}")
    print(f"[DEBUG] Distribuição de categorias: {contagem_categorias}")
    
    conn.close()
    return list(jogadores_unicos.values())


@app.get("/api/players/ultimos")
async def get_players_ultimos(
    dias: int = Query(90, description="Dias para trás no histórico"),
    regiao: str = Query(None, description="Filtrar por região (ex: BR, PT)"),
    nivel_vip: str = Query(None, description="Filtrar por nível VIP (1-5)")
):
    """
    Retorna o último registro de todos os jogadores que já apareceram.
    Útil para manter a lista completa mesmo quando jogadores estão ausentes.
    Aceita filtros de região e nível VIP.
    """
    try:
        jogadores = get_ultimo_registro_todos_jogadores(dias, regiao, nivel_vip)
        
        return {
            "success": True,
            "total": len(jogadores),
            "dias_considerados": dias,
            "regiao_filtro": regiao,
            "nivel_vip_filtro": nivel_vip,
            "jogadores": jogadores
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar jogadores: {str(e)}"
        }


@app.get("/api/player/{player_id}/evolucao")
async def get_player_evolucao(
    player_id: str,
    dias: int = Query(30, description="Número de dias no histórico")
):
    """
    Retorna a evolução histórica de um jogador específico.
    Permite analisar flutuação entre clusters e impacto de campanhas.
    """
    try:
        evolucao = get_evolucao_player(player_id, dias)
        
        if "error" in evolucao:
            return {
                "success": False,
                "message": evolucao["error"]
            }
        
        return {
            "success": True,
            "player_id": player_id,
            "dias_analisados": dias,
            "evolucao": evolucao
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar evolução: {str(e)}"
        }


@app.get("/api/players/flutuacao")
async def get_players_flutuacao(
    cluster_origem: str = Query(None, description="Cluster de origem (ex: '⚠️ Atenção')"),
    cluster_destino: str = Query(None, description="Cluster de destino (ex: '📈 Bom')"),
    dias: int = Query(7, description="Período de análise em dias"),
    tipo: str = Query("qualquer", description="Tipo: 'melhora', 'piora', 'qualquer'")
):
    """
    Identifica jogadores que mudaram de cluster significativamente.
    Útil para medir impacto de campanhas ou detectar churn.
    """
    try:
        players = get_players_com_flutuacao(cluster_origem, cluster_destino, dias, tipo)
        
        return {
            "success": True,
            "total": len(players),
            "filtros": {
                "cluster_origem": cluster_origem,
                "cluster_destino": cluster_destino,
                "dias": dias,
                "tipo": tipo
            },
            "players": players[:50]  # Limita a 50 resultados
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar flutuações: {str(e)}"
        }


@app.get("/api/campanhas/analise")
async def analisar_campanhas(
    campanha_nome: str = Query(..., description="Nome da campanha para análise"),
    dias_antes: int = Query(7, description="Dias antes do início da campanha"),
    dias_depois: int = Query(7, description="Dias depois do início da campanha")
):
    """
    Analisa a eficácia de uma campanha comparando comportamento antes/depois.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Busca jogadores que participaram da campanha
        cursor.execute('''
            SELECT player_id, data, score_geral, score_engajamento, score_compras, categoria
            FROM player_snapshots 
            WHERE campanha_nome = ?
            ORDER BY player_id, data ASC
        ''', (campanha_nome,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "success": False,
                "message": f"Nenhum dado encontrado para a campanha '{campanha_nome}'"
            }
        
        # Agrupa por jogador
        players_data = {}
        for row in rows:
            pid = row['player_id']
            if pid not in players_data:
                players_data[pid] = []
            players_data[pid].append(row)
        
        # Analisa impacto
        analise = {
            "total_participantes": len(players_data),
            "melhoraram": 0,
            "pioraram": 0,
            "mantiveram": 0,
            "variacao_media_geral": 0,
            "variacao_media_compras": 0,
            "variacao_media_engajamento": 0
        }
        
        variacoes_geral = []
        variacoes_compras = []
        variacoes_engajamento = []
        
        for pid, registros in players_data.items():
            if len(registros) < 2:
                continue
            
            primeiro = registros[0]
            ultimo = registros[-1]
            
            var_geral = ultimo['score_geral'] - primeiro['score_geral']
            var_compras = ultimo['score_compras'] - primeiro['score_compras']
            var_engajamento = ultimo['score_engajamento'] - primeiro['score_engajamento']
            
            variacoes_geral.append(var_geral)
            variacoes_compras.append(var_compras)
            variacoes_engajamento.append(var_engajamento)
            
            if var_geral > 5:
                analise["melhoraram"] += 1
            elif var_geral < -5:
                analise["pioraram"] += 1
            else:
                analise["mantiveram"] += 1
        
        if variacoes_geral:
            analise["variacao_media_geral"] = round(sum(variacoes_geral) / len(variacoes_geral), 2)
            analise["variacao_media_compras"] = round(sum(variacoes_compras) / len(variacoes_compras), 2)
            analise["variacao_media_engajamento"] = round(sum(variacoes_engajamento) / len(variacoes_engajamento), 2)
        
        conn.close()
        
        return {
            "success": True,
            "campanha": campanha_nome,
            "analise": analise
        }
        
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "message": f"Erro na análise: {str(e)}"
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
    # Porta dinâmica para deploy (Render, Railway, etc)
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "127.0.0.1")
    
    print("=" * 60)
    print("  Health Score Dashboard - Iniciando servidor...")
    print("=" * 60)
    print()
    print(f"  Acesse no navegador:")
    print(f"  http://{host}:{port}")
    print()
    print("  Pressione CTRL+C para parar")
    print("=" * 60)
    print()
    
    # No modo executável (PyInstaller onefile), desativa config de logging padrão
    # para evitar erro com stdout/stderr None
    if IS_FROZEN:
        uvicorn.run(app, host=host, port=port, log_config=None)
    else:
        uvicorn.run(app, host=host, port=port)
