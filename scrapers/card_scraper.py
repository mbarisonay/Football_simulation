import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
import os
import subprocess

# --- AYARLAR ---
# Ana dosyanın yolu (URL'leri buradan alacağız)
SOURCE_FILE = "ALL_LEAGUES_DETAILED_MATCHES.csv"
# Kartların kaydedileceği yeni dosya
OUTPUT_FILE = "MATCH_CARDS.csv"


# --- DRIVER YÖNETİMİ ---
def init_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = 'eager'  # Hız için
    try:
        d = uc.Chrome(options=options, use_subprocess=True)
        d.set_page_load_timeout(60)
        return d
    except:
        time.sleep(5)
        return init_driver()


# --- DOSYA OKUMA ---
if not os.path.exists(SOURCE_FILE):
    print(f"❌ HATA: {SOURCE_FILE} bulunamadı. Önce diğer scraper'ı çalıştırın.")
    exit()

# Sadece URL'leri alıyoruz
df_source = pd.read_csv(SOURCE_FILE, usecols=['MatchURL'])
all_urls = df_source['MatchURL'].unique().tolist()

# Daha önce çekilen kartlar varsa onları atlayalım
scraped_urls = set()
if os.path.exists(OUTPUT_FILE):
    try:
        df_existing = pd.read_csv(OUTPUT_FILE)
        scraped_urls = set(df_existing['MatchURL'].tolist())
        print(f"📥 {len(scraped_urls)} maçın kart verisi zaten var, atlanacak.")
    except:
        pass

# Çekilecek URL listesi
urls_to_scrape = [u for u in all_urls if u not in scraped_urls]
print(f"🚀 Toplam {len(urls_to_scrape)} maçın kart verisi çekilecek...")

driver = init_driver()


# --- PARSER ---
def extract_cards_only(soup):
    """ Sadece kart ikonlarını sayar """
    # "Cards" başlığını bul
    header = soup.find(lambda tag: tag.name in ["div", "th"] and "Cards" in tag.get_text())
    hy, hr, ay, ar = 0, 0, 0, 0

    if header:
        container = None
        if header.name == "th":
            container = header.find_parent("tr").find_next_sibling("tr")
        else:
            # Div yapısı
            container = header.find_parent("tr")
            if container: container = container.find_next_sibling("tr")

        if container:
            cols = container.find_all("td")  # veya div
            if not cols: cols = container.find_all("div", recursive=False)

            if len(cols) >= 2:
                # Ev Sahibi
                hy = len(cols[0].select('.yellow_card'))
                hr = len(cols[0].select('.red_card')) + len(cols[0].select('.yellow_red_card'))

                # Deplasman
                ay = len(cols[1].select('.yellow_card'))
                ar = len(cols[1].select('.red_card')) + len(cols[1].select('.yellow_red_card'))

    return hy, hr, ay, ar


# --- DÖNGÜ ---
try:
    for i, url in enumerate(urls_to_scrape, 1):
        try:
            driver.get(url)
            time.sleep(random.uniform(1.5, 3.0))  # Sadece kart bakacağımız için biraz hızlı olabilir

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Kartları Çek
            hy, hr, ay, ar = extract_cards_only(soup)

            card_data = {
                "MatchURL": url,
                "HomeYellowCards": hy,
                "HomeRedCards": hr,
                "AwayYellowCards": ay,
                "AwayRedCards": ar
            }

            # Anlık Kayıt
            df_single = pd.DataFrame([card_data])
            header_mode = not os.path.exists(OUTPUT_FILE)
            df_single.to_csv(OUTPUT_FILE, mode='a', header=header_mode, index=False)

            print(f"✅ {i}/{len(urls_to_scrape)} Kartlar: 🟨 {hy}-{ay} | 🟥 {hr}-{ar}")

        except Exception as e:
            print(f"⚠️ Hata ({url}): {e}")
            # Hata olsa bile driver'ı yeniden başlatıp devam etmeye çalış
            try:
                driver.quit(); driver = init_driver()
            except:
                pass

except KeyboardInterrupt:
    print("\n🛑 Durduruldu.")

finally:
    if driver: driver.quit()
    print("\n🏁 Kart çekme işlemi bitti.")