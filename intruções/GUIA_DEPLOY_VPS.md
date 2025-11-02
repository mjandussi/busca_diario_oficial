# Guia de Deploy na VPS (Easy Panel)

Este guia mostra como fazer o deploy completo na sua VPS após testar localmente.

## Pré-requisitos

- [x] Testes locais concluídos com sucesso
- [x] VPS com Easy Panel configurado
- [x] PostgreSQL rodando na VPS
- [x] Acesso SSH à VPS

---

## Parte 1: Preparar Código para Deploy

### 1.1 Commit e Push do código

No seu computador local:

```bash
# Verificar status
git status

# Adicionar arquivos
git add .

# Commit
git commit -m "Refatoração completa: PostgreSQL + detecção inteligente + modo headless"

# Push para o repositório
git push origin main
```

**IMPORTANTE:** Nunca faça commit do arquivo `.env` (ele já está no `.gitignore`)

---

## Parte 2: Configurar PostgreSQL na VPS

### 2.1 Conectar via SSH

```bash
ssh usuario@seu-servidor-vps.com
```

### 2.2 Criar banco de dados

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar banco
CREATE DATABASE decreto_oficial;

# Criar usuário dedicado (opcional, mais seguro)
CREATE USER decreto_user WITH PASSWORD 'senha_forte_aqui';

# Dar permissões
GRANT ALL PRIVILEGES ON DATABASE decreto_oficial TO decreto_user;

# Sair
\q
```

### 2.3 Executar scripts SQL

```bash
# Transferir arquivos SQL para VPS (do seu PC local)
scp schema.sql usuario@vps:/home/usuario/

# Na VPS, executar
psql -U decreto_user -d decreto_oficial -f schema.sql
```

**Resultado esperado:**
```
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
```

---

## Parte 3: Deploy do Código

### 3.1 Clonar repositório na VPS

```bash
# Navegar para o diretório de apps
cd /home/usuario/apps
# ou conforme configuração do Easy Panel

# Clonar
git clone https://github.com/seu-usuario/busca_diario_oficial.git
cd busca_diario_oficial
```

### 3.2 Criar ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.3 Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Instalar Chrome/Chromium

```bash
# Atualizar repositórios
sudo apt update

# Instalar Chromium e ChromeDriver
sudo apt install -y chromium chromium-driver

# Verificar instalação
chromium --version
chromedriver --version
```

**Se houver erro de permissões do webdriver-manager:**

```bash
# Criar diretório para cache do driver
mkdir -p ~/.wdm
chmod 755 ~/.wdm
```

---

## Parte 4: Configurar Secrets no Easy Panel

### 4.1 Acessar Easy Panel

1. Login no Easy Panel: `https://seu-dominio.com:3000`
2. Vá para o serviço/app do projeto
3. Clique em **Environment** ou **Secrets**

### 4.2 Adicionar variáveis de ambiente

Adicione as seguintes variáveis:

```env
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_app_password_16_digitos
EMAIL_RECIPIENTS=destinatario1@gov.br,destinatario2@gov.br
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=decreto_oficial
POSTGRES_USER=decreto_user
POSTGRES_PASSWORD=senha_forte_aqui

# Ou use DSN (mais limpo):
# POSTGRES_DSN=postgresql://decreto_user:senha@localhost:5432/decreto_oficial

SEARCH_TERM=46930
HEADLESS=true
```

**IMPORTANTE:** No Easy Panel, use o **Secrets Manager** ao invés de arquivo `.env`

---

## Parte 5: Teste Manual na VPS

### 5.1 Executar uma vez manualmente

```bash
# Ativar ambiente virtual (se não estiver ativo)
source .venv/bin/activate

# Executar
python busca_decreto_receita_despesa.py
```

**Logs esperados:**

```
============================================================
Iniciando execução do scraper do Decreto 46930
============================================================
Chrome configurado em modo headless
Iniciando busca por '46930' no DOERJ
...
Email enviado com sucesso para 2 destinatário(s)
Processo concluído: X novas publicações notificadas
============================================================
```

### 5.2 Verificar log

```bash
cat decreto_scraper.log
```

### 5.3 Verificar banco de dados

```bash
psql -U decreto_user -d decreto_oficial

# No psql:
SELECT * FROM decree_publications ORDER BY publication_date DESC;
\q
```

---

## Parte 6: Configurar Agendamento (Cron)

### Opção A: Via Easy Panel (Recomendado)

1. No Easy Panel, vá em **Cron Jobs** ou **Scheduler**
2. Clique em **Add Cron Job**
3. Preencha:
   - **Name:** Busca Decreto 46930
   - **Schedule:** `30 11 * * *` (11:30 todo dia)
   - **Command:** `/home/usuario/apps/busca_diario_oficial/.venv/bin/python /home/usuario/apps/busca_diario_oficial/busca_decreto_receita_despesa.py`
   - **Working Directory:** `/home/usuario/apps/busca_diario_oficial`
4. Salvar

### Opção B: Via Crontab Manual

```bash
# Editar crontab
crontab -e

# Adicionar linha (ajuste os caminhos):
30 11 * * * /home/usuario/apps/busca_diario_oficial/.venv/bin/python /home/usuario/apps/busca_diario_oficial/busca_decreto_receita_despesa.py >> /var/log/decreto.log 2>&1
```

**Verificar cron configurado:**
```bash
crontab -l
```

---

## Parte 7: Monitoramento e Manutenção

### 7.1 Configurar rotação de logs

```bash
# Criar arquivo de configuração do logrotate
sudo nano /etc/logrotate.d/decreto-scraper
```

Conteúdo:
```
/home/usuario/apps/busca_diario_oficial/decreto_scraper.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 usuario usuario
}
```

### 7.2 Monitorar logs em tempo real

```bash
# Ver logs do script
tail -f /home/usuario/apps/busca_diario_oficial/decreto_scraper.log

# Ver logs do cron (se usar Opção B)
tail -f /var/log/decreto.log
```

### 7.3 Verificar última execução

```bash
# Ver últimas linhas do log
tail -50 decreto_scraper.log | grep "Execução finalizada"

# Ver no banco
psql -U decreto_user -d decreto_oficial -c "
SELECT
    publication_date,
    first_seen_at
FROM decree_publications
WHERE first_seen_at > NOW() - INTERVAL '24 hours'
ORDER BY first_seen_at DESC;
"
```

---

## Parte 8: Troubleshooting na VPS

### Problema: Chrome não funciona em headless

**Erro:** "selenium.common.exceptions.WebDriverException: Message: unknown error: Chrome failed to start"

**Solução:**
```bash
# Instalar dependências faltantes
sudo apt install -y libnss3 libgconf-2-4 libxss1 libasound2

# Testar Chrome
chromium --headless --disable-gpu --dump-dom https://www.google.com
```

### Problema: Permissão negada no diretório .wdm

**Erro:** "PermissionError: [Errno 13] Permission denied: '/root/.wdm'"

**Solução:**
```bash
# Criar diretório com permissões corretas
mkdir -p ~/.wdm
chmod -R 755 ~/.wdm

# Ou definir variável de ambiente
export WDM_LOCAL=1
```

### Problema: Email não está sendo enviado

**Checklist:**
- [ ] App Password está correto no secrets do Easy Panel
- [ ] Porta 587 está liberada no firewall
- [ ] Verificar logs: `grep "Email enviado" decreto_scraper.log`

**Testar SMTP manualmente:**
```python
# Criar test_smtp.py
import smtplib
import ssl
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = 'Teste VPS'
msg['From'] = 'seu_email@gmail.com'
msg['To'] = 'seu_email@gmail.com'
msg.set_content('Teste de envio da VPS')

context = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls(context=context)
    server.login('seu_email@gmail.com', 'app_password_aqui')
    server.send_message(msg)
print("Email enviado!")
```

### Problema: Cron não executa

**Verificar:**
```bash
# Ver logs do cron
sudo grep CRON /var/log/syslog

# Testar comando manualmente
/home/usuario/apps/busca_diario_oficial/.venv/bin/python /home/usuario/apps/busca_diario_oficial/busca_decreto_receita_despesa.py
```

**Dica:** No cron, as variáveis de ambiente podem não estar carregadas. Use caminhos absolutos.

---

## Parte 9: Atualizar Código na VPS

Quando fizer mudanças no código:

```bash
# Na VPS
cd /home/usuario/apps/busca_diario_oficial

# Fazer backup do .env (se existir)
cp .env .env.backup

# Atualizar código
git pull origin main

# Reinstalar dependências (se houver mudanças)
source .venv/bin/activate
pip install -r requirements.txt

# Restaurar .env (se necessário)
cp .env.backup .env

# Testar
python busca_decreto_receita_despesa.py
```

---

## Parte 10: Backup e Recuperação

### 10.1 Backup do banco de dados

```bash
# Criar backup
pg_dump -U decreto_user -d decreto_oficial > backup_decreto_$(date +%Y%m%d).sql

# Compactar
gzip backup_decreto_$(date +%Y%m%d).sql
```

### 10.2 Restaurar backup

```bash
# Descompactar
gunzip backup_decreto_20251102.sql.gz

# Restaurar
psql -U decreto_user -d decreto_oficial < backup_decreto_20251102.sql
```

### 10.3 Automatizar backup (cron)

```bash
crontab -e

# Adicionar (backup diário às 23:00):
0 23 * * * pg_dump -U decreto_user decreto_oficial | gzip > /home/usuario/backups/decreto_$(date +\%Y\%m\%d).sql.gz
```

---

## Parte 11: Consultas Úteis (Produção)

### Ver estatísticas

```sql
-- Publicações por mês
SELECT
    DATE_TRUNC('month', publication_date) as mes,
    COUNT(*) as total
FROM decree_publications
GROUP BY mes
ORDER BY mes DESC;

-- Novas publicações hoje
SELECT * FROM decree_publications
WHERE first_seen_at::date = CURRENT_DATE;

-- Histórico de execuções (via logs)
```

### Limpar dados antigos (se necessário)

```sql
-- Manter apenas últimos 2 anos
DELETE FROM decree_publications
WHERE publication_date < CURRENT_DATE - INTERVAL '2 years';
```

---

## Checklist de Deploy Completo

- [ ] Código commitado e pusheado
- [ ] PostgreSQL configurado na VPS
- [ ] Tabelas criadas (schema.sql)
- [ ] Repositório clonado na VPS
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Chromium/ChromeDriver instalado
- [ ] Secrets configurados no Easy Panel
- [ ] Teste manual executado com sucesso
- [ ] Email de teste recebido
- [ ] Cron configurado
- [ ] Logs sendo gerados corretamente
- [ ] Rotação de logs configurada
- [ ] Backup automático configurado

---

## Resumo do Fluxo de Deploy

```
1. Local: Commit e push
   ↓
2. VPS: Criar banco PostgreSQL
   ↓
3. VPS: Executar schema.sql
   ↓
4. VPS: git clone
   ↓
5. VPS: Criar .venv e pip install
   ↓
6. VPS: Instalar chromium
   ↓
7. Easy Panel: Configurar secrets
   ↓
8. VPS: Teste manual
   ↓
9. Easy Panel: Configurar cron
   ↓
10. Monitorar logs
```

**Deploy concluído!** O sistema rodará automaticamente todo dia às 11:30. 🎉

---

## Próximos Passos (Opcional)

- [ ] Configurar alerta via Telegram/Slack além de email
- [ ] Criar dashboard web para visualizar histórico
- [ ] Adicionar mais decretos para monitorar
- [ ] Implementar healthcheck endpoint
- [ ] Configurar notificação se o scraper falhar
