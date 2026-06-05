import streamlit as st
import pandas as pd
import sqlite3

# -------------------
# Configuração da página
# -------------------
st.set_page_config(
    page_title="Monitor de Notícias",
    layout="wide",
    page_icon="📰"
)

# --- CSS CUSTOMIZADO PARA ESTILIZAÇÃO GERAL E TABELA ULTRA VISÍVEL ---
st.markdown("""
    <style>
    /* Ajuste de cor e fonte da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* --- TURBO NA VISIBILIDADE DA TABELA --- */
    /* Força o aumento da fonte e espaçamento interno das células */
    [data-testid="stTable"] td, [data-testid="stDataFrame"] td {
        font-size: 15px !important;
        padding: 12px 10px !important;
    }
    /* Estilização dos cabeçalhos da tabela */
    [data-testid="stDataFrame"] th {
        font-size: 14px !important;
        font-weight: 700 !important;
        background-color: #F1F5F9 !important;
        color: #1E293B !important;
    }
    /* Borda arredondada externa na tabela */
    .stDataFrame {
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    /* Customização do botão de download */
    .stDownloadButton button {
        border-radius: 8px;
        background-color: #4F46E5;
        color: white;
        border: none;
        padding: 8px 20px;
        font-weight: 600;
    }
    .stDownloadButton button:hover {
        background-color: #4338CA;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------
# 1. CARREGA DADOS FIRST
# -------------------
try:
    with sqlite3.connect("noticias.db", check_same_thread=False) as conn:
        df = pd.read_sql("SELECT * FROM noticias ORDER BY data_publicacao DESC", conn)
except:
    df = pd.DataFrame(columns=["veiculo", "titulo", "autor", "url", "data_publicacao", "data_coleta"])

# -------------------
# Tratamento de Dados Blindado
# -------------------
if not df.empty:
    try:
        df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        df['data_publicacao'] = df['data_publicacao'].dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass

# -------------------
# 2. HEADER CUSTOMIZADO
# -------------------
if not df.empty and 'data_coleta' in df.columns:
    ultima_atualizacao = df['data_coleta'].max()
    try:
        ultima_atualizacao = pd.to_datetime(ultima_atualizacao).strftime('%H:%M - %d/%m/%Y')
    except:
        ultima_atualizacao = "Agora"
else:
    ultima_atualizacao = "--:--"

col_tit, col_stat = st.columns([4, 1])

with col_tit:
    st.markdown("""
        <div style="margin-bottom: -15px;">
            <h1 style="color: #1E293B; font-size: 42px; font-weight: 800; margin-bottom: 0;">
                Monitor de <span style="color: #4F46E5;">Notícias</span>
            </h1>
            <p style="color: #64748B; font-size: 16px; margin-top: 5px;">
                Análise e clipping em tempo real dos principais portais brasileiros.
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_stat:
    st.markdown(f"""
        <div style="text-align: right; padding-top: 20px;">
            <div style="display: inline-flex; align-items: center; background-color: #ECFDF5; border: 1px solid #10B981; padding: 4px 12px; border-radius: 20px;">
                <span style="height: 8px; width: 8px; background-color: #10B981; border-radius: 50%; display: inline-block; margin-right: 8px; animation: pulse 2s infinite;"></span>
                <span style="color: #065F46; font-size: 12px; font-weight: 700; text-transform: uppercase;">Sistema Live</span>
            </div>
            <p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 500;">
                Última coleta: {ultima_atualizacao}
            </p>
        </div>
        
        <style>
        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}
        </style>
    """, unsafe_allow_html=True)

st.markdown("---")

# -------------------
# BARRA LATERAL (Ranking de Autores)
# -------------------
with st.sidebar:
    st.header("✍️ Ranking de Autores")
    if not df.empty:
        ranking = df["autor"].value_counts().reset_index()
        ranking.columns = ["Autor", "Qtd"]
        st.dataframe(ranking.head(15), use_container_width=True, hide_index=True, height=450)
    else:
        st.write("Nenhum autor mapeado.")
    st.caption("v1.9 • Atualizado via GitHub Actions")

# -------------------
# MÉTRICAS CUSTOMIZADAS
# -------------------
total = len(df)
contagem = df["veiculo"].value_counts()

c_tot, c_est, c_fol, c_uol, c_out = st.columns(5)

with c_tot:
    st.html(f"""
        <div style="background-color: #4F46E5; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #4F46E5; min-height: 95px;">
            <p style="margin: 0; font-size: 11px; color: #E0E7FF; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">📈 Total Geral</p>
            <h3 style="margin: 5px 0 0 0; font-size: 26px; color: #FFFFFF; font-weight: 700;">{total}</h3>
        </div>
    """)

with c_est:
    st.html(f"""
        <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #1E293B; min-height: 95px;">
            <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔹 Estadão</p>
            <h3 style="margin: 5px 0 0 0; font-size: 26px; color: #1E293B; font-weight: 700;">{contagem.get("Estadão", 0)}</h3>
        </div>
    """)

with c_fol:
    st.html(f"""
        <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #E11D48; min-height: 95px;">
            <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔸 Folha</p>
            <h3 style="margin: 5px 0 0 0; font-size: 26px; color: #1E293B; font-weight: 700;">{contagem.get("Folha", 0)}</h3>
        </div>
    """)

with c_uol:
    st.html(f"""
        <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #2563EB; min-height: 95px;">
            <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase;">🟡 UOL</p>
            <h3 style="margin: 5px 0 0 0; font-size: 26px; color: #1E293B; font-weight: 700;">{contagem.get("UOL", 0)}</h3>
        </div>
    """)

with c_out:
    qtd_outros = contagem.get("CNN Brasil", 0) + contagem.get("JOTA", 0)
    st.html(f"""
        <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #EEF0F5; border-left: 5px solid #059669; min-height: 95px;">
            <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase;">🔴 CNN & JOTA</p>
            <h3 style="margin: 5px 0 0 0; font-size: 26px; color: #1E293B; font-weight: 700;">{qtd_outros}</h3>
        </div>
    """)

st.markdown("###") # Espaçador

# -------------------
# FILTROS E BUSCA
# -------------------
with st.expander("🔍 Ferramentas de Filtro e Busca", expanded=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        busca = st.text_input("Buscar palavra-chave no título...")
    with c2:
        opcoes_v = sorted(df["veiculo"].unique()) if not df.empty else []
        veiculos = st.multiselect("Veículos", options=opcoes_v, default=opcoes_v)
    with c3:
        opcoes_a = sorted(df["autor"].dropna().unique()) if not df.empty else []
        autores = st.multiselect("Filtrar por Autor", options=opcoes_a)

# Aplicação dos filtros selecionados (Corrigido os recuos internos)
if not df.empty:
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    if veiculos:
        df = df[df["veiculo"].isin(veiculos)]
    if autores:
        df = df[df["autor"].isin(autores)]

# -------------------
# TABELA PRINCIPAL COM SELEÇÃO
# -------------------
st.subheader("📋 Clipping de Notícias")

if not df.empty:

    # Dados exibidos
    df_exibicao = df[
        ["veiculo", "titulo", "autor", "url", "data_publicacao"]
    ].copy()

    # Checkbox
    if "Selecionar" not in df_exibicao.columns:
        df_exibicao.insert(0, "Selecionar", False)

    # Inicializa estado
    if "df_editor" not in st.session_state:
        st.session_state.df_editor = df_exibicao

    # Editor
    edited_df = st.data_editor(
        st.session_state.df_editor,
        use_container_width=True,
        hide_index=True,
        height=900,
        key="editor_noticias",
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "✓",
                help="Selecione notícias para exportação"
            ),
            "veiculo": st.column_config.TextColumn(
                "Fonte",
                width="small"
            ),
            "titulo": st.column_config.TextColumn(
                "Notícia (Título)",
                width="large"
            ),
            "autor": st.column_config.TextColumn(
                "Autor",
                width="medium"
            ),
            "data_publicacao": st.column_config.TextColumn(
                "Horário",
                width="small"
            ),
            "url": st.column_config.LinkColumn(
                "Link",
                display_text="Ler Agora",
                width="small"
            )
        }
    )

    st.session_state.df_editor = edited_df

    selecionadas = edited_df[
        edited_df["Selecionar"] == True
    ]

    # -------------------
    # BARRA DE EXPORTAÇÃO
    # -------------------

    st.markdown(
        f"**📰 Notícias selecionadas: {len(selecionadas)}**"
    )

    col1, col2 = st.columns(2)

    with col1:

        csv_total = (
            df.drop(columns=["id"], errors="ignore")
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "📥 Exportar Tudo",
            csv_total,
            "clipping_completo.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:

        if len(selecionadas) > 0:

            csv_sel = (
                selecionadas
                .drop(columns=["Selecionar"])
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                f"✅ Exportar {len(selecionadas)} Selecionadas",
                csv_sel,
                "noticias_selecionadas.csv",
                "text/csv",
                use_container_width=True
            )

        else:

            st.button(
                "✅ Exportar Selecionadas",
                disabled=True,
                use_container_width=True
            )

    st.markdown("---")

    # -------------------
    # TABELA
    # -------------------

    st.dataframe(
        edited_df,
        use_container_width=True,
        hide_index=True,
        height=900,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("✓"),
            "veiculo": st.column_config.TextColumn("Fonte"),
            "titulo": st.column_config.TextColumn("Notícia"),
            "autor": st.column_config.TextColumn("Autor"),
            "data_publicacao": st.column_config.TextColumn("Horário"),
            "url": st.column_config.LinkColumn(
                "Link",
                display_text="Ler Agora"
            )
        }
    )

else:
    st.info(
        "Nenhum dado encontrado para os filtros aplicados ou banco de dados vazio."
    )
