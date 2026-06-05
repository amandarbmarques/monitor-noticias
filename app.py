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
        "💰 Economia": ["ibovespa", "inflação", "selic", "dólar", "mercado", "petrobras", "banco central", "campos neto", "taxa", "juros", "fazenda", "haddad", "gasto", "iof", "ir", "imposto"],
        "⚽ Esportes": ["corinthians", "flamengo", "palmeiras", "futebol", "tite", "neymar", "libertadores", "brasileirão", "contrata", "negocia"],
        "🚨 Segurança Pública": ["polícia", "pf", "assalto", "crime", "segurança", "preso", "apreensão", "tráfico", "operação policial", "milícia"]
    }
    
    # LINHA 92 CORRIGIDA DEFINITIVA E LIMPA:
    for tema, palavras in regras.items():
        if any(palavra in titulo_lower for palavra in palavras):
            return tema
    return "📰 Geral"

# -------------------
# 1. PROCESSAMENTO DOS DADOS (AGORA CONECTADO AO SUPABASE!)
# -------------------
import psycopg2  # Certifique-se de manter os imports no topo se preferir

try:
    # URL de conexão com o Supabase
    DB_URI = "postgresql://postgres:23062011Cf!!04@db.hhfttkctypcgrdwvnhug.supabase.co:5432/postgres"
    
    # Conecta e puxa os dados da nuvem
    with psycopg2.connect(DB_URI) as conn:
        df = pd.read_sql("SELECT * FROM noticias", conn)
except Exception as e:
    st.error(f"Erro ao conectar ao banco na nuvem: {e}")
    df = pd.DataFrame(columns=["id", "veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# Daqui para baixo o código de fuso e de 5 dias que já estava no seu app.py continua IGUAL!
if not df.empty:
    df['data_publicacao_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_convert('America/Sao_Paulo')
    df['data_publicacao_dt'] = df['data_publicacao_dt'].dt.tz_localize(None)
# ... restante do código do app.py
# -------------------
# 📊 DASHBOARD DE ASSUNTOS
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
# BARRA LATERAL (Placares)
# -------------------
with st.sidebar:
    st.header("🏆 Placar de Furos")
    if not df.empty:
        furos_df = df[df["furo"] == "🥇 Primeiro"]
        placar_furos = furos_df["veiculo"].value_counts().reset_index()
        placar_furos.columns = ["Veículo", "Furos"]
        st.dataframe(placar_furos, use_container_width=True, hide_index=True)
    else:
        st.write("Sem dados de furos.")
        
    st.markdown("---")
    
    st.header("✍️ Ranking de Autores")
    if not df.empty:
        ranking = df["autor"].value_counts().reset_index()
        ranking.columns = ["Autor", "Qtd"]
        st.dataframe(ranking.head(15), use_container_width=True, hide_index=True, height=250)
    else:
        st.write("Nenhum autor mapeado.")
    st.caption("v5.6 • Sem Bugs Orientais")

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
        opcoes_f = sorted(df["furo"].unique()) if not df.empty else []
        filtro_furo = st.multiselect("Status (Furo)", options=opcoes_f)
    with c4:
        opcoes_t = sorted(df["tema"].unique()) if not df.empty else []
        temas_selecionados = st.multiselect("🏷️ Tema", options=opcoes_t, default=opcoes_t)

# Aplicação dos filtros selecionados
if not df.empty:
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    if veiculos:
        df = df[df["veiculo"].isin(veiculos)]
    if filtro_furo:
        df = df[df["furo"].isin(filtro_furo)]
    if temas_selecionados:
        df = df[df["tema"].isin(temas_selecionados)]

# -------------------
# TABELA PRINCIPAL COM SELEÇÃO E EXPORTAÇÃO
# -------------------
st.subheader("📋 Clipping de Notícias")

if not df.empty:
    df_exibicao = df[["id", "furo", "tema", "veiculo", "titulo", "autor", "url", "data_publicacao"]].copy()

    if "noticias_selecionadas" not in st.session_state:
        st.session_state.noticias_selecionadas = set()

    selecionar_tudo = st.checkbox("Selecionar todas as notícias exibidas")

    if selecionar_tudo:
        st.session_state.noticias_selecionadas = set(df_exibicao["id"].tolist())
    elif selecionar_tudo is False:
        if len(st.session_state.noticias_selecionadas) == len(df_exibicao):
            st.session_state.noticias_selecionadas = set()

    df_exibicao["Selecionar"] = df_exibicao["id"].apply(lambda x: x in st.session_state.noticias_selecionadas)

    cols = ["Selecionar", "id", "furo", "tema", "veiculo", "titulo", "autor", "url", "data_publicacao"]
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
            "furo": st.column_config.TextColumn("🥇 Status", width="medium"),
            "tema": st.column_config.TextColumn("🏷️ Tema", width="medium"),
            "veiculo": st.column_config.TextColumn("Fonte", width="small"),
            "titulo": st.column_config.TextColumn("Notícia (Título)", width="large"),
            "autor": st.column_config.TextColumn("Autor"),
            "url": st.column_config.LinkColumn("Link", display_text="Ler Agora", width="small"),
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
        csv_total = df.drop(columns=["id", "data_publicacao_dt"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("📥 Exportar Tudo", csv_total, "clipping_completo.csv", "text/csv", use_container_width=True)

    with col2:
        if len(selecionadas_df) > 0:
            csv_sel = selecionadas_df.drop(columns=["id", "data_publicacao_dt"], errors="ignore").to_csv(index=False).encode("utf-8")
            st.download_button("✅ Exportar " + str(len(selecionadas_df)) + " Selecionadas", csv_sel, "noticias_selecionadas.csv", "text/csv", use_container_width=True)
        else:
            st.button("✅ Exportar Selecionadas", disabled=True, use_container_width=True)
else:
    st.info("Nenhum dado encontrado para os filtros aplicados ou banco de dados vazio.")
