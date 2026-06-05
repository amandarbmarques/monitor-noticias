import streamlit as st
import pandas as pd
import sqlite3
import re
from rapidfuzz import fuzz

# -------------------
# Configuração da página
# -------------------
st.set_page_config(
    page_title="Monitor de Notícias",
    layout="wide",
    page_icon="📰"
)

# --- CSS CUSTOMIZADO LIMPO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    .stDataFrame {
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .stDownloadButton button {
        border-radius: 8px;
        background-color: #4F46E5;
        color: white;
        border: none;
        padding: 8px 20px;
        font-weight: 600;
    }
    .stDownloadButton button:hover {
        background-color: #4338CA;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------
# 1. CARREGA DADOS E FILTRA ÚLTIMOS 5 DIAS
# -------------------
try:
    with sqlite3.connect("noticias.db", check_same_thread=False) as conn:
        df = pd.read_sql("SELECT * FROM noticias", conn)
except:
    df = pd.DataFrame(columns=["id", "veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

if not df.empty:
    df['data_publicacao_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
    
    # 1. Ajuste de Fuso Horário
    try:
        if df['data_publicacao_dt'].dt.tz is None:
            df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        else:
            df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_convert('America/Sao_Paulo')
    except:
        df['data_publicacao_dt'] = df['data_publicacao_dt'] - pd.Timedelta(hours=3)

    # 2. A GRANDE SACADA: Corte dos últimos 5 dias
    agora = pd.Timestamp.now(tz='America/Sao_Paulo')
    limite_5_dias = agora - pd.Timedelta(days=5)
    df = df[df['data_publicacao_dt'] >= limite_5_dias].copy()

# -------------------
# 🥇 PRIORIDADE 2: INDICADOR DE FUROS (COM CACHE)
# -------------------
def limpar_titulo(titulo):
    titulo = str(titulo).lower()
    titulo = re.sub(r'[^a-zà-ú0-9 ]', '', titulo)
    return titulo

@st.cache_data(ttl=300) # Memória temporária de 5 min para voar no carregamento
def processar_furos(df_temp):
    if df_temp.empty:
        df_temp['furo'] = []
        return df_temp
        
    df_temp = df_temp.sort_values(by='data_publicacao_dt', ascending=True).reset_index(drop=True)
    
    pautas_vistas = []
    status_furo = []
    
    for idx, row in df_temp.iterrows():
        tit_limpo = limpar_titulo(row['titulo'])
        matched = False
        
        for pauta in reversed(pautas_vistas[-150:]):
            if fuzz.ratio(tit_limpo, pauta['titulo_limpo']) > 80:
                matched = True
                if pauta['veiculo'] == row['veiculo']:
                    status_furo.append("🔄 Atualização")
                else:
                    status_furo.append("🥈 Seguiu " + pauta['veiculo'])
                break
                
        if not matched:
            status_furo.append("🥇 Primeiro")
            pautas_vistas.append({
                'titulo_limpo': tit_limpo,
                'veiculo': row['veiculo']
            })
            
    df_temp['furo'] = status_furo
    return df_temp

if not df.empty:
    df = processar_furos(df)
    # Reordenar para exibir as mais novas no topo e formatar data
    df = df.sort_values(by='data_publicacao_dt', ascending=False).reset_index(drop=True)
    df['data_publicacao'] = df['data_publicacao_dt'].dt.strftime('%d/%m/%Y %H:%M')
else:
    df['furo'] = []

# -------------------
# 📊 PRIORIDADE 1: CLASSIFICAÇÃO AUTOMÁTICA DE TEMAS
# -------------------
def classificar_tema(titulo):
    titulo_lower = str(titulo).lower()
    
    regras = {
        "⚖️ Judiciário/STF": ["stf", "supremo", "julga", "justiça", "moraes", "tse", "liminar", "tribunal", "ministro do stf", "pauta jurídica"],
        "🏛️ Política": ["lula", "governo", "planalto", "congresso", "senado", "câmara", "ministros", "bolsa família", "partido", "eleição", "votação", "pec"],
        "💰 Economia": ["ibovespa", "inflação", "selic", "dólar", "mercado", "petrobras", "banco central", "campos neto", "taxa", "juros", "fazenda", "haddad", "gasto", "iof", "ir", "imposto"],
        "⚽ Esportes": ["corinthians", "flamengo", "palmeiras", "futebol",
