import sqlite3

DB_NAME = "noticias.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo TEXT,
        titulo TEXT,
        autor TEXT,
        url TEXT UNIQUE,
        data_publicacao TEXT,
        data_coleta TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_news(item):

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO noticias
            (
                veiculo,
                titulo,
                autor,
                url,
                data_publicacao,
                data_coleta
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item["veiculo"],
                item["titulo"],
                item["autor"],
                item["url"],
                item["data_publicacao"],
                item["data_coleta"]
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:
        pass

    finally:
        conn.close()
