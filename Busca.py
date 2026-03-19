import hashlib
import os
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "hashes.json"

def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

urls = {
    "Senior Sistemas": "https://senior.gupy.io/",
    "Softplan": "https://softplan.gupy.io/"
}
vagas_relevantes = ["Júnior", "Junior", "Pleno", "Java", "Angular"]

old_hashes = {}
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
        old_hashes = json.load(f)

new_hashes = {}
changes_detected = []

for nome, url in urls.items():
    try:
        driver.get(url)
        driver.implicitly_wait(5)
        text = driver.find_element("tag name", "body").text.lower()

        if any(palavra.lower() in text for palavra in vagas_relevantes):
            current_hash = get_hash(text)
            new_hashes[url] = current_hash

            if old_hashes.get(url) != current_hash:
                changes_detected.append(f"🚀 Nova vaga ou alteração em {nome}:\n{url}")
    except Exception as e:
        print(f"Erro ao acessar {nome}: {e}")

driver.quit()

if changes_detected:
    for alerta in changes_detected:
        send_alert(alerta)

    with open(HASH_FILE, "w") as f:
        json.dump(new_hashes, f)
else:
    print("Sem novidades relevantes hoje.")