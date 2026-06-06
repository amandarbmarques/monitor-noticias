import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import difflib

# ==========================================
# CONFIG PÁGINA
# ==========================================
st.set_page_config(
    page_title="Monitor de Notícias Pro",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS CUSTOMIZADO - DESIGN MODERNO
# ==========================================
st.markdown("""
    <style>
    /* Root colors */
    :root {
        --primary: #2E7D32;
        --primary-light: #66BB6A;
        --secondary: #F57C00;
        --dark: #1A1A1A;
        --light: #F5F5F5;
        --danger: #E53935;
    }
    
    /* Main background */
    body {
        background: linear-gradient(135deg, #F5F5F5 0%, #EEEEEE 100%);
    }
    
    /* Cards styling */
    .news-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border-left: 5px solid #2E7D32;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .news-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .news-card.furo {
        border-left: 5px solid #F57C00;
        background: linear-gradient(90deg, rgba(245,124,0,0.05) 0%, white 20%);
    }
    
    /* Header styling */
    .header-title {
        font-size: 2.5em;
        font-weight: 800;
        color: #1A1A1A;
        margin-bottom: 8px;
        letter-spacing: -1px;
    }
    
    .header-subtitle {
        font-size: 1.1em;
        color: #666;
        margin-bottom: 20px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .badge-primeiro {
        background-color: #FFF3CD;
        color: #856404;
        border: 1px solid #FFEAA7;
    }
    
    .badge-tema {
        background-color: #E3F2FD;
        color: #1565C0;
        border: 1px solid #BBDEFB;
    }
    
    .badge-veiculo {
        background-color: #F3E5F5;
        color: #6A1B9A;
        border: 1px solid #E1BEE7;
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-number {
        font-size: 2.5em;
        font-weight: 800;
        color: #2E7D32;
    }
    
    .metric-label {
        font-size: 0.95em;
        color: #666;
        margin-top: 8px;
    }
    
    /* Timeline */
    .timeline {
        border-left: 3px solid #E0E0E0;
        padding-left: 20px;
        margin-top: 15px;
    }
    
    .timeline-item {
        position: relative;
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
    
    .timeline-item:before {
        content: '';
        position: absolute;
        left: -23px;
        top: 0;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: white;
        border: 3px solid #2E7D32;
    }
    
    .timeline-item.primeiro:before {
        background: #F57C00;
        border-color: #F57C00;
        box-shadow: 0 0 0 4px rgba(245,124,0,0.1);
    }
    
    .timeline-time {
        font-size: 0.85em;
        color: #999;
        font-weight: 600;
    }
    
    .timeline-veiculo {
        font-weight: 600;
        color: #2E7D32;
        margin-top: 4px;
    }
    
    /* Filters */
    .filter-section {
        background: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .filter-title {
        font-weight: 700;
        color: #2E7D32;
        margin-bottom: 12px;
        font-size: 0.95em;
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
        return "Outros"
    t = titulo.lower()
    if any(x in t for x in ["lula", "governo", "stf", "política", "congresso", "senado", "flávio", "moraes"]):
        return "Política"
    if any(x in t for x in ["economia", "dólar", "mercado", "juros", "haddad", "imposto", "tarifa", "investimento"]):
        return "Economia"
    if any(x in t for x in ["tecnologia", "ia", "google", "meta", "facebook", "amazon", "apple"]):
        return "Tecnologia"
    return "Geral"

def extrair_palavras_chave(titulo, n=5):
    """Extrai palavras-chave principais do título"""
    stop_words = {"a", "o", "e", "de", "da", "do", "em", "para", "por", "que", "é", "um", "uma", "os", "as", "dos", "das"}
    palavras = titulo.lower().split()
    palavras_filtradas = [p for p in palavras if p not in stop_words and len(p) > 3]
    return palavras_filtradas[:n]

def calcular_furos_inteligentes(df):
    """
    NOVO ALGORITMO: Detecta qual jornal publicou PRIMEIRO analisando 
    similaridade de palavras-chave nos títulos
    """
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
        
        # Procura por notícias similares já vistas
        melhor_grupo = None
        melhor_score = 0
        
        for grupo_id, palavras_grupo in grupos_vistos.items():
            # Calcula similaridade Jaccard
            interseccao = len(palavras_atuais & palavras_grupo)
            uniao = len(palavras_atuais | palavras_grupo)
            score = interseccao / uniao if uniao > 0 else 0
            
            if score > 0.5 and score > melhor_score:  # Threshold de 50% similar
                melhor_score = score
                melhor_grupo = grupo_id
        
        if melhor_grupo is None:
            # Nova notícia, cria novo grupo
            melhor_grupo = len(grupos_vistos)
            grupos_vistos[melhor_grupo] = palavras_atuais
            
            # É o PRIMEIRO a falar disso
            df.at[index, 'furo'] = "🥇 Primeiro"
        else:
            # Já existe similar
            df.at[index, 'furo'] = ""
        
        df.at[index, 'grupo_noticia'] = melhor_grupo
    
    return df.sort_values(by='data_dt', ascending=False)

@st.cache_data(ttl=30)
def carregar_dados():
    """Carrega dados do banco com cache de 30 segundos"""
    try:
        DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_coleta DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco: {e}")
        return pd.DataFrame()

# ==========================================
# CARREGAR E PROCESSAR DADOS
# ==========================================
df = carregar_dados()

if not df.empty:
    # Processamento de datas
    df['data_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    if 'data_coleta' in df.columns:
        df['data_dt'] = df['data_dt'].fillna(pd.to_datetime(df['data_coleta'], errors='coerce', utc=True))
    df['data_dt'] = df['data_dt'].fillna(pd.Timestamp.now(tz='UTC'))
    df['data_dt'] = df['data_dt'].dt.tz_convert('America/Sao_Paulo')
    df['data_formatada'] = df['data_dt'].dt.strftime('%d/%m %H:%M')
    df['hora_publicacao'] = df['data_dt'].dt.strftime('%H:%M')
    
    # Classificação
    df["tema"] = df["titulo"].apply(classificar_tema)
    
    # Detecção de furos (NOVO ALGORITMO)
    df = calcular_furos_inteligentes(df)
    
    # ==========================================
    # SIDEBAR - FILTROS
    # ==========================================
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2965/2965879.png", width=50)
        st.title("🔍 Filtros")
        
        # Busca
        busca = st.text_input("🔎 Buscar no título", placeholder="Ex: Lula, economia...")
        
        # Veículos
        veiculos_disponiveis = sorted(df['veiculo'].dropna().unique().tolist())
        veiculos_selecionados = st.multiselect(
            "📰 Veículos",
            veiculos_disponiveis,
            default=veiculos_disponiveis[:5]
        )
        
        # Temas
        temas_selecionados = st.multiselect(
            "🏷️ Temas",
            df['tema'].dropna().unique().tolist(),
            default=df['tema'].dropna().unique().tolist()
        )
        
        # Filtro de furos
        mostrar_furos = st.checkbox("🥇 Apenas furos", value=False)
        
        st.divider()
        
        # Estatísticas rápidas
        st.markdown("### 📊 Resumo")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(df))
        with col2:
            furos_total = len(df[df['furo'] == '🥇 Primeiro'])
            st.metric("Furos", furos_total)
    
    # ==========================================
    # APLICAR FILTROS
    # ==========================================
    df_filtrado = df.copy()
    
    if busca:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busca, case=False, na=False)]
    
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['veiculo'].isin(veiculos_selecionados)]
    
    if temas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tema'].isin(temas_selecionados)]
    
    if mostrar_furos:
        df_filtrado = df_filtrado[df_filtrado['furo'] == '🥇 Primeiro']
    
    # ==========================================
    # HEADER
    # ==========================================
    st.markdown('<div class="header-title">📰 Monitor de Notícias</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="header-subtitle">Acompanhamento em tempo real com detecção automática de furos jornalísticos</div>',
        unsafe_allow_html=True
    )
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{len(df_filtrado)}</div>
                <div class="metric-label">Notícias</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        furos = len(df_filtrado[df_filtrado['furo'] == '🥇 Primeiro'])
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #F57C00;">{furos}</div>
                <div class="metric-label">Furos Detectados</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        veiculos = df_filtrado['veiculo'].nunique()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #1565C0;">{veiculos}</div>
                <div class="metric-label">Veículos</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        temas_unicos = df_filtrado['tema'].nunique()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #6A1B9A;">{temas_unicos}</div>
                <div class="metric-label">Temas</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==========================================
    # EXIBIÇÃO DE NOTÍCIAS EM CARDS
    # ==========================================
    st.markdown("### 📌 Notícias Recentes")
    
    for index, row in df_filtrado.iterrows():
        # Define classe do card
        classe = "news-card furo" if row['furo'] == '🥇 Primeiro' else "news-card"
        
        # Monta o card
        with st.container():
            col_left, col_right = st.columns([4, 1])
            
            with col_left:
                # Badges
                badges = ""
                
                if row['furo'] == '🥇 Primeiro':
                    badges += '<span class="badge badge-primeiro">🥇 PRIMEIRO!</span>'
                
                badges += f'<span class="badge badge-tema">{row["tema"]}</span>'
                badges += f'<span class="badge badge-veiculo">{row["veiculo"]}</span>'
                
                st.markdown(f"""
                    <div class="{classe}">
                        <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                            {badges}
                        </div>
                        <h3 style="margin: 0 0 12px 0; color: #1A1A1A; line-height: 1.4;">
                            {row['titulo']}
                        </h3>
                        <div style="font-size: 0.9em; color: #999; margin-bottom: 12px;">
                            📅 {row['data_formatada']} | ✍️ {row['autor']}
                        </div>
                        <a href="{row['url']}" target="_blank" style="
                            display: inline-block;
                            padding: 8px 16px;
                            background: #2E7D32;
                            color: white;
                            text-decoration: none;
                            border-radius: 6px;
                            font-weight: 600;
                            font-size: 0.9em;
                            transition: background 0.3s;
                        " onmouseover="this.style.background='#1B5E20'" onmouseout="this.style.background='#2E7D32'">
                            🔗 Abrir Notícia
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_right:
                # Timeline de notícias similares
                grupo = row['grupo_noticia']
                noticias_grupo = df_filtrado[df_filtrado['grupo_noticia'] == grupo].sort_values('data_dt')
                
                if len(noticias_grupo) > 1:
                    st.markdown(f"""
                        <div class="timeline">
                            <div style="font-size: 0.8em; font-weight: 600; color: #666; margin-bottom: 10px;">
                                {len(noticias_grupo)} jornais
                            </div>
                    """, unsafe_allow_html=True)
                    
                    for _, noticia_similar in noticias_grupo.iterrows():
                        primeiro = "primeiro" if noticia_similar['furo'] == '🥇 Primeiro' else ""
                        st.markdown(f"""
                            <div class="timeline-item {primeiro}">
                                <div class="timeline-time">{noticia_similar['hora_publicacao']}</div>
                                <div class="timeline-veiculo">{noticia_similar['veiculo']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhuma notícia carregada. Verifique a conexão com o banco de dados.")
