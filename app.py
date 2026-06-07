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
    if any(x in t for x in
