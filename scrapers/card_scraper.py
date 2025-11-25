import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
import os
import sys
import subprocess

# --- YOL AYARLARI ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

# Hedef Dosya: İşlenmiş Ana Veri Seti
SOURCE_FILE = os.path.join(BASE_DIR, "data", "processed", "MASTER_MATCH_STATS.csv")

# Kartların Kaydedileceği Yer (Raw klasörüne atalım, sonra birleştiririz)
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "MATCH_CARDS.csv")

# --- KONTROLLER ---
if not os.path.exists(SOURCE_FILE):
    print(f"❌ HATA: '{SOURCE_FILE}' bulunamadı!")
    print("   Önce 'etl/merge_data.py' (final_merge) dosyasını çalıştırıp Master dosyayı oluşturun.")
    sys.exit()

print(f"📂 Kaynak Dosya: {SOURCE_FILE}")


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
    options.page_load_strategy = 'eager'
    try:
        d = uc.Chrome(options=options, use_subprocess=True)
        d.set_page_load_timeout(60)
        return d
    except:
        time.sleep(5)
        return init_driver()


# --- URL LİSTESİNİ HAZIRLA ---
try:
    df_source = pd.read_csv(SOURCE_FILE)

    # MatchURL sütunu var mı kontrol et
    if 'MatchURL' not in df_source.columns:
        print("❌ HATA: Master dosyasında 'MatchURL' sütunu yok!")
        print("   Link olmadan kartları çekemeyiz. Merge işleminde URL'lerin silinmediğinden emin olun.")
        sys.exit()

    all_urls = df_source['MatchURL'].dropna().unique().tolist()
except Exception as e:
    print(f"❌ Dosya okuma hatası: {e}")
    sys.exit()

# Zaten çekilmiş kartlar varsa atla
scraped_urls = set()
if os.path.exists(OUTPUT_FILE):
    try:
        df_existing = pd.read_csv(OUTPUT_FILE)
        scraped_urls = set(df_existing['MatchURL'].tolist())
        print(f"📥 {len(scraped_urls)} maçın kart verisi zaten çekilmiş, atlanacak.")
    except:
        pass

urls_to_scrape = [u for u in all_urls if u not in scraped_urls]
print(f"🚀 Toplam {len(urls_to_scrape)} maç taranacak...")

if not urls_to_scrape:
    print("✅ Tüm maçların kart verisi zaten var. İşlem yapmaya gerek yok.")
    sys.exit()

driver = init_driver()


# --- PARSER ---
def extract_cards_only(soup):
    """ Kart İkonlarını Sayar """
    header = soup.find(lambda tag: tag.name in ["div", "th"] and "Cards" in tag.get_text())
    hy, hr, ay, ar = 0, 0, 0, 0

    if header:
        container = None
        if header.name == "th":
            container = header.find_parent("tr").find_next_sibling("tr")
        else:
            # Div yapısı için en yakın tablo satırını bul
            container = header.find_parent("tr")
            if container: container = container.find_next_sibling("tr")

        if container:
            # .cards class'ına sahip divleri bul
            # Bazı sayfalarda td içinde, bazılarında div içinde olabilir
            card_divs = container.select(".cards")

            if len(card_divs) >= 2:
                # Ev Sahibi
                hy = len(card_divs[0].select('.yellow_card'))
                hr = len(card_divs[0].select('.red_card')) + len(card_divs[0].select('.yellow_red_card'))
                # Deplasman
                ay = len(card_divs[1].select('.yellow_card'))
                ar = len(card_divs[1].select('.red_card')) + len(card_divs[1].select('.yellow_red_card'))

    return hy, hr, ay, ar


# --- DÖNGÜ ---
try:
    for i, url in enumerate(urls_to_scrape, 1):
        try:
            driver.get(url)
            # Kartlar hızlı yüklenir
            time.sleep(random.uniform(1.0, 2.5))

            soup = BeautifulSoup(driver.page_source, "html.parser")

            hy, hr, ay, ar = extract_cards_only(soup)

            card_data = {
                "MatchURL": url,
                "HomeYellowCards": hy,
                "HomeRedCards": hr,
                "AwayYellowCards": ay,
                "AwayRedCards": ar
            }

            df_single = pd.DataFrame([card_data])
            header_mode = not os.path.exists(OUTPUT_FILE)
            df_single.to_csv(OUTPUT_FILE, mode='a', header=header_mode, index=False)

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
    print("\n🏁 İşlem bitti.")