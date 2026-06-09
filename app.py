
# VERSÃO 2 - Monitor de Notícias
# Melhorias:
# - Dashboard de métricas
# - Modal de repercussão
# - Cards com status de repercussão
# - Ordenação por repercussão
# - Modo Editor (tabela por pauta)

import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(
    page_title="Monitor de Notícias",
    page_icon="📰",
    layout="wide"
)

if "modal_aberto" not in st.session_state:
    st.session_state.modal_aberto = None

def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Geral"

    t = titulo.lower()

    if any(x in t for x in [
        "lula","governo","stf","política","congresso",
        "senado","moraes","pt","pl","eleições"
    ]):
        return "Política/Judiciário"

    if any(x in t for x in [
        "economia","inflação","dólar","mercado",
        "haddad","juros","pib"
    ]):
        return "Economia"

    return "Geral"

def extrair_palavras_chave(titulo, n=7):
    stop_words = {
        "a","o","e","de","da","do","em","para","por",
        "que","é","um","uma","os","as","com","mais",
        "não","sobre","após","contra"
    }

    for char in [".", ",", "!", "?", "(", ")", "-", ":"]:
        titulo = titulo.replace(char, " ")

    palavras = titulo.lower().split()

    return [
        p for p in palavras
        if p not in stop_words and len(p) > 3
    ][:n]

df = agrupar_noticias_semelhantes(df)

df_pautas = construir_pautas(df)

    df = df.sort_values("data_dt").reset_index(drop=True)
    df["grupo_noticia"] = None

    grupos = {}

    for idx, row in df.iterrows():

        palavras = set(
            extrair_palavras_chave(
                str(row["titulo"])
            )
        )

        data_atual = row["data_dt"]

        melhor = None
        score_melhor = 0

        for grupo_id, dados in grupos.items():

            diferenca_horas = abs(
                (data_atual - dados["data"]).total_seconds()
            ) / 3600

            if diferenca_horas > 24:
                continue

            inter = len(
                palavras & dados["palavras"]
            )

            menor = min(
                len(palavras),
                len(dados["palavras"])
            )

            score = inter / menor if menor else 0

            if score >= 0.55 and score > score_melhor:
                score_melhor = score
                melhor = grupo_id

        if melhor is None:
            melhor = len(grupos)
            grupos[melhor] = {
                "palavras": palavras,
                "data": data_atual
            }
        else:
            grupos[melhor]["palavras"].update(
                palavras
            )

        df.at[idx, "grupo_noticia"] = melhor

    return df.sort_values(
        "data_dt",
        ascending=False
    )

def construir_pautas(df):

    pautas = []

    agora = pd.Timestamp.now(
        tz="America/Sao_Paulo"
    )

    for grupo_id, grupo in df.groupby("grupo_noticia"):

        grupo = grupo.sort_values("data_dt")

        primeiro = grupo.iloc[0]
        ultimo = grupo.iloc[-1]

        total_materias = len(grupo)
        total_veiculos = grupo["veiculo"].nunique()

        idade_horas = (
            agora - ultimo["data_dt"]
        ).total_seconds() / 3600

        score = (
            total_veiculos * 5
            +
            total_materias * 2
            +
            max(0, 24 - idade_horas)
        )

        if idade_horas <= 12 and total_veiculos >= 3:
            status = "🔥 Quente"
        elif idade_horas <= 24:
            status = "📈 Crescendo"
        else:
            status = "💤 Esfriando"

        pautas.append({
            "grupo_id": grupo_id,
            "titulo": primeiro["titulo"],
            "origem": primeiro["veiculo"],
            "url": primeiro["url"],
            "primeira_data": primeiro["data_dt"],
            "ultima_data": ultimo["data_dt"],
            "ultima_data_fmt": ultimo["data_dt"].strftime("%d/%m %H:%M"),
            "total_materias": total_materias,
            "total_veiculos": total_veiculos,
            "veiculos": list(grupo["veiculo"].unique()),
            "score": round(score),
            "status": status,
            "grupo": grupo
        })

    return pd.DataFrame(pautas)

@st.cache_data(ttl=30)
def carregar_dados():
    DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

    conn = psycopg2.connect(DB_URI)

    df = pd.read_sql(
        "SELECT * FROM noticias ORDER BY data_coleta DESC",
        conn
    )

    conn.close()
    return df

@st.dialog("📚 Repercussão da pauta")
def mostrar_dialog(titulo, grupo):

    st.markdown(f"### {titulo}")

    primeira = grupo.iloc[0]

    st.success(
        f"Primeiro registro: "
        f"{primeira['veiculo']} "
        f"({primeira['data_formatada']})"
    )

    st.divider()

    for pos, (_, row) in enumerate(
        grupo.iterrows(),
        start=1
    ):

        st.markdown(
            f"**{pos}. {row['veiculo']}**"
        )

        st.caption(
            row["data_formatada"]
        )

        st.write(row["titulo"])

        st.link_button(
            "Abrir notícia",
            row["url"]
        )

        st.divider()

df = carregar_dados()

df["data_dt"] = pd.to_datetime(
    df["data_publicacao"],
    errors="coerce",
    utc=True
)

if "data_coleta" in df.columns:
    df["data_dt"] = df["data_dt"].fillna(
        pd.to_datetime(
            df["data_coleta"],
            errors="coerce",
            utc=True
        )
    )

df["data_dt"] = df["data_dt"].fillna(
    pd.Timestamp.now(tz="UTC")
)

df["data_dt"] = (
    df["data_dt"]
    .dt.tz_convert("America/Sao_Paulo")
)

df["data_formatada"] = (
    df["data_dt"]
    .dt.strftime("%d/%m %H:%M")
)

df["tema"] = df["titulo"].apply(
    classificar_tema
)

df = agrupar_noticias_semelhantes(df)

st.title("📰 Monitor de Notícias")

modo = st.radio(
    "Visualização",
    ["Cards", "Editor"],
    horizontal=True
)

busca = st.text_input(
    "",
    placeholder="🔎 Buscar...",
    label_visibility="collapsed"
)

df_filtrado = df.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["titulo"].str.contains(
            busca,
            case=False,
            na=False
        )
    ]

grupos = (
    df_filtrado.groupby("grupo_noticia")
    .size()
    .reset_index(name="total")
)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Notícias", len(df_filtrado))
m2.metric("Pautas", len(grupos))
m3.metric(
    "Repercutidas",
    len(grupos[grupos.total > 1])
)
m4.metric(
    "Veículos",
    df_filtrado["veiculo"].nunique()
)

st.divider()

if modo == "Editor":

    linhas = []

    for grupo_id, grupo in df_filtrado.groupby(
        "grupo_noticia"
    ):

        grupo = grupo.sort_values(
            "data_dt"
        )

        primeiro = grupo.iloc[0]

        linhas.append({
            "Tema": primeiro["titulo"][:120],
            "Primeiro veículo": primeiro["veiculo"],
            "Hora": primeiro["hora"]
            if "hora" in primeiro
            else primeiro["data_dt"].strftime("%H:%M"),
            "Veículos": len(grupo)
        })

    tabela = pd.DataFrame(linhas)

    tabela = tabela.sort_values(
        "Veículos",
        ascending=False
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )

else:

    df_filtrado["total_similares"] = (
        df_filtrado.groupby("grupo_noticia")
        ["grupo_noticia"]
        .transform("count")
    )

    df_filtrado = df_filtrado.sort_values(
        ["total_similares","data_dt"],
        ascending=[False,False]
    )

    itens = df_filtrado.reset_index(
        drop=True
    )

    for i in range(0, len(itens), 3):

        cols = st.columns(3)

        for j in range(3):

            if i+j >= len(itens):
                continue

            row = itens.iloc[i+j]

            grupo = df[
                df["grupo_noticia"]
                == row["grupo_noticia"]
            ]

            with cols[j]:

                with st.container(border=True):

                    st.markdown(
                        f"### {row['titulo']}"
                    )

                    st.caption(
                        row["veiculo"]
                    )

                    st.caption(
                        row["data_formatada"]
                    )

                    st.write(
                        f"Repercussão: "
                        f"{len(grupo)} veículos"
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        st.link_button(
                            "Abrir",
                            row["url"],
                            use_container_width=True
                        )

                    with c2:
                        if len(grupo) > 1:
                            if st.button(
                                "Repercussão",
                                key=f"r_{i}_{j}",
                                use_container_width=True
                            ):
                                mostrar_dialog(
                                    row["titulo"],
                                    grupo.sort_values(
                                        "data_dt"
                                    )
                                )
