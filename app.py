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
# 1. CARREGA DADOS FIRST
# -------------------
try:
    with sqlite3.connect("noticias.db", check_same_thread=False) as conn:
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_publicacao DESC", conn)
except:
    df = pd.DataFrame(columns=["id", "veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# -------------------
# 🥇 PRIORIDADE 2: FUSO HORÁRIO E INDICADOR DE FUROS
# -------------------
def limpar_titulo(titulo):
    titulo = str(titulo).lower()
    titulo = re.sub(r'[^a-zà-ú0-9 ]', '', titulo)
    return titulo

if not df.empty:
    # 1. Converter para data real e ajustar FUSO HORÁRIO (UTC para Brasília)
    df['data_publicacao_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
    
    try:
        if df['data_publicacao_dt'].dt.tz is None:
            df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        else:
            df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_convert('America/Sao_Paulo')
    except:
        # Fallback de segurança se o servidor der erro de fuso
        df['data_publicacao_dt'] = df['data_publicacao_dt'] - pd.Timedelta(hours=3)

    # Ordenar cronologicamente (do mais antigo pro mais novo) para achar quem deu primeiro
    df = df.sort_values(by='data_publicacao_dt', ascending=True).reset_index(drop=True)
    
    pautas_vistas = []
    status_furo = []
    
    for idx, row in df.iterrows():
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
            
    df['furo'] = status_furo
    
    # 3. Reordenar para o painel (mais recentes no topo) e formatar a data final
    df = df.sort_values(by='data_publicacao_dt', ascending=False).reset_index(drop=True)
    df['data_publicacao'] = df['data_publicacao_dt'].dt.strftime('%d/%m/%Y %H:%M')
else:
    df['furo'] = []

# -------------------
