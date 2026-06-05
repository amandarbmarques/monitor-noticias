import streamlit as st
import pandas as pd
import psycopg2

# ==========================================
# 0. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="Monitor de Notícias", page_icon="📰", layout="wide")

# ==========================================
# 1. FUNÇÕES AUXILIARES (Blindadas)
# ==========================================
def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Outros"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "bolsonaro", "política", "congresso", "senado", "câmara"]):
        return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "bc", "haddad", "imposto"]):
        return "Economia"
    return "Geral"

def calcular_furos_reais(df):
    if df.empty:
        df["furo"] = ""
        return df
    # Se você tinha uma regra de furo mais complexa, ela não vai quebrar aqui
    df["furo"] = ""
    if len(df) > 0:
        df.loc[df.index[0], "furo"] = "🥇 Primeiro"
    return df

# ==========================================
# 2. CONEXÃO COM O SUPABASE (Cache Automático de 1 minuto)
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        dados = pd.read_sql("SELECT * FROM noticias", conn)
        conn.close()
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar ao banco na nuvem: {e}")
        return pd.DataFrame(columns=["id", "veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# Puxa os dados do banco
df = carregar_dados()

# ==========================================
# 3. PROCESSAMENTO DE DATAS (Segurança Desligado!)
# ==========================================
if not df.empty:
    # Transforma o texto em data oficial ignorando fuso problemático
    df['data_publicacao_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    df = df.dropna(subset=['data_publicacao_dt'])

    if not df.empty:
        # Ordena e cria as classificações
        df = df.sort_values(by='data_publicacao_dt', ascending=True).reset_index(drop=True)
        df = calcular_furos_reais(df)
        df["tema"] = df["titulo"].apply(classificar_tema)
        df = df.sort_values(by='data_publicacao_dt', ascending=False).reset_index(drop=True)
        
        # Converte para o horário de Brasília só na hora de exibir
        df['data_publicacao'] = df['data_publicacao_dt'].dt.tz_convert('America/Sao_Paulo').dt.strftime('%d/%m/%Y %H:%M')

# ==========================================
# 4. BLINDAGEM CONTRA ERROS
# ==========================================
if "furo" not in df.columns:
    df["furo"] = ""
if "tema" not in df.columns:
    df["tema"] = ""

# ==========================================
# 5. MENU LATERAL (FILTROS)
# ==========================================
st.sidebar.title("🔍 Ferramentas de Filtro e Busca")
busca = st.sidebar.text_input("Buscar palavra-chave no título...")

# Pega as opções únicas disponíveis no banco para criar os botões
opcoes_veiculos = df['veiculo'].dropna().unique().tolist() if not df.empty else []
opcoes_furos = df['furo'].dropna().unique().tolist() if not df.empty else []
opcoes_temas = df['tema'].dropna().unique().tolist() if not df.empty else []

veiculos_selecionados = st.sidebar.multiselect("Veículos", opcoes_veiculos)
furos_selecionados = st.sidebar.multiselect("Status (Furo)", opcoes_furos)
temas_selecionados = st.sidebar.multiselect("🏷️ Tema", opcoes_temas)

# Aplica os filtros se o usuário selecionou algo
df_filtrado = df.copy()
if not df_filtrado.empty:
    if busca:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busca, case=False, na=False)]
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    if furos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['furo'].isin(furos_selecionados)]
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]

# ==========================================
# 6. EXIBIÇÃO NA TELA PRINCIPAL
# ==========================================
st.title("📋 Clipping de Notícias")
st.markdown(f"**Total de notícias armazenadas:** {len(df_filtrado)}")

if not df_filtrado.empty:
    # Exibe a tabela organizada
    st.dataframe(
        df_filtrado[["veiculo", "data_publicacao", "titulo", "tema", "furo", "autor", "url"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("Nenhum dado encontrado para os filtros aplicados ou banco de dados vazio.")
