import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(
    page_title="Monitor de Notícias",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.modal-title { font-size: 1.6em; font-weight: 800; color: #1A1A1A; margin: 20px 0; }
.modal-item { padding: 16px; background: #f8f9fa; border-left: 4px solid #2E7D32; border-radius: 6px; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)

if "modal_aberto" not in st.session_state:
    st.session_state.modal_aberto = None


def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Geral"

    t = titulo.lower()

    if any(x in t for x in [
        "lula","governo","stf","política","congresso","senado",
        "flávio","moraes","pl","pt","eleições","pgr","tse",
        "liminar","julgamento","ministro","voto"
    ]):
        return "Política/Judiciário"

    if any(x in t for x in [
        "economia","dólar","mercado","juros","haddad",
        "banco central","inflação","pib","ações",
        "vendas","faturamento","receita"
    ]):
        return "Economia"

    return "Geral"


def extrair_palavras_chave(titulo, n=7):
    stop_words = {
        "a","o","e","de","da","do","em","para","por","que","é",
        "um","uma","os","as","com","ao","aos","nas","nos",
        "mais","não","pelo","pela","se","diz","vê","após",
        "contra","pode","sobre","nesta","neste","veja",
        "ser","tem","vai","comentou"
    }

    for char in [".", ",", '"', "'", "!", "?", "(", ")", "-", ":", "—"]:
        titulo = titulo.replace(char, " ")

    palavras = titulo.lower().split()
    return [p for p in palavras if p not in stop_words and len(p) > 3][:n]


def agrupar_noticias_semelhantes(df):
    if df.empty:
        return df

    df = df.sort_values(by="data_dt", ascending=True).reset_index(drop=True)
    df["grupo_noticia"] = None

    grupos_vistos = {}

    for index, row in df.iterrows():
        palavras_atuais = set(extrair_palavras_chave(str(row["titulo"])))
        data_atual = row["data_dt"]

        if not palavras_atuais:
            continue

        melhor_grupo = None
        melhor_score = 0

        for grupo_id, dados_grupo in grupos_vistos.items():
            diferenca_horas = abs(
                (data_atual - dados_grupo["ultima_data"]).total_seconds()
            ) / 3600

            if diferenca_horas > 24:
                continue

            interseccao = len(palavras_atuais & dados_grupo["palavras"])
            menor = min(len(palavras_atuais), len(dados_grupo["palavras"]))

            score = interseccao / menor if menor else 0

            if score >= 0.55 and score > melhor_score:
                melhor_score = score
                melhor_grupo = grupo_id

        if melhor_grupo is None:
            melhor_grupo = len(grupos_vistos)
            grupos_vistos[melhor_grupo] = {
                "palavras": palavras_atuais,
                "ultima_data": data_atual
            }
        else:
            grupos_vistos[melhor_grupo]["palavras"].update(palavras_atuais)

        df.at[index, "grupo_noticia"] = melhor_grupo

    return df.sort_values(by="data_dt", ascending=False)


@st.cache_data(ttl=30)
def carregar_dados():
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql(
            "SELECT * FROM noticias ORDER BY data_coleta DESC",
            conn
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
        return pd.DataFrame()


@st.dialog("📰 Repercussão da pauta")
def mostrar_dialog(noticia_selecionada, noticias_grupo):

    noticias_grupo = noticias_grupo.sort_values("data_dt")

    st.markdown(f"### {noticia_selecionada['titulo']}")
    st.caption(
        f"{len(noticias_grupo)} veículos publicaram sobre este tema"
    )

    st.divider()

    primeira = noticias_grupo.iloc[0]

    st.success(
        f"⏰ Primeira publicação registrada: "
        f"{primeira['veiculo']} ({primeira['data_formatada']})"
    )

    st.divider()

    for posicao, (_, noticia) in enumerate(
        noticias_grupo.iterrows(),
        start=1
    ):
        st.markdown(
            f"""
**{posicao}. {noticia['veiculo']}**

📅 {noticia['data_formatada']}

{noticia['titulo']}
"""
        )

        st.link_button("🔗 Abrir notícia", noticia["url"])
        st.divider()

    if st.button("Fechar", use_container_width=True):
        st.session_state.modal_aberto = None
        st.rerun()


df = carregar_dados()

if not df.empty:

    df["veiculo"] = (
        df["veiculo"]
        .fillna("Desconhecido")
        .astype(str)
        .str.strip()
    )

    df["data_dt"] = pd.to_datetime(
        df["data_publicacao"],
        errors="coerce",
        format="mixed",
        utc=True
    )

    if "data_coleta" in df.columns:
        df["data_dt"] = df["data_dt"].fillna(
            pd.to_datetime(
                df["data_coleta"],
                errors="coerce",
                format="mixed",
                utc=True
            )
        )

    df["data_dt"] = df["data_dt"].fillna(
        pd.Timestamp.now(tz="UTC")
    )

    df["data_dt"] = df["data_dt"].dt.tz_convert(
        "America/Sao_Paulo"
    )

    df["data_formatada"] = df["data_dt"].dt.strftime("%d/%m %H:%M")

    df["tema"] = df["titulo"].apply(classificar_tema)

    df = agrupar_noticias_semelhantes(df)

    st.title("📰 Monitor de Notícias")

    with st.container(border=True):

        c1, c2, c3 = st.columns([3, 2, 2])

        with c1:
            busca = st.text_input(
                "",
                placeholder="🔎 Buscar termo...",
                label_visibility="collapsed"
            )

        with c2:
            veiculos_disponiveis = sorted(
                df["veiculo"].unique().tolist()
            )

            veiculos_selecionados = st.multiselect(
                "",
                veiculos_disponiveis,
                default=veiculos_disponiveis,
                placeholder="📰 Veículos",
                label_visibility="collapsed"
            )

        with c3:
            temas_disponiveis = sorted(
                df["tema"].unique().tolist()
            )

            temas_selecionados = st.multiselect(
                "",
                temas_disponiveis,
                default=temas_disponiveis,
                placeholder="🏷️ Temas",
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

    if veiculos_selecionados:
        df_filtrado = df_filtrado[
            df_filtrado["veiculo"].isin(
                veiculos_selecionados
            )
        ]

    if temas_selecionados:
        df_filtrado = df_filtrado[
            df_filtrado["tema"].isin(
                temas_selecionados
            )
        ]

    grupos = (
        df_filtrado.groupby("grupo_noticia")
        .size()
        .reset_index(name="total")
    )

    repercutidas = len(grupos[grupos["total"] > 1])
    isoladas = len(grupos[grupos["total"] == 1])

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("📰 Notícias", len(df_filtrado))
    m2.metric("📚 Pautas repercutidas", repercutidas)
    m3.metric("📄 Pautas isoladas", isoladas)
    m4.metric("🏢 Veículos", df_filtrado["veiculo"].nunique())

    st.divider()

    df_filtrado["total_similares"] = (
        df_filtrado.groupby("grupo_noticia")
        ["grupo_noticia"]
        .transform("count")
    )

    df_filtrado = df_filtrado.sort_values(
        ["total_similares", "data_dt"],
        ascending=[False, False]
    )

    st.markdown(
        f"### 📌 Notícias ({len(df_filtrado)} encontradas)"
    )

    df_filtrado_reset = df_filtrado.reset_index(drop=True)

    for i in range(0, len(df_filtrado_reset), 3):

        cols = st.columns(3)

        for j in range(3):

            if i + j >= len(df_filtrado_reset):
                continue

            row = df_filtrado_reset.iloc[i + j]
            card_id = i + j

            grupo = row["grupo_noticia"]
            noticias_grupo = df[df["grupo_noticia"] == grupo]

            tem_similares = len(noticias_grupo) > 1

            if tem_similares:
                status = (
                    f"🟠 Repercutida por "
                    f"{len(noticias_grupo)} veículos"
                )
            else:
                status = "🟢 Sem repercussão encontrada"

            with cols[j]:
                with st.container(border=True):

                    st.markdown(
                        f"""
<div style="margin-bottom:12px;">
<div style="font-weight:700;font-size:1.02em;line-height:1.45;color:#1A1A1A;margin-bottom:8px;">
{row['titulo']}
</div>

<div style="font-size:0.85em;color:#666;">
<div style="color:#2E7D32;font-weight:700;margin-bottom:4px;">
{row['veiculo']}
</div>

<div style="margin-top:6px;margin-bottom:8px;font-size:0.82em;font-weight:700;color:#C77700;">
{status}
</div>

<div style="margin-bottom:2px;">
📅 {row['data_formatada']}
</div>

<div>
✍️ {row.get('autor', 'Desconhecido')}
</div>
</div>
</div>
""",
                        unsafe_allow_html=True
                    )

                    b1, b2 = st.columns(2)

                    with b1:
                        st.link_button(
                            "🔗 Abrir",
                            row["url"],
                            use_container_width=True
                        )

                    with b2:
                        if tem_similares:
                            if st.button(
                                "📚 Ver repercussão",
                                key=f"btn_{card_id}",
                                use_container_width=True
                            ):
                                st.session_state.modal_aberto = card_id
                                st.rerun()
                        else:
                            st.button(
                                "Sem repercussão",
                                disabled=True,
                                key=f"btn_{card_id}",
                                use_container_width=True
                            )

    if st.session_state.modal_aberto is not None:
        try:
            noticia_selecionada = df_filtrado_reset.iloc[
                st.session_state.modal_aberto
            ]

            grupo = noticia_selecionada["grupo_noticia"]

            noticias_grupo = df[
                df["grupo_noticia"] == grupo
            ].sort_values("data_dt")

            mostrar_dialog(
                noticia_selecionada,
                noticias_grupo
            )

        except Exception as e:
            st.error(f"Erro ao abrir o detalhamento: {e}")
            st.session_state.modal_aberto = None

else:
    st.warning(
        "Nenhum dado disponível. Verifique o banco de dados."
    )
