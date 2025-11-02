# Guia de Deploy - EasyPanel (Hostinger VPS)

Este guia é específico para deploy no **EasyPanel da Hostinger**, usando a interface visual ao invés de comandos SSH.

---

## 📋 Pré-requisitos

- [x] Testes locais concluídos com sucesso ✅
- [x] VPS Hostinger ativa
- [x] EasyPanel instalado e acessível
- [x] Conta GitHub (para fazer deploy via Git)
- [x] App Password do Gmail configurado

---

## Parte 1: Preparar Repositório GitHub

### 1.1 Fazer commit de todos os arquivos

No seu PC local, no terminal do VS Code:

```bash
# Verificar arquivos modificados
git status

# Adicionar todos os arquivos (exceto .env que já está no .gitignore)
git add .

# Fazer commit
git commit -m "Deploy para EasyPanel: Script completo com PostgreSQL"

# Enviar para GitHub
git push origin main
```

**IMPORTANTE:** O arquivo `.env` NÃO será enviado (está no `.gitignore`). As credenciais serão configuradas direto no EasyPanel.

---

## Parte 2: Criar Banco de Dados PostgreSQL no EasyPanel

### 2.1 Acessar EasyPanel

1. Acesse seu EasyPanel: `https://seu-dominio-hostinger.com:3000`
2. Faça login

### 2.2 Criar serviço PostgreSQL

1. Clique em **+ Create Service** ou **New Service**
2. Selecione **Database** → **PostgreSQL**
3. Preencha:
   - **Name:** `decreto-rec-e-dps-postgres` (ou nome de sua preferência)
   - **Database:** `decreto-rec-e-dps`
   - **Username:** `postgres`
   - **Password:** Clique em **Generate** (copie a senha gerada!)
   - **Version:** `postgres:17` 
4. Clique em **Create**
5. **Aguarde** o PostgreSQL inicializar (status deve ficar verde)

### 2.3 Anotar credenciais

O EasyPanel vai gerar automaticamente:
- **Internal Hostname:** algo como `decreto-rec-e-dps-postgres` (use este para conexão interna)
- **Port:** `5432` (porta padrão interna)
- **Password:** A senha que foi gerada

**Anote tudo!** Você vai precisar para configurar as variáveis de ambiente.

---

## Parte 3: Criar Tabelas no Banco

### 3.1 Acessar console do PostgreSQL no EasyPanel

1. No serviço `decreto-postgres`, clique em **Console** ou **Terminal**
2. Execute:

```bash
psql -U postgres -d decreto-rec-e-dps
```

3. Cole o conteúdo do arquivo `schema.sql` (copie do seu PC)

**Ou se o EasyPanel permitir upload de arquivos:**

1. Clique em **Files** ou **File Manager**
2. Faça upload do `schema.sql`
3. No terminal, execute:

```bash
psql -U postgres -d decreto-rec-e-dps -f /path/to/schema.sql
```

### 3.2 Verificar tabelas criadas

No console psql:

```sql
\dt
-- Deve mostrar: decree_publications e notifications_log

\q
-- Sair
```

---

## Parte 4: Deploy do Script Python

### 4.1 Criar serviço App (Script Python)

1. No EasyPanel, clique em **+ Create Service**
2. Selecione **App** → **From GitHub**
3. Preencha:
   - **Name:** `decreto-scraper`
   - **Repository:** Conecte sua conta GitHub e selecione o repo `busca_diario_oficial`
   - **Branch:** `main`
   - **Build Method:** `Dockerfile` (vamos criar um)

### 4.2 Criar Dockerfile

Volte ao seu PC e crie o arquivo `Dockerfile`:

```dockerfile
# Use imagem Python slim
FROM python:3.11-slim

# Instalar dependências do sistema (Chrome headless)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretório para logs
RUN mkdir -p /var/log

# Comando padrão (para cron, não executa agora)
CMD ["tail", "-f", "/dev/null"]
```

Salve, faça commit e push:

```bash
git add Dockerfile
git commit -m "Adiciona Dockerfile para EasyPanel"
git push origin main
```

### 4.3 Configurar Build no EasyPanel

1. No serviço `decreto-scraper`, vá em **Build**
2. Dockerfile Path: `Dockerfile` (deve detectar automaticamente)
3. Clique em **Deploy** ou **Build**
4. Aguarde o build completar (pode levar alguns minutos)

---

## Parte 5: Configurar Variáveis de Ambiente (Secrets)

### 5.1 Adicionar Environment Variables

No serviço `decreto-scraper`, vá em **Environment** ou **Env Variables**.

Adicione cada variável abaixo:

#### Email

| Key | Value |
|-----|-------|
| `EMAIL_USER` | `seu_email@gmail.com` |
| `EMAIL_PASSWORD` | `sua_app_password_16_digitos` |
| `EMAIL_RECIPIENTS` | `destinatario1@gov.br,destinatario2@gov.br` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |

#### PostgreSQL (use as credenciais do Parte 2.3)

| Key | Value |
|-----|-------|
| `POSTGRES_HOST` | `decreto-postgres` ← hostname interno |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `decreto_oficial` |
| `POSTGRES_USER` | `decreto_user` |
| `POSTGRES_PASSWORD` | `senha_gerada_no_passo_2.2` |

#### Scraping

| Key | Value |
|-----|-------|
| `SEARCH_TERM` | `46930` |
| `HEADLESS` | `true` |

**IMPORTANTE:** Marque todas como **Secret** (ícone de cadeado) para proteger as senhas!

### 5.2 Salvar e Redeploy

1. Clique em **Save**
2. Clique em **Redeploy** para aplicar as variáveis

---

## Parte 6: Teste Manual

### 6.1 Executar uma vez manualmente

1. No serviço `decreto-scraper`, vá em **Console** ou **Terminal**
2. Execute:

```bash
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
Email enviado com sucesso
Processo concluído: X novas publicações notificadas
============================================================
```

### 6.2 Verificar email

- Deve chegar um email na caixa configurada
- Se não chegar, verifique:
  - App Password está correto?
  - Variável `EMAIL_PASSWORD` foi marcada como secret?
  - Verificar pasta SPAM

### 6.3 Verificar banco de dados

No console do PostgreSQL (`decreto-postgres`):

```bash
psql -U decreto_user -d decreto_oficial

# No psql:
SELECT * FROM decree_publications ORDER BY publication_date DESC;
```

Deve mostrar as datas encontradas!

---

## Parte 7: Agendar Execução Diária (Cron)

### 7.1 Configurar Cron Job no EasyPanel

1. No menu lateral, clique em **Cron Jobs** (pode estar em Settings ou Services)
2. Clique em **+ Add Cron Job** ou **Create**
3. Preencha:

   - **Name:** `Decreto 46930 - Scraping Diário`
   - **Service:** Selecione `decreto-scraper`
   - **Schedule:** `30 11 * * *` (11:30 todo dia)
   - **Command:** `python /app/busca_decreto_receita_despesa.py`
   - **Timezone:** `America/Sao_Paulo` (ou seu fuso)

4. Clique em **Save** ou **Create**

### 7.2 Formato do Schedule (Cron Expression)

```
30 11 * * *
│  │  │ │ │
│  │  │ │ └─ Dia da semana (0-6, Dom=0)
│  │  │ └─── Mês (1-12)
│  │  └───── Dia do mês (1-31)
│  └──────── Hora (0-23)
└─────────── Minuto (0-59)
```

**Exemplos:**

- `30 11 * * *` → Todo dia às 11:30
- `0 9,15 * * *` → 9h e 15h todo dia
- `30 11 * * 1-5` → 11:30 apenas em dias úteis (seg-sex)
- `0 */6 * * *` → A cada 6 horas

---

## Parte 8: Monitoramento

### 8.1 Ver logs em tempo real

1. No serviço `decreto-scraper`, clique em **Logs**
2. Deve mostrar as execuções do cron
3. Procure por:
   - `Execução finalizada com sucesso` ✅
   - `Email enviado com sucesso` ✅
   - Erros (se houver) ❌

### 8.2 Verificar última execução

No console do PostgreSQL:

```sql
-- Ver publicações descobertas hoje
SELECT
    publication_date,
    first_seen_at,
    AGE(NOW(), first_seen_at) as tempo
FROM decree_publications
WHERE first_seen_at::date = CURRENT_DATE
ORDER BY first_seen_at DESC;
```

### 8.3 Configurar alertas (Opcional)

No EasyPanel, você pode configurar:

1. **Notificações de falha:** Vá em Settings do serviço → Notifications
2. Adicione email ou webhook para ser avisado se o cron falhar

---

## Parte 9: Troubleshooting no EasyPanel

### Problema: Build falha com "Chrome not found"

**Solução:** Verifique se o Dockerfile tem as linhas:

```dockerfile
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*
```

Rebuild: Clique em **Rebuild** no EasyPanel.

### Problema: "Connection refused" ao conectar no PostgreSQL

**Causas possíveis:**

1. **Hostname errado:** Use o hostname interno (ex: `decreto-postgres`), NÃO `localhost`
2. **Serviços em projetos diferentes:** PostgreSQL e Script devem estar no mesmo **Project** do EasyPanel
3. **Port errado:** Use `5432` (porta interna), não `5433`

**Solução:**

1. Vá em Environment Variables
2. Confirme: `POSTGRES_HOST=decreto-postgres` (nome exato do serviço)
3. Confirme: `POSTGRES_PORT=5432`
4. Redeploy

### Problema: Email não está sendo enviado

**Checklist:**

- [ ] `EMAIL_PASSWORD` está marcado como **Secret**?
- [ ] App Password tem 16 dígitos (sem espaços)?
- [ ] `EMAIL_USER` está correto (email completo)?
- [ ] Porta 587 está liberada no firewall da Hostinger?

**Teste SMTP manualmente:**

No console do serviço, crie um arquivo `test_email.py`:

```python
import os
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = 'Teste EasyPanel'
msg['From'] = os.getenv('EMAIL_USER')
msg['To'] = os.getenv('EMAIL_USER')
msg.set_content('Teste de envio da VPS Hostinger')

with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
    server.starttls()
    server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
    server.send_message(msg)
print("Email enviado!")
```

Execute: `python test_email.py`

### Problema: Cron não executa

**Verificar:**

1. Cron Job está **ativo** (toggle ON)?
2. Schedule está correto? (usar [crontab.guru](https://crontab.guru/) para validar)
3. Timezone correto?
4. Verificar logs em **Logs** do serviço

### Problema: "Timeout" ao acessar site do DOERJ

**Solução:** Aumentar timeout no código (já está em 15s, pode aumentar para 30s)

Se persistir, verifique se a Hostinger não está bloqueando scraping.

---

## Parte 10: Atualizar Código

Quando fizer mudanças no código:

### Fluxo de atualização

```bash
# No seu PC:
git add .
git commit -m "Ajustes no scraper"
git push origin main

# No EasyPanel:
# 1. Vá no serviço decreto-scraper
# 2. Clique em "Rebuild" ou "Deploy"
# 3. Aguarde build completar
# 4. Pronto! Nova versão no ar
```

**O EasyPanel pode fazer deploy automático:**

1. Vá em Settings do serviço
2. Ative **Auto Deploy** (se disponível)
3. Toda vez que você fizer `git push`, ele faz deploy automaticamente

---

## Parte 11: Backup

### 11.1 Backup do Banco (Manual)

No console do PostgreSQL (`decreto-postgres`):

```bash
# Criar backup
pg_dump -U decreto_user decreto_oficial > backup_$(date +%Y%m%d).sql

# Baixar o arquivo
# Use a interface Files do EasyPanel para fazer download
```

### 11.2 Backup Automático (Cron)

Crie outro Cron Job:

- **Name:** Backup Banco Decreto
- **Service:** `decreto-postgres`
- **Schedule:** `0 23 * * *` (todo dia 23h)
- **Command:** `pg_dump -U decreto_user decreto_oficial > /backups/backup_$(date +\%Y\%m\%d).sql`

**IMPORTANTE:** Certifique-se de ter um volume persistente em `/backups`

---

## Parte 12: Estrutura Final no EasyPanel

Após tudo configurado, você terá:

```
📦 Projeto: Decreto DOERJ
│
├── 🗄️ decreto-postgres (PostgreSQL)
│   ├── Database: decreto_oficial
│   ├── User: decreto_user
│   └── Tables: decree_publications, notifications_log
│
├── 🐍 decreto-scraper (Python App)
│   ├── Build: Dockerfile
│   ├── Env: 11 variáveis (secrets)
│   └── Status: Running
│
└── ⏰ Cron Jobs
    ├── Scraping Diário (11:30)
    └── Backup Banco (23:00) [opcional]
```

---

## Parte 13: Consultas Úteis (Produção)

No console PostgreSQL:

### Ver estatísticas

```sql
-- Total de publicações
SELECT COUNT(*) FROM decree_publications;

-- Publicações por mês
SELECT
    TO_CHAR(publication_date, 'YYYY-MM') as mes,
    COUNT(*) as total
FROM decree_publications
GROUP BY mes
ORDER BY mes DESC;

-- Últimas 10 publicações
SELECT
    publication_date,
    first_seen_at,
    AGE(NOW(), first_seen_at) as descoberta_ha
FROM decree_publications
ORDER BY publication_date DESC
LIMIT 10;
```

### Limpar dados antigos

```sql
-- Manter apenas últimos 2 anos
DELETE FROM decree_publications
WHERE publication_date < CURRENT_DATE - INTERVAL '2 years';
```

---

## Checklist de Deploy Completo ✅

- [ ] Código commitado e pusheado no GitHub
- [ ] PostgreSQL criado no EasyPanel
- [ ] Tabelas criadas (schema.sql executado)
- [ ] Serviço Python criado com Dockerfile
- [ ] 11 variáveis de ambiente configuradas (todas secrets)
- [ ] Teste manual executado com sucesso
- [ ] Email de teste recebido
- [ ] Cron Job configurado (11:30 diário)
- [ ] Logs verificados (sem erros)
- [ ] Timezone do cron correto (America/Sao_Paulo)
- [ ] Auto deploy ativado (opcional)
- [ ] Backup configurado (opcional)

---

## Resumo do Fluxo (EasyPanel)

```
1. GitHub: Commit + Push
   ↓
2. EasyPanel: Criar PostgreSQL
   ↓
3. Console: Executar schema.sql
   ↓
4. EasyPanel: Criar App (GitHub + Dockerfile)
   ↓
5. EasyPanel: Configurar 11 Env Variables
   ↓
6. Console: Teste manual
   ↓
7. EasyPanel: Criar Cron Job
   ↓
8. Logs: Monitorar execuções
```

**Deploy concluído!** 🚀

O sistema rodará automaticamente todo dia às 11:30, buscando novas publicações do Decreto 46930 e enviando email apenas quando houver novidades.

---

## Suporte e Próximos Passos

### Recursos da Hostinger/EasyPanel

- [Documentação EasyPanel](https://easypanel.io/docs)
- [Suporte Hostinger](https://www.hostinger.com.br/suporte)

### Melhorias Futuras

- [ ] Dashboard web para visualizar histórico
- [ ] Notificação via Telegram/WhatsApp
- [ ] Monitorar múltiplos decretos
- [ ] Gerar relatórios mensais
- [ ] API REST para consultar publicações

**Tudo pronto para produção!** 🎉
