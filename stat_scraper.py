# scrape_sofifa_detailed.py (Bir Takımın Detaylı Oyuncu Statlarını Çeken Kod)

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
# FIFA 15 (v=15), Chelsea (ID=5)
TARGET_URL = "https://sofifa.com/team/5/chelsea/?v=15"

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# options.add_argument("--headless=new")

driver = None
try:
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 15)

    print(f"Hedef URL'ye gidiliyor: {TARGET_URL}")
    driver.get(TARGET_URL)

    # Oyuncu tablosunun yüklenmesini bekle
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-players")))

    # Sayfadaki tüm oyuncuların linklerini ve temel bilgilerini topla
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

    # Adım 2: Her oyuncunun kendi sayfasına git
    for i, player_info in enumerate(player_info_list, 1):
        print(f"  -> İşleniyor: {i}/{len(player_info_list)} - {player_info['name']}")
        driver.get(player_info['url'])

        try:
            # Oyuncu detaylarının (grid) yüklenmesini bekle
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid")))
            player_soup = BeautifulSoup(driver.page_source, "html.parser")

            # Oyuncunun temel bilgilerini (Overall, Potential) doğrudan profil sayfasından alalım
            # Bu, en doğru bilgiyi garanti eder
            grid_cols = player_soup.select("div.grid > div.col")
            overall = int(grid_cols[0].find("em").get_text(strip=True))
            potential = int(grid_cols[1].find("em").get_text(strip=True))

            # Statları toplamak için bir sözlük oluştur
            player_stats = {
                "GameVersion": "FIFA 15",
                "Season": "2014-2015",
                "PlayerName": player_info['name'],
                "Club": "Chelsea",  # Sabit olarak biliyoruz
                "Overall": overall,
                "Potential": potential
            }

            # Tüm "grid attribute" bloklarını bul
            attribute_blocks = player_soup.select("div.grid.attribute")
            for block in attribute_blocks:
                # Blok başlığını al (örn: "Attacking", "Goalkeeping")
                block_title = block.find("h5").get_text(strip=True)

                # Blok içindeki her bir stat'ı (`col` div'i) işle
                for stat_col in block.select("div.col"):
                    try:
                        value = int(stat_col.find("em").get_text(strip=True))
                        # Stat ismini alırken, "GK Diving" gibi isimleri birleştirelim
                        stat_name_raw = stat_col.get_text(strip=True)
                        stat_name = re.sub(r'^\d+', '', stat_name_raw).strip()  # Başındaki sayıyı kaldır

                        # Eğer kaleci statı ise başına "GK" ekleyelim ki karışmasın
                        if block_title == "Goalkeeping":
                            stat_name = f"GK {stat_name}"

                        player_stats[stat_name] = value
                    except:
                        continue  # Hatalı stat satırını atla

            all_players_data.append(player_stats)
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"    - HATA: {player_info['name']} işlenirken sorun oluştu: {e}")
            continue

finally:
    if driver:
        driver.quit()

# Adım 3: Tüm verileri bir DataFrame'e dönüştür ve CSV dosyasına kaydet
if all_players_data:
    df = pd.DataFrame(all_players_data)
    # NaN (boş) değerleri 0 ile dolduralım. Örneğin, bir forvetin GK statları boş kalacaktır.
    df.fillna(0, inplace=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ İşlem tamamlandı! {len(df)} oyuncu kaydı '{OUTPUT_FILE}' dosyasına başarıyla kaydedildi.")
else:
    print("\n❌ Hiçbir veri çekilemedi. Bir sorun oluştu.")