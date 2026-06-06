import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ==========================================
# CONFIG PÁGINA
# ==========================================
st.set_page_config(
    page_title="Monitor de Notícias",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INICIALIZAR SESSION STATE
# ==========================================
if 'card_expandido' not in st.session_state:
    st.session_state.card_expandido = None

# ==========================================
# FUNÇÕES
# ==========================================

def classificar_tema(titulo):
    """Classifica notícia por tema"""
    if not isinstance(titulo, str):
        return "Geral"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado", "flávio", "moraes"]):
        return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad", "imposto", "tarifa", "investimento"]):
        return "Economia"
    if any(x in t for x in ["tecnologia", "ia", "google", "meta", "facebook", "amazon", "apple"]):
        return "Tech"
    return "Geral"

def extrair_palavras_chave(titulo, n=5):
    """Extrai palavras-chave principais do título"""
    stop_words = {"a", "o", "e", "de", "da", "do", "em", "para", "por", "que", "é", "um", "uma", "os", "as", "dos", "das"}
    palavras = titulo.lower().split()
    palavras_filtradas = [p for p in palavras if p not in stop_words and len(p) > 3]
    return palavras_filtradas[:n]

def calcular_furos_inteligentes(df):
    """Detecta qual jornal publicou PRIMEIRO"""
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
    """Carrega dados do banco"""
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_coleta DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        return pd.DataFrame()

# ==========================================
# CARREGAR E PROCESSAR
# ==========================================
df = carregar_dados()

if not df.empty:
    # Datas
    df['data_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    if 'data_coleta' in df.columns:
        df['data_dt'] = df['data_dt'].fillna(pd.to_datetime(df['data_coleta'], errors='coerce', utc=True))
    df['data_dt'] = df['data_dt'].fillna(pd.Timestamp.now(tz='UTC'))
    df['data_dt'] = df['data_dt'].dt.tz_convert('America/Sao_Paulo')
    df['data_formatada'] = df['data_dt'].dt.strftime('%d/%m %H:%M')
    df['hora_publicacao'] = df['data_dt'].dt.strftime('%H:%M')
    
    # Temas
    df["tema"] = df["titulo"].apply(classificar_tema)
    
    # Furos
    df = calcular_furos_inteligentes(df)
    
    # ==========================================
    # SIDEBAR
    # ==========================================
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2965/2965879.png", width=50)
        st.title("🔍 Filtros")
        
        busca = st.text_input("🔎 Buscar...", placeholder="Ex: Lula, economia...")
        
        veiculos_disponiveis = sorted(df['veiculo'].dropna().unique().tolist())
        veiculos_selecionados = st.multiselect(
            "📰 Veículos",
            veiculos_disponiveis,
            default=veiculos_disponiveis[:5]
        )
        
        temas_selecionados = st.multiselect(
            "🏷️ Temas",
            sorted(df['tema'].unique()),
            default=sorted(df['tema'].unique())
        )
        
        mostrar_furos = st.checkbox("🥇 Apenas furos", value=False)
        
        st.divider()
        
        st.markdown("### 📊 Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(df))
        with col2:
            furos_total = len(df[df['furo'] == '🥇'])
            st.metric("Furos", furos_total)
    
    # ==========================================
    # FILTROS
    # ==========================================
    df_filtrado = df.copy()
    
    if busca:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busca, case=False, na=False)]
    
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]
    
    if mostrar_furos:
        df_filtrado = df_filtrado[df_filtrado['furo'] == '🥇']
    
    # ==========================================
    # HEADER
    # ==========================================
    st.title("📰 Monitor de Notícias")
    st.markdown("Clique em 'Ver similares' para ver outros veículos que publicaram sobre o mesmo tema")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Notícias", len(df_filtrado))
    
    with col2:
        furos = len(df_filtrado[df_filtrado['furo'] == '🥇'])
        st.metric("Furos", furos)
    
    with col3:
        veiculos = df_filtrado['veiculo'].nunique()
        st.metric("Veículos", veiculos)
    
    with col4:
        temas_unicos = df_filtrado['tema'].nunique()
        st.metric("Temas", temas_unicos)
    
    st.divider()
    
    # ==========================================
    # NOTÍCIAS - GRID 3 COLUNAS
    # ==========================================
    st.markdown("### 📌 Notícias")
    
    # Renderiza cards em grid de 3 colunas
    df_filtrado_reset = df_filtrado.reset_index(drop=True)
    
    for i in range(0, len(df_filtrado_reset), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(df_filtrado_reset):
                row = df_filtrado_reset.iloc[i + j]
                index = df_filtrado_reset.index[i + j]
                
                with cols[j]:
                    # Verifica similares
                    grupo = row['grupo_noticia']
                    noticias_grupo = df[df['grupo_noticia'] == grupo]
                    tem_similares = len(noticias_grupo) > 1
                    
                    # Badge
                    badge = "🥇 " if row['furo'] == '🥇' else ""
                    
                    # Card HTML
                    st.markdown(f"""
                        <div style="
                            background: white;
                            border-left: 4px solid #2E7D32;
                            border-radius: 8px;
                            padding: 16px;
                            margin-bottom: 8px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            min-height: 140px;
                            display: flex;
                            flex-direction: column;
                        ">
                            <div style="font-weight: 700; font-size: 0.95em; line-height: 1.35; color: #1A1A1A; margin-bottom: 12px; flex-grow: 1;">
                                {badge}{row['titulo'][:60]}{'...' if len(row['titulo']) > 60 else ''}
                            </div>
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 12px;">
                                <div style="color: #2E7D32; font-weight: 700; margin-bottom: 4px;">{row['veiculo']}</div>
                                <div style="color: #999; margin-bottom: 2px;">📅 {row['data_formatada']}</div>
                                <div style="color: #999;">✍️ {row['autor']}</div>
                            </div>
                            <div style="padding-top: 12px; border-top: 1px solid #E0E0E0;">
                                <a href="{row['url']}" target="_blank" style="
                                    color: #2E7D32;
                                    text-decoration: none;
                                    font-weight: 600;
                                    font-size: 0.9em;
                                ">🔗 Abrir notícia</a>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão (só aparece se tem similares)
                    if tem_similares:
                        if st.button(f"ℹ️ Ver similares ({len(noticias_grupo)})", key=f"btn_{i}_{j}", use_container_width=True):
                            st.session_state.card_expandido = i + j
    
    # ==========================================
    # EXPANSÃO - MOSTRAR NOTÍCIAS SIMILARES
    # ==========================================
    if st.session_state.card_expandido is not None:
        noticia_selecionada = df_filtrado.loc[st.session_state.card_expandido]
        grupo = noticia_selecionada['grupo_noticia']
        
        # Busca outras notícias do mesmo grupo
        noticias_grupo = df[df['grupo_noticia'] == grupo].sort_values('data_dt')
        
        st.divider()
        
        with st.expander("📰 Outros veículos que publicaram sobre este tema", expanded=True):
            st.markdown(f"### Tema: {noticia_selecionada['titulo'][:80]}")
            st.markdown(f"**Total de publicações:** {len(noticias_grupo)} veículos")
            
            st.markdown("---")
            
            # Timeline
            for idx, noticia in noticias_grupo.iterrows():
                primeiro = "🥇 **PRIMEIRO A PUBLICAR**" if noticia['furo'] == '🥇' else ""
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **{noticia['veiculo']}** {primeiro}
                    
                    {noticia['titulo']}
                    
                    Autor: {noticia['autor']} | [🔗 Abrir]({noticia['url']})
                    """)
                
                with col2:
                    st.markdown(f"""
                    **{noticia['hora_publicacao']}**
                    
                    {noticia['data_formatada'].split()[0]}
                    """)
                
                st.markdown("---")
        
        # Botão para fechar
        if st.button("✕ Fechar expansão"):
            st.session_state.card_expandido = None

else:
    st.warning("⚠️ Nenhuma notícia carregada.")
