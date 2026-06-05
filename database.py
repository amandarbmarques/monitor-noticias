import psycopg2

DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf%21%2104@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

def get_connection():
    return psycopg2.connect(DB_URI)

def create_table():
    query = """
    CREATE TABLE IF NOT EXISTS noticias (
        id SERIAL PRIMARY KEY,
        veiculo VARCHAR(100),
        titulo TEXT UNIQUE,
        autor VARCHAR(255),
        url TEXT,
        data_publicacao VARCHAR(100),
        data_coleta VARCHAR(100)
    );
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()
        print("✅ Tabela 'noticias' verificada/criada no Supabase!")
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
    finally:
        # A MÁGICA ESTÁ AQUI: Garante que a porta será fechada
        if conn is not None:
            conn.close()

def insert_news(noticia):
    query = """
    INSERT INTO noticias (veiculo, titulo, autor, url, data_publicacao, data_coleta)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (titulo) DO NOTHING;
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (
            noticia["veiculo"],
            noticia["titulo"],
            noticia["autor"],
            noticia["url"],
            noticia["data_publicacao"],
            noticia["data_coleta"]
        ))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"❌ Erro ao inserir: {e}")
    finally:
        # A MÁGICA ESTÁ AQUI: Garante que a porta será fechada

        def insert_many_news(lista_noticias):
    """Insere várias notícias no banco em uma única viagem (conexão única)"""
    if not lista_noticias:
        return
        
    query = """
    INSERT INTO noticias (veiculo, titulo, autor, url, data_publicacao, data_coleta)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (titulo) DO NOTHING;
    """
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # O caminhão descarregando tudo de uma vez
        for noticia in lista_noticias:
            cursor.execute(query, (
                noticia["veiculo"],
                noticia["titulo"],
                noticia["autor"],
                noticia["url"],
                noticia["data_publicacao"],
                noticia["data_coleta"]
            ))
            
        conn.commit() # Salva tudo
        cursor.close()
        print(f"🚚 SUCESSO REAL: Lote de {len(lista_noticias)} notícias injetadas de uma vez!")
    except Exception as e:
        print(f"❌ ERRO REAL: O banco recusou a inserção do lote. Motivo: {e}")
    finally:
        if conn is not None:
            conn.close()
        if conn is not None:
            conn.close()
