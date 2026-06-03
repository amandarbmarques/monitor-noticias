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

    print("Coletando Folha...")
    coletar_folha()

    print("Coletando Estadão...")
    coletar_estadao()

    print("Coletando UOL...")
    coletar_uol()

    print("Coletando CNN Brasil...")
    coletar_cnn()

    print("Coletando JOTA...")
    coletar_jota()

    print("Coletando Poder360...")
    for item in poder360_news():
        insert_news(item)

    print("Finalizado!")


if __name__ == "__main__":
    main()