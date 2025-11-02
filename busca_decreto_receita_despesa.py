# Importar a biblioteca Selenium e webdriver_manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import smtplib
import email.message
import re


###############################################################################################################################       
###############################################################################################################################       
###############################################################################################################################       



# Configurar o serviço do ChromeDriver usando o webdriver_manager
service = Service(ChromeDriverManager().install())

# Criar uma instância do navegador Chrome
nav = webdriver.Chrome(service=service)

# Entrar no site especificado
nav.get("https://www.ioerj.com.br/portal/modules/conteudoonline/busca_do.php?acao=busca")


try:
    # Esperar até que o elemento de entrada esteja presente
    input_box = WebDriverWait(nav, 10).until(EC.presence_of_element_located((By.NAME, "textobusca")))

    palavra_busca = "46930"
    # Enviar texto para o elemento de entrada
    input_box.send_keys(palavra_busca)

    # Esperar até que o botão esteja presente
    #button = WebDriverWait(nav, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="xo-content"]/form/table/tbody/tr/td/div/div[7]/div/input')))
    button = WebDriverWait(nav, 10).until(EC.element_to_be_clickable((By.NAME, "buscar")))
    #button = WebDriverWait(nav, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Buscar']")))


    # Usar ActionChains para mover o cursor até o botão e clicar nele
    actions = ActionChains(nav)
    actions.move_to_element(button).click().perform()


    # Esperar até que o <tbody> esteja presente
    tbody = WebDriverWait(nav, 10).until(
        EC.presence_of_element_located((By.XPATH, "//tbody"))
    )

    # Iterar sobre as <tr> dentro do <tbody>
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    texts = []
    for row in rows:
        # Extrair os textos dentro das <td> de cada <tr>
        cells = row.find_elements(By.TAG_NAME, "td")
        row_text = []
        for cell in cells:
            row_text.append(cell.text)
        texts.append(" ".join(row_text))

    # Fechar o navegador após a pausa (opcional)
    nav.quit()

    # Concatenar todos os textos em uma única string
    all_text = " ".join(texts)

    # Definir o padrão regex para datas no formato dd/mm/yyyy
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'

    # Encontrar todas as datas no texto
    dates = re.findall(date_pattern, all_text)

    # Selecionar as três últimas datas
    last_three_dates = dates[:3]

    # Formatar o corpo do email com separadores
    separator = " --- "  # Você pode mudar o separador para qualquer caractere que preferir
    body = separator.join(last_three_dates)


    ###############################################################################################################################       
    ###############################################################################################################################       
    ###############################################################################################################################       
    ###############################################################################################################################       
    ###############################################################################################################################       
    ###############################################################################################################################       

    
    corpo_email = f"""
                <p>Prezados,</p>
                <p><b>Busca Automática de Datas no DIÁRIO OFICIAL pela palavra: {palavra_busca}</b></p>
                <p>{body}</p>
                <p></p>

                """

    msg = email.message.Message()
    msg['Subject'] = f'Lista de Datas da palavra buscada igual a: {palavra_busca}'
    msg['From'] = 'mjandussi@gmail.com'
    msg['To'] = 'mjandussi@fazenda.rj.gov.br'
    password = password 
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(corpo_email)
    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()
    # Login Credentials for sending the mail
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('iso-8859-1')) #utf-8
    print('Email enviado')

    nav.quit()


except Exception as e:
    print(f"Ocorreu um erro: {e}")
    nav.quit()
