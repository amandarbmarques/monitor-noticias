# author.py
import requests
from bs4 import BeautifulSoup
import json

def get_author(url):
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10
        )
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. TENTATIVA PADRÃO: JSON-LD (Funciona muito bem na Folha, UOL e CNN)
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if "author" in data:
                    author = data["author"]
                    if isinstance(author, list) and len(author) > 0:
                        return author[0]["name"]
                    if isinstance(author, dict):
                        return author["name"]
            except:
                continue

        # 2. PLANO B: Seletores HTML específicos (Caso o JSON-LD falhe ou para o JOTA)
        # Seletor JOTA (meta tag) ou classes comuns da CNN/UOL
        meta_author = soup.find("meta", {"name": "author"}) or soup.find("meta", {"property": "article:author"})
        if meta_author and meta_author.get("content"):
            return meta_author["content"].strip()
            
        # Classes CSS específicas
        html_author = soup.find(class_="jota__author") or soup.find(class_="author__name") or soup.find(class_="c-news__author")
        if html_author:
            return html_author.text.strip()

    except Exception:
        pass

    return "Não identificado"