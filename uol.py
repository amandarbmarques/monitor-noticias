import feedparser
import requests
import html
import urllib.parse
from datetime import datetime
from database import insert_news

def coletar_via_google_news():
    # Buscaremos por termos chave que englobam as pautas dos grandes portais brasileiros
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    
    # URL do feed oficial do Google News Brasil configurado para o fuso local
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("📡 Conectando ao hub do Google News...")
    try:
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        rss = feedparser.parse(resposta.text)

        if not rss.entries:
            print("❌ O hub do Google também retornou vazio (Inprovável).")
            return

        print(f"🔥 Sucesso! Encontramos {len(rss.entries)} notícias quentes no hub.")
        
        contador = 0
        for item in rss.entries[:40]: # Limita nas 40 mais recentes para não pesar
            try:
                titulo_completo = html.unescape(item.title)
                
                # O Google News formata o título assim: "Título da Matéria - Nome do Veículo"
                # Vamos separar o título do veículo para manter seu Placar de Furos perfeito!
                if " - " in titulo_completo:
                    partes = titulo_completo.rsplit(" - ", 1)
                    titulo_limpo = partes[0].strip()
                    veiculo = partes[1].strip()
                else:
                    titulo_limpo = titulo_completo
                    veiculo = "Google News"

                # Filtra para focar apenas nos veículos que você monitora
                veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1"]
                # Se o veículo não estiver explicitamente na lista, chamamos de "Outros" ou aceitamos todos
                if not any(v.lower() in veiculo.lower() for v in veiculos_alvo):
                    # Se quiser aceitar qualquer veículo do Brasil, comente a linha abaixo
                    continue 

                if hasattr(item, "published_parsed") and item.published_parsed:
                    data_iso = datetime(*item.published_parsed[:6]).isoformat()
                else:
                    data_iso = datetime.now().isoformat()

                noticia = {
                    "veiculo": veiculo,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_iso,
                    "data_coleta": datetime.now().isoformat()
                }

                insert_news(noticia)
                print(f"✅ [Hub] Salvo {veiculo}: {titulo_limpo}")
                contador += 1

            except Exception as e:
                continue
                
        print(f"🏁 Coleta via Hub finalizada. {contador} novas notícias injetadas no banco!")

    except Exception as e:
        print(f"❌ Erro na conexão com o Hub: {e}")

if __name__ == "__main__":
    coletar_via_google_news()
