import feedparser
import requests
import html
import urllib.parse
from datetime import datetime, timedelta
import time
import re
from database import insert_many_news

print("\n" + "="*80)
print("🔴 ARQUIVO uol_debug_insert.py INICIADO!")
print("="*80 + "\n")

def extrair_data_publicacao(item, numero_item=0):
    """Extrai data com debug"""
    
    titulo = item.title if hasattr(item, "title") else "SEM TÍTULO"
    
    # 1️⃣ published_parsed
    if hasattr(item, "published_parsed") and item.published_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.published_parsed))
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            return resultado
        except:
            pass
    
    # 2️⃣ published (string)
    if hasattr(item, "published") and item.published:
        formatos = [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S GMT',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]
        for fmt in formatos:
            try:
                dt = datetime.strptime(item.published, fmt)
                resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
                return resultado
            except:
                pass
    
    # 3️⃣ updated_parsed
    if hasattr(item, "updated_parsed") and item.updated_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.updated_parsed))
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            return resultado
        except:
            pass
    
    # 4️⃣ Summary
    if hasattr(item, "summary") and item.summary:
        summary_limpo = html.unescape(item.summary)
        summary_limpo = re.sub(r'<[^>]+>', '', summary_limpo)
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
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            return resultado
    
    # 5️⃣ Title
    if hasattr(item, "title") and item.title:
        title = item.title.lower()
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
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            return resultado
    
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
            return
        
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        noticias_para_salvar = []
        
        for idx, item in enumerate(rss.entries):
            try:
                titulo_completo = html.unescape(item.title)
                veiculo_origem = item.source.title if hasattr(item, "source") and "title" in item.source else "Google News"
                veiculo_encontrado = next((v for v in veiculos_alvo if v.lower() in veiculo_origem.lower() or v.lower() in titulo_completo.lower()), None)
                
                if not veiculo_encontrado:
                    continue
                
                titulo_limpo = titulo_completo.rsplit(" - ", 1)[0].strip() if " - " in titulo_completo else titulo_completo
                
                # EXTRAI DATA
                data_publicacao = extrair_data_publicacao(item, idx)
                
                if not data_publicacao:
                    data_publicacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 🔍 DEBUG: MOSTRA O QUE VAI SER SALVO
                print(f"\n{'─'*80}")
                print(f"NOTÍCIA #{len(noticias_para_salvar) + 1}")
                print(f"{'─'*80}")
                print(f"Veículo: {veiculo_encontrado}")
                print(f"Título: {titulo_limpo[:80]}...")
                print(f"📅 DATA_PUBLICACAO (ANTES DE SALVAR): {data_publicacao}")
                print(f"🕐 DATA_COLETA (AGORA): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                noticia = {
                    "veiculo": veiculo_encontrado,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_publicacao,
                    "data_coleta": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"\n📦 DICT QUE SERÁ SALVO:")
                for chave, valor in noticia.items():
                    print(f"   {chave}: {valor}")
                
                noticias_para_salvar.append(noticia)
                
            except Exception as e:
                print(f"❌ ERRO: {e}")
                continue
        
        # 🔍 DEBUG: ANTES DE CHAMAR INSERT
        print("\n" + "="*80)
        print(f"🔍 DEBUG: ANTES DE CHAMAR insert_many_news()")
        print("="*80)
        print(f"Total de notícias a salvar: {len(noticias_para_salvar)}\n")
        
        # Mostra as primeiras 3 notícias que vão ser salvas
        for i, noticia in enumerate(noticias_para_salvar[:3]):
            print(f"Notícia #{i+1}:")
            print(f"  data_publicacao: {noticia['data_publicacao']}")
            print(f"  data_coleta: {noticia['data_coleta']}")
            print()
        
        # CHAMA A FUNÇÃO DE INSERT
        print("\n" + "="*80)
        print("📤 CHAMANDO insert_many_news()...")
        print("="*80 + "\n")
        
        insert_many_news(noticias_para_salvar)
        
        print(f"\n✅ Função insert_many_news() retornou com sucesso!")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    coletar_via_google_news()
