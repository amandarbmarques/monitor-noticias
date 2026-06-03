import feedparser
from datetime import datetime

from database import insert_news


def coletar_estadao():

    rss = feedparser.parse(
        "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/politica/"
    )

    for item in rss.entries:

        noticia = {
            "veiculo": "Estadão",
            "titulo": item.title,
            "autor": item.author,
            "url": item.link,
            "data_publicacao": item.published,
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)

        print(
            f"Salvo: {item.title} | {item.author}"
        )


if __name__ == "__main__":
    coletar_estadao()
