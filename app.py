# app.py

import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(
    page_title="Monitor Editorial",
    page_icon="📰",
    layout="wide"
)

# =====================================
# BANCO
# =====================================

DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"


@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
def carregar_dados():

    try:
        conn = psycopg2.connect(DB_URI)

        df = pd.read_sql(
            """
            SELECT *
            FROM noticias
            ORDER BY data_coleta DESC
            """,
            conn
        )

        conn.close()

        return df

    except Exception as e:

        st.error("Erro ao conectar ao banco")

        st.write("Tipo do erro:")
        st.write(type(e))

        st.write("Mensagem:")
        st.write(str(e))

        st.stop()


# =====================================
# TEXTO
# =====================================

def extrair_palavras_chave(titulo):

    stop_words = {
        "a","o","e","de","da","do","em",
        "para","por","que","é","um","uma",
        "os","as","com","mais","não",
        "sobre","após","contra","entre"
    }

    titulo = str(titulo)

    for char in [".", ",", "!", "?", ":", ";", "-", "(", ")"]:
        titulo = titulo.replace(char, " ")

    palavras = titulo.lower().split()

    return {
        p for p in palavras
        if p not in stop_words and len(p) > 3
    }


# =====================================
# AGRUPAMENTO
# =====================================

def agrupar_pautas(df):

    df = df.sort_values(
        "data_dt"
    ).reset_index(drop=True)

    df["grupo_pauta"] = None

    grupos = {}

    for idx, row in df.iterrows():

        palavras = extrair_palavras_chave(
            row["titulo"]
        )

        melhor_grupo = None
        melhor_score = 0

        for grupo_id, dados in grupos.items():

            inter = len(
                palavras &
                dados["palavras"]
            )

            menor = min(
                len(palavras),
                len(dados["palavras"])
            )

            score = (
                inter / menor
                if menor else 0
            )

            if score > 0.50 and score > melhor_score:
                melhor_score = score
                melhor_grupo = grupo_id

        if melhor_grupo is None:

            novo_id = len(grupos)

            grupos[novo_id] = {
                "palavras": palavras
            }

            melhor_grupo = novo_id

        else:

            grupos[
                melhor_grupo
            ]["palavras"].update(
                palavras
            )

        df.at[
            idx,
            "grupo_pauta"
        ] = melhor_grupo

    return df


# =====================================
# CONSTRUIR PAUTAS
# =====================================

def construir_pautas(df):

    pautas = []

    agora = pd.Timestamp.now(
        tz="America/Sao_Paulo"
    )

    for grupo_id, grupo in df.groupby(
        "grupo_pauta"
    ):

        grupo = grupo.sort_values(
            "data_dt"
        )

        primeiro = grupo.iloc[0]
        ultimo = grupo.iloc[-1]

        total_materias = len(grupo)
        total_veiculos = grupo[
            "veiculo"
        ].nunique()

        idade_horas = (
            agora - ultimo["data_dt"]
        ).total_seconds() / 3600

        duracao = (
            grupo["data_dt"].max()
            -
            grupo["data_dt"].min()
        ).total_seconds() / 3600

        duracao = max(duracao, 1)

        velocidade = (
            total_materias / duracao
        )

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

            "titulo":
                primeiro["titulo"],

            "origem":
                primeiro["veiculo"],

            "url":
                primeiro["url"],

            "primeira_data":
                primeiro["data_dt"],

            "ultima_data":
                ultimo["data_dt"],

            "ultima_data_fmt":
                ultimo["data_dt"].strftime(
                    "%d/%m %H:%M"
                ),

            "total_materias":
                total_materias,

            "total_veiculos":
                total_veiculos,

            "veiculos":
                list(
                    grupo["veiculo"]
                    .unique()
                ),

            "velocidade":
                round(
                    velocidade,
                    1
                ),

            "score":
                round(score),

            "idade_horas":
                round(
                    idade_horas,
                    1
                ),

            "status":
                status,

            "grupo":
                grupo
        })

    return pd.DataFrame(
        pautas
    )


# =====================================
# DIALOG
# =====================================

@st.dialog("📰 Cobertura")
def mostrar_cobertura(
    titulo,
    grupo
):

    grupo = grupo.sort_values(
        "data_dt"
    )

    st.subheader(titulo)

    inicio = grupo.iloc[0][
        "data_dt"
    ]

    for i, (
        _,
        row
    ) in enumerate(
        grupo.iterrows(),
        start=1
    ):

        delta = (
            row["data_dt"]
            -
            inicio
        )

        minutos = int(
            delta.total_seconds()
            / 60
        )

        st.markdown(
            f"### {i}. {row['veiculo']}"
        )

        st.caption(
            f"{row['data_dt'].strftime('%d/%m %H:%M')} "
            f"(+{minutos} min)"
        )

        st.write(
            row["titulo"]
        )

        st.link_button(
            "Abrir matéria",
            row["url"]
        )

        st.divider()


# =====================================
# DADOS
# =====================================

df = carregar_dados()

df["data_dt"] = pd.to_datetime(
    df["data_publicacao"],
    errors="coerce",
    utc=True
)

df["data_dt"] = df[
    "data_dt"
].fillna(

    pd.to_datetime(
        df["data_coleta"],
        utc=True,
        errors="coerce"
    )
)

df["data_dt"] = (
    df["data_dt"]
    .dt.tz_convert(
        "America/Sao_Paulo"
    )
)

# =====================================
# ALERTA SAÚDE
# =====================================

ultima_coleta = pd.to_datetime(
    df["data_coleta"].max(),
    utc=True
)

horas = (
    pd.Timestamp.now(
        tz="UTC"
    )
    -
    ultima_coleta
).total_seconds() / 3600

if horas > 6:

    st.error(
        f"⚠️ Sem novas notícias há {horas:.1f} horas"
    )

else:

    st.success(
        f"✅ Atualizado há {horas:.1f} horas"
    )

# =====================================
# PAUTAS
# =====================================

df = agrupar_pautas(df)

df_pautas = construir_pautas(df)

st.title(
    "📰 Monitor Editorial"
)

busca = st.text_input(
    "",
    placeholder="🔎 Buscar pauta...",
    label_visibility="collapsed"
)

if busca:

    df_pautas = df_pautas[
        df_pautas["titulo"]
        .str.contains(
            busca,
            case=False,
            na=False
        )
    ]

# =====================================
# MÉTRICAS
# =====================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Pautas",
    len(df_pautas)
)

c2.metric(
    "Matérias",
    int(
        df_pautas[
            "total_materias"
        ].sum()
    )
)

c3.metric(
    "Veículos",
    df["veiculo"].nunique()
)

c4.metric(
    "Última coleta",
    ultima_coleta
    .tz_convert(
        "America/Sao_Paulo"
    )
    .strftime("%d/%m %H:%M")
)

st.divider()

# =====================================
# PAUTAS QUENTES
# =====================================

st.subheader(
    "🔥 Pautas Quentes"
)

quentes = df_pautas[
    df_pautas["status"]
    == "🔥 Quente"
].sort_values(
    "score",
    ascending=False
)

for _, pauta in quentes.head(10).iterrows():

    with st.container(
        border=True
    ):

        st.markdown(
            f"### {pauta['titulo']}"
        )

        st.caption(
            pauta["status"]
        )

        st.write(
            f"📡 {pauta['total_veiculos']} veículos"
        )

        st.write(
            f"📰 {pauta['total_materias']} matérias"
        )

        st.write(
            f"⚡ {pauta['velocidade']} matérias/h"
        )

        st.write(
            f"🎯 Score: {pauta['score']}"
        )

        st.caption(
            f"Última repercussão: "
            f"{pauta['ultima_data_fmt']}"
        )

        a, b = st.columns(2)

        with a:

            st.link_button(
                "Origem",
                pauta["url"]
            )

        with b:

            if st.button(
                "Cobertura",
                key=f"cob_{pauta['grupo_id']}"
            ):
                mostrar_cobertura(
                    pauta["titulo"],
                    pauta["grupo"]
                )

# =====================================
# RANKING
# =====================================

st.divider()

st.subheader(
    "📊 Ranking Editorial"
)

ranking = df_pautas[
    [
        "titulo",
        "status",
        "total_veiculos",
        "total_materias",
        "velocidade",
        "score"
    ]
].sort_values(
    "score",
    ascending=False
)

st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=True
)
