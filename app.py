# ==========================================
# 3. PROCESSAMENTO DA BASE
# ==========================================
if not df.empty:
    # Tenta transformar a data de publicação, mas SEM deletar quem falhar!
    df['data_dt'] = pd.to_datetime(df['data_publicacao'], errors='coerce', utc=True)
    
    # Se a data do jornal falhar (ficar vazia/NaT), usamos a data que o robô fez a coleta!
    if 'data_coleta' in df.columns:
        coleta_segura = pd.to_datetime(df['data_coleta'], errors='coerce', utc=True)
        df['data_dt'] = df['data_dt'].fillna(coleta_segura)
        
    # Se por algum milagre tudo falhar, coloca o horário de agora para não quebrar a tela
    df['data_dt'] = df['data_dt'].fillna(pd.Timestamp.now(tz='UTC'))
    
    # Agora sim, converte todo mundo para Brasília com segurança
    df['data_dt'] = df['data_dt'].dt.tz_convert('America/Sao_Paulo')
    
    # Cria a coluna visual bonita no padrão brasileiro
    df['data_formatada'] = df['data_dt'].dt.strftime('%d/%m/%Y %H:%M')

    df["tema"] = df["titulo"].apply(classificar_tema)
    
    # Calcula os furos
    df = calcular_furos_reais(df)
    
    # Ordena as mais recentes no topo
    df = df.sort_values(by='data_dt', ascending=False).reset_index(drop=True)
