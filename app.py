import streamlit as st
import pandas as pd
import sqlite3

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
# Tratamento de Dados Blindado
# -------------------
if not df.empty:
    try:
        df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        df['data_publicacao'] = df['data_publicacao'].dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass

# -------------------
# 📊 PRIORIDADE 1: CLASSIFICAÇÃO AUTOMÁTICA DE TEMAS
# -------------------
def classificar_tema(titulo):
    titulo_lower = str(titulo).lower()
    
    regras = {
        "⚖️ Judiciário/STF": ["stf", "supremo", "julga", "justiça", "moraes", "tse", "liminar", "tribunal", "ministro do stf", "pauta jurídica"],
        "🏛️ Política": ["lula", "governo", "planalto", "congresso", "senado", "câmara", "ministros", "bolsa família", "partido", "eleição", "votação", "pec"],
        "💰 Economia": ["ibovespa", "inflação", "selic", "dólar", "mercado", "petrobras", "banco central", "campos neto", "taxa", "juros", "fazenda", "haddad", "gasto", "iof", "ir", "imposto"],
        "⚽ Esportes": ["corinthians", "flamengo", "palmeiras", "futebol", "tite", "neymar", "libertadores", "brasileirão", "contrata", "negocia"],
        "🚨 Segurança Pública": ["polícia", "pf", "assalto", "crime", "segurança", "preso", "apreensão", "tráfico", "operação policial", "milícia"]
    }
    
    # CORREÇÃO DEFINITIVA DA LINHA 76: 'regras' em vez de 'reggae'
    for tema, palavras in regras.items():
        if any(palavra in titulo_lower for palavra in palavras):
            return tema
            
    return "📰 Geral"

# Aplicação da função criando a coluna 'tema'
if not df.empty:
    df["tema"] = df["titulo"].apply(classificar_tema)
else:
    df["tema"] = []

# -------------------
# 2. HEADER CUSTOMIZADO
# -------------------
if not df.empty and 'data_coleta' in df.columns:
    ultima_atualizacao = df['data_coleta'].max()
    try:
        ultima_atualizacao = pd.to_datetime(ultima_atualizacao).strftime('%H:%M - %d/%m/%Y')
    except:
        ultima_atualizacao = "Agora"
else:
    ultima_atualizacao = "--:--"

col_tit, col_stat = st.columns([4, 1])

with col_tit:
    st.markdown("""
        <div style="margin-bottom: -1
