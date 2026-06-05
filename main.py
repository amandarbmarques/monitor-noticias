import requests
import feedparser
import html

def teste_uol_direto():
    url_feed = "https://noticias.uol.com.br/feed/index.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    print("📡 TESTE FORÇADO: Conectando ao UOL...")
    resposta = requests.get(url_feed, headers=headers, timeout=15)
    rss = feedparser.parse(resposta.text)
    
    if not rss.entries:
        print("❌ O feed retornou vazio no GitHub!")
        return
        
    print(f"🔥 SUCESSO! Encontramos {len(rss.entries)} notícias no feed.")
    for item in rss.entries[:5]: # Mostra apenas as 5 primeiras
        print(f"👉 TÍTULO ENCONTRADO: {html.unescape(item.title)}")

if __name__ == "__main__":
    teste_uol_direto()
