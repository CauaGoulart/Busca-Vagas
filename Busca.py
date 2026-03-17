import hashlib
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configurações do ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"

def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

# Configuração Selenium Headless
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

urls = ["https://senior.gupy.io/", "https://softplan.gupy.io/"]
vagas_relevantes = ["Júnior", "Junior", "Pleno", "Java", "Angular"] # Seus focos

content_total = ""
for url in urls:
    driver.get(url)
    driver.implicitly_wait(5)
    text = driver.find_element("tag name", "body").text.lower()

    # Verifica se as palavras-chave aparecem
    if any(palavra.lower() in text for palavra in vagas_relevantes):
        content_total += text

driver.quit()

if content_total:
    new_hash = get_hash(content_total)

    # Carrega o hash anterior
    old_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            old_hash = f.read().strip()

    # Só avisa se houver mudança REAL
    if new_hash != old_hash:
        with open(HASH_FILE, "w") as f:
            f.write(new_hash)
        send_alert("🚀 ATENÇÃO: Novas vagas detectadas em SC para o seu perfil!")
    else:
        print("Nenhuma alteração relevante detectada.")