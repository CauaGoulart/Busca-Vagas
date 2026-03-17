from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import hashlib
import requests
import os

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# Pega o token das variáveis de ambiente do sistema
TOKEN = os.getenv("8269304939:AAGk-CV9dlyONyRKoiYIWW8Tm3IBAFF9wvo")
CHAT_ID = os.getenv("8731025797")

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

# Exemplo de monitoramento
urls = ["https://senior.gupy.io/", "https://softplan.gupy.io/"]

driver = webdriver.Chrome()

for url in urls:
    driver.get(url)
    content = driver.find_element("tag name", "body").text

    # Gera um "hash" único do conteúdo atual
    current_hash = hashlib.md5(content.encode()).hexdigest()

    # Compara com o hash salvo em um arquivo .txt ou banco SQL
    # Se current_hash != last_hash:
    #     send_alert(f"⚠️ Mudança detectada na página: {url}")