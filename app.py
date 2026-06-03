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

# --- CSS CUSTOMIZADO PARA ESTILIZAÇÃO GERAL ---
st.markdown("""
    <style>
    /* Ajuste de cor e fonte da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Estilização da tabela principal */
    .stDataFrame {
        border: 1px solid #eef0f5;
        border-radius: 12px;
    }
    
    /* Customização do botão de download */
    .stDownloadButton button {
        border-radius: 8px;
        background-color: #4F46E5;
        color: white;
        border: none;
        padding: 6px 16px;
    }
    .stDownloadButton button:hover {
        background-color: #4338CA;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------
# 1. CARREGA DADOS FIRST (Corrigindo o NameError)
# -------------------
try:
    with sqlite3.connect("noticias.db", check_same_thread=False) as conn:
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_publicacao DESC", conn)
except:
    df = pd.DataFrame(columns=["veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# -------------------
# Tratamento de Dados (Fuso Horário Brasília)
# -------------------
if not df.empty:
    try:
        df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        if df['data_publicacao'].dt.tz is not None:
            df['data_publicacao'] = df['data_publicacao'].dt.tz_convert('America/Sao_Paulo')
        else:
            df['data_publicacao'] = df['data_publicacao'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        df['data_publicacao'] = df['data_publicacao'].dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass

# -------------------
# 2. HEADER CUSTOMIZADO (Agora o df existe!)
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
    st.markdown(f"""
        <div style="margin-bottom: -15px;">
            <h1 style="color: #1E293B; font-size: 42px; font-weight: 800; margin-bottom: 0;">
                Monitor de <span style="color: #4F46E5;">Notícias</span>
            </h1>
            <p style="color: #64748B; font-size: 16px; margin-top: 5px;">
                Análise e clipping em tempo real dos principais portais brasileiros.
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_stat:
    st.markdown(f"""
        <div style="text-align: right; padding-top: 20px;">
            <div style="display: inline-flex; align-items: center; background-color: #ECFDF5; border: 1px solid #10B981; padding: 4px 12px; border-radius: 20px;">
                <span style="height: 8px; width: 8px; background-color: #10B981; border-radius: 50%; display: inline-block; margin-right: 8px; animation: pulse 2s infinite;"></span>
                <span style="color: #065F46; font-size: 12px; font-weight: 700; text-transform: uppercase;">Sistema Live</span>
            </div>
            <p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 500;">
                Última coleta: {ultima_atualizacao}
            </p>
        </div>
        
        <style>
        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}
        </style>
    """, unsafe_allow_html=True)

st.markdown("---")

# -------------------
# BARRA LATERAL (Ranking de Autores)
# -------------------
with st.sidebar:
    st.header("✍️ Ranking de Autores")
    if not df.empty:
        ranking = df["autor"].value_counts().reset_index()
        ranking.columns = ["Autor", "Qtd"]
        st.dataframe(ranking.head(15), use_container_width=True, hide_index=True, height=450)
    else:
        st.write("Nenhum autor mapeado.")
    st.caption("v1.4 • Atualizado via GitHub Actions")

# -------------------
# MÉTRICAS CUSTOMIZADAS (CARDS EM HTML)
# -------------------
total = len(df)
contagem = df["veiculo"].value_counts()

html_cards = """
    <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 25px;">
        <div style="flex: 1; min-width: 160px; background-color: #4F46E5; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #4F46E5;">
            <p style="margin: 0; font-size: 12px; color: #E0E7FF; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">📈 Total Geral</p>
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #FFFFFF; font-weight: 700;">{total_geral}</h3>
        </div>
        <div style="flex: 1; min-width: 160px; background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #1E293B;">
            <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔹 Estadão</p>
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #1E293B; font-weight: 700;">{qtd_estadao}</h3>
        </div>
        <div style="flex: 1; min-width: 160px; background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #E11D48;">
            <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔸 Folha</p>
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #1E29
