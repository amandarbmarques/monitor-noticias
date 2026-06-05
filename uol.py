import feedparser
import requests
import html
import urllib.parse
from datetime import datetime
import dateutil.parser

from database import insert_news

def coletar_via_google_news():
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("📡 Conectando ao super hub do Google News...")
    try:
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        rss = feedparser.parse(resposta.text)

        if not rss.entries:
            print("❌ O hub do Google retornou vazio.")
            return

        print(f"🔥 Sucesso! Encontramos {len(rss.entries)} notícias no hub.")
        
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        
        contador = 0
        for item in rss.entries:
            try:
                titulo_completo = html.unescape(item.title)
                
                # 1. Pega a fonte direto da TAG OFICIAL do Google (Infalível)
                veiculo_origem = "Google News"
                if hasattr(item, "source") and "title" in item.source:
                    veiculo_origem = item.source.title

                # 2. Verifica se a fonte oficial está na sua lista
                veiculo_encontrado = None
                for v in veiculos_alvo:
                    if v.lower() in veiculo_origem.lower() or v.lower() in titulo_completo.lower():
                        veiculo_encontrado = v
                        break

                if not veiculo_encontrado:
                    continue  # Pula os que não são da lista
                
                # 3. Limpa o título não importa qual traço o Google invente de usar
                titulo_limpo = titulo_completo
                for sep in [" - ", " – ", " — ", " | "]:
                    if sep in titulo_limpo:
                        titulo_limpo = titulo_limpo.rsplit(sep, 1)[0].strip()
                        break

                # 4. Tratamento de data seguro
                data_iso = None
                if hasattr(item, "published"):
                    try:
                        dt = dateutil.parser.parse(item.published)
                        data_iso = dt.isoformat()
                    except:
                        pass
                
                if not data_iso:
                    data_iso = datetime.now().isoformat()

                noticia = {
                    "veiculo": veiculo_encontrado,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_iso,
                    "data_coleta": datetime.now().isoformat()
                }

                insert_news(noticia)
                print(f"✅ [Hub] Salvo {veiculo_encontrado}: {titulo_limpo}")
                contador += 1

            except Exception as e:
                continue
                
        print(f"🏁 Coleta via Hub finalizada. {contador} notícias injetadas no Supabase!")

    except Exception as e:
        print(f"❌ Erro na conexão com o Hub: {e}")

if __name__ == "__main__":
    coletar_via_google_news()
