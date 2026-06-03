import feedparser
from datetime import datetime


RSS_URL = "https://www.poder360.com.br/feed/"


def get_news():

    noticias = []

    feed = feedparser.parse(RSS_URL)

    for item in feed.entries:

        autor = item.get("author", "Não identificado")

        noticias.append(
            {
                "veiculo": "Poder360",
                "titulo": item.title,
                "autor": autor,
                "url": item.link,
                "data_publicacao": item.get(
                    "published",
                    ""
                ),
                "data_coleta": datetime.now().isoformat()
            }
        )

    return noticias