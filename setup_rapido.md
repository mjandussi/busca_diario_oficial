# Setup Rápido - PostgreSQL Porta 5433

## Seu PostgreSQL está na porta 5433!

Todos os comandos devem incluir `-p 5433`

## Passo 1: Criar arquivo .env

Copie o template:
```bash
copy .env.local.example .env
```

Edite o `.env` e preencha com estes valores:

```env
# Email (use suas credenciais reais)
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_app_password_16_digitos
EMAIL_RECIPIENTS=seu_email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# PostgreSQL - PORTA 5433!
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=decreto_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_postgres_aqui

# Busca
SEARCH_TERM=46930

# Selenium
HEADLESS=false
```

## Passo 2: Executar comandos na ordem

```bash
# 1. Criar banco (vai pedir senha do postgres)
psql -U postgres -p 5433 -c "CREATE DATABASE decreto_test;"

# 2. Criar tabelas
psql -U postgres -p 5433 -d decreto_test -f schema.sql

# 3. Popular dados históricos
psql -U postgres -p 5433 -d decreto_test -f setup_test_database.sql

# 4. Testar conexão Python
python test_connection.py

# 5. Executar script principal
python busca_decreto_receita_despesa.py
```

## Alternativa: Usar o arquivo .bat

```bash
.\criar_banco.bat
```

Depois continuar com os passos 2-5 acima.
