import feedparser
import requests
import html
import urllib.parse
from datetime import datetime, timedelta
import time
import re
from database import insert_many_news

# 🔴 TESTE: Se você vê isso, o arquivo CORRETO está rodando!
print("\n" + "="*80)
print("🔴 ARQUIVO uol_teste_simples.py INICIADO COM SUCESSO!")
print("="*80 + "\n")

def extrair_data_publicacao(item, numero_item=0):
    """Extrai data com muitos prints para debugar"""
    
    print(f"\n{'─'*80}")
    print(f"ITEM #{numero_item} - Extraindo data...")
    print(f"{'─'*80}")
    
    titulo = item.title if hasattr(item, "title") else "SEM TÍTULO"
    print(f"📰 Título: {titulo[:100]}...\n")
    
    # 1️⃣ ESTRATÉGIA 1: published_parsed
    print(f"1️⃣  Tentando 'published_parsed'...", end=" ")
    if hasattr(item, "published_parsed") and item.published_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.published_parsed))
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ SUCESSO! {resultado}")
            return resultado
        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print(f"❌ Campo vazio ou não existe")
    
    # 2️⃣ ESTRATÉGIA 2: published (string)
    print(f"2️⃣  Tentando 'published' (string)...", end=" ")
    if hasattr(item, "published") and item.published:
        print(f"(valor: '{item.published}')")
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
                print(f"   ✅ SUCESSO com formato '{fmt}': {resultado}")
                return resultado
            except:
                pass
        print(f"   ❌ Nenhum formato funcionou")
    else:
        print(f"❌ Campo vazio ou não existe")
    
    # 3️⃣ ESTRATÉGIA 3: updated_parsed
    print(f"3️⃣  Tentando 'updated_parsed'...", end=" ")
    if hasattr(item, "updated_parsed") and item.updated_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(item.updated_parsed))
            resultado = dt.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ SUCESSO! {resultado}")
            return resultado
        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print(f"❌ Campo vazio ou não existe")
    
    # 4️⃣ ESTRATÉGIA 4: Summary
    print(f"4️⃣  Procurando em 'summary'...", end=" ")
    if hasattr(item, "summary") and item.summary:
        summary_limpo = html.unescape(item.summary)
        summary_limpo = re.sub(r'<[^>]+>', '', summary_limpo)
        print(f"('{summary_limpo[:80]}...')")
        
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
            print(f"   ✅ SUCESSO! Encontrado '{quantidade} {unidade}' atrás: {resultado}")
            return resultado
        else:
            print(f"   ❌ Nenhum padrão 'há X tempo' encontrado")
    else:
        print(f"❌ Campo vazio ou não existe")
    
    # 5️⃣ ESTRATÉGIA 5: Title
    print(f"5️⃣  Procurando em 'title'...", end=" ")
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
            print(f"✅ SUCESSO! {resultado}")
            return resultado
        else:
            print(f"❌ Nenhum padrão encontrado")
    else:
        print(f"❌ Campo vazio ou não existe")
    
    # FALHA
    print(f"\n🚨 NENHUMA ESTRATÉGIA FUNCIONOU! Será usado fallback (data de coleta)")
    return None

def coletar_via_google_news():
    print("\n" + "="*80)
    print("🚛 INICIANDO O HUB DO GOOGLE NEWS (VERSÃO COM DEBUG)")
    print("="*80)
    
    termo_busca = "Lula OR governo OR STF OR economia OR política"
    termo_codificado = urllib.parse.quote(termo_busca)
    url_feed = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        print(f"\n📡 Conectando ao Google News...")
        resposta = requests.get(url_feed, headers=headers, timeout=15)
        print(f"✅ Conectado! Status: {resposta.status_code}\n")
        
        rss = feedparser.parse(resposta.text)
        print(f"📊 Total de entradas encontradas: {len(rss.entries)}\n")
        
        if not rss.entries: 
            print("❌ Nenhuma entrada encontrada!")
            return
        
        veiculos_alvo = ["UOL", "Folha de S.Paulo", "Estadão", "CNN Brasil", "JOTA", "Poder360", "G1", "O Globo", "Valor Econômico"]
        noticias_para_salvar = []
        
        # PROCESSAMENTO COM DEBUG
        for idx, item in enumerate(rss.entries):
            try:
                titulo_completo = html.unescape(item.title)
                veiculo_origem = item.source.title if hasattr(item, "source") and "title" in item.source else "Google News"
                veiculo_encontrado = next((v for v in veiculos_alvo if v.lower() in veiculo_origem.lower() or v.lower() in titulo_completo.lower()), None)
                
                if not veiculo_encontrado:
                    print(f"❌ REJEITADO: Veículo '{veiculo_origem}' não está na lista\n")
                    continue
                
                titulo_limpo = titulo_completo.rsplit(" - ", 1)[0].strip() if " - " in titulo_completo else titulo_completo
                
                # EXTRAI DATA COM DEBUG COMPLETO
                data_publicacao = extrair_data_publicacao(item, idx)
                
                # Fallback
                if not data_publicacao:
                    data_publicacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"⚠️  Usando fallback (data de coleta): {data_publicacao}\n")
                
                noticia = {
                    "veiculo": veiculo_encontrado,
                    "titulo": titulo_limpo,
                    "autor": "Redação",
                    "url": item.link,
                    "data_publicacao": data_publicacao,
                    "data_coleta": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                noticias_para_salvar.append(noticia)
                print(f"✅ ACEITO: {veiculo_encontrado} - {titulo_limpo[:60]}...\n")
                
            except Exception as e:
                print(f"❌ ERRO ao processar item: {e}\n")
                continue
        
        # RESUMO
        print("\n" + "="*80)
        print(f"📊 RESUMO FINAL")
        print("="*80)
        print(f"✅ Notícias ACEITAS: {len(noticias_para_salvar)}")
        print(f"📦 Salvando no Supabase...\n")
        
        insert_many_news(noticias_para_salvar)
        print(f"🚚 SUCESSO! {len(noticias_para_salvar)} notícias injetadas!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    coletar_via_google_news()
