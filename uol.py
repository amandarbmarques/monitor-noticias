import feedparser
import requests
import html
from datetime import datetime
from author import get_author
from database import insert_news

def coletar_uol():
    # URL MODERNA E ATIVA: Feed de tempo real do UOL Notícias
    url_feed = "https://noticias.uol.com.br/feed/index.xml"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml"
    }

    try:
        print(f"Tentando conectar ao novo feed do UOL...")
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        
        if resposta.status_code != 200:
            print(f"❌ UOL rejeitou o acesso (Status: {resposta.status_code})")
            return

        # Passa o conteúdo de texto para o feedparser analisar
        rss = feedparser.parse(resposta.text)

        if not rss.entries:
            print("⚠️ O feed foi lido, mas a estrutura XML veio vazia ou incompatível.")
            return

        print(f"Conectado! Processando {len(rss.entries)} potenciais notícias do UOL...")
        
        contador_salvas = 0
        for item in rss.entries:
            try:
                # Sanitiza o título contra caracteres especiais de HTML
                titulo_limpo = html.unescape(item.title).strip()
                link_limpo = item.link.split("?")[0] # Remove parâmetros de rastreamento da URL

                autor = get_author(link_limpo)

                # Trata a estrutura de data do parser
                if hasattr(item, "published_parsed") and item.published_parsed:
                    data_iso = datetime(*item.published_parsed[:6]).isoformat()
                elif hasattr(item, "updated_parsed") and item.updated_parsed:
                    data_iso = datetime(*item.updated_parsed[:6]).isoformat()
                else:
                    data_iso = datetime.now().isoformat()

                noticia = {
                    "veiculo": "UOL",
                    "titulo": titulo_limpo,
                    "autor": autor if autor else "Redação UOL",
                    "url": link_limpo,
                    "data_publicacao": data_iso,
                    "data_coleta": datetime.now().isoformat()
                }

                insert_news(noticia)
                print(f"✅ Salvo UOL: {titulo_limpo}")
                contador_salvas += 1
                
            except Exception as e:
                continue

        print(f"🏁 Coleta do UOL concluída! {contador_salvas} notícias processadas.")

except Exception as e:
    print(f"❌ Erro crítico na rotina do UOL: {e}")

if __name__ == "__main__":
    coletar_uol()
