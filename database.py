import psycopg2
from datetime import datetime

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
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
            conn.commit()  # ✅ COMMIT IMPORTANTE!
        print("✅ Tabela 'noticias' verificada/criada no Supabase!")
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")

def insert_news(noticia):
    """Insere uma notícia individual"""
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
            conn.commit()  # ✅ COMMIT IMPORTANTE!
    except Exception as e:
        print(f"❌ Erro ao inserir: {e}")

def insert_many_news(lista_noticias):
    """Insere várias notícias no banco em uma única transação"""
    if not lista_noticias:
        print("⚠️  Lista de notícias vazia, nada a inserir")
        return
        
    query = """
    INSERT INTO noticias (veiculo, titulo, autor, url, data_publicacao, data_coleta)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (titulo) DO NOTHING;
    """
    
    insertadas = 0
    duplicadas = 0
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for noticia in lista_noticias:
                    # 🔍 DEBUG: Mostra cada inserção
                    print(f"  Inserindo: {noticia['veiculo']:20} | {noticia['data_publicacao']} | {noticia['titulo'][:60]}...")
                    
                    cursor.execute(query, (
                        noticia["veiculo"],
                        noticia["titulo"],
                        noticia["autor"],
                        noticia["url"],
                        noticia["data_publicacao"],
                        noticia["data_coleta"]
                    ))
                    
                    # Verifica se a linha foi inserida (rowcount = 1) ou ignorada (rowcount = 0)
                    if cursor.rowcount == 1:
                        insertadas += 1
                    else:
                        duplicadas += 1
            
            # ✅ COMMIT SUPER IMPORTANTE - SEM ISSO NADA É SALVO!
            conn.commit()
            
        print(f"\n{'='*80}")
        print(f"🚚 SUCESSO! Notícias processadas:")
        print(f"   ✅ Novas inseridas: {insertadas}")
        print(f"   ⚠️  Duplicadas (ignoradas): {duplicadas}")
        print(f"   📊 Total processado: {len(lista_noticias)}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO ao inserir lote: {e}")
        import traceback
        traceback.print_exc()

def update_data_publicacao(titulo, nova_data):
    """Atualiza a data de publicação de uma notícia (útil se descobrirmos a data certa depois)"""
    query = """
    UPDATE noticias 
    SET data_publicacao = %s 
    WHERE titulo = %s;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (nova_data, titulo))
            conn.commit()
        print(f"✅ Data de '{titulo[:50]}...' atualizada para {nova_data}")
    except Exception as e:
        print(f"❌ Erro ao atualizar: {e}")

def limpar_noticias_antigas(dias=7):
    """Remove notícias com mais de X dias (útil para manter o banco limpo)"""
    query = """
    DELETE FROM noticias 
    WHERE data_coleta < NOW() - INTERVAL '%s days';
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (dias,))
            conn.commit()
        print(f"✅ Notícias com mais de {dias} dias removidas!")
    except Exception as e:
        print(f"❌ Erro ao limpar: {e}")

def get_noticias_por_data_range(data_inicio, data_fim):
    """Retorna notícias dentro de um intervalo de datas"""
    query = """
    SELECT * FROM noticias 
    WHERE data_publicacao BETWEEN %s AND %s
    ORDER BY data_publicacao DESC;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (data_inicio, data_fim))
                return cursor.fetchall()
    except Exception as e:
        print(f"❌ Erro ao buscar: {e}")
        return []
