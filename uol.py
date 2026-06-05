import feedparser
import requests
import html
import urllib.parse
from datetime import datetime
import time
from database import insert_many_news

def coletar_via_google_news():
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        rss = feedparser.parse(resposta.text)

        if not rss.entries: return
        
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        noticias_para_salvar = []
        
        for item in rss.entries:
            try:
                titulo_completo = html.unescape(item.title)
                veiculo_origem = item.source.title if hasattr(item, "source") and "title" in item.source else "Google News"

                veiculo_encontrado = next((v for v in veiculos_alvo if v.lower() in veiculo_origem.lower() or v.lower() in titulo_completo.lower()), None)
                if not veiculo_encontrado: continue  
                
                titulo_limpo = titulo_completo.rsplit(" - ", 1)[0].strip() if " - " in titulo_completo else titulo_completo

                # =======================================================
                # 🛠️ CONVERSOR DE DATA SEGURO (MÁGICA ACONTECE AQUI)
                # =======================================================
                data_iso = None
                if hasattr(item, "published_parsed") and item.published_parsed:
                    # Transforma a estrutura do Google em uma data real do Python
                    dt = datetime.fromtimestamp(time.mktime(item.published_parsed))
                    data_iso = dt.strftime('%Y-%m-%d %H:%M:%S') # Formato perfeito que o banco AMA
                
                if not data_iso:
                    data_iso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                noticia = {
                    "veiculo": veiculo_encontrado,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_iso, 
                    "data_coleta": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                noticias_para_salvar.append(noticia)
            except:
                continue
                
        print(f"📦 Enviando {len(noticias_para_salvar)} notícias filtradas para o Supabase...")
        insert_many_news(noticias_para_salvar)

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    coletar_via_google_news()
