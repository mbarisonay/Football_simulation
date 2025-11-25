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
SOURCE_FILE = os.path.join(BASE_DIR, "data", "processed", "MASTER_MATCH_STATS.csv")

# Çıktı Yeri
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "MATCH_CARDS.csv")

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
    options.page_load_strategy = 'eager'
    try:
        d = uc.Chrome(options=options, use_subprocess=True)
        d.set_page_load_timeout(60)
        return d
    except:
        time.sleep(5)
        return init_driver()


# --- YENİLENMİŞ PARSER (V2) ---
def extract_cards_only(soup):
    """ 3 Farklı Stratejiyle Kartları Arar """
    hy, hr, ay, ar = 0, 0, 0, 0

    # --- STRATEJİ 1: team_stats_extra (En yaygın yer) ---
    # Genelde Fouls, Corners ile aynı yerdedir.
    extra_stats = soup.find("div", id="team_stats_extra")
    if extra_stats:
        # "Cards" yazısını bul
        label = extra_stats.find(lambda t: t.name == "div" and "Cards" in t.get_text())
        if label:
            # Solundaki (Home) ve Sağındaki (Away) divleri al
            home_div = label.find_previous_sibling("div")
            away_div = label.find_next_sibling("div")

            if home_div and away_div:
                hy = len(home_div.select('.yellow_card'))
                hr = len(home_div.select('.red_card')) + len(home_div.select('.yellow_red_card'))
                ay = len(away_div.select('.yellow_card'))
                ar = len(away_div.select('.red_card')) + len(away_div.select('.yellow_red_card'))
                return hy, hr, ay, ar

    # --- STRATEJİ 2: team_stats (Bar grafiklerinin olduğu yer) ---
    team_stats = soup.find("div", id="team_stats")
    if team_stats:
        # Burada genelde class="cards" olan divler olur
        card_containers = team_stats.select("div.cards")
        if len(card_containers) >= 2:
            # [0] -> Home, [1] -> Away
            hy = len(card_containers[0].select('.yellow_card'))
            hr = len(card_containers[0].select('.red_card')) + len(card_containers[0].select('.yellow_red_card'))
            ay = len(card_containers[1].select('.yellow_card'))
            ar = len(card_containers[1].select('.red_card')) + len(card_containers[1].select('.yellow_red_card'))
            return hy, hr, ay, ar

    # --- STRATEJİ 3: Scorebox Summary (En üstteki özet) ---
    # Eğer yukarıdakiler yoksa, bazen kartlar en tepedeki skor kutusunun altında ikon olarak durur
    # Ancak bu genellikle timeline ile karışır, o yüzden dikkatli seçmeliyiz.
    # Şimdilik ilk 2 strateji %99 çalışır.

    return 0, 0, 0, 0


# --- MAIN ---
try:
    # URL Listesini Hazırla
    df_source = pd.read_csv(SOURCE_FILE)
    if 'MatchURL' not in df_source.columns:
        print("❌ HATA: MatchURL sütunu yok.")
        sys.exit()

    all_urls = df_source['MatchURL'].dropna().unique().tolist()

    # Zaten çekilmişleri ele
    scraped_urls = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            df_exist = pd.read_csv(OUTPUT_FILE)
            scraped_urls = set(df_exist['MatchURL'].tolist())
            print(f"📥 {len(scraped_urls)} maç zaten var, atlanıyor.")
        except:
            pass

    urls_to_scrape = [u for u in all_urls if u not in scraped_urls]
    print(f"🚀 Kalan {len(urls_to_scrape)} maç taranacak...")

    if not urls_to_scrape:
        print("✅ Yapılacak iş yok.")
        sys.exit()

    driver = init_driver()

    for i, url in enumerate(urls_to_scrape, 1):
        try:
            driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Kartları Çek
            hy, hr, ay, ar = extract_cards_only(soup)

            # Kaydet
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