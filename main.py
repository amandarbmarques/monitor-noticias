from database import create_table, insert_news
from folha import coletar_folha
from estadao import coletar_estadao
from poder360 import get_news as poder360_news
# Novos imports
from uol import coletar_uol
from cnn import coletar_cnn
from jota import coletar_jota

def main():
    create_table()

    # --- COLETA DA FOLHA ---
    try:
        print("Coletando Folha...")
        coletar_folha()
    except Exception as e:
        print(f"❌ Erro ao coletar a Folha: {e}")

    # --- COLETA DO ESTADÃO ---
    try:
        print("Coletando Estadão...")
        coletar_estadao()
    except Exception as e:
        print(f"❌ Erro ao coletar o Estadão: {e}")

    # --- COLETA DO UOL ---
    try:
        print("Coletando UOL...")
        coletar_uol()
    except Exception as e:
        print(f"❌ Erro ao coletar o UOL: {e}")

    # --- COLETA DA CNN BRASIL ---
    try:
        print("Coletando CNN Brasil...")
        coletar_cnn()
    except Exception as e:
        print(f"❌ Erro ao coletar a CNN Brasil: {e}")

    # --- COLETA DO JOTA ---
    try:
        print("Coletando JOTA...")
        coletar_jota()
    except Exception as e:
        print(f"❌ Erro ao coletar o JOTA: {e}")

    # --- COLETA DO PODER360 ---
    try:
        print("Coletando Poder360...")
        for item in poder360_news():
            try:
                insert_news(item)
            except Exception as e:
                print(f"❌ Erro ao inserir notícia do Poder360: {e}")
    except Exception as e:
        print(f"❌ Erro geral ao coletar o Poder360: {e}")

    print("🏁 Processo de automação finalizado!")

if __name__ == "__main__":
    main()
