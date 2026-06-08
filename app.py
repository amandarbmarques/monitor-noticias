# app_monitor_pautas.py
import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(
    page_title="Monitor de Pautas",
    page_icon="📰",
    layout="wide"
)

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


def agrupar_noticias_semelhantes(df):

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

    for grupo_id, grupo in df.groupby("grupo_noticia"):

        grupo = grupo.sort_values("data_dt")

        primeiro = grupo.iloc[0]

        pautas.append({
            "grupo_id": grupo_id,
            "titulo": primeiro["titulo"],
            "primeiro_veiculo": primeiro["veiculo"],
            "primeira_data": primeiro["data_dt"],
            "primeira_data_formatada": primeiro["data_formatada"],
            "url_origem": primeiro["url"],
            "total_materias": len(grupo),
            "total_veiculos": grupo["veiculo"].nunique(),
            "veiculos": list(grupo["veiculo"].unique()),
            "grupo": grupo
        })

    return pd.DataFrame(pautas)


@st.cache_data(ttl=30)
def carregar_dados():

    DB_URI = "SEU_DB_URI_AQUI"

    conn = psycopg2.connect(DB_URI)

    df = pd.read_sql(
        "SELECT * FROM noticias ORDER BY data_coleta DESC",
        conn
    )

    conn.close()

    return df


@st.dialog("📚 Cobertura da pauta")
def mostrar_dialog(titulo, grupo):

    grupo = grupo.sort_values("data_dt")

    st.markdown(f"### {titulo}")

    primeira = grupo.iloc[0]
    inicio = primeira["data_dt"]

    st.success(
        f"Origem: {primeira['veiculo']} "
        f"({primeira['data_formatada']})"
    )

    st.divider()

    for pos, (_, row) in enumerate(
        grupo.iterrows(),
        start=1
    ):

        delta = row["data_dt"] - inicio
        minutos = int(delta.total_seconds() / 60)

        st.markdown(
            f"**{pos}. {row['veiculo']}**"
        )

        st.caption(
            f"{row['data_formatada']} "
            f"(+{minutos} min)"
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

df_pautas = construir_pautas(df)

st.title("📰 Monitor de Pautas")

modo = st.radio(
    "Visualização",
    ["Cards", "Editor"],
    horizontal=True
)

busca = st.text_input(
    "",
    placeholder="🔎 Buscar pauta...",
    label_visibility="collapsed"
)

df_filtrado = df_pautas.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["titulo"].str.contains(
            busca,
            case=False,
            na=False
        )
    ]

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Pautas",
    len(df_filtrado)
)

m2.metric(
    "Matérias",
    int(df_filtrado["total_materias"].sum())
)

m3.metric(
    "Pautas repercutidas",
    len(
        df_filtrado[
            df_filtrado["total_veiculos"] > 1
        ]
    )
)

m4.metric(
    "Veículos",
    df["veiculo"].nunique()
)

st.divider()

if modo == "Editor":

    tabela = (
        df_filtrado[
            [
                "titulo",
                "primeiro_veiculo",
                "primeira_data_formatada",
                "total_veiculos",
                "total_materias"
            ]
        ]
        .rename(
            columns={
                "titulo": "Pauta",
                "primeiro_veiculo": "Origem",
                "primeira_data_formatada": "Hora",
                "total_veiculos": "Veículos",
                "total_materias": "Matérias"
            }
        )
        .sort_values(
            "Veículos",
            ascending=False
        )
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )

else:

    pautas = df_filtrado.sort_values(
        ["total_veiculos", "primeira_data"],
        ascending=[False, False]
    )

    itens = pautas.reset_index(drop=True)

    for i in range(0, len(itens), 3):

        cols = st.columns(3)

        for j in range(3):

            if i + j >= len(itens):
                continue

            pauta = itens.iloc[i + j]

            with cols[j]:

                with st.container(border=True):

                    st.markdown(
                        f"### {pauta['titulo']}"
                    )

                    st.caption(
                        f"🚀 Primeiro: "
                        f"{pauta['primeiro_veiculo']}"
                    )

                    st.caption(
                        pauta["primeira_data_formatada"]
                    )

                    st.write(
                        f"📡 {pauta['total_veiculos']} veículos"
                    )

                    st.write(
                        f"📰 {pauta['total_materias']} matérias"
                    )

                    st.caption(
                        " • ".join(
                            pauta["veiculos"][:5]
                        )
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        st.link_button(
                            "Origem",
                            pauta["url_origem"],
                            use_container_width=True
                        )

                    with c2:
                        if st.button(
                            "Cobertura",
                            key=f"pauta_{pauta['grupo_id']}",
                            use_container_width=True
                        ):
                            mostrar_dialog(
                                pauta["titulo"],
                                pauta["grupo"]
                            )
