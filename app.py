import streamlit as st
import pandas as pd
import psycopg2
from dateutil import parser as dateparser
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Monitor de Pauta",
    page_icon="📡",
    layout="wide"
)

st.markdown("""
<style>
    .pauta-card { border-radius: 8px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

BR_TZ = ZoneInfo("America/Sao_Paulo")


def parse_data(valor):
    if pd.isna(valor) or valor == "" or valor is None:
        return pd.NaT
    try:
        dt = dateparser.parse(str(valor))
        if dt is None:
            return pd.NaT
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BR_TZ)
        else:
            dt = dt.astimezone(BR_TZ)
        return pd.Timestamp(dt)
    except Exception:
        return pd.NaT


def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Geral"
    t = titulo.lower()
    if any(x in t for x in [
        "lula", "governo", "stf", "politica", "congresso",
        "senado", "moraes", "pt", "pl", "eleicoes", "política", "eleições"
    ]):
        return "Política/Judiciário"
    if any(x in t for x in [
        "economia", "inflacao", "dolar", "mercado",
        "haddad", "juros", "pib", "inflação", "dólar"
    ]):
        return "Economia"
    return "Geral"


def extrair_palavras_chave(titulo, n=7):
    stop_words = {
        "a", "o", "e", "de", "da", "do", "em", "para", "por",
        "que", "e", "um", "uma", "os", "as", "com", "mais",
        "nao", "sobre", "apos", "contra", "no", "na", "ao", "dos",
        "das", "pelo", "pela", "entre", "seus", "sua", "isso", "este",
        "não", "após"
    }
    for char in [".", ",", "!", "?", "(", ")", "-", ":", "'"]:
        titulo = titulo.replace(char, " ")
    palavras = titulo.lower().split()
    return [p for p in palavras if p not in stop_words and len(p) > 3][:n]


def agrupar_noticias_semelhantes(df):
    df = df.sort_values("data_publicacao_dt").reset_index(drop=True)
    df["grupo_noticia"] = None
    grupos = {}

    for idx, row in df.iterrows():
        palavras = set(extrair_palavras_chave(str(row["titulo"])))
        data_atual = row["data_publicacao_dt"]

        if pd.isna(data_atual):
            melhor = len(grupos)
            grupos[melhor] = {"palavras": palavras, "data": pd.Timestamp.now(tz=BR_TZ)}
            df.at[idx, "grupo_noticia"] = melhor
            continue

        melhor = None
        score_melhor = 0

        for grupo_id, dados in grupos.items():
            data_grupo = dados["data"]
            if pd.isna(data_grupo):
                continue
            diferenca_horas = abs((data_atual - data_grupo).total_seconds()) / 3600
            if diferenca_horas > 36:
                continue
            inter = len(palavras & dados["palavras"])
            menor = min(len(palavras), len(dados["palavras"]))
            score = inter / menor if menor else 0
            if score >= 0.5 and score > score_melhor:
                score_melhor = score
                melhor = grupo_id

        if melhor is None:
            melhor = len(grupos)
            grupos[melhor] = {"palavras": palavras, "data": data_atual}
        else:
            grupos[melhor]["palavras"].update(palavras)

        df.at[idx, "grupo_noticia"] = melhor

    return df.sort_values("data_publicacao_dt", ascending=False)


def construir_pautas(df):
    pautas = []
    agora = pd.Timestamp.now(tz=BR_TZ)

    for grupo_id, grupo in df.groupby("grupo_noticia"):
        grupo = grupo.sort_values("data_publicacao_dt")
        grupo_com_data = grupo.dropna(subset=["data_publicacao_dt"])

        if grupo_com_data.empty:
            continue

        primeiro = grupo_com_data.iloc[0]
        ultimo = grupo_com_data.iloc[-1]

        total_materias = len(grupo)
        total_veiculos = grupo["veiculo"].nunique()

        idade_horas = (agora - ultimo["data_publicacao_dt"]).total_seconds() / 3600
        score = (
            total_veiculos * 5
            + total_materias * 2
            + max(0, 24 - idade_horas)
        )

        # Furo: 1 publicou primeiro + pelo menos 3 outros seguiram (4+ veiculos total)
        if total_veiculos >= 4:
            status = "🎯 Furo"
        elif total_veiculos >= 2 and idade_horas <= 12:
            status = "🔥 Quente"
        elif idade_horas <= 24:
            status = "📈 Crescendo"
        else:
            status = "💤 Esfriando"

        pautas.append({
            "grupo_id":          grupo_id,
            "titulo":            primeiro["titulo"],
            "origem":            primeiro["veiculo"],
            "url":               primeiro["url"],
            "primeira_data":     primeiro["data_publicacao_dt"],
            "ultima_data":       ultimo["data_publicacao_dt"],
            "primeira_data_fmt": primeiro["data_publicacao_dt"].strftime("%d/%m %H:%M"),
            "ultima_data_fmt":   ultimo["data_publicacao_dt"].strftime("%d/%m %H:%M"),
            "total_materias":    total_materias,
            "total_veiculos":    total_veiculos,
            "veiculos":          list(grupo["veiculo"].unique()),
            "score":             round(score),
            "status":            status,
            "grupo":             grupo_com_data.reset_index(drop=True),
            "tema":              classificar_tema(primeiro["titulo"]),
        })

    return pd.DataFrame(pautas)


@st.cache_data(ttl=60)
def carregar_dados():
    DB_URI = st.secrets["DB_URI"]
    conn = psycopg2.connect(DB_URI)
    df = pd.read_sql(
        "SELECT * FROM noticias ORDER BY data_coleta DESC",
        conn
    )
    conn.close()

    df["data_publicacao_dt"] = df["data_publicacao"].apply(parse_data)

    df["data_coleta_dt"] = pd.to_datetime(df["data_coleta"], utc=True, errors="coerce")
    df["data_coleta_dt"] = df["data_coleta_dt"].dt.tz_convert(BR_TZ)

    df["data_publicacao_dt"] = df["data_publicacao_dt"].fillna(df["data_coleta_dt"])

    return df


# ─────────────────────────────────────────────
# MODAL — LINHA DO TEMPO DA COBERTURA
# Agrupa por veículo: linha do tempo mostra primeira publicação de cada um
# e lista todas as matérias daquele veículo abaixo
# ─────────────────────────────────────────────
@st.dialog("Cobertura da pauta", width="large")
def mostrar_cobertura(titulo, grupo):
    st.markdown(f"### {titulo}")

    # Primeira publicacao de cada veiculo para montar a linha do tempo
    primeiro_por_veiculo = (
        grupo.sort_values("data_publicacao_dt")
        .groupby("veiculo", sort=False)
        .first()
        .reset_index()
        .sort_values("data_publicacao_dt")
        .reset_index(drop=True)
    )

    primeiro = primeiro_por_veiculo.iloc[0]
    st.success(
        f"Primeiro a publicar: **{primeiro['veiculo']}** "
        f"— {primeiro['data_publicacao_dt'].strftime('%d/%m/%Y as %H:%M')}"
    )

    total_veiculos = len(primeiro_por_veiculo)
    total_materias = len(grupo)
    if total_materias > total_veiculos:
        st.caption(
            f"{total_materias} materias no total "
            f"({total_materias - total_veiculos} republicacoes)"
        )

    st.divider()
    st.markdown("#### Linha do tempo")

    for i, row in primeiro_por_veiculo.iterrows():
        delta = ""
        if i > 0:
            anterior = primeiro_por_veiculo.iloc[i - 1]["data_publicacao_dt"]
            atual = row["data_publicacao_dt"]
            diff_min = int((atual - anterior).total_seconds() / 60)
            if diff_min < 60:
                delta = f" _(+{diff_min} min)_"
            else:
                delta = f" _(+{diff_min / 60:.1f}h)_"

        hora_fmt = row["data_publicacao_dt"].strftime("%d/%m %H:%M")

        col_hora, col_info = st.columns([1, 4])
        with col_hora:
            if i == 0:
                st.markdown(f"**{hora_fmt}** 🥇")
            else:
                st.markdown(f"{hora_fmt}{delta}")
        with col_info:
            materias_veiculo = (
                grupo[grupo["veiculo"] == row["veiculo"]]
                .sort_values("data_publicacao_dt")
            )
            st.markdown(f"**{row['veiculo']}**")
            for _, mat in materias_veiculo.iterrows():
                hora_mat = mat["data_publicacao_dt"].strftime("%H:%M")
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;↳ [{mat['titulo']}]({mat['url']}) `{hora_mat}`",
                    unsafe_allow_html=True
                )

        if i < len(primeiro_por_veiculo) - 1:
            st.markdown(
                "<hr style='margin:4px 0; border-color:#eee'>",
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ─────────────────────────────────────────────
st.title("Monitor de Pauta")

df_raw = carregar_dados()

# Alerta de coleta
ultima_coleta = df_raw["data_coleta_dt"].max()
if pd.notna(ultima_coleta):
    horas_sem_atualizar = (
        pd.Timestamp.now(tz=BR_TZ) - ultima_coleta
    ).total_seconds() / 3600

    if horas_sem_atualizar > 6:
        st.error(f"Sem atualizacao ha {horas_sem_atualizar:.1f} horas")
    else:
        st.success(
            f"Ultima coleta: "
            f"{ultima_coleta.strftime('%d/%m/%Y as %H:%M')} "
            f"({horas_sem_atualizar:.1f}h atras)"
        )

st.divider()

df_agrupado = agrupar_noticias_semelhantes(df_raw)
df_pautas   = construir_pautas(df_agrupado)

if df_pautas.empty:
    st.warning("Nenhuma pauta encontrada.")
    st.stop()

# Filtros
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])

with col_f1:
    busca = st.text_input("Buscar pauta", placeholder="Palavra-chave...")

with col_f2:
    temas_disponiveis = ["Todos"] + sorted(df_pautas["tema"].unique().tolist())
    tema_sel = st.selectbox("Tema", temas_disponiveis)

with col_f3:
    status_disponiveis = ["Todos"] + sorted(df_pautas["status"].unique().tolist())
    status_sel = st.selectbox("Status", status_disponiveis)

with col_f4:
    modo = st.radio("Visualizacao", ["Cards", "Tabela"], horizontal=True)

df_filtrado = df_pautas.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["titulo"].str.contains(busca, case=False, na=False)
    ]

if tema_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tema"] == tema_sel]

if status_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == status_sel]

# Metricas
m1, m2, m3, m4 = st.columns(4)
m1.metric("Pautas", len(df_filtrado))
m2.metric("🎯 Furos", len(df_filtrado[df_filtrado["status"] == "🎯 Furo"]))
m3.metric("🔥 Quentes", len(df_filtrado[df_filtrado["status"] == "🔥 Quente"]))
m4.metric("Materias totais", int(df_filtrado["total_materias"].sum()))

st.divider()

pautas_ord = df_filtrado.sort_values(
    ["score", "ultima_data"], ascending=[False, False]
).reset_index(drop=True)

if modo == "Tabela":
    tabela = pautas_ord[[
        "titulo", "origem", "primeira_data_fmt", "ultima_data_fmt",
        "total_veiculos", "total_materias", "score", "status", "tema"
    ]].rename(columns={
        "titulo":            "Pauta",
        "origem":            "Quem publicou primeiro",
        "primeira_data_fmt": "Hora da 1a publicacao",
        "ultima_data_fmt":   "Ultima repercussao",
        "total_veiculos":    "Veiculos",
        "total_materias":    "Materias",
        "score":             "Score",
        "status":            "Status",
        "tema":              "Tema",
    })
    st.dataframe(tabela, use_container_width=True, hide_index=True)

else:
    for i in range(0, len(pautas_ord), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j >= len(pautas_ord):
                break
            pauta = pautas_ord.iloc[i + j]
            with cols[j]:
                with st.container(border=True):

                    st.markdown(f"**{pauta['status']}** · {pauta['tema']}")
                    st.markdown(f"#### {pauta['titulo']}")

                    if pauta["status"] == "🎯 Furo":
                        st.info(
                            f"🎯 **Furo de {pauta['origem']}** — "
                            f"{pauta['total_veiculos'] - 1} veiculos seguiram"
                        )
                    else:
                        st.caption(
                            f"Primeiro: **{pauta['origem']}** "
                            f"— {pauta['primeira_data_fmt']}"
                        )

                    st.caption(f"Ultima repercussao: {pauta['ultima_data_fmt']}")

                    st.write(
                        f"📡 {pauta['total_veiculos']} veiculos "
                        f"· 📰 {pauta['total_materias']} materias "
                        f"· ⭐ Score {pauta['score']}"
                    )

                    st.caption(" • ".join(pauta["veiculos"][:6]))

                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button(
                            "Ver origem",
                            pauta["url"],
                            use_container_width=True
                        )
                    with c2:
                        if st.button(
                            "Cobertura",
                            key=f"pauta_{pauta['grupo_id']}",
                            use_container_width=True
                        ):
                            mostrar_cobertura(
                                pauta["titulo"],
                                pauta["grupo"]
                            )
