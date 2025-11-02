-- Script para criação das tabelas do projeto busca_diario_oficial
-- Execute este script no seu banco PostgreSQL antes de rodar a aplicação

-- Criar schema (opcional, se quiser separar do schema public)
-- CREATE SCHEMA IF NOT EXISTS diario_oficial;
-- SET search_path TO diario_oficial;

-- Tabela principal para armazenar as datas de publicação do Decreto 46930
CREATE TABLE IF NOT EXISTS decree_publications (
    publication_date DATE PRIMARY KEY,
    raw_title TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    search_term VARCHAR(50) DEFAULT '46930'
);

-- Índice para busca por data de descoberta
CREATE INDEX IF NOT EXISTS idx_first_seen_at ON decree_publications(first_seen_at DESC);

-- Tabela opcional para auditoria de notificações enviadas
CREATE TABLE IF NOT EXISTS notifications_log (
    id SERIAL PRIMARY KEY,
    publication_date DATE NOT NULL REFERENCES decree_publications(publication_date),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    email_to TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'sent', -- sent, failed
    error_message TEXT
);

-- Índice para busca de notificações por data
CREATE INDEX IF NOT EXISTS idx_notifications_date ON notifications_log(publication_date);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications_log(sent_at DESC);

-- View para facilitar consultas de novas publicações
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

-- Comentários nas tabelas
COMMENT ON TABLE decree_publications IS 'Armazena as datas de publicações encontradas do Decreto 46930 no Diário Oficial';
COMMENT ON TABLE notifications_log IS 'Log de emails enviados para notificação de novas publicações';
COMMENT ON COLUMN decree_publications.publication_date IS 'Data da publicação no Diário Oficial';
COMMENT ON COLUMN decree_publications.raw_title IS 'Título completo da publicação (opcional)';
COMMENT ON COLUMN decree_publications.first_seen_at IS 'Data e hora em que a publicação foi encontrada pela primeira vez';
