import feedparser
import requests
from datetime import datetime
from author import get_author
from database import insert_news

def coletar_uol():
    # URL atualizada com HTTPS
    url_feed = "https://rss.uol.com.br/feed/noticias.xml"
    
    # Cabeçalho para fingir que somos o Google Chrome e furar o bloqueio do UOL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Baixa o feed usando a proteção do requests
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        
        if resposta.status_code != 200:
            print(f"❌ UOL bloqueou a requisição (Status: {resposta.status_code})")
            return

        # Passa o conteúdo baixado para o feedparser ler
        rss = feedparser.parse(resposta.text)

        if not rss.entries:
            print("⚠️ Feed do UOL lido, mas nenhuma notícia encontrada.")
            return

        for item in rss.entries:
            try:
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
                print(f"✅ Salvo UOL: {item.title} | {autor}")
                
            except Exception as e:
                print(f"❌ Erro ao processar notícia individual do UOL: {e}")
                continue

    except Exception as e:
        print(f"❌ Erro geral na conexão com o UOL: {e}")

if __name__ == "__main__":
    coletar_uol()
