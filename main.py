from database import create_table, insert_news
from folha import coletar_folha
from poder360 import get_news as poder360_news
# Importando o novo super hub que criamos no arquivo uol.py
from uol import coletar_via_google_news

def main():
    # Garante que a tabela do banco de dados existe antes de começar
    create_table()

    print("=== INICIANDO ROTINA DE COLETA BLINDADA ===")

    # 1. COLETA DA FOLHA (Direta, pois não bloqueia o GitHub)
    try:
        print("\n📰 Coletando Folha de S.Paulo...")
        coletar_folha()
    except Exception as e:
        print(f"❌ Erro ao coletar a Folha: {e}")

    # 2. COLETA VIA HUB GOOGLE NEWS (Traz UOL, Estadão, CNN, JOTA sem bloqueio)
    try:
        print("\n📡 Coletando via Super Hub do Google News (UOL, Estadão, CNN, JOTA)...")
        coletar_via_google_news()
    except Exception as e:
        print(f"❌ Erro no Super Hub de notícias: {e}")

    # 3. COLETA DO PODER360
    try:
        print("\n🏛️ Coletando Poder360...")
        for item in poder360_news():
            try:
                insert_news(item)
            except Exception as e:
                print(f"❌ Erro ao inserir notícia do Poder360: {e}")
    except Exception as e:
        print(f"❌ Erro geral ao coletar o Poder360: {e}")

    print("\n🏁 === PROCESSO DE AUTOMAÇÃO FINALIZADO COM SUCESSO! ===")

if __name__ == "__main__":
    main()
