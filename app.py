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
# Carrega dados
# -------------------

conn = sqlite3.connect("noticias.db")

df = pd.read_sql(
    """
    SELECT *
    FROM noticias
    ORDER BY data_publicacao DESC
    """,
    conn
)

conn.close()

# ... código anterior de carga de dados ...
df = pd.read_sql("SELECT * FROM noticias ORDER BY data_publicacao DESC", conn)
conn.close()

# -------------------
# Correção do Fuso Horário (UTC para Brasília)
# -------------------
try:
    # Converte a coluna para o tipo datetime do pandas
    df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
    
    # Se a data vier com fuso (UTC), localiza e converte para o de Brasília (-3)
    if df['data_publicacao'].dt.tz is not None:
        df['data_publicacao'] = df['data_publicacao'].dt.tz_convert('America/Sao_Paulo')
    else:
        # Se vier sem fuso, assume que é UTC e converte para Brasília
        df['data_publicacao'] = df['data_publicacao'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        
    # Formata a exibição para ficar bonita na tabela (Ex: 03/06/2026 12:44)
    df['data_publicacao'] = df['data_publicacao'].dt.strftime('%d/%m/%Y %H:%M')
except Exception as e:
    # Caso alguma linha dê erro de conversão, mantém o texto original para não quebrar o app
    pass

# -------------------
# Métricas Dinâmicas
# -------------------

# Métrica geral destacada
st.metric("Total de matérias monitoradas", len(df))

# Agrupa por veículo para gerar as mini-métricas
contagem_veiculos = df["veiculo"].value_counts()

if not contagem_veiculos.empty:
    # Cria colunas automaticamente dependendo de quantos veículos existem no banco
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

if busca:
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

veiculos = st.multiselect(
    "Veículos",
    options=sorted(df["veiculo"].unique()),
    default=sorted(df["veiculo"].unique())
)

df = df[
    df["veiculo"].isin(veiculos)
]

# -------------------
# Filtro por autor
# -------------------

autores = st.multiselect(
    "Autores",
    options=sorted(df["autor"].dropna().unique())
)

if autores:
    df = df[
        df["autor"].isin(autores)
    ]

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