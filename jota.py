import feedparser
from datetime import datetime
from author import get_author
from database import insert_news

def coletar_jota():
    # Feed principal do JOTA
    rss = feedparser.parse("https://www.jota.info/feed")

    for item in rss.entries:
        autor = get_author(item.link)

        noticia = {
            "veiculo": "JOTA",
            "titulo": item.title,
            "autor": autor,
            "url": item.link,
            "data_publicacao": getattr(item, "published", datetime.now().isoformat()),
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)
        print(f"Salvo JOTA: {item.title} | {autor}")

if __name__ == "__main__":
    coletar_jota()