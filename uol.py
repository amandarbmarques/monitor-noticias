import feedparser
import requests
import html
import urllib.parse
from datetime import datetime, timedelta
import time
import re
from database import insert_many_news

def extrair_data_publicacao(item):
    """
    Tenta extrair a data de publicação de múltiplas fontes no item do feedparser.
    Google News RSS é meio chato, então tentamos várias estratégias.
    """
    
    # 1️⃣ Estratégia 1: published_parsed (ideal, mas nem sempre vem)
    if hasattr(item, "published_parsed") and item.published_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.published_parsed))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 2️⃣ Estratégia 2: Campo "published" (string)
    if hasattr(item, "published") and item.published:
        try:
            # Google News às vezes retorna algo como "Mon, 05 Jun 2024 14:30:00 GMT"
            dt = datetime.strptime(item.published, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 3️⃣ Estratégia 3: Campo "updated_parsed" (às vezes tem data atualizada)
    if hasattr(item, "updated_parsed") and item.updated_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.updated_parsed))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 4️⃣ Estratégia 4: Summary (Google News coloca a data aqui às vezes!)
    if hasattr(item, "summary") and item.summary:
        try:
            # Tira HTML tags
            summary_limpo = html.unescape(item.summary)
            summary_limpo = re.sub(r'<[^>]+>', '', summary_limpo)
            
            # Procura por padrões de data tipo "há 2 horas", "há 30 minutos", etc
            match = re.search(r'há (\d+)\s+(horas?|minutos?|dias?)', summary_limpo, re.IGNORECASE)
            if match:
                quantidade = int(match.group(1))
                unidade = match.group(2).lower()
                
                agora = datetime.now()
                if 'hora' in unidade:
                    dt = agora - timedelta(hours=quantidade)
                elif 'minuto' in unidade:
                    dt = agora - timedelta(minutes=quantidade)
                elif 'dia' in unidade:
                    dt = agora - timedelta(days=quantidade)
                
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 5️⃣ Estratégia 5: Análise do título (último recurso, mas funciona!)
    if hasattr(item, "title") and item.title:
        try:
            title = item.title.lower()
            # Procura padrões como "há 2 horas" ou "2h atrás"
            match = re.search(r'há (\d+)\s+(horas?|h|minutos?|min|dias?|d)\s+atrás', title)
            if match:
                quantidade = int(match.group(1))
                unidade = match.group(2).lower()
                
                agora = datetime.now()
                if 'hora' in unidade or 'h' == unidade:
                    dt = agora - timedelta(hours=quantidade)
                elif 'minuto' in unidade or 'min' in unidade:
                    dt = agora - timedelta(minutes=quantidade)
                elif 'dia' in unidade or 'd' == unidade:
                    dt = agora - timedelta(days=quantidade)
                
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 🚨 Se chegou aqui, nenhuma estratégia funcionou
    # Retorna None e o código principal vai lidar
    return None

def coletar_via_google_news():
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        rss = feedparser.parse(resposta.text)
        if not rss.entries: 
            print("❌ Nenhuma entrada encontrada no feed do Google News")
            return
        
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        noticias_para_salvar = []
        
        for item in rss.entries:
            try:
                titulo_completo = html.unescape(item.title)
                veiculo_origem = item.source.title if hasattr(item, "source") and "title" in item.source else "Google News"
                veiculo_encontrado = next((v for v in veiculos_alvo if v.lower() in veiculo_origem.lower() or v.lower() in titulo_completo.lower()), None)
                if not veiculo_encontrado: 
                    continue  
                
                titulo_limpo = titulo_completo.rsplit(" - ", 1)[0].strip() if " - " in titulo_completo else titulo_completo
                
                # 🎯 AQUI ESTÁ A MÁGICA NOVA!
                data_publicacao = extrair_data_publicacao(item)
                
                # Se mesmo assim não conseguiu a data, usa a coleta (último recurso)
                if not data_publicacao:
                    print(f"⚠️  Não consegui extrair data para: {titulo_limpo[:50]}... usando data de coleta")
                    data_publicacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                noticia = {
                    "veiculo": veiculo_encontrado,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_publicacao,  # ← DATA REAL AGORA!
                    "data_coleta": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                noticias_para_salvar.append(noticia)
                
            except Exception as e:
                print(f"⚠️  Erro ao processar item: {e}")
                continue
                
        print(f"📦 Enviando {len(noticias_para_salvar)} notícias filtradas para o Supabase...")
        insert_many_news(noticias_para_salvar)
        
    except Exception as e:
        print(f"❌ Erro na coleta via Google News: {e}")

if __name__ == "__main__":
    coletar_via_google_news()
