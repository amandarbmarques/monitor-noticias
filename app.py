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
# FUNÇÕES DE APOIO
# -------------------
def limpar_titulo(titulo):
    titulo = str(titulo).lower()
    titulo = re.sub(r'[^a-zà-ú0-9 ]', '', titulo)
    return titulo

# Cache de furos trabalhando com datas normalizadas sem fuso
@st.cache_data(ttl=300)
def calcular_furos_reais(df_cronologico):
    pautas_vistas = []
    status_furo = []
    
    for idx, row in df_cronologico.iterrows():
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
            
    df_cronologico['furo'] = status_furo
    return df_cronologico

def classificar_tema(titulo):
    titulo_lower = str(titulo).lower()
    regras = {
        "⚖️ Judiciário/STF": ["stf", "supremo", "julga", "justiça", "moraes", "tse", "liminar", "tribunal", "ministro do stf", "pauta jurídica"],
        "🏛️ Política": ["lula", "governo", "planalto", "congresso", "senado", "câmara", "ministros", "bolsa família", "partido", "eleição", "votação", "pec"],
        "💰 Econom
