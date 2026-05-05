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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "hashes.json"

# 1. Vagas Principais (O seu foco principal)
PALAVRAS_CHAVE_DEV = ["Java", "Angular", "Engenharia de Software", "Programador", "Desenvolvedor"]

# 2. Vagas Plano B (Tecnologia/Sistemas, mas não necessariamente programação pura)
PALAVRAS_CHAVE_PLAN_B = ["Suporte", "Implantação", "Sistemas", "QA", "Qualidade", "TI", "Dados"]

# Unimos as duas listas para o robô pesquisar
TODAS_PALAVRAS = PALAVRAS_CHAVE_DEV + PALAVRAS_CHAVE_PLAN_B

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
    wait = WebDriverWait(driver, 10) # Tempo máximo de espera para elementos

    old_hashes = {}
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            old_hashes = json.load(f)

    new_hashes = old_hashes.copy()
    alertas = []

    for keyword in TODAS_PALAVRAS:

        # ==========================================
        # BUSCA 1: REDE DE TALENTOS (ACIC)
        # ==========================================
        try:
            print(f"🔎 [ACIC] Varrendo '{keyword}'...")
            url_acic = f"https://www.rededetalentos.com.br/vagas?order=&keyword={keyword}"
            driver.get(url_acic)
            time.sleep(random.uniform(2, 4))

            cards_acic = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or .//a[contains(text(), 'Página da vaga')]]")

            for card in cards_acic[:5]:
                try:
                    texto_card = card.text
                    if "CÓD." in texto_card:
                        vaga_id = texto_card.split("CÓD.")[1].split("\n")[0].strip()

                        # FIX DO BUG: Verifica no new_hashes em vez do old_hashes para evitar duplicatas na mesma execução
                        if new_hashes.get(vaga_id) != "visto":
                            try:
                                link_elemento = card.find_element(By.XPATH, ".//a[contains(text(), 'Página da vaga')]")
                                link_vaga = link_elemento.get_attribute("href")
                            except:
                                link_vaga = url_acic

                            linhas = texto_card.split('\n')
                            titulo = linhas[0] if len(linhas) > 0 else "Nova Vaga"
                            cidade = "SC"
                            if "- SC" in texto_card:
                                cidade = texto_card.split("- SC")[0].split("\n")[-1].strip() + " - SC"

                            # Classifica se é Plano A ou Plano B
                            tag = "🚀 DEV" if keyword in PALAVRAS_CHAVE_DEV else "🛡️ PLANO B"

                            alertas.append(
                                f"🎯 ACIC ({tag}) - NOVA VAGA!\n"
                                f"📌 {titulo}\n"
                                f"📍 {cidade}\n"
                                f"🆔 CÓD: {vaga_id}\n"
                                f"🔗 Link: {link_vaga}"
                            )
                            # Salva imediatamente na memória para não repetir na próxima palavra-chave
                            new_hashes[vaga_id] = "visto"
                except Exception as e:
                    continue
        except Exception as e:
            print(f"❌ Erro ACIC: {e}")

        # ==========================================
        # BUSCA 2: ACIT TUBARÃO (Interação com Formulário)
        # ==========================================
        try:
            print(f"🔎 [ACIT] Varrendo '{keyword}'...")
            driver.get("https://www.acittubarao.com.br/emprego.html")

            # Aguarda o campo de pesquisa aparecer e digita a palavra
            input_busca = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='O que você procura?']")))
            input_busca.clear()
            input_busca.send_keys(keyword)
            time.sleep(1) # Pausa humana

            # Clica no botão verde "Pesquisar"
            btn_pesquisar = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'PESQUISAR', 'pesquisar'), 'pesquisar')] | //input[contains(@class, 'btn') or @type='submit']")
            driver.execute_script("arguments[0].click();", btn_pesquisar)

            time.sleep(random.uniform(3, 5)) # Aguarda os resultados carregarem

            # Busca os cards de resultado. Como não sabemos a classe exata, procuramos por blocos de texto genéricos
            cards_acit = driver.find_elements(By.XPATH, "//div[contains(@class, 'vaga') or contains(@class, 'item') or contains(@class, 'card')]")

            # Fallback caso a classe seja diferente
            if not cards_acit:
                cards_acit = driver.find_elements(By.XPATH, "//h3/..")

            for card in cards_acit[:5]:
                texto_card = card.text.strip()
                if len(texto_card) > 10:
                    # Cria um hash do texto do card, já que a ACIT não tem "CÓD." visível
                    vaga_id = "ACIT_" + hashlib.md5(texto_card[:100].encode()).hexdigest()

                    if new_hashes.get(vaga_id) != "visto":
                        linhas = texto_card.split('\n')
                        titulo = linhas[0] if len(linhas) > 0 else "Vaga Encontrada"
                        tag = "🚀 DEV" if keyword in PALAVRAS_CHAVE_DEV else "🛡️ PLANO B"

                        alertas.append(
                            f"🏢 ACIT TUBARÃO ({tag}) - NOVA VAGA!\n"
                            f"📌 {titulo}\n"
                            f"📍 Tubarão/SC\n"
                            f"🔗 Link: https://www.acittubarao.com.br/emprego.html\n"
                            f"⚠️ (Pesquise por '{keyword}' no site para ver os detalhes)"
                        )
                        new_hashes[vaga_id] = "visto"
        except Exception as e:
            print(f"❌ Erro ACIT para '{keyword}': {e}")

    driver.quit()

    # Envio de Notificações
    if alertas:
        for a in alertas:
            send_alert(a)
        with open(HASH_FILE, "w") as f:
            json.dump(new_hashes, f)
        print(f"✅ {len(alertas)} alertas enviados!")
    else:
        print("😴 Sem novidades hoje nas duas plataformas.")

if __name__ == "__main__":
    rodar_monitor()