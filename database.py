import psycopg2
from datetime import datetime

# URL CORRIGIDA DE ACORDO COM A NOVA INFRAESTRUTURA DO SUPABASE
DB_URI = "postgresql://postgres.hhfttkctypcgrdwvnhug:23062011Cf!!04@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

def get_connection():
    """Retorna uma conexão limpa com o banco de dados Supabase"""
    return psycopg2.connect(DB_URI)

def create_table():
    """Cria a tabela de notícias na nuvem se ela não existir"""
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
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
        print("✅ Tabela 'noticias' verificada/criada no Supabase com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabela no Supabase: {e}")

def insert_news(noticia):
    """Insere uma única notícia no Supabase, ignorando duplicadas pelo título"""
    query = """
    INSERT INTO noticias (veiculo, titulo, autor, url, data_publicacao, data_coleta)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (titulo) DO NOTHING;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    noticia["veiculo"],
                    noticia["titulo"],
                    noticia["autor"],
                    noticia["url"],
                    noticia["data_publicacao"],
                    noticia["data_coleta"]
                ))
                conn.commit()
    except Exception as e:
        print(f"❌ Erro ao inserir notícia no Supabase: {e}")
