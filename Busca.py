import hashlib
import os
import requests
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "hashes.json"

# Foco na sua stack técnica
TERMO_BUSCA = "empresa de software java SC"
VAGAS_INTERESSE = ["Júnior", "Junior", "Pleno", "Java", "Angular", "Engenharia de Software"]

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def send_alert(message):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url)

def rodar_monitor():
    driver = configurar_driver()
    old_hashes = {}
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            old_hashes = json.load(f)

    new_hashes = old_hashes.copy()
    alertas = []

    try:
        # 1. VARREDURA NO GOOGLE JOBS
        print(f"🔎 Iniciando sweep no Google Jobs para: {TERMO_BUSCA}")
        url_google = f"https://www.google.com/search?q={TERMO_BUSCA.replace(' ', '+')}&ibp=htl;jobs"
        driver.get(url_google)
        time.sleep(random.uniform(4, 7)) # Pausa humana

        itens_vagas = driver.find_elements(By.CSS_SELECTOR, "[role='listitem']")

        for item in itens_vagas[:10]:
            try:
                texto_vaga = item.text
                if any(p.lower() in texto_vaga.lower() for p in VAGAS_INTERESSE):
                    vaga_id = hashlib.md5(texto_vaga[:100].encode()).hexdigest()

                    if old_hashes.get(vaga_id) != "visto":
                        linhas = texto_vaga.split('\n')
                        titulo = linhas[0] if len(linhas) > 0 else "Nova Vaga"
                        empresa = linhas[1] if len(linhas) > 1 else "Empresa não identificada"

                        alertas.append(f"💼 GOOGLE JOBS - NOVA VAGA!\n📌 {titulo}\n🏢 {empresa}\n📍 Santa Catarina\nLink: {url_google}")
                        new_hashes[vaga_id] = "visto"
            except:
                continue

    except Exception as e:
        print(f"❌ Erro no sweep: {e}")
    driver.quit()

    if alertas:
        for a in alertas:
            send_alert(a)
        with open(HASH_FILE, "w") as f:
            json.dump(new_hashes, f)
        print(f"✅ {len(alertas)} novas vagas encontradas!")
    else:
        print("😴 Sem novidades no Google Jobs.")

if __name__ == "__main__":
    rodar_monitor()