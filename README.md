# Busca Diário Oficial - Decreto 46930

Script automatizado para monitoramento de publicações do Decreto 46930 (Tabela de Classificação de Natureza de Receita e Despesas do Estado do RJ) no Diário Oficial do Estado do Rio de Janeiro.

## Funcionalidades

- **Scraping automático** do site do DOERJ
- **Armazenamento em PostgreSQL** com histórico de publicações
- **Detecção inteligente** de novas datas
- **Notificação por email** apenas quando há novas publicações
- **Modo headless** para execução em servidor VPS
- **Logging estruturado** para auditoria e debug

## Requisitos

- Python 3.11+
- PostgreSQL 12+
- Google Chrome ou Chromium (para o Selenium)
- Conta Gmail com App Password (para envio de emails)

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd busca_diario_oficial
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o banco de dados

Execute o script SQL para criar as tabelas:

```bash
psql -U seu_usuario -d seu_banco -f schema.sql
```

Ou conecte-se ao PostgreSQL e execute:

```sql
\i schema.sql
```

### 6. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Configurações de Email
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app_password_aqui
EMAIL_RECIPIENTS=destinatario1@example.com,destinatario2@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Configurações do PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nome_do_banco
POSTGRES_USER=usuario_postgres
POSTGRES_PASSWORD=senha_postgres

# Configurações de Busca
SEARCH_TERM=46930

# Configurações do Selenium
HEADLESS=true
```

### 7. Obtenha um App Password do Gmail

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas** (ative se não estiver ativada)
3. Role até **Senhas de app** e clique
4. Selecione **App: Outro** e dê um nome (ex: "Scraper DOERJ")
5. Copie a senha gerada e cole em `EMAIL_PASSWORD` no arquivo `.env`

## Uso

### Executar manualmente

```bash
python busca_decreto_receita_despesa.py
```

### Executar em modo headless (recomendado para VPS)

Certifique-se de que `HEADLESS=true` está configurado no `.env`:

```bash
python busca_decreto_receita_despesa.py
```

## Agendamento

### No Windows (Agendador de Tarefas)

1. Abra o **Agendador de Tarefas**
2. Clique em **Criar Tarefa Básica**
3. Configure para executar diariamente às 11:30
4. Ação: **Iniciar um programa**
   - Programa: `C:\caminho\para\.venv\Scripts\python.exe`
   - Argumentos: `busca_decreto_receita_despesa.py`
   - Iniciar em: `C:\caminho\para\busca_diario_oficial`

### No Linux/VPS (Cron)

Edite o crontab:

```bash
crontab -e
```

Adicione a linha (executa diariamente às 11:30):

```cron
30 11 * * * /caminho/para/.venv/bin/python /caminho/para/busca_diario_oficial/busca_decreto_receita_despesa.py >> /var/log/decreto.log 2>&1
```

### No Easy Panel (VPS)

1. **Via Cron Jobs do Easy Panel:**
   - Acesse o painel do Easy Panel
   - Vá em **Cron Jobs** ou **Scheduler**
   - Adicione um novo job:
     - Schedule: `30 11 * * *`
     - Command: `/caminho/para/.venv/bin/python /app/busca_decreto_receita_despesa.py`

2. **Via Dockerfile do container:**

Adicione ao seu `Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    cron

COPY crontab /etc/cron.d/decreto-cron
RUN chmod 0644 /etc/cron.d/decreto-cron
RUN crontab /etc/cron.d/decreto-cron
```

Crie um arquivo `crontab`:

```
30 11 * * * /app/.venv/bin/python /app/busca_decreto_receita_despesa.py >> /var/log/decreto.log 2>&1
```

## Estrutura do Banco de Dados

### Tabela `decree_publications`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `publication_date` | DATE | Data da publicação (PK) |
| `raw_title` | TEXT | Título completo (opcional) |
| `first_seen_at` | TIMESTAMPTZ | Quando foi detectada pela primeira vez |
| `search_term` | VARCHAR(50) | Termo de busca usado |

### Tabela `notifications_log`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | SERIAL | ID único |
| `publication_date` | DATE | Referência à publicação |
| `sent_at` | TIMESTAMPTZ | Quando o email foi enviado |
| `email_to` | TEXT | Destinatários |
| `status` | VARCHAR(20) | sent ou failed |
| `error_message` | TEXT | Mensagem de erro (se houver) |

## Logs

O script gera dois tipos de logs:

1. **Console/stdout**: Para execução interativa
2. **Arquivo `decreto_scraper.log`**: Para auditoria e debug

Formato do log:
```
2025-11-02 11:30:00 - INFO - Iniciando execução do scraper do Decreto 46930
2025-11-02 11:30:02 - INFO - Encontradas 15 datas na busca
2025-11-02 11:30:03 - INFO - Nova publicação encontrada: 25/10/2025
2025-11-02 11:30:04 - INFO - Email enviado com sucesso para 2 destinatário(s)
```

## Monitoramento e Troubleshooting

### Ver logs em tempo real (Linux/VPS)

```bash
tail -f decreto_scraper.log
```

### Verificar últimas publicações no banco

```sql
SELECT * FROM decree_publications ORDER BY publication_date DESC LIMIT 10;
```

### Verificar emails enviados

```sql
SELECT * FROM notifications_log ORDER BY sent_at DESC LIMIT 10;
```

### Problemas comuns

**Erro: "ChromeDriver not found"**
- Solução: Execute `pip install webdriver-manager` novamente
- Em VPS: Instale o Chrome/Chromium: `apt install chromium chromium-driver`

**Erro: "Permission denied" para webdriver-manager**
- Solução: Certifique-se de que o diretório `~/.wdm` tem permissão de escrita
- Alternativa: Defina `WDM_LOCAL=1` no `.env`

**Email não está sendo enviado**
- Verifique se usou App Password (não a senha normal do Gmail)
- Verifique se a verificação em 2 etapas está ativada
- Confira os logs para mensagens de erro

**Nenhuma data encontrada**
- Verifique se o site do DOERJ está acessível
- Teste manualmente em um navegador
- Aumente o timeout no código se necessário

## Segurança

- **NUNCA** versione o arquivo `.env` (já está no `.gitignore`)
- Use **App Passwords** do Gmail, não sua senha principal
- No Easy Panel, use **Secrets Manager** para variáveis sensíveis
- Limite permissões do usuário PostgreSQL (apenas INSERT/SELECT nas tabelas específicas)

## Consultas Úteis

### Ver todas as publicações novas hoje

```sql
SELECT * FROM recent_publications WHERE is_new = true;
```

### Contar publicações por mês

```sql
SELECT
    DATE_TRUNC('month', publication_date) as mes,
    COUNT(*) as total
FROM decree_publications
GROUP BY mes
ORDER BY mes DESC;
```

### Ver histórico de notificações

```sql
SELECT
    dp.publication_date,
    nl.sent_at,
    nl.status
FROM decree_publications dp
LEFT JOIN notifications_log nl ON dp.publication_date = nl.publication_date
ORDER BY dp.publication_date DESC;
```

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto é de uso interno para fins educacionais e de automação pessoal.

## Suporte

Para dúvidas ou problemas:
- Verifique os logs em `decreto_scraper.log`
- Consulte a seção de troubleshooting acima
- Abra uma issue no repositório
