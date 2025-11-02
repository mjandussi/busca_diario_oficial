"""
Scheduler para execução automática do scraper do Decreto 46930
Roda diariamente às 11:30 (horário de Brasília)
"""

import time
import logging
import sys
from datetime import datetime
import schedule

# Importar a função main do scraper
from busca_decreto_receita_despesa import main

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def run_scraper():
    """Executa o scraper e trata erros"""
    try:
        now = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Scheduler disparado em {now.strftime('%d/%m/%Y às %H:%M:%S')}")
        logger.info("=" * 60)

        # Executar o scraper
        main()

        logger.info("=" * 60)
        logger.info("Scheduler concluído com sucesso!")
        logger.info("Próxima execução: amanhã às 11:30")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERRO no scheduler: {e}", exc_info=True)
        logger.error("=" * 60)


# Agendar execução diária às 11:30
schedule.every().day.at("11:44").do(run_scraper)

# Mensagem de inicialização
logger.info("=" * 60)
logger.info("SCHEDULER INICIADO!")
logger.info("Horário configurado: 11:30 (diariamente)")
logger.info("Timezone: America/Sao_Paulo (configurar TZ nas env vars)")
logger.info("Aguardando próxima execução...")
logger.info("=" * 60)

# Loop infinito mantém o script rodando
try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 1 minuto
except KeyboardInterrupt:
    logger.info("Scheduler encerrado pelo usuário")
