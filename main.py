from database import create_table
# Importa o funcionário da Folha (se o seu arquivo tiver outro nome, ajuste aqui)
from folha import sua_funcao_da_folha  
# Importa o NOSSO NOVO funcionário do Caminhão
from uol import coletar_via_google_news

def iniciar_coleta():
    print("🚀 Iniciando o robô de coleta...")
    
    # 1. Garante que o banco está criado
    create_table()
    
    # 2. Manda a Folha trabalhar
    try:
        print("📰 Coletando Folha...")
        sua_funcao_da_folha() # <- Mude para o nome real da sua função da folha
    except Exception as e:
        print(f"❌ Erro na Folha: {e}")
        
    # 3. MANDA O CAMINHÃO DO HUB TRABALHAR (UOL, GLOBO, ESTADÃO, ETC)
    try:
        print("🚛 Iniciando o Hub do Google News...")
        coletar_via_google_news()
    except Exception as e:
        print(f"❌ Erro no Hub: {e}")
        
    print("✅ Expediente encerrado! Todas as coletas terminaram.")

if __name__ == "__main__":
    iniciar_coleta()
