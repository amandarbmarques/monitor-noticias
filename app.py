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
# CSS CUSTOMIZADO - MINIMALISTA
# ==========================================
st.markdown("""
    <style>
    /* News item - compacto */
    .news-item {
        background: white;
        border-left: 4px solid #2E7D32;
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    
    .news-item:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }
    
    .news-item.furo {
        border-left: 4px solid #F57C00;
        background: linear-gradient(90deg, rgba(245,124,0,0.03) 0%, white 10%);
    }
    
    /* Grid de informações */
    .news-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1.5fr 1fr 0.8fr auto;
        gap: 12px;
        align-items: center;
        font-size: 0.95em;
    }
    
    .news-titulo {
        font-weight: 600;
        color: #1A1A1A;
        line-height: 1.3;
    }
    
    .news-veiculo {
        color: #2E7D32;
        font-weight: 600;
        font-size: 0.9em;
    }
    
    .news-data {
        color: #999;
        font-size: 0.9em;
    }
    
    .news-tema {
        display: inline-block;
        background: #E3F2FD;
        color: #1565C0;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 600;
    }
    
    .news-link {
        text-decoration: none;
        color: #2E7D32;
        font-weight: 600;
        font-size: 0.9em;
        white-space: nowrap;
    }
    
    .badge-primeiro {
        background: #FFF3CD;
        color: #856404;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8em;
        font-weight: 700;
    }
    
    /* Header */
    .header {
        margin-bottom: 24px;
    }
    
    .header-title {
        font-size: 2em;
        font-weight: 800;
        color: #1A1A1A;
        margin-bottom: 4px;
    }
    
    .header-subtitle {
        font-size: 0.95em;
        color: #999;
    }
    
    /* Metrics compactas */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .metric-box {
        background: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .metric-number {
        font-size: 1.8em;
        font-weight: 800;
        color: #2E7D32;
    }
    
    .metric-label {
        font-size: 0.8em;
        color: #999;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Filter section */
    .filter-box {
        background: white;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .filter-label {
        font-weight: 700;
        color: #2E7D32;
        font-size: 0.85em;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="header"><div class="header-title">📰 Monitor de Notícias</div><div class="header-subtitle">Monitoramento de publicações e furos jornalísticos</div></div>', unsafe_allow_html=True)
    
    # Métricas
    st.markdown(f"""
        <div class="metrics-row">
            <div class="metric-box">
                <div class="metric-number">{len(df_filtrado)}</div>
                <div class="metric-label">Notícias</div>
            </div>
            <div class="metric-box">
                <div class="metric-number" style="color: #F57C00;">{len(df_filtrado[df_filtrado['furo'] == '🥇'])}</div>
                <div class="metric-label">Furos</div>
            </div>
            <div class="metric-box">
                <div class="metric-number" style="color: #1565C0;">{df_filtrado['veiculo'].nunique()}</div>
                <div class="metric-label">Veículos</div>
            </div>
            <div class="metric-box">
                <div class="metric-number" style="color: #6A1B9A;">{df_filtrado['tema'].nunique()}</div>
                <div class="metric-label">Temas</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==========================================
    # NOTÍCIAS - CARDS COMPACTOS
    # ==========================================
    st.markdown("### 📌 Notícias")
    
    for index, row in df_filtrado.iterrows():
        classe = "news-item furo" if row['furo'] == '🥇' else "news-item"
        badge = '<span class="badge-primeiro">🥇 PRIMEIRO</span>' if row['furo'] == '🥇' else ''
        
        st.markdown(f"""
            <div class="{classe}">
                <div class="news-row">
                    <div>
                        <div class="news-titulo">{row['titulo'][:100]}...</div>
                    </div>
                    <div class="news-veiculo">{row['veiculo']}</div>
                    <div class="news-data">{row['data_formatada']}</div>
                    <div class="news-tema">{row['tema']}</div>
                    <div>{badge}</div>
                    <div><a href="{row['url']}" target="_blank" class="news-link">🔗</a></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhuma notícia carregada.")
