import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import os
import sys
import subprocess

# --- YOL AYARLARI ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
SOURCE_FILE = os.path.join(BASE_DIR, "data", "processed", "MASTER_MATCH_STATS.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "MATCH_CARDS.csv")

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

# --- KONTROLLER ---
if not os.path.exists(SOURCE_FILE):
    print(f"❌ HATA: '{SOURCE_FILE}' bulunamadı!")
    sys.exit()


# --- DRIVER YÖNETİMİ ---
def kill_chrome():
    try:
        subprocess.call("taskkill /F /IM chrome.exe /T", shell=True, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        subprocess.call("taskkill /F /IM chromedriver.exe /T", shell=True, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except:
        pass


def init_driver():
    kill_chrome()
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'eager'  # HTML yüklensin yeter, resimleri bekleme

    try:
        d = uc.Chrome(options=options, use_subprocess=True)
        d.set_page_load_timeout(20)  # 20 saniyeden fazla bekleme
        return d
    except:
        time.sleep(5)
        return init_driver()


# --- PARSER ---
def extract_cards_only(soup):
    """ 3 Farklı Stratejiyle Kartları Arar """
    hy, hr, ay, ar = 0, 0, 0, 0

    # Strateji 1: team_stats_extra
    extra = soup.find("div", id="team_stats_extra")
    if extra:
        label = extra.find(lambda t: t.name == "div" and "Cards" in t.get_text())
        if label:
            h_div, a_div = label.find_previous_sibling("div"), label.find_next_sibling("div")
            if h_div and a_div:
                hy = len(h_div.select('.yellow_card'))
                hr = len(h_div.select('.red_card')) + len(h_div.select('.yellow_red_card'))
                ay = len(a_div.select('.yellow_card'))
                ar = len(a_div.select('.red_card')) + len(a_div.select('.yellow_red_card'))
                return hy, hr, ay, ar

    # Strateji 2: team_stats (Bar Charts)
    team_stats = soup.find("div", id="team_stats")
    if team_stats:
        cards = team_stats.select("div.cards")
        if len(cards) >= 2:
            hy = len(cards[0].select('.yellow_card'))
            hr = len(cards[0].select('.red_card')) + len(cards[0].select('.yellow_red_card'))
            ay = len(cards[1].select('.yellow_card'))
            ar = len(cards[1].select('.red_card')) + len(cards[1].select('.yellow_red_card'))
            return hy, hr, ay, ar

    return 0, 0, 0, 0


# --- HAZIRLIK ---
try:
    df_source = pd.read_csv(SOURCE_FILE)
    all_urls = df_source['MatchURL'].dropna().unique().tolist()

    scraped_urls = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            df_exist = pd.read_csv(OUTPUT_FILE)
            scraped_urls = set(df_exist['MatchURL'].tolist())
            print(f"📥 {len(scraped_urls)} maç zaten var.")
        except:
            pass

    urls_to_scrape = [u for u in all_urls if u not in scraped_urls]
    print(f"🚀 Kalan {len(urls_to_scrape)} maç taranacak...")

    if not urls_to_scrape:
        print("✅ Bitti.")
        sys.exit()

    driver = init_driver()

    # --- DÖNGÜ ---
    for i, url in enumerate(urls_to_scrape, 1):

        # Her 50 maçta bir tarayıcıyı yenile (RAM Şişmesini Önle)
        if i % 50 == 0:
            print("♻️  Tarayıcı yenileniyor...")
            driver.quit()
            time.sleep(2)
            driver = init_driver()

        try:
            try:
                driver.get(url)
            except TimeoutException:
                # Sayfa yüklenmesi uzun sürdüyse (reklam vs), durdur ve veriyi almaya çalış
                driver.execute_script("window.stop();")
            except WebDriverException:
                # Tarayıcı çöktüyse
                print("    🚨 Tarayıcı çöktü, yenileniyor...")
                driver = init_driver()
                driver.get(url)

            # Biraz bekle ki HTML oluşsun
            time.sleep(random.uniform(1.0, 2.0))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            hy, hr, ay, ar = extract_cards_only(soup)

            # Veri boşsa (0-0) ve sayfada hata varsa (bazen olur), retry yapılabilir
            # Ama şimdilik 0 olarak kaydediyoruz, akış bozulmasın.

            df_single = pd.DataFrame([{
                "MatchURL": url,
                "HomeYellowCards": hy, "HomeRedCards": hr,
                "AwayYellowCards": ay, "AwayRedCards": ar
            }])

            hdr = not os.path.exists(OUTPUT_FILE)
            df_single.to_csv(OUTPUT_FILE, mode='a', header=hdr, index=False)

            print(f"✅ {i}/{len(urls_to_scrape)} | 🟨 {hy}-{ay} 🟥 {hr}-{ar} | {url.split('/')[-1]}")

        except Exception as e:
            print(f"⚠️ Hata: {e}")
            try:
                driver.quit(); driver = init_driver()
            except:
                pass

except KeyboardInterrupt:
    print("\n🛑 Durduruldu.")
finally:
    if driver: driver.quit()