import feedparser
import requests
import html
import urllib.parse
from datetime import datetime
import dateutil.parser  # Certifique-se de que python-dateutil está no requirements.txt, ou o pandas resolve

from database import insert_news

def coletar_via_google_news():
    # Buscaremos termos chave que englobam as pautas dos grandes portais brasileiros
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    
    # URL do feed oficial do Google News Brasil
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("📡 Conectando ao super hub do Google News...")
    try:
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        rss = feedparser.parse(resposta.text)

        if not rss.entries:
            print("❌ O hub do Google retornou vazio.")
            return

        print(f"🔥 Sucesso! Encontramos {len(rss.entries)} notícias no hub.")
        
        # VEÍCULOS ALVO ATUALIZADOS: Adicionados O Globo e Valor Econômico!
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        
        contador = 0
        for item in rss.entries:
            try:
                titulo_completo = html.unescape(item.title)
                
                # Separa o título do veículo ("Matéria - Nome do Veículo")
                if " - " in titulo_completo:
                    partes = titulo_completo.rsplit(" - ", 1)
                    titulo_limpo = partes[0].strip()
                    veiculo = partes[1].strip()
                else:
                    titulo_limpo = titulo_completo
                    veiculo = "Google News"

                # Normalização de nomes para bater com a sua lista (evita "O Globo - Política" etc)
                veiculo_encontrado = None
                for v in veiculos_alvo:
                    if v.lower() in veiculo.lower():
                        veiculo_encontrado = v
                        break

                if not veiculo_encontrado:
                    continue  # Pula portais que não estão na sua lista

                # 📅 TRATAMENTO DE DATA BLINDADO PARA O GOOGLE NEWS
                data_iso = None
                
                # Tenta pegar pelos atributos nativos do feedparser primeiro
                if hasattr(item, "published"):
                    try:
                        # O dateutil.parser consegue ler textos como "Fri, 05 Jun 2026..." perfeitamente
                        dt = dateutil.parser.parse(item.published)
                        data_iso = dt.isoformat()
                    except:
                        pass
                
                if not data_iso and hasattr(item, "published_parsed") and item.published_parsed:
                    try:
                        data_iso = datetime(*item.published_parsed[:6]).isoformat()
                    except:
                        pass
                
                # Se tudo falhar, joga a hora atual para não deixar em branco de jeito nenhum
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
                
        print(f"🏁 Coleta via Hub finalizada. {contador} notícias injetadas no banco!")

    except Exception as e:
        print(f"❌ Erro na conexão com o Hub: {e}")

if __name__ == "__main__":
    coletar_via_google_news()
