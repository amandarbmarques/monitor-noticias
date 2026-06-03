import feedparser
from datetime import datetime
from database import insert_news

def coletar_estadao():
    rss = feedparser.parse(
        "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/politica/"
    )

    for item in rss.entries:
        # Trata e padroniza a data do RSS
        if hasattr(item, "published_parsed") and item.published_parsed:
            data_iso = datetime(*item.published_parsed[:6]).isoformat()
        else:
            data_iso = datetime.now().isoformat()

        autor = getattr(item, "author", "Estadão")

        noticia = {
            "veiculo": "Estadão",
            "titulo": item.title,
            "autor": autor,
            "url": item.link,
            "data_publicacao": data_iso,
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)
        print(f"Salvo Estadão: {item.title} | {autor}")

if __name__ == "__main__":
    coletar_estadao()
