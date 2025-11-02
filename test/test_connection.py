"""
Script de teste de conexão com PostgreSQL
Execute para verificar se as credenciais estão corretas e o banco está acessível
"""

import os
from dotenv import load_dotenv
import psycopg

# Carregar variáveis de ambiente
load_dotenv()

def test_database_connection():
    """Testa conexão com PostgreSQL e mostra dados atuais"""
    try:
        # Tentar conectar
        dsn = os.getenv("POSTGRES_DSN")
        if dsn:
            conn = psycopg.connect(dsn)
        else:
            conn = psycopg.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5433"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )

        print("=" * 60)
        print("✅ CONEXÃO COM POSTGRESQL OK!")
        print("=" * 60)

        # Verificar se as tabelas existem
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('decree_publications', 'notifications_log')
                ORDER BY table_name
            """)
            tables = cur.fetchall()

            if len(tables) == 0:
                print("\n⚠️  ATENÇÃO: Tabelas não encontradas!")
                print("Execute primeiro: psql -U postgres -d decreto_test -f schema.sql")
                conn.close()
                return

            print(f"\n✅ Tabelas encontradas: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")

            # Contar publicações
            cur.execute("SELECT COUNT(*) FROM decree_publications")
            count = cur.fetchone()[0]
            print(f"\n📊 Total de publicações na base: {count}")

            if count == 0:
                print("\n💡 Dica: Execute o script de setup para popular dados de teste:")
                print("   psql -U postgres -d decreto_test -f setup_test_database.sql")
            else:
                # Mostrar datas
                cur.execute("""
                    SELECT
                        publication_date,
                        search_term,
                        first_seen_at
                    FROM decree_publications
                    ORDER BY publication_date DESC
                """)
                dates = cur.fetchall()

                print("\n📅 Datas no banco (histórico):")
                print("-" * 60)
                for date, term, discovered in dates:
                    print(f"   {date.strftime('%d/%m/%Y')} | Termo: {term} | Descoberta: {discovered.strftime('%d/%m/%Y %H:%M')}")

            # Verificar notificações
            cur.execute("SELECT COUNT(*) FROM notifications_log")
            notif_count = cur.fetchone()[0]
            print(f"\n📧 Total de notificações enviadas: {notif_count}")

        conn.close()
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)

    except psycopg.OperationalError as e:
        print("=" * 60)
        print("❌ ERRO DE CONEXÃO COM POSTGRESQL")
        print("=" * 60)
        print(f"\nDetalhes: {e}")
        print("\n🔧 Verifique:")
        print("   1. PostgreSQL está rodando?")
        print("   2. Credenciais no .env estão corretas?")
        print("   3. Banco de dados 'decreto_test' existe?")
        print("\n💡 Para criar o banco:")
        print("   psql -U postgres -c 'CREATE DATABASE decreto_test;'")

    except Exception as e:
        print("=" * 60)
        print("❌ ERRO INESPERADO")
        print("=" * 60)
        print(f"\nDetalhes: {e}")


if __name__ == "__main__":
    # Verificar se .env existe
    if not os.path.exists(".env"):
        print("=" * 60)
        print("⚠️  ARQUIVO .env NÃO ENCONTRADO")
        print("=" * 60)
        print("\n1. Copie o arquivo de exemplo:")
        print("   copy .env.local.example .env")
        print("\n2. Edite o .env com suas credenciais")
        print("\n3. Execute este script novamente")
        exit(1)

    test_database_connection()
