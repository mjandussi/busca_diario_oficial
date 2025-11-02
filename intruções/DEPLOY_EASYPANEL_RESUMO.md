# Deploy EasyPanel - Resumo Rápido

## Fluxo Simplificado (13 passos)

### 1️⃣ Commit para GitHub
```bash
git add .
git commit -m "Deploy EasyPanel completo"
git push origin main
```

### 2️⃣ Criar PostgreSQL no EasyPanel
- **+ Create Service** → **Database** → **PostgreSQL**
- Name: `decreto-postgres`
- Database: `decreto_oficial`
- User: `decreto_user`
- **Copiar senha gerada!**

### 3️⃣ Executar schema.sql
No console do PostgreSQL:
```bash
psql -U decreto_user -d decreto_oficial
# Colar conteúdo do schema.sql
```

### 4️⃣ Criar App Python
- **+ Create Service** → **App** → **From GitHub**
- Name: `decreto-scraper`
- Repo: `busca_diario_oficial`
- Build: **Dockerfile**

### 5️⃣ Configurar 11 Variáveis de Ambiente

| Variável | Valor |
|----------|-------|
| EMAIL_USER | seu_email@gmail.com |
| EMAIL_PASSWORD | app_password_16_digitos |
| EMAIL_RECIPIENTS | emails@separados,por,virgula |
| SMTP_HOST | smtp.gmail.com |
| SMTP_PORT | 587 |
| POSTGRES_HOST | decreto-postgres |
| POSTGRES_PORT | 5432 |
| POSTGRES_DB | decreto_oficial |
| POSTGRES_USER | decreto_user |
| POSTGRES_PASSWORD | senha_do_passo_2 |
| SEARCH_TERM | 46930 |
| HEADLESS | true |

**Marcar todas como Secret!**

### 6️⃣ Teste Manual
Console do `decreto-scraper`:
```bash
python busca_decreto_receita_despesa.py
```

### 7️⃣ Configurar Cron
- **Cron Jobs** → **+ Add**
- Service: `decreto-scraper`
- Schedule: `30 11 * * *`
- Command: `python /app/busca_decreto_receita_despesa.py`
- Timezone: `America/Sao_Paulo`

---

## Troubleshooting Rápido

### PostgreSQL não conecta
→ `POSTGRES_HOST` deve ser o **nome do serviço** (ex: `decreto-postgres`), NÃO `localhost`

### Email não envia
→ Usar **App Password** do Gmail (16 dígitos)
→ Marcar `EMAIL_PASSWORD` como **Secret**

### Chrome não funciona
→ Verificar Dockerfile tem `chromium` e `chromium-driver`
→ `HEADLESS=true` nas variáveis

### Cron não executa
→ Verificar timezone: `America/Sao_Paulo`
→ Comando: `python /app/busca_decreto_receita_despesa.py`

---

## Checklist Final ✅

- [ ] PostgreSQL criado e rodando
- [ ] Tabelas criadas (schema.sql)
- [ ] App Python deployado
- [ ] 11 variáveis configuradas
- [ ] Teste manual OK + email recebido
- [ ] Cron configurado (11:30 diário)
- [ ] Logs verificados

**Pronto! Sistema em produção.** 🚀
