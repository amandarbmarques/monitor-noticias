import streamlit as st
import pandas as pd
import sqlite3

# -------------------
# Configuração da página
# -------------------
st.set_page_config(
    page_title="Monitor de Notícias",
    layout="wide"  # Garante que o app use a tela inteira
)

st.title("📰 Monitor de Notícias")

# -------------------
# Carrega dados (Seguro contra concorrência)
# -------------------
try:
    with sqlite3.connect("noticias.db", check_same_thread=False) as conn:
        df = pd.read_sql(
            """
            SELECT *
            FROM noticias
            ORDER BY data_publicacao DESC
            """,
            conn
        )
except Exception as e:
    df = pd.DataFrame(columns=["veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# -------------------
# Correção do Fuso Horário (UTC para Brasília)
# -------------------
if not df.empty:
    try:
        df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        if df['data_publicacao'].dt.tz is not None:
            df['data_publicacao'] = df['data_publicacao'].dt.tz_convert('America/Sao_Paulo')
        else:
            df['data_publicacao'] = df['data_publicacao'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        df['data_publicacao'] = df['data_publicacao'].dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        pass

# -------------------
# BARRA LATERAL (Sidebar) - Perfil de Autores e Infos
# -------------------
st.sidebar.header("✍️ Ranking de Autores")

if not df.empty:
    ranking_autores = df["autor"].value_counts().reset_index()
    ranking_autores.columns = ["Autor", "Matérias"]
    
    # Exibe a tabela de autores na barra lateral de forma compacta
    st.sidebar.dataframe(
        ranking_autores.head(15),
        use_container_width=True,
        hide_index=True,
        height=400  # Define um tamanho fixo bom para a barra lateral
    )
else:
    st.sidebar.write("Nenhum autor mapeado ainda.")

st.sidebar.divider()
st.sidebar.write("💡 *Dica: Use os filtros principais para ajustar a tabela ao lado.*")

# -------------------
# CORPO PRINCIPAL - Métricas Dinâmicas
# -------------------
st.metric("Total de matérias monitoradas", len(df))

contagem_veiculos = df["veiculo"].value_counts()
if not contagem_veiculos.empty:
    cols = st.columns(len(contagem_veiculos))
    for i, (veiculo, total) in enumerate(contagem_veiculos.items()):
        cols[i].metric(veiculo, total)

st.divider()

# -------------------
# Resumo informativo e Filtros de Busca
# -------------------
st.subheader("Filtros e Busca")

col_busca, col_mult1, col_mult2 = st.columns([2, 1, 1])

with col_busca:
    busca = st.text_input("🔎 Buscar no título")

with col_mult1:
    opcoes_veiculos = sorted(df["veiculo"].unique()) if not df.empty else []
    veiculos = st.multiselect("Veículos", options=opcoes_veiculos, default=opcoes_veiculos)

with col_mult2:
    opcoes_autores = sorted(df["autor"].dropna().unique()) if not df.empty else []
    autores = st.multiselect("Filtrar por Autor", options=opcoes_autores)

# Aplicando os filtros no DataFrame
if not df.empty:
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    df = df[df["veiculo"].isin(veiculos)]
    if autores:
        df = df[df["autor"].isin(autores)]

# -------------------
# Tabela de Resultados EXPANDIDA
# -------------------
st.subheader("📋 Matérias Capturadas")

if not df.empty:
    # Exibe a tabela bem grande e espaçada
    st.dataframe(
        df[["veiculo", "titulo", "autor", "url", "data_publicacao"]],
        use_container_width=True,
        hide_index=True,
        height=600,  # Aumentei consideravelmente a altura para não parecer minimizada
        column_config={
            "veiculo": st.column_config.TextColumn("Veículo", width="medium"),
            "titulo": st.column_config.TextColumn("Título da Matéria", width="large"),
            "autor": st.column_config.TextColumn("Autor", width="medium"),
            "data_publicacao": st.column_config.TextColumn("Data/Hora", width="small"),
            "url": st.column_config.LinkColumn(
                "Abrir",
                help="Clique para ler a matéria original",
                display_text="Ler Matéria",
                width="small"
            )
        }
    )
else:
    st.info("Nenhuma notícia encontrada para os filtros selecionados.")

# -------------------
# Download CSV (Discretamente no rodapé)
# -------------------
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name="noticias_filtradas.csv",
        mime="text/csv"
    )
