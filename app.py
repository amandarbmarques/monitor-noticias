import streamlit as st
import pandas as pd
import psycopg2

# 1. Configuração da Página
st.set_page_config(page_title="Monitor de Notícias", page_icon="📰", layout="wide", initial_sidebar_state="expanded")

# 2. CSS Customizado para o Modal/Dialog
st.markdown("""
    <style>
    .modal-title { font-size: 1.6em; font-weight: 800; color: #1A1A1A; margin: 20px 0; }
    .modal-item { padding: 16px; background: #f8f9fa; border-left: 4px solid #2E7D32; border-radius: 6px; margin-bottom: 16px; }
    </style>
""", unsafe_allow_html=True)

if 'modal_aberto' not in st.session_state:
    st.session_state.modal_aberto = None

# 3. Funções Auxiliares e Algoritmo de Similaridade
def classificar_tema(titulo):
    if not isinstance(titulo, str):
        return "Geral"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado", "flávio", "moraes", "pl", "pt", "eleições", "stf"]):
        return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad", "banco central", "inflação", "pib", "ações", "vendas", "faturamento"]):
        return "Economia"
    return "Geral"

def extrair_palavras_chave(titulo, n=7):
    stop_words = {
        "a", "o", "e", "de", "da", "do", "em", "para", "por", "que", "é", "um", "uma", "os", "as",
        "com", "ao", "aos", "nas", "nos", "uma", "mais", "não", "pelo", "pela", "se", "diz", "vê",
        "após", "contra", "pode", "sobre", "nesta", "neste", "veja", "ser", "tem", "vai", "comentou"
    }
    for char in [".", ",", '"', "'", "!", "?", "(", ")", "-", ":", "—"]:
        titulo = titulo.replace(char, " ")
        
    palavras = titulo.lower().split()
    return [p for p in palavras if p not in stop_words and len(p) > 3][:n]

def calcular_furos_refinado(df):
    if df.empty:
        df["furo"] = ""
        return df
        
    df = df.sort_values(by='data_dt', ascending=True).reset_index(drop=True)
    df["furo"] = ""
    df["grupo_noticia"] = None
    
    grupos_vistos = {}
    
    for index, row in df.iterrows():
        titulo = str(row['titulo'])
        palavras_atuais = set(extrair_palavras_chave(titulo))
        data_atual = row['data_dt']
        
        if not palavras_atuais:
            continue
            
        melhor_grupo = None
        melhor_score = 0
        
        for grupo_id, dados_grupo in grupos_vistos.items():
            palavras_grupo = dados_grupo["palavras"]
            data_grupo = dados_grupo["ultima_data"]
            
            diferenca_horas = abs((data_atual - data_grupo).total_seconds()) / 3600
            if diferenca_horas > 24:
                continue
            
            interseccao = len(palavras_atuais & palavras_grupo)
            menor_tamanho = min(len(palavras_atuais), len(palavras_grupo))
            score = interseccao / menor_tamanho if menor_tamanho > 0 else 0
            
            if score >= 0.55 and score > melhor_score:
                melhor_score = score
                melhor_grupo = grupo_id
        
        if melhor_grupo is None:
            melhor_grupo = len(grupos_vistos)
            grupos_vistos[melhor_grupo] = {
                "palavras": palavras_atuais,
                "ultima_data": data_atual
            }
            df.at[index, 'furo'] = "🥇"
        else:
            grupos_vistos[melhor_grupo]["palavras"].update(palavras_atuais)
            
        df.at[index, 'grupo_noticia'] = melhor_grupo
    
    return df.sort_values(by='data_dt', ascending=False)

# 4. Carregamento de Dados
@st.cache_data(ttl=30)
def carregar_dados():
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_coleta DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
        return pd.DataFrame()

# 5. Definição do Modal (Diálogo)
@st.dialog("📰 Veículos que publicaram esta pauta")
def mostrar_dialog(noticia_selecionada, noticias_grupo):
    st.markdown(f"### {noticia_selecionada['titulo']}")
    st.caption(f"{len(noticias_grupo)} veículos publicaram sobre este tema")
    st.divider()

    for _, noticia in noticias_grupo.iterrows():
        if noticia["furo"] == "🥇":
            st.success(f"🥇 {noticia['veiculo']} — PRIMEIRO A PUBLICAR")
        else:
            st.info(noticia["veiculo"])

        st.write(noticia["titulo"])
        st.caption(f"📅 {noticia['data_formatada']} | ✍️ {noticia.get('autor', 'Desconhecido')}")
        st.link_button("🔗 Abrir notícia", noticia["url"])
        st.divider()

    if st.button("Fechar", use_container_width=True):
        st.session_state.modal_aberto = None
        st.rerun()

# --- Fluxo de Execução Principal ---
df = carregar_dados()

if not df.empty:
    # Tratamento e conversão de datas
    df['data_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', format='mixed', utc=True)
    if 'data_coleta' in df.columns:
        df['data_dt'] = df['data_dt'].fillna(pd.to_datetime(df['data_coleta'], errors='coerce', format='mixed', utc=True))
        
    df['data_dt'] = df['data_dt'].fillna(pd.Timestamp.now(tz='UTC'))
    df['data_dt'] = df['data_dt'].dt.tz_convert('America/Sao_Paulo')
    
    df['data_formatada'] = df['data_dt'].dt.strftime('%d/%m %H:%M')
    df['hora'] = df['data_dt'].dt.strftime('%H:%M')
    
    df["tema"] = df["titulo"].apply(classificar_tema)
    df = calcular_furos_refinado(df)
    
   # --- NOVO CABEÇALHO INTEGRADO COM FILTROS (CORRIGIDO) ---
    st.markdown("""
        <h2 style="margin-bottom: 0px; font-weight: 800; color: #1A1A1A;">📰 Sala de Situação — Clipping Automatizado</h2>
        <p style="color: #666; margin-bottom: 15px;">Ajuste os parâmetros abaixo para refinar a análise de pautas em tempo real.</p>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        f_col1, f_col2, f_col3 = st.columns([2, 3, 3])
        
        with f_col1:
            busca = st.text_input("🔎 Buscar por termo", placeholder="Ex: Lula, Inflação...")
            
        with f_col2:
            veiculos_disponiveis = sorted(df['veiculo'].dropna().unique().tolist())
            veiculos_desejados = ["Folha de S.Paulo", "Folha", "Estadão", "O Estado de S. Paulo", "UOL", "O Globo", "Valor Econômico", "BBC Brasil"]
            padrao_veiculos = [v for v in veiculos_disponiveis if any(d.lower() in v.lower() for d in veiculos_desejados)]
            
            if not padrao_veiculos:
                padrao_veiculos = veiculos_disponiveis[:5]
                
            veiculos_selecionados = st.multiselect("📰 Filtrar Veículos", veiculos_disponiveis, default=padrao_veiculos)
            
        with f_col3:
            temas_disponiveis = sorted(df['tema'].unique())
            temas_selecionados = st.multiselect("🏷️ Filtrar Temas", temas_disponiveis, default=temas_disponiveis)
            
    st.divider()
    # --- FIM DO BLOCO DE FILTROS ---
    
    # Lógica do Modal/Dialog
    if st.session_state.modal_aberto is not None:
        try:
            noticia_selecionada = df_filtrado_reset.iloc[st.session_state.modal_aberto]
            grupo = noticia_selecionada["grupo_noticia"]
            noticias_grupo = df[df["grupo_noticia"] == grupo].sort_values("data_dt")
            mostrar_dialog(noticia_selecionada, noticias_grupo)
        except Exception as e:
            st.error(f"Erro ao abrir o detalhamento: {e}")
            st.session_state.modal_aberto = None
else:
    st.warning("Nenhum dado disponível. Verifique o banco de dados.")
