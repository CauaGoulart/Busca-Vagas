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

# Suas tecnologias e níveis de interesse [cite: 4, 18]
# O bot vai pesquisar uma por uma na Rede de Talentos
PALAVRAS_CHAVE = ["Java", "Angular", "Engenharia de Software", "Programador", "Desenvolvedor"]

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
        for keyword in PALAVRAS_CHAVE:
            print(f"🔎 Pesquisando por '{keyword}' na Rede de Talentos...")
            url_busca = f"https://www.rededetalentos.com.br/vagas?order=&keyword={keyword}"
            driver.get(url_busca)
            time.sleep(random.uniform(3, 5)) # Pausa para carregar a lista

            # Seleciona os cards das vagas baseados na estrutura visual do site
            # Geralmente são divs que contêm o texto "CÓD." ou o título da vaga
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or .//a[contains(text(), 'Página da vaga')]]")

            for card in cards[:5]: # Foca nas mais recentes de cada busca
                try:
                    texto_card = card.text
                    # Extraímos o Código da Vaga (ex: CÓD. 230379) para ser nosso ID único
                    if "CÓD." in texto_card:
                        vaga_id = texto_card.split("CÓD.")[1].split("\n")[0].strip()

                        if old_hashes.get(vaga_id) != "visto":
                            linhas = texto_card.split('\n')
                            titulo = linhas[0] if len(linhas) > 0 else "Nova Vaga"
                            cidade = "SC"
                            if "- SC" in texto_card:
                                cidade = texto_card.split("- SC")[0].split("\n")[-1] + " - SC"

                            alertas.append(
                                f"🎯 REDE DE TALENTOS (ACIC) - NOVA VAGA!\n"
                                f"📌 {titulo}\n"
                                f"📍 {cidade.strip()}\n"
                                f"🆔 CÓD: {vaga_id}\n"
                                f"🔗 Link: {url_busca}"
                            )
                            new_hashes[vaga_id] = "visto"
                except:
                    continue

    except Exception as e:
        print(f"❌ Erro ao acessar Rede de Talentos: {e}")

    driver.quit()

    if alertas:
        for a in alertas:
            send_alert(a)
        with open(HASH_FILE, "w") as f:
            json.dump(new_hashes, f)
        print(f"✅ {len(alertas)} novas vagas locais encontradas!")
    else:
        print("😴 Sem novidades na Rede de Talentos.")

if __name__ == "__main__":
    rodar_monitor()