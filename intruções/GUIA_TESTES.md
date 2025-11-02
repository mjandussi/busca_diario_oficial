# Guia de Testes - Busca Diário Oficial

Este guia mostra como testar o sistema **localmente** antes de subir para a VPS.

## Pré-requisitos

- [x] Python 3.11+ instalado
- [x] PostgreSQL instalado localmente
- [x] Google Chrome instalado
- [x] Conta Gmail com App Password configurado

---

## Parte 1: Configuração do Ambiente Local

### 1.1 Instalar PostgreSQL (se ainda não tiver)

**Windows:**
1. Baixe de [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Instale com as configurações padrão
3. Anote a senha do usuário `postgres`

**Verificar instalação:**
```bash
psql --version
```

### 1.2 Criar ambiente virtual Python

```bash
# No diretório do projeto
python -m venv .venv
```

**Ativar ambiente:**
```bash
# Windows
.venv\Scripts\activate

# Verificar ativação (deve mostrar (.venv) no prompt)
```

### 1.3 Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Parte 2: Configuração do Banco de Dados

### 2.1 Criar banco de dados de teste

Abra o **pgAdmin** ou **psql** e execute:

```sql
CREATE DATABASE decreto_test;
```

Ou via linha de comando:
```bash
psql -U postgres -c "CREATE DATABASE decreto_test;"
```

### 2.2 Executar script de criação das tabelas

```bash
psql -U postgres -d decreto_test -f schema.sql
```

Você deve ver:
```
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
...
```

### 2.3 Popular com dados históricos (base de teste)

```bash
psql -U postgres -d decreto_test -f setup_test_database.sql
```

Resultado esperado:
```
TRUNCATE TABLE
TRUNCATE TABLE
INSERT 0 4

 publication_date | search_term |       first_seen_at        | tempo_desde_descoberta
------------------+-------------+----------------------------+------------------------
 2025-10-06       | 46930       | 2025-10-13 ...             | 20 days ...
 2025-09-25       | 46930       | 2025-10-03 ...             | 30 days ...
 2025-09-10       | 46930       | 2025-09-18 ...             | 45 days ...
 2025-08-07       | 46930       | 2025-08-04 ...             | 60 days ...
```

---

## Parte 3: Configuração de Credenciais

### 3.1 Obter App Password do Gmail

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas** (ative se não estiver)
3. Role até **Senhas de app**
4. Selecione **App: Outro** → Digite "Decreto DOERJ"
5. **Copie a senha gerada** (16 caracteres)

### 3.2 Criar arquivo .env

```bash
# Copiar o template
copy .env.local.example .env
```

**Edite o arquivo `.env`** com seus dados reais:

```env
# Exemplo preenchido:
EMAIL_USER=seuemail@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop  # ← App Password de 16 dígitos
EMAIL_RECIPIENTS=seuemail@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=decreto_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_real

SEARCH_TERM=46930
HEADLESS=false  # ← false para ver o navegador
```

---

## Parte 4: Executar Testes

### 4.1 Teste de Conexão com Banco

Crie um arquivo `test_connection.py`:

```python
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

try:
    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    print("✅ Conexão com PostgreSQL OK!")

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM decree_publications")
        count = cur.fetchone()[0]
        print(f"✅ Total de publicações na base: {count}")

        cur.execute("SELECT publication_date FROM decree_publications ORDER BY publication_date DESC")
        dates = cur.fetchall()
        print("\n📅 Datas históricas (já no banco):")
        for d in dates:
            print(f"   - {d[0].strftime('%d/%m/%Y')}")

    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")
```

Execute:
```bash
python test_connection.py
```

**Resultado esperado:**
```
✅ Conexão com PostgreSQL OK!
✅ Total de publicações na base: 4

📅 Datas históricas (já no banco):
   - 06/10/2025
   - 25/09/2025
   - 10/09/2025
   - 07/08/2025
```

### 4.2 Executar Script Principal (TESTE REAL)

```bash
python busca_decreto_receita_despesa.py
```

**O que deve acontecer:**

1. **Navegador Chrome abre** (se HEADLESS=false)
2. Acessa o site do DOERJ
3. Preenche campo de busca com "46930"
4. Clica em buscar
5. Extrai as datas da página

**Logs esperados no console:**

```
============================================================
Iniciando execução do scraper do Decreto 46930
============================================================
Iniciando busca por '46930' no DOERJ
Campo de busca preenchido com '46930'
Botão de busca clicado
Encontradas 9 datas na busca
Navegador fechado
8 datas únicas após normalização
Conexão com banco de dados estabelecida
Nova publicação encontrada: 28/10/2025
Nova publicação encontrada: 16/10/2025
Nova publicação encontrada: 08/10/2025
3 novas publicações inseridas no banco
Email enviado com sucesso para 1 destinatário(s)
Processo concluído: 3 novas publicações notificadas
Conexão com banco fechada
============================================================
Execução finalizada com sucesso
============================================================
```

### 4.3 Verificar Email Recebido

Abra seu Gmail e verifique se recebeu um email com assunto:

```
ALERTA: Novas publicações do Decreto 46930
```

**Conteúdo esperado:**
```
Prezados,

Foram encontradas 3 nova(s) publicação(ões) do Decreto 46930 no Diário Oficial:

• 28/10/2025
• 16/10/2025
• 08/10/2025

Acesse o Diário Oficial para consultar os detalhes.

Mensagem automática gerada em 02/11/2025 às 14:30:00
```

### 4.4 Verificar Banco de Dados

Execute no pgAdmin ou psql:

```sql
-- Ver todas as publicações
SELECT
    publication_date,
    search_term,
    first_seen_at,
    AGE(NOW(), first_seen_at) as tempo_desde_descoberta
FROM decree_publications
ORDER BY publication_date DESC;
```

**Resultado esperado: 7 publicações totais**
- 3 antigas (inseridas há dias)
- 3 novas (inseridas agora)

```sql
-- Ver log de notificações
SELECT * FROM notifications_log ORDER BY sent_at DESC;
```

**Deve mostrar:** 1 registro (ainda não implementamos o log, mas a tabela existe)

---

## Parte 5: Teste de Idempotência (Re-execução)

### 5.1 Executar novamente o script

```bash
python busca_decreto_receita_despesa.py
```

**Resultado esperado:**
```
...
Encontradas 9 datas na busca
8 datas únicas após normalização
Conexão com banco de dados estabelecida
0 novas publicações inseridas no banco
Processo concluído: nenhuma nova publicação encontrada
...
```

**NÃO deve enviar email** (porque não há datas novas)

---

## Parte 6: Teste em Modo Headless (Simular VPS)

### 6.1 Editar .env

```env
HEADLESS=true  # ← mudar para true
```

### 6.2 Limpar banco e reexecutar

```bash
# Recriar base histórica
psql -U postgres -d decreto_test -f setup_test_database.sql

# Executar script
python busca_decreto_receita_despesa.py
```

**Agora o navegador NÃO deve abrir** (modo headless)

Logs devem incluir:
```
Chrome configurado em modo headless
```

---

## Parte 7: Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'psycopg'"

**Solução:**
```bash
# Certifique-se de estar no ambiente virtual
.venv\Scripts\activate

# Reinstale
pip install psycopg[binary]
```

### Erro: "connection to server at localhost (127.0.0.1), port 5432 failed"

**Solução:**
1. Verifique se o PostgreSQL está rodando:
   ```bash
   # Windows: Abrir "Serviços" e procurar "PostgreSQL"
   ```
2. Verifique a porta no `.env` (padrão: 5432)

### Erro: "ChromeDriver not found"

**Solução:**
```bash
pip install --upgrade webdriver-manager
```

### Email não chega

**Checklist:**
- [ ] Usou App Password (não senha normal)
- [ ] Verificação em 2 etapas está ativada no Gmail
- [ ] EMAIL_USER e EMAIL_PASSWORD corretos no `.env`
- [ ] Verificar pasta de SPAM

### Site retorna dados diferentes

**Motivo:** O site do DOERJ pode ter mais/menos publicações

**Solução:** Ajuste as datas no `setup_test_database.sql` conforme as datas reais que aparecem no site hoje

---

## Parte 8: Próximos Passos (Deploy VPS)

Após os testes locais funcionarem 100%, vá para o deploy na VPS:

1. Fazer commit e push do código
2. Clonar na VPS
3. Criar banco PostgreSQL na VPS
4. Configurar `.env` na VPS (usar Secrets do EasyPanel)
5. Instalar Chromium na VPS: `apt install chromium chromium-driver`
6. Configurar cron
7. Testar uma execução manual
8. Verificar logs

---

## Resumo do Fluxo de Teste

```
1. Setup banco (schema.sql + setup_test_database.sql)
   ↓
2. Configurar .env
   ↓
3. Testar conexão (test_connection.py)
   ↓
4. Executar script principal
   ↓
5. Verificar:
   - Logs no console ✅
   - Email recebido ✅
   - Dados no banco ✅
   ↓
6. Re-executar (não deve enviar email)
   ↓
7. Testar modo headless
   ↓
8. Deploy VPS
```

---

## Checklist de Validação

Antes de considerar o teste completo, verifique:

- [ ] PostgreSQL conectou com sucesso
- [ ] 4 datas históricas foram inseridas
- [ ] Script executou sem erros
- [ ] Navegador abriu e acessou o site (HEADLESS=false)
- [ ] Encontrou as datas corretas do site
- [ ] Detectou 3 datas novas (08/10, 16/10, 28/10)
- [ ] Enviou 1 email
- [ ] Email chegou na caixa de entrada
- [ ] Ao re-executar, NÃO enviou novo email
- [ ] Modo headless funciona (HEADLESS=true)
- [ ] Log foi criado (`decreto_scraper.log`)

**Tudo OK?** Você está pronto para o deploy na VPS! 🚀
