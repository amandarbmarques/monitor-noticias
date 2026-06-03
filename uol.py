import feedparser
from datetime import datetime
from author import get_author
from database import insert_news

def coletar_uol():
    # Feed de notícias gerais do UOL
    rss = feedparser.parse("http://rss.uol.com.br/feed/noticias.xml")

    for item in rss.entries:
        autor = get_author(item.link)

        # Trata e padroniza a data do RSS
        if hasattr(item, "published_parsed") and item.published_parsed:
            data_iso = datetime(*item.published_parsed[:6]).isoformat()
        else:
            data_iso = datetime.now().isoformat()

        noticia = {
            "veiculo": "UOL",
            "titulo": item.title,
            "autor": autor,
            "url": item.link,
            "data_publicacao": data_iso,
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)
        print(f"Salvo UOL: {item.title} | {autor}")

if __name__ == "__main__":
    coletar_uol()
