from database import create_table
from folha import coletar_folha
from uol import coletar_via_google_news

def iniciar_coleta():
    print("🚀 Iniciando o robô de coleta...")
    
    # 1. Cria a tabela no Supabase (se não existir)
    create_table()
    
    # 2. Manda a Folha trabalhar
    try:
        print("📰 Coletando Folha...")
        coletar_folha()
    except Exception as e:
        print(f"❌ Erro na Folha: {e}")
        
    # 3. Manda o Caminhão do Hub trabalhar (UOL, G1, Estadão, etc)
    try:
        print("🚛 Iniciando o Hub do Google News...")
        coletar_via_google_news()
    except Exception as e:
        print(f"❌ Erro no Hub: {e}")
        
    print("✅ Expediente encerrado! Todas as coletas terminaram.")

if __name__ == "__main__":
    iniciar_coleta()
