import streamlit as st
import pandas as pd
import sqlite3

# -------------------
# Configuração da página
# -------------------

st.set_page_config(
    page_title="Monitor de Notícias",
    layout="wide"
)

st.title("📰 Monitor de Notícias")

# -------------------
# Carrega dados (Seguro contra concorrência)
# -------------------

try:
    # O check_same_thread=False permite que o Streamlit consulte o banco sem travamentos
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
    # Caso o banco de dados ainda não exista na nuvem, cria um DataFrame estruturado vazio
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
# Métricas Dinâmicas
# -------------------

st.metric("Total de matérias monitoradas", len(df))

# Descobre e conta os veículos presentes no banco de dados automaticamente
contagem_veiculos = df["veiculo"].value_counts()

if not contagem_veiculos.empty:
    cols = st.columns(len(contagem_veiculos))
    for i, (veiculo, total) in enumerate(contagem_veiculos.items()):
        cols[i].metric(veiculo, total)

st.divider()

# -------------------
# Resumo informativo
# -------------------

st.subheader("Resumo")

st.write(
    f"""
    Existem **{len(df)} matérias** monitoradas.

    Foram encontradas matérias de **{df['veiculo'].nunique()} veículos** e
    **{df['autor'].nunique()} autores**.
    """
)

st.subheader("Autores mais ativos")

ranking_autores = (
    df["autor"]
    .value_counts()
    .reset_index()
)

ranking_autores.columns = [
    "Autor",
    "Matérias"
]

st.dataframe(
    ranking_autores.head(20),
    use_container_width=True,
    hide_index=True
)

# -------------------
# Busca por palavra
# -------------------

busca = st.text_input(
    "🔎 Buscar no título"
)

if busca and not df.empty:
    df = df[
        df["titulo"].str.contains(
            busca,
            case=False,
            na=False
        )
    ]

# -------------------
# Filtro por veículo
# -------------------

opcoes_veiculos = sorted(df["veiculo"].unique()) if not df.empty else []

veiculos = st.multiselect(
    "Veículos",
    options=opcoes_veiculos,
    default=opcoes_veiculos
)

if not df.empty:
    df = df[df["veiculo"].isin(veiculos)]

# -------------------
# Filtro por autor
# -------------------

opcoes_autores = sorted(df["autor"].dropna().unique()) if not df.empty else []

autores = st.multiselect(
    "Autores",
    options=opcoes_autores
)

if autores and not df.empty:
    df = df[df["autor"].isin(autores)]

st.divider()

# -------------------
# Download CSV
# -------------------

csv = df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="📥 Baixar CSV",
    data=csv,
    file_name="noticias.csv",
    mime="text/csv"
)

# -------------------
# Tabela de Resultados
# -------------------

st.dataframe(
    df[
        [
            "veiculo",
            "titulo",
            "autor",
            "url",
            "data_publicacao"
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "veiculo": "Veículo",
        "titulo": "Título",
        "autor": "Autor",
        "data_publicacao": "Data",

        "url": st.column_config.LinkColumn(
            "Abrir",
            help="Abrir matéria",
            display_text="Abrir"
        )
    }
)
