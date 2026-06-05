import streamlit as st
import pandas as pd
import psycopg2

# ==========================================
# 0. CONFIG DA PÁGINA & CSS
# ==========================================
st.set_page_config(page_title="Monitor de Notícias", page_icon="📰", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. FUNÇÕES DE LÓGICA & FURO
# ==========================================
def classificar_tema(titulo):
    if not isinstance(titulo, str): return "Outros"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado"]): return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad", "imposto"]): return "Economia"
    return "Geral"

def calcular_furos_reais(df):
    if df.empty:
        df["furo"] = ""
        return df
    
    df["furo"] = ""
    # Ordena do mais antigo para o mais novo para achar o primeiro a publicar
    df = df.sort_values(by='data_publicacao', ascending=True)
    
    temas_vistos = set()
    for index, row in df.iterrows():
        # Se for o primeiro a falar sobre aquele tema (e não for "Outros"), ganha a medalha
        if row['tema'] not in temas_vistos and row['tema'] != "Outros":
            df.at[index, 'furo'] = "🥇 Primeiro"
            temas_vistos.add(row['tema'])
            
    # Volta para a ordem normal (mais recentes no topo)
    return df.sort_values(by='data_publicacao', ascending=False)

# ==========================================
# 2. CONEXÃO COM O BANCO
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql("SELECT * FROM noticias", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return pd.DataFrame()

df = carregar_dados()

# ==========================================
# 3. PROCESSAMENTO DA BASE
# ==========================================
if not df.empty:
    df["tema"] = df["titulo"].apply(classificar_tema)
    df = calcular_furos_reais(df)

    # ==========================================
    # 4. BARRA LATERAL (FILTROS COMPLETOS)
    # ==========================================
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2965/2965879.png", width=50)
    st.sidebar.title("🔍 Filtros de Busca")
    
    busca = st.sidebar.text_input("Buscar palavra-chave no título...")
    
    veiculos_selecionados = st.sidebar.multiselect("📰 Veículos", df['veiculo'].dropna().unique().tolist())
    temas_selecionados = st.sidebar.multiselect("🏷️ Temas", df['tema'].dropna().unique().tolist())
    furos_selecionados = st.sidebar.multiselect("🏆 Status (Furo)", ["🥇 Primeiro", ""])

    # Aplicação dos Filtros
    df_filtrado = df.copy()
    if busca:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busca, case=False, na=False)]
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]
    if furos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['furo'].isin(furos_selecionados)]

    # ==========================================
    # 5. TELA PRINCIPAL (HEADER E CARDS)
    # ==========================================
    st.title("📰 Painel de Monitoramento de Notícias")
    st.markdown("Acompanhamento em tempo real de publicações e furos jornalísticos.")
    st.markdown("---")

    # Cards de Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("📌 Total de Notícias", len(df_filtrado))
    
    furos_count = len(df_filtrado[df_filtrado['furo'] == '🥇 Primeiro'])
    col2.metric("🏆 Furos Identificados", furos_count)
    
    veiculos_count = df_filtrado['veiculo'].nunique()
    col3.metric("🏢 Veículos Monitorados", veiculos_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 6. TABELA COM LINKS CLICÁVEIS
    # ==========================================
    st.dataframe(
        df_filtrado[["veiculo", "data_publicacao", "titulo", "tema", "furo", "url"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "veiculo": st.column_config.TextColumn("Veículo", width="medium"),
            "data_publicacao": st.column_config.TextColumn("Data de Publicação", width="medium"),
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "tema": st.column_config.TextColumn("Tema", width="small"),
            "furo": st.column_config.TextColumn("Furo", width="small"),
            "url": st.column_config.LinkColumn("Link", display_text="Abrir Notícia 🔗", width="small")
        }
    )
else:
    st.warning("O banco de dados está vazio ou não retornou nada.")
