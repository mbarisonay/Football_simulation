# scrape_sofifa_detailed.py (Hata Düzeltmeli ve Sağlamlaştırılmış Versiyon)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import re

# --- AYARLAR ---
BASE_URL = "https://sofifa.com"
OUTPUT_FILE = "fifa15_chelsea_detailed_stats.csv"
all_players_data = []

# --- HEDEF ---
TARGET_URL = "https://sofifa.com/team/5/chelsea/?v=15"

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# options.add_argument("--headless=new")

driver = None
try:
    driver = webdriver.Chrome(service=Service(), options=options)
    # Bekleme süresini 20 saniyeye çıkaralım
    wait = WebDriverWait(driver, 20)

    print(f"Hedef URL'ye gidiliyor: {TARGET_URL}")
    driver.get(TARGET_URL)

    # --- YENİ BÖLÜM: Çerez (Cookie) Penceresini Kapatma ---
    try:
        print("-> Çerez onay penceresi kontrol ediliyor...")
        # Butonun metni "Accept All" veya benzeri olabilir. Metne göre arama yapıyoruz.
        accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
        accept_button.click()
        print("-> Çerezler kabul edildi.")
        time.sleep(2)  # Sayfanın yeniden oturması için kısa bir bekleme
    except Exception:
        # Eğer buton bulunamazsa veya tıklanamazsa, sorun değil. Muhtemelen pencere yoktu.
        print("-> Çerez onay penceresi bulunamadı veya zaten kabul edilmiş. Devam ediliyor.")
        pass
    # --- YENİ BÖLÜM SONU ---

    # Oyuncu tablosunun yüklenmesini bekle
    print("-> Oyuncu tablosunun yüklenmesi bekleniyor...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-players")))
    print("-> Oyuncu tablosu başarıyla yüklendi.")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    player_rows = soup.select("table.table-players tbody tr")

    player_info_list = []
    for row in player_rows:
        link_tag = row.select_one("td.col-name a")
        if link_tag:
            player_info_list.append({
                'url': BASE_URL + link_tag['href'],
                'name': link_tag.select_one("div").get_text(strip=True),
                'overall': int(row.select_one("td.col-oa span").get_text(strip=True)),
                'potential': int(row.select_one("td.col-pt span").get_text(strip=True))
            })

    print(f"-> {len(player_info_list)} oyuncu bulundu. Detaylı statlar çekiliyor...")

    # (Kodun geri kalan kısmı aynı, burada değişiklik yok)
    for i, player_info in enumerate(player_info_list, 1):
        print(f"  -> İşleniyor: {i}/{len(player_info_list)} - {player_info['name']}")
        driver.get(player_info['url'])

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid")))
            player_soup = BeautifulSoup(driver.page_source, "html.parser")

            grid_cols = player_soup.select("div.grid > div.col")
            overall = int(grid_cols[0].find("em").get_text(strip=True))
            potential = int(grid_cols[1].find("em").get_text(strip=True))

            player_stats = {
                "GameVersion": "FIFA 15",
                "Season": "2014-2015",
                "PlayerName": player_info['name'],
                "Club": "Chelsea",
                "Overall": overall,
                "Potential": potential
            }

            attribute_blocks = player_soup.select("div.grid.attribute")
            for block in attribute_blocks:
                block_title = block.find("h5").get_text(strip=True)
                for stat_col in block.select("div.col"):
                    try:
                        value = int(stat_col.find("em").get_text(strip=True))
                        stat_name_raw = stat_col.get_text(strip=True)
                        stat_name = re.sub(r'^\d+', '', stat_name_raw).strip()
                        if block_title == "Goalkeeping":
                            stat_name = f"GK {stat_name}"
                        player_stats[stat_name] = value
                    except:
                        continue

            all_players_data.append(player_stats)
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"    - HATA: {player_info['name']} işlenirken sorun oluştu: {e}")
            continue

finally:
    if driver:
        driver.quit()

if all_players_data:
    df = pd.DataFrame(all_players_data)
    df.fillna(0, inplace=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ İşlem tamamlandı! {len(df)} oyuncu kaydı '{OUTPUT_FILE}' dosyasına başarıyla kaydedildi.")
else:
    print("\n❌ Hiçbir veri çekilemedi. Bir sorun oluştu.")