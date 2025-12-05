DOCKER DO EASYPANEL

Conectar ao banco:
psql -U postgres -d decreto-rec-e-dps

Exemplo de Criar tabelas (tabelas de datas do Decreto de Receitas e Despesas da SEPLAG):
-- Criar tabela de publicações
CREATE TABLE IF NOT EXISTS decree_publications (
    publication_date DATE PRIMARY KEY,
    raw_title TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    search_term VARCHAR(50) DEFAULT '46930'
);

-- Criar tabela de notificações
CREATE TABLE IF NOT EXISTS notifications_log (
    id SERIAL PRIMARY KEY,
    publication_date DATE NOT NULL REFERENCES decree_publications(publication_date),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    email_to TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_first_seen_at ON decree_publications(first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_date ON notifications_log(publication_date);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications_log(sent_at DESC);

-- Criar view
CREATE OR REPLACE VIEW recent_publications AS
SELECT
    publication_date,
    raw_title,
    first_seen_at,
    CASE
        WHEN first_seen_at > NOW() - INTERVAL '24 hours' THEN true
        ELSE false
    END AS is_new
FROM decree_publications
ORDER BY publication_date DESC;


Verificar se foi criado:
\dt

Sair:
\q


Conectar ao banco:
psql -U postgres -d decreto-rec-e-dps

Se estiver escrito postgres=# ou outra coisa, digite:
\c "decreto-rec-e-dps"

Primeiro, veja o que existe no banco:
SELECT * FROM decree_publications ORDER BY publication_date DESC;

Para deletar APENAS a data 28/10/2025
DELETE FROM decree_publications WHERE publication_date = '2025-10-28';

Para deletar TODAS as datas (se quiser limpar tudo):
DELETE FROM decree_publications;

