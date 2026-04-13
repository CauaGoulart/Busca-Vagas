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

# Foco na sua stack técnica e região (SC/Criciúma)
PALAVRAS_CHAVE = ["Java", "Angular", "Engenharia de Software", "Programador", "Desenvolvedor"]

def configurar_driver():
    """Configuração otimizada para GitHub Actions e anti-detecção."""
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
    """Envia a notificação via API do Telegram."""
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
            print(f"🔎 Varrendo '{keyword}' na Rede de Talentos...")
            url_busca = f"https://www.rededetalentos.com.br/vagas?order=&keyword={keyword}"
            driver.get(url_busca)
            time.sleep(random.uniform(3, 5))

            # Localiza os cards das vagas
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or .//a[contains(text(), 'Página da vaga')]]")

            for card in cards[:5]:
                try:
                    texto_card = card.text

                    # 1. Extração do Código Único da Vaga
                    if "CÓD." in texto_card:
                        vaga_id = texto_card.split("CÓD.")[1].split("\n")[0].strip()

                        if old_hashes.get(vaga_id) != "visto":
                            # 2. CAPTURA DO LINK DIRETO
                            try:
                                link_elemento = card.find_element(By.XPATH, ".//a[contains(text(), 'Página da vaga')]")
                                link_vaga = link_elemento.get_attribute("href")
                            except:
                                link_vaga = url_busca # Fallback caso o link direto não seja encontrado

                            linhas = texto_card.split('\n')
                            titulo = linhas[0] if len(linhas) > 0 else "Nova Vaga"

                            cidade = "SC"
                            if "- SC" in texto_card:
                                cidade = texto_card.split("- SC")[0].split("\n")[-1].strip() + " - SC"

                            # 3. Montagem do Alerta Estratégico
                            alertas.append(
                                f"🎯 REDE DE TALENTOS - NOVA VAGA!\n"
                                f"📌 {titulo}\n"
                                f"📍 {cidade}\n"
                                f"🆔 CÓD: {vaga_id}\n"
                                f"🔗 Link Direto: {link_vaga}"
                            )
                            new_hashes[vaga_id] = "visto"
                except Exception as e:
                    print(f"Erro ao processar card: {e}")
                    continue

    except Exception as e:
        print(f"❌ Erro ao acessar portal: {e}")

    driver.quit()

    # 4. Envio de Notificações e Persistência de Dados
    if alertas:
        for a in alertas:
            send_alert(a)
        with open(HASH_FILE, "w") as f:
            json.dump(new_hashes, f)
        print(f"✅ {len(alertas)} alertas enviados!")
    else:
        print("😴 Sem novidades na Rede de Talentos hoje.")

if __name__ == "__main__":
    rodar_monitor()