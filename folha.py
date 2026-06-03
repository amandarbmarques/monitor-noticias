import feedparser
from datetime import datetime

from author import get_author
from database import insert_news


def coletar_folha():

    rss = feedparser.parse(
        "https://feeds.folha.uol.com.br/poder/rss091.xml"
    )

    for item in rss.entries:

        autor = get_author(item.link)

        noticia = {
            "veiculo": "Folha",
            "titulo": item.title,
            "autor": autor,
            "url": item.link,
            "data_publicacao": item.published,
            "data_coleta": datetime.now().isoformat()
        }

        insert_news(noticia)

        print(
            f"Salvo: {item.title} | {autor}"
        )


if __name__ == "__main__":
    coletar_folha()
