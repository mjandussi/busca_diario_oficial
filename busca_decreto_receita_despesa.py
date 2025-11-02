"""
Script para monitoramento de publicações do Decreto 46930 no Diário Oficial do RJ
Realiza scraping do site do DOERJ, armazena datas em PostgreSQL e envia email quando há novas publicações
"""

import os
import sys
import logging
import re
import smtplib
from datetime import datetime
from typing import List
from email.message import EmailMessage

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import psycopg
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('decreto_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Constantes
DIARIO_URL = "https://www.ioerj.com.br/portal/modules/conteudoonline/busca_do.php?acao=busca"
SEARCH_TERM = os.getenv("SEARCH_TERM", "46930")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


def get_db_connection():
    """Cria e retorna uma conexão com o banco PostgreSQL"""
    try:
        # Tentar usar DSN primeiro
        dsn = os.getenv("POSTGRES_DSN")
        if dsn:
            conn = psycopg.connect(dsn)
        else:
            # Caso contrário, construir a string de conexão
            conn = psycopg.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
        logger.info("Conexão com banco de dados estabelecida")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise


def create_chrome_driver() -> webdriver.Chrome:
    """Cria e configura uma instância do Chrome WebDriver"""
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        logger.info("Chrome configurado em modo headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    return driver


def fetch_publications(search_term: str = SEARCH_TERM) -> List[str]:
    """
    Realiza scraping do site do DOERJ e retorna lista de datas encontradas

    Args:
        search_term: Termo de busca (número do decreto)

    Returns:
        Lista de strings com datas no formato dd/mm/yyyy
    """
    driver = None
    try:
        logger.info(f"Iniciando busca por '{search_term}' no DOERJ")
        driver = create_chrome_driver()
        driver.get(DIARIO_URL)

        # Esperar e preencher campo de busca
        input_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "textobusca"))
        )
        input_box.send_keys(search_term)
        logger.info(f"Campo de busca preenchido com '{search_term}'")

        # Clicar no botão de busca
        button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "buscar"))
        )
        actions = ActionChains(driver)
        actions.move_to_element(button).click().perform()
        logger.info("Botão de busca clicado")

        # Aguardar resultados
        tbody = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//tbody"))
        )

        # Extrair textos das linhas
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_text = " ".join([cell.text for cell in cells])
            texts.append(row_text)

        all_text = " ".join(texts)

        # Extrair datas com regex
        date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'
        dates = re.findall(date_pattern, all_text)

        logger.info(f"Encontradas {len(dates)} datas na busca")
        return dates

    except Exception as e:
        logger.error(f"Erro ao realizar scraping: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador fechado")


def normalize_dates(date_strings: List[str]) -> List[datetime.date]:
    """
    Converte strings de data para objetos date e remove duplicatas

    Args:
        date_strings: Lista de strings no formato dd/mm/yyyy

    Returns:
        Lista de objetos date ordenados (mais recente primeiro)
    """
    dates = []
    for date_str in date_strings:
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
            dates.append(date_obj)
        except ValueError:
            logger.warning(f"Data inválida ignorada: {date_str}")

    # Remover duplicatas e ordenar (mais recente primeiro)
    unique_dates = sorted(list(set(dates)), reverse=True)
    logger.info(f"{len(unique_dates)} datas únicas após normalização")

    return unique_dates


def upsert_publications(conn, dates: List[datetime.date]) -> List[datetime.date]:
    """
    Insere datas no banco e retorna quais são novas

    Args:
        conn: Conexão com o banco PostgreSQL
        dates: Lista de datas para inserir

    Returns:
        Lista de datas que são novas (não existiam no banco)
    """
    new_dates = []

    try:
        with conn.cursor() as cur:
            for date in dates:
                # Tentar inserir, ignorando se já existe
                cur.execute(
                    """
                    INSERT INTO decree_publications (publication_date, search_term)
                    VALUES (%s, %s)
                    ON CONFLICT (publication_date) DO NOTHING
                    RETURNING publication_date
                    """,
                    (date, SEARCH_TERM)
                )

                # Se retornou algo, é porque inseriu (data nova)
                result = cur.fetchone()
                if result:
                    new_dates.append(date)
                    logger.info(f"Nova publicação encontrada: {date.strftime('%d/%m/%Y')}")

        conn.commit()
        logger.info(f"{len(new_dates)} novas publicações inseridas no banco")

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao inserir publicações no banco: {e}")
        raise

    return new_dates


def send_email(new_dates: List[datetime.date]):
    """
    Envia email notificando sobre novas publicações

    Args:
        new_dates: Lista de datas novas para incluir no email
    """
    if not new_dates:
        logger.info("Nenhuma data nova para notificar")
        return

    try:
        # Configurações de email
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        email_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if not email_user or not email_password:
            logger.error("Credenciais de email não configuradas")
            return

        # Formatar datas para o corpo do email
        dates_formatted = [date.strftime("%d/%m/%Y") for date in new_dates]
        dates_html = "<br>".join([f"• {date}" for date in dates_formatted])

        # Criar mensagem
        msg = EmailMessage()
        msg['Subject'] = f'ALERTA: Novas publicações do Decreto {SEARCH_TERM}'
        msg['From'] = email_user
        msg['To'] = ", ".join(email_recipients)

        corpo_email = f"""
        <html>
        <body>
            <p>Prezados,</p>
            <p><b>Foram encontradas {len(new_dates)} nova(s) publicação(ões) do Decreto {SEARCH_TERM} no Diário Oficial:</b></p>
            <p>{dates_html}</p>
            <p>Acesse o <a href="{DIARIO_URL}">Diário Oficial</a> para consultar os detalhes.</p>
            <br>
            <p><em>Mensagem automática gerada em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</em></p>
        </body>
        </html>
        """

        msg.set_content(corpo_email, subtype='html')

        # Enviar email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)

        logger.info(f"Email enviado com sucesso para {len(email_recipients)} destinatário(s)")

    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        raise


def main():
    """Função principal que orquestra o fluxo de execução"""
    try:
        logger.info("=" * 60)
        logger.info("Iniciando execução do scraper do Decreto 46930")
        logger.info("=" * 60)

        # 1. Buscar publicações no site
        date_strings = fetch_publications(SEARCH_TERM)

        if not date_strings:
            logger.warning("Nenhuma data encontrada na busca")
            return

        # 2. Normalizar datas
        dates = normalize_dates(date_strings)

        # 3. Conectar ao banco e inserir/verificar datas novas
        conn = get_db_connection()
        try:
            new_dates = upsert_publications(conn, dates)

            # 4. Enviar email se houver datas novas
            if new_dates:
                send_email(new_dates)
                logger.info(f"Processo concluído: {len(new_dates)} novas publicações notificadas")
            else:
                logger.info("Processo concluído: nenhuma nova publicação encontrada")

        finally:
            conn.close()
            logger.info("Conexão com banco fechada")

        logger.info("=" * 60)
        logger.info("Execução finalizada com sucesso")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Erro crítico na execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
