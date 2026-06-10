import streamlit as st
import pandas as pd
import psycopg2
import anthropic
from dateutil import parser as dateparser
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Monitor de Pauta",
    page_icon="📡",
    layout="wide"
)

BR_TZ = ZoneInfo("America/Sao_Paulo")

# ─────────────────────────────────────────────
# PARSING DE DATA
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# CLASSIFICACAO DE TEMA
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# PALAVRAS-CHAVE
# ─────────────────────────────────────────────
def extrair_palavras_chave(titulo, n=7):
    stop_words = {
        "a", "o", "e", "de", "da", "do", "em", "para", "por",
        "que", "um", "uma", "os", "as", "com", "mais",
        "nao", "sobre", "apos", "contra", "no", "na", "ao", "dos",
        "das", "pelo", "pela", "entre", "seus", "sua", "isso", "este",
        "não", "após"
    }
    for char in [".", ",", "!", "?", "(", ")", "-", ":", "'"]:
        titulo = titulo.replace(char, " ")
    palavras = titulo.lower().split()
    return [p for p in palavras if p not in stop_words and len(p) > 3][:n]


# ─────────────────────────────────────────────
# AGRUPAMENTO DE NOTICIAS
# ─────────────────────────────────────────────
def agrupar_noticias_semelhantes(df, janela_horas=36):
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
            if diferenca_horas > janela_horas:
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
            grupos[melhor]["data"] = data_atual

        df.at[idx, "grupo_noticia"] = melhor

    return df.sort_values("data_publicacao_dt", ascending=False)


# ─────────────────────────────────────────────
# CONSTRUCAO DE PAUTAS
# ─────────────────────────────────────────────
def construir_pautas(df, horas_quente=12, horas_esfriando=24):
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
            total_veiculos * 8
            + total_materias * 2
            + max(0, 36 - idade_horas)
        )

        if total_veiculos == 1 and idade_horas <= 6:
            status = "🎯 Exclusiva"
        elif total_veiculos >= 4 and idade_horas <= 12:
            status = "🔥 Viralizando"
        elif total_veiculos >= 2:
            status = "📈 Repercutindo"
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


# ─────────────────────────────────────────────
# CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────
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
# RESUMO AUTOMATICO VIA CLAUDE
# So funciona se ANTHROPIC_API_KEY estiver em secrets.toml
# ─────────────────────────────────────────────
def gerar_resumo(titulo_principal, titulos_cobertura):
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)

        titulos_fmt = "\n".join(f"- {t}" for t in titulos_cobertura[:10])
        prompt = (
            f"Voce e um editor de jornalismo. Com base nos titulos abaixo de uma mesma pauta, "
            f"escreva um resumo jornalistico objetivo em 2-3 frases explicando o que aconteceu. "
            f"Sem especulacao, apenas o que os titulos indicam.\n\n"
            f"Titulos:\n{titulos_fmt}\n\n"
            f"Resumo:"
        )

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()

    except Exception:
        return None


# ─────────────────────────────────────────────
# MODAL — LINHA DO TEMPO DA COBERTURA
# ─────────────────────────────────────────────
@st.dialog("Cobertura da pauta", width="large")
def mostrar_cobertura(titulo, grupo):
    st.markdown(f"### {titulo}")

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

    # Resumo automatico
    tem_api = bool(st.secrets.get("ANTHROPIC_API_KEY", None))
    if tem_api:
        if st.button("Gerar resumo automatico", key=f"resumo_{titulo[:20]}"):
            with st.spinner("Gerando resumo..."):
                titulos = grupo["titulo"].tolist()
                resumo = gerar_resumo(titulo, titulos)
                if resumo:
                    st.info(resumo)
                else:
                    st.warning("Nao foi possivel gerar o resumo.")
    else:
        st.caption(
            "Resumo automatico disponivel apos configurar ANTHROPIC_API_KEY no secrets.toml"
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

# Estado para pautas ignoradas
if "pautas_ignoradas" not in st.session_state:
    st.session_state.pautas_ignoradas = set()

df_raw = carregar_dados()

# Alerta de coleta
ultima_coleta = df_raw["data_coleta_dt"].max()
if pd.notna(ultima_coleta):
    horas_sem_atualizar = (
        pd.Timestamp.now(tz=BR_TZ) - ultima_coleta
    ).total_seconds() / 3600

    if horas_sem_atualizar > 2:
        st.error(f"Sem atualizacao ha {horas_sem_atualizar:.1f} horas")
    else:
        st.success(
            f"Ultima coleta: "
            f"{ultima_coleta.strftime('%d/%m/%Y as %H:%M')} "
            f"({horas_sem_atualizar:.1f}h atras)"
        )

st.divider()

# ── FILTROS E CONFIGURACOES ──────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])

with col_f1:
    busca = st.text_input("Buscar pauta", placeholder="Palavra-chave...")

with col_f2:
    modo = st.radio("Visualizacao", ["Cards", "Tabela"], horizontal=True)

with col_f3:
    janela_horas = st.slider(
        "Janela de agrupamento (h)",
        min_value=6, max_value=72, value=36, step=6,
        help="Maximo de horas entre publicacoes para considerar a mesma pauta"
    )

with col_f4:
    horas_quente = st.slider(
        "Quente se ultima repercussao em (h)",
        min_value=1, max_value=24, value=12, step=1,
    )

col_s1, col_s2, col_s3, col_s4 = st.columns([1, 1, 1, 1])

with col_s1:
    horas_esfriando = st.slider(
        "Esfriando apos (h)",
        min_value=12, max_value=168, value=24, step=6,
    )

with col_s2:
    mostrar_ignoradas = st.toggle("Mostrar pautas ignoradas", value=False)

with col_s3:
    if st.session_state.pautas_ignoradas and st.button("Restaurar todas ignoradas"):
        st.session_state.pautas_ignoradas = set()
        st.rerun()

df_agrupado = agrupar_noticias_semelhantes(df_raw, janela_horas=janela_horas)
df_pautas = construir_pautas(df_agrupado, horas_quente=horas_quente, horas_esfriando=horas_esfriando)

if df_pautas.empty:
    st.warning("Nenhuma pauta encontrada.")
    st.stop()

# Banner de furos novos — pautas com furo que ainda nao foram ignoradas
furos = df_pautas[
    (df_pautas["status"] == "🎯 Furo") &
    (~df_pautas["grupo_id"].isin(st.session_state.pautas_ignoradas))
]
if not furos.empty:
    nomes = ", ".join(furos["origem"].tolist()[:5])
    st.warning(
        f"🎯 **{len(furos)} furo(s) detectado(s):** {nomes} "
        f"{'e outros' if len(furos) > 5 else ''}"
    )

with col_s3:
    temas_disponiveis = ["Todos"] + sorted(df_pautas["tema"].unique().tolist())
    tema_sel = st.selectbox("Tema", temas_disponiveis)

with col_s4:
    status_disponiveis = ["Todos"] + sorted(df_pautas["status"].unique().tolist())
    status_sel = st.selectbox("Status", status_disponiveis)

col_s5, col_s6 = st.columns(2)

with col_s5:
    ordenar_por = st.selectbox(
        "Ordenar por",
        [
            "Score",
            "Última repercussão",
            "Primeira publicação",
            "Quantidade de veículos",
            "Quantidade de matérias"
        ]
    )

with col_s6:
    ordem = st.radio(
        "Ordem",
        ["Decrescente", "Crescente"],
        horizontal=True
    )

# Aplica filtros
df_filtrado = df_pautas.copy()

if not mostrar_ignoradas:
    df_filtrado = df_filtrado[
        ~df_filtrado["grupo_id"].isin(st.session_state.pautas_ignoradas)
    ]

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

ascending = ordem == "Crescente"

if ordenar_por == "Score":
    pautas_ord = df_filtrado.sort_values(
        "score",
        ascending=ascending
    )

elif ordenar_por == "Última repercussão":
    pautas_ord = df_filtrado.sort_values(
        "ultima_data",
        ascending=ascending
    )

elif ordenar_por == "Primeira publicação":
    pautas_ord = df_filtrado.sort_values(
        "primeira_data",
        ascending=ascending
    )

elif ordenar_por == "Quantidade de veículos":
    pautas_ord = df_filtrado.sort_values(
        "total_veiculos",
        ascending=ascending
    )

elif ordenar_por == "Quantidade de matérias":
    pautas_ord = df_filtrado.sort_values(
        "total_materias",
        ascending=ascending
    )

pautas_ord = pautas_ord.reset_index(drop=True)

# ── VISUALIZACAO ─────────────────────────────
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
            ignorada = pauta["grupo_id"] in st.session_state.pautas_ignoradas

            with cols[j]:
                with st.container(border=True):

                    if ignorada:
                        st.markdown(f"~~{pauta['titulo']}~~ _(ignorada)_")
                        if st.button(
                            "Restaurar",
                            key=f"restaurar_{pauta['grupo_id']}",
                            use_container_width=True
                        ):
                            st.session_state.pautas_ignoradas.discard(pauta["grupo_id"])
                            st.rerun()
                        continue

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

                    c1, c2, c3 = st.columns(3)
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
                    with c3:
                        if st.button(
                            "Ignorar",
                            key=f"ignorar_{pauta['grupo_id']}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            st.session_state.pautas_ignoradas.add(pauta["grupo_id"])
                            st.rerun()
