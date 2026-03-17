from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import hashlib
import requests
import os

# Configurações para rodar no GitHub Actions (sem interface gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializa o driver usando o manager para evitar erros de versão
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# IMPORTANTE: Use o NOME da variável que você definiu no GitHub Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url)
    else:
        print("Erro: Variáveis de ambiente do Telegram não encontradas.")

# Lista de URLs para monitorar
urls = ["https://senior.gupy.io/", "https://softplan.gupy.io/"]

for url in urls:
    try:
        driver.get(url)
        # Aguarda o carregamento básico da página
        driver.implicitly_wait(10)
        content = driver.find_element("tag name", "body").text

        # Por enquanto, apenas avisamos que o robô acessou a página com sucesso
        # No futuro, você pode implementar a lógica de comparação de hash aqui
        send_alert(f"🤖 O robô verificou a página: {url}")

    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")

driver.quit()