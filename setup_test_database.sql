-- Script para setup do banco de dados de TESTES
-- Execute este script para criar o ambiente de testes local

-- 1. Criar as tabelas (se ainda não existirem)
CREATE TABLE IF NOT EXISTS decree_publications (
    publication_date DATE PRIMARY KEY,
    raw_title TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    search_term VARCHAR(50) DEFAULT '46930'
);

CREATE TABLE IF NOT EXISTS notifications_log (
    id SERIAL PRIMARY KEY,
    publication_date DATE NOT NULL REFERENCES decree_publications(publication_date),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    email_to TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT
);

-- 2. Limpar dados anteriores (apenas para testes)
TRUNCATE TABLE notifications_log CASCADE;
TRUNCATE TABLE decree_publications CASCADE;

-- 3. Inserir DADOS HISTÓRICOS (base já existente)
-- Estas são as publicações "antigas" que já deveriam existir no banco
INSERT INTO decree_publications (publication_date, search_term, first_seen_at)
VALUES
    ('2025-08-07', '46930', NOW() - INTERVAL '60 days'),
    ('2025-09-10', '46930', NOW() - INTERVAL '45 days'),
    ('2025-09-25', '46930', NOW() - INTERVAL '30 days'),
    ('2025-10-06', '46930', NOW() - INTERVAL '20 days')
ON CONFLICT (publication_date) DO NOTHING;

-- 4. Verificar os dados inseridos
SELECT
    publication_date,
    search_term,
    first_seen_at,
    AGE(NOW(), first_seen_at) as "tempo_desde_descoberta"
FROM decree_publications
ORDER BY publication_date DESC;

-- 5. Informações para o teste
SELECT
    COUNT(*) as "total_publicacoes_base",
    MIN(publication_date) as "mais_antiga",
    MAX(publication_date) as "mais_recente"
FROM decree_publications;

COMMIT;

-- ============================================================
-- APÓS EXECUTAR ESTE SCRIPT, as seguintes datas estarão no banco:
-- - 07/08/2025 (descoberta há ~60 dias)
-- - 10/09/2025 (descoberta há ~45 dias)
-- - 25/09/2025 (descoberta há ~30 dias)
-- - 06/10/2025 (descoberta há ~20 dias)
--
-- O script Python irá buscar e encontrar TAMBÉM:
-- - 08/10/2025 ← NOVA (deve disparar email)
-- - 16/10/2025 ← NOVA (deve disparar email)
-- - 28/10/2025 ← NOVA (deve disparar email)
--
-- Resultado esperado: 3 novas publicações detectadas + email enviado
-- ============================================================
