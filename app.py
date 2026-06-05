import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Monitor de Notícias", page_icon="📰", layout="wide")

def classificar_tema(titulo):
    if not isinstance(titulo, str): return "Outros"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado"]): return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad"]): return "Economia"
    return "Geral"

# ==========================================
# 1. CONEXÃO DIRETA COM O BANCO
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
        st.error(f"Erro ao conectar ao banco na nuvem: {e}")
        return pd.DataFrame()

df = carregar_dados()

# ==========================================
# 2. PROCESSAMENTO SEM CORTES (O QUE ESTAVA ANTES)
# ==========================================
if not df.empty:
    # Apenas garantindo que não dê erro de coluna faltando (a blindagem que funcionou)
    if "furo" not in df.columns:
        df["furo"] = ""
        
    df["tema"] = df["titulo"].apply(classificar_tema)
    
    # Ordena de forma simples pela data de publicação (sem frescura de fuso)
    df = df.sort_values(by='data_publicacao', ascending=False).reset_index(drop=True)

    # ==========================================
    # 3. FILTROS LATERAIS
    # ==========================================
    st.sidebar.title("🔍 Filtros")
    veiculos_selecionados = st.sidebar.multiselect("Veículos", df['veiculo'].dropna().unique().tolist())
    temas_selecionados = st.sidebar.multiselect("Temas", df['tema'].dropna().unique().tolist())
    
    df_filtrado = df.copy()
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]

    # ==========================================
    # 4. TELA PRINCIPAL
    # ==========================================
    st.title("📋 Clipping de Notícias")
    st.markdown(f"**Total de notícias armazenadas no banco:** {len(df_filtrado)}")

    st.dataframe(
        df_filtrado[["veiculo", "data_publicacao", "titulo", "tema", "furo", "url"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("O banco de dados está vazio ou não retornou nada.")
