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
# CSS CUSTOMIZADO - GRID LAYOUT
# ==========================================
st.markdown("""
    <style>
    /* Container do grid */
    .news-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 20px;
    }
    
    /* Card individual */
    .news-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border-top: 4px solid #2E7D32;
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 220px;
    }
    
    .news-card:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        transform: translateY(-4px);
    }
    
    .news-card.furo {
        border-top: 4px solid #F57C00;
        background: linear-gradient(135deg, rgba(245,124,0,0.03) 0%, white 100%);
    }
    
    .news-card.furo .badge-primeiro {
        display: inline-block;
        background: #FFF3CD;
        color: #856404;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    /* Título */
    .card-titulo {
        font-weight: 700;
        font-size: 0.95em;
        color: #1A1A1A;
        line-height: 1.35;
        margin-bottom: 12px;
        flex-grow: 1;
    }
    
    /* Info */
    .card-info {
        font-size: 0.85em;
        color: #666;
        margin-bottom: 8px;
    }
    
    .card-veiculo {
        font-weight: 700;
        color: #2E7D32;
        font-size: 0.9em;
        margin-bottom: 6px;
    }
    
    .card-data {
        color: #999;
        font-size: 0.8em;
    }
    
    .card-autor {
        color: #999;
        font-size: 0.8em;
    }
    
    /* Link */
    .card-link {
        margin-top: auto;
        padding-top: 12px;
        border-top: 1px solid #E0E0E0;
    }
    
    .card-link a {
        display: inline-block;
        color: #2E7D32;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9em;
        transition: color 0.2s;
    }
    
    .card-link a:hover {
        color: #1B5E20;
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
    
    /* Metrics */
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
    # NOTÍCIAS - GRID LAYOUT
    # ==========================================
    st.markdown("### 📌 Notícias")
    
    # Cria o HTML do grid
    grid_html = '<div class="news-grid">'
    
    for index, row in df_filtrado.iterrows():
        classe = "news-card furo" if row['furo'] == '🥇' else "news-card"
        badge = '<div class="badge-primeiro">🥇 PRIMEIRO</div>' if row['furo'] == '🥇' else ''
        
        # Limita título a ~50 caracteres
        titulo_exibido = row['titulo'][:55] + '...' if len(row['titulo']) > 55 else row['titulo']
        
        grid_html += f"""
            <div class="{classe}">
                {badge}
                <div class="card-titulo">{titulo_exibido}</div>
                <div class="card-info">
                    <div class="card-veiculo">{row['veiculo']}</div>
                    <div class="card-data">📅 {row['data_formatada']}</div>
                    <div class="card-autor">✍️ {row['autor']}</div>
                </div>
                <div class="card-link">
                    <a href="{row['url']}" target="_blank">🔗 Abrir</a>
                </div>
            </div>
        """
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhuma notícia carregada.")
