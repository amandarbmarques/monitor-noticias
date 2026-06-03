import feedparser
from datetime import datetime
from author import get_author
from database import insert_news

def coletar_uol():
    # Feed de notícias gerais do UOL
    rss = feedparser.parse("http://rss.uol.com.br/feed/noticias.xml")

    for item in rss.entries:
        autor = get_author(item.link)

        noticia = {
            "veiculo": "UOL",
            "titulo": item.title,
            "autor": autor,
            "url": item.link,
            "data_publicacao": getattr(item, "published", datetime.now().isoformat()),
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)
        print(f"Salvo UOL: {item.title} | {autor}")

if __name__ == "__main__":
    coletar_uol()