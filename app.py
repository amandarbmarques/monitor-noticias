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
    
    for tema, palavras in regras.items():
        if any(palavra in titulo_lower for palavra in palavras):
            return tema
            
    return "📰 Geral"

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
    titulo_html = '<h1>Monitor de <span style="color:#4F46E5;">Notícias</span></h1><p style="color:#64748B;font-size:16px;margin-top:-10px;">Análise e clipping em tempo real dos principais portais brasileiros.</p>'
    st.markdown(titulo_html, unsafe_allow_html=True)

with col_stat:
    status_html = '<div style="text-align: right; padding-top: 10px;"><div style="display: inline-flex; align-items: center; background-color: #ECFDF5; border: 1px solid #10B981; padding: 4px 12px; border-radius: 20px;"><span class="dot-pulsing" style="height: 8px; width: 8px; background-color: #10B981; border-radius: 50%; display: inline-block; margin-right: 8px;"></span><span style="color: #065F46; font-size: 12px; font-weight: 700; text-transform: uppercase;">Sistema Live</span></div><p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 500;">Última coleta: ' + ultima_atualizacao + '</p></div>'
    st.markdown(status_html, unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        .dot-pulsing {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        </style>
    """, unsafe_allow_html=True)

st.markdown("---")

# -------------------
# 📊 6. DASHBOARD DE ASSUNTOS (TOP CONTADORES)
# -------------------
if not df.empty:
    st.markdown("### 📊 Temas Mais Cobertos")
    contagem_temas = df["tema"].value_counts()
    
    cols_temas = st.columns(len(contagem_temas))
    for idx, (tema, qtd) in enumerate(contagem_temas.items()):
        with cols_temas[idx]:
            card_tema = '<div style="background-color: #FFFFFF; padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); border: 1px solid #E2E8F0; text-align: center;"><p style="margin: 0; font-size: 13px; color: #64748B; font-weight: 600;">' + tema + '</p><h4 style="margin: 5px 0 0 0; font-size: 22px; color: #1E293B; font-weight: 700;">' + str(qtd) + '</h4></div>'
            st.markdown(card_tema, unsafe_allow_html=True)
    st.markdown("###")

# -------------------
# BARRA LATERAL (Ranking de Autores)
# -------------------
with st.sidebar:
    st.header("✍️ Ranking de Autores")
    if not df.empty:
        ranking = df["autor"].value_counts().reset_index()
        ranking.columns = ["Autor", "Qtd"]
        st.dataframe(ranking.head(15), use_container_width=True, hide_index=True, height=350)
    else:
        st.write("Nenhum autor mapeado.")
    st.caption("v2.0 • Tags de Assunto Ativas")

# -------------------
# FILTROS E BUSCA
# -------------------
with st.expander("🔍 Ferramentas de Filtro e Busca", expanded=True):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        busca = st.text_input("Buscar palavra-chave no título...")
    with c2:
        opcoes_v = sorted(df["veiculo"].unique()) if not df.empty else []
        veiculos = st.multiselect("Veículos", options=opcoes_v, default=opcoes_v)
    with c3:
        opcoes_a = sorted(df["autor"].dropna().unique()) if not df.empty else []
        autores = st.multiselect("Filtrar por Autor", options=opcoes_a)
    with c4:
        opcoes_t = sorted(df["tema"].unique()) if not df.empty else []
        temas_selecionados = st.multiselect("🏷️ Filtrar por Tema", options=opcoes_t, default=opcoes_t)

# Aplicação dos filtros selecionados
if not df.empty:
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    if veiculos:
        df = df[df["veiculo"].isin(veiculos)]
    if autores:
        df = df[df["autor"].isin(autores)]
    if temas_selecionados:
        df = df[df["tema"].isin(temas_selecionados)]

# -------------------
# TABELA PRINCIPAL COM SELEÇÃO E EXPORTAÇÃO
# -------------------
st.subheader("📋 Clipping de Notícias")

if not df.empty:
    df_exibicao = df[["id", "tema", "veiculo", "titulo", "autor", "url", "data_publicacao"]].copy()

    if "noticias_selecionadas" not in st.session_state:
        st.session_state.noticias_selecionadas = set()

    selecionar_tudo = st.checkbox("Selecionar todas as notícias exibidas")

    if selecionar_tudo:
        st.session_state.noticias_selecionadas = set(df_exibicao["id"].tolist())
    elif selecionar_tudo is False:
        if len(st.session_state.noticias_selecionadas) == len(df_exibicao):
            st.session_state.noticias_selecionadas = set()

    df_exibicao["Selecionar"] = df_exibicao["id"].apply(lambda x: x in st.session_state.noticias_selecionadas)

    cols = ["Selecionar", "id", "tema", "veiculo", "titulo", "autor", "url", "data_publicacao"]
    df_exibicao = df_exibicao[cols]

    edited_df = st.data_editor(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=900,
        key="editor_noticias",
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("✓"),
            "id": None,
            "tema": st.column_config.TextColumn("🏷️ Tema", width="medium"),
            "veiculo": st.column_config.TextColumn("Fonte"),
            "titulo": st.column_config.TextColumn("Notícia (Título)", width="large"),
            "autor": st.column_config.TextColumn("Autor"),
            "url": st.column_config.LinkColumn("Link", display_text="Ler Agora"),
            "data_publicacao": st.column_config.TextColumn("Horário")
        }
    )

    ids_marcados = edited_df.loc[edited_df["Selecionar"], "id"].tolist()
    st.session_state.noticias_selecionadas = set(ids_marcados)

    selecionadas_df = df[df["id"].isin(st.session_state.noticias_selecionadas)]
    st.markdown("### 📰 " + str(len(selecionadas_df)) + " notícia(s) selecionada(s)")

    # -------------------
    # EXPORTAÇÃO
    # -------------------
    col1, col2 = st.columns(2)

    with col1:
        csv_total = df.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("📥 Exportar Tudo", csv_total, "clipping_completo.csv", "text/csv", use_container_width=True)

    with col2:
        if len(selecionadas_df) > 0:
            csv_sel = selecionadas_df.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")
            st.download_button("✅ Exportar " + str(len(selecionadas_df)) + " Selecionadas", csv_sel, "noticias_selecionadas.csv", "text/csv", use_container_width=True)
        else:
            st.button("✅ Exportar Selecionadas", disabled=True, use_container_width=True)
else:
    st.info("Nenhum dado encontrado para os filtros aplicados ou banco de dados vazio.")
