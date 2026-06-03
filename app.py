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

st.title("📰 Monitor de Notícias")
st.markdown("---")

# -------------------
# HEADER CUSTOMIZADO
# -------------------

# Captura a última atualização do banco para exibir no header
if not df.empty:
    ultima_atualizacao = df['data_coleta'].max()
    try:
        # Tenta formatar a data de coleta para algo legível
        ultima_atualizacao = pd.to_datetime(ultima_atualizacao).strftime('%H:%M - %d/%m/%Y')
    except:
        ultima_atualizacao = "Agora"
else:
    ultima_atualizacao = "--:--"

# Layout do Header
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
# Carrega dados (Seguro contra concorrência)
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
    st.caption("v1.3 • Atualizado via GitHub Actions")

# -------------------
# MÉTRICAS CUSTOMIZADAS (CARDS EM HTML - VERSÃO BLINDADA)
# -------------------
total = len(df)
contagem = df["veiculo"].value_counts()

# Criamos a string HTML limpa, usando marcadores isolados para as variáveis
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
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #1E293B; font-weight: 700;">{qtd_folha}</h3>
        </div>

        <div style="flex: 1; min-width: 160px; background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #2563EB;">
            <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">🟡 UOL</p>
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #1E293B; font-weight: 700;">{qtd_uol}</h3>
        </div>

        <div style="flex: 1; min-width: 160px; background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #059669;">
            <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔴 CNN & JOTA</p>
            <h3 style="margin: 5px 0 0 0; font-size: 28px; color: #1E293B; font-weight: 700;">{qtd_outros}</h3>
        </div>

    </div>
"""

# Injeta os números dinâmicos com segurança usando .format()
st.html(
    html_cards.format(
        total_geral=total,
        qtd_estadao=contagem.get("Estadão", 0),
        qtd_folha=contagem.get("Folha", 0),
        qtd_uol=contagem.get("UOL", 0),
        qtd_outros=contagem.get("CNN Brasil", 0) + contagem.get("JOTA", 0)
    )
)

# -------------------
# FILTROS E BUSCA (Dentro de um painel expansível)
# -------------------
with st.expander("🔍 Ferramentas de Filtro e Busca", expanded=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        busca = st.text_input("Buscar palavra-chave no título...")
    with c2:
        opcoes_v = sorted(df["veiculo"].unique()) if not df.empty else []
        veiculos = st.multiselect("Veículos", options=opcoes_v, default=opcoes_v)
    with c3:
        opcoes_a = sorted(df["autor"].dropna().unique()) if not df.empty else []
        autores = st.multiselect("Filtrar por Autor", options=opcoes_a)

# Aplicação dos filtros selecionados
if not df.empty:
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    df = df[df["veiculo"].isin(veiculos)]
    if autores:
        df = df[df["autor"].isin(autores)]

# -------------------
# TABELA PRINCIPAL EXPANDIDA
# -------------------
st.subheader("📋 Clipping de Notícias")

if not df.empty:
    st.dataframe(
        df[["veiculo", "titulo", "autor", "url", "data_publicacao"]],
        use_container_width=True,
        hide_index=True,
        height=620,  # Altura ampliada para exibição profissional
        column_config={
            "veiculo": st.column_config.TextColumn("Fonte", width="small"),
            "titulo": st.column_config.TextColumn("Notícia (Título)", width="large"),
            "autor": st.column_config.TextColumn("Autor", width="medium"),
            "data_publicacao": st.column_config.TextColumn("Horário", width="small"),
            "url": st.column_config.LinkColumn(
                "Link", 
                display_text="Ler Agora", 
                help="Clique para abrir a matéria original",
                width="small"
            )
        }
    )
    
    # Botão para download dos dados limpos
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exportar Clipping para Excel/CSV", csv, "clipping_noticias.csv", "text/csv")
else:
    st.warning("Nenhum dado encontrado para os filtros aplicados.")
