"""
Scheduler para execução automática do scraper do Decreto 46930
Roda diariamente às 11:30 (horário de Brasília)
Pula sábados, domingos e feriados (nacionais + opcionais por estado/município)
"""

import os
import time
import logging
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
import schedule
import holidays

# Importar a função main do scraper
from busca_decreto_receita_despesa import main

# ====================== Configurações ======================

# Timezone de referência para o agendador/log e para a regra de feriados
TZ_NAME = os.getenv("SCHEDULER_TZ", "America/Sao_Paulo")
TZ = ZoneInfo(TZ_NAME)

# Estado (UF) para feriados estaduais. Ex.: "RJ", "SP", etc. (opcional)
FERIADOS_UF = os.getenv("FERIADOS_UF", "").strip() or None

# Lista EXTRA de feriados próprios/locais (strings "YYYY-MM-DD" separadas por vírgula)
# Exemplo: "2025-01-20,2025-11-20"
FERIADOS_CUSTOM = {
    s.strip()
    for s in os.getenv("FERIADOS_CUSTOM", "").split(",")
    if s.strip()
}

# Horário (HH:MM) no TZ definido
HORARIO = "11:30"

# ====================== Logging ======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ====================== Feriados BR ======================

def build_feriados_br(years: list[int]) -> holidays.HolidayBase:
    """
    Constrói o calendário de feriados para os anos informados, incluindo:
      - feriados nacionais do Brasil;
      - feriados estaduais (se FERIADOS_UF estiver definido);
      - feriados customizados via env FERIADOS_CUSTOM.
    """
    cal = holidays.BR(prov=FERIADOS_UF, state=FERIADOS_UF, years=years)
    # Adiciona feriados customizados
    for ds in FERIADOS_CUSTOM:
        try:
            y, m, d = map(int, ds.split("-"))
            cal[date(y, m, d)] = "Feriado (customizado)"
        except Exception:
            logger.warning(f"Data inválida em FERIADOS_CUSTOM: {ds!r} — ignorando.")
    return cal

# Pré-construímos para o ano corrente e vizinhos (para viradas de ano)
NOW_TZ = datetime.now(TZ)
FERIADOS = build_feriados_br([NOW_TZ.year - 1, NOW_TZ.year, NOW_TZ.year + 1])

# ====================== Funções ======================

def eh_fim_de_semana(d: date) -> bool:
    """Verifica se a data é sábado ou domingo."""
    # Monday=0 ... Sunday=6
    return d.weekday() >= 5  # 5=sábado, 6=domingo

def eh_feriado(d: date) -> bool:
    """Verifica se a data é feriado (nacional, estadual ou customizado)."""
    if d in FERIADOS:
        return True
    ds = d.strftime("%Y-%m-%d")
    return ds in FERIADOS_CUSTOM


def run_scraper():
    """Executa o scraper às 11:30, pulando fds e feriados (no TZ configurado)."""
    try:
        now = datetime.now(TZ)
        hoje = now.date()

        # Pula fim de semana
        if eh_fim_de_semana(hoje):
            logger.info(f"⏸️ Ignorado ({now.strftime('%A')}) — fim de semana no fuso {TZ_NAME}.")
            return

        # Pula feriado
        if eh_feriado(hoje):
            nome = FERIADOS.get(hoje) or "Feriado"
            logger.info(f"⏸️ Ignorado — {nome} ({hoje.isoformat()}) no fuso {TZ_NAME}.")
            return

        logger.info("=" * 60)
        logger.info(f"🚀 Scheduler disparado em {now.strftime('%d/%m/%Y às %H:%M:%S')} [{TZ_NAME}]")
        logger.info("=" * 60)

        main()

        logger.info("=" * 60)
        logger.info("✅ Scheduler concluído com sucesso!")
        logger.info(f"Próxima execução: amanhã às {HORARIO}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"💥 ERRO no scheduler: {e}", exc_info=True)
        logger.error("=" * 60)


# ====================== Agendamento ======================

schedule.every().day.at(HORARIO).do(run_scraper)

# ====================== Inicialização ======================

logger.info("=" * 60)
logger.info("SCHEDULER INICIADO!")
logger.info(
    "Horário: %s (TZ: %s) — pula sábados, domingos e feriados%s%s.",
    HORARIO,
    TZ_NAME,
    f" (UF={FERIADOS_UF})" if FERIADOS_UF else "",
    f" + {len(FERIADOS_CUSTOM)} custom" if FERIADOS_CUSTOM else "",
)
logger.info("Aguardando próxima execução...")
logger.info("=" * 60)

# ====================== Loop ======================

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 1 minuto
except KeyboardInterrupt:
    logger.info("Scheduler encerrado pelo usuário")
