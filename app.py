import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Monitor de Notícias", page_icon="📰", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Modal flutuante */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    
    .modal-popup {
        background: white;
        border-radius: 12px;
        padding: 30px;
        max-width: 700px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    
    .modal-close {
        float: right;
        font-size: 28px;
        font-weight: bold;
        color: #999;
        cursor: pointer;
        border: none;
        background: none;
    }
    
    .modal-close:hover {
        color: #333;
    }
    
    .modal-title {
        font-size: 1.6em;
        font-weight: 800;
        color: #1A1A1A;
        margin: 20px 0;
        clear: both;
    }
    
    .modal-item {
        padding: 16px;
        background: #f8f9fa;
        border-left: 4px solid #2E7D32;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    
    .modal-item.primeiro {
        background: #FFF3CD;
        border-left: 4px solid #F57C00;
    }
    </style>
""", unsafe_allow_html=True)

if 'modal_aberto' not in st.session_state:
    st.session_state.modal_aberto = None

def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Geral"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado", "flávio", "moraes"]):
        return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad"]):
        return "Economia"
    return "Geral"

def extrair_palavras_chave(titulo, n=5):
    stop_words = {"a", "o", "e", "de", "da", "do", "em", "para", "por", "que", "é", "um", "uma", "os", "as"}
    palavras = titulo.lower().split()
    return [p for p in palavras if p not in stop_words and len(p) > 3][:n]

def calcular_furos(df):
    if df.empty:
        df["furo"] = ""
        return df
    df = df.sort_values(by='data_dt', ascending=True).reset_index(drop=True)
    df["furo"] = ""
    df["grupo_noticia"] = None
    grupos_vistos = {}
    
    for index, row in df.iterrows():
        titulo = str(row['titulo']).lower()
        palavras_atuais = set(extrair_palavras_chave(titulo))
        melhor_grupo = None
        melhor_score = 0
        
        for grupo_id, palavras_grupo in grupos_vistos.items():
            interseccao = len(palavras_atuais & palavras_grupo)
            uniao = len(palavras_atuais | palavras_grupo)
            score = interseccao / uniao if uniao > 0 else 0
            if score > 0.5 and score > melhor_score:
                melhor_score = score
                melhor_grupo = grupo_id
        
        if melhor_grupo is None:
            melhor_grupo = len(grupos_vistos)
            grupos_vistos[melhor_grupo] = palavras_atuais
            df.at[index, 'furo'] = "🥇"
        df.at[index, 'grupo_noticia'] = melhor_grupo
    
    return df.sort_values(by='data_dt', ascending=False)

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_coleta DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    df['data_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    if 'data_coleta' in df.columns:
        df['data_dt'] = df['data_dt'].fillna(pd.to_datetime(df['data_coleta'], errors='coerce', utc=True))
    df['data_dt'] = df['data_dt'].fillna(pd.Timestamp.now(tz='UTC'))
    df['data_dt'] = df['data_dt'].dt.tz_convert('America/Sao_Paulo')
    df['data_formatada'] = df['data_dt'].dt.strftime('%d/%m %H:%M')
    df['hora'] = df['data_dt'].dt.strftime('%H:%M')
    df["tema"] = df["titulo"].apply(classificar_tema)
    df = calcular_furos(df)
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2965/2965879.png", width=50)
        st.title("🔍 Filtros")
        busca = st.text_input("🔎 Buscar...", placeholder="Ex: Lula")
        veiculos_disponiveis = sorted(df['veiculo'].dropna().unique().tolist())
        veiculos_selecionados = st.multiselect("📰 Veículos", veiculos_disponiveis, default=veiculos_disponiveis[:5])
        temas_selecionados = st.multiselect("🏷️ Temas", sorted(df['tema'].unique()), default=sorted(df['tema'].unique()))
        st.divider()
        st.metric("Total", len(df))
    
    df_filtrado = df.copy()
    if busca:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busca, case=False, na=False)]
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]
    
    st.title("📰 Monitor de Notícias")
    col1, col2, col3 = st.columns(3)
    col1.metric("Notícias", len(df_filtrado))
    col2.metric("Veículos", df_filtrado['veiculo'].nunique())
    col3.metric("Temas", df_filtrado['tema'].nunique())
    st.divider()
    
    st.markdown("### 📌 Notícias")
    
    df_filtrado_reset = df_filtrado.reset_index(drop=True)
    
  for i in range(0, len(df_filtrado_reset), 3):

    cols = st.columns(3)

    for j in range(3):

        if i + j < len(df_filtrado_reset):

            row = df_filtrado_reset.iloc[i + j]
            card_id = i + j

            grupo = row["grupo_noticia"]
            noticias_grupo = df[df["grupo_noticia"] == grupo]

            tem_similares = len(noticias_grupo) > 1
            badge = "🥇 " if row["furo"] == "🥇" else ""

            with cols[j]:

                st.markdown(
                    f"""
                    <div style="
                        background:white;
                        border-left:4px solid #2E7D32;
                        border-radius:8px;
                        padding:16px;
                        margin-bottom:16px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.1);
                        min-height:180px;
                    ">
                        <div style="
                            font-weight:700;
                            font-size:0.95em;
                            line-height:1.35;
                            color:#1A1A1A;
                            margin-bottom:12px;
                        ">
                            {badge}{row['titulo'][:80]}
                        </div>

                        <div style="
                            font-size:0.85em;
                            color:#666;
                            margin-bottom:12px;
                        ">
                            <div style="
                                color:#2E7D32;
                                font-weight:700;
                            ">
                                {row['veiculo']}
                            </div>

                            <div>
                                📅 {row['data_formatada']}
                            </div>

                            <div>
                                ✍️ {row['autor']}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2 = st.columns(2)

                with c1:

                    st.link_button(
                        "🔗 Abrir",
                        row["url"],
                        use_container_width=True
                    )

                with c2:

                    if tem_similares:

                        if st.button(
                            f"📚 Similares ({len(noticias_grupo)})",
                            key=f"btn_{card_id}",
                            use_container_width=True
                        ):

                            st.session_state.modal_aberto = card_id
                            st.rerun()
    
   # POPUP NATIVO STREAMLIT
if st.session_state.modal_aberto is not None:

    try:

        noticia_selecionada = df_filtrado_reset.iloc[
            st.session_state.modal_aberto
        ]

        grupo = noticia_selecionada["grupo_noticia"]

        noticias_grupo = (
            df[df["grupo_noticia"] == grupo]
            .sort_values("data_dt")
        )

        @st.dialog("📰 Veículos que publicaram esta pauta")
        def mostrar_dialog():

            st.markdown(
                f"### {noticia_selecionada['titulo']}"
            )

            st.caption(
                f"{len(noticias_grupo)} veículos publicaram sobre este tema"
            )

            st.divider()

            for _, noticia in noticias_grupo.iterrows():

                if noticia["furo"] == "🥇":

                    st.success(
                        f"🥇 {noticia['veiculo']} — PRIMEIRO A PUBLICAR"
                    )

                else:

                    st.info(
                        noticia["veiculo"]
                    )

                st.write(
                    noticia["titulo"]
                )

                st.caption(
                    f"📅 {noticia['data_formatada']} | ✍️ {noticia['autor']}"
                )

                st.link_button(
                    "🔗 Abrir notícia",
                    noticia["url"]
                )

                st.divider()

            if st.button(
                "Fechar",
                use_container_width=True
            ):
                st.session_state.modal_aberto = None
                st.rerun()

        mostrar_dialog()

    except Exception as e:

        st.error(f"Erro: {e}")
        st.session_state.modal_aberto = None
