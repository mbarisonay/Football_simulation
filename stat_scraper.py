# scrape_sofifa.py (FIFA 15'ten FC 25'e Premier Lig Oyuncu Reytinglerini Çeken Kod)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random

# --- AYARLAR ---
BASE_URL = "https://sofifa.com/players"
OUTPUT_FILE = "sofifa_player_ratings_fifa15_fc25.csv"
all_players_data = []

# SoFIFA'daki sürüm kodlarını ve oyun isimlerini eşleştirelim
# FIFA 15 -> v=15, EA FC 25 -> v=25
FIFA_VERSIONS = {
    15: "FIFA 15", 16: "FIFA 16", 17: "FIFA 17", 18: "FIFA 18", 19: "FIFA 19",
    20: "FIFA 20", 21: "FIFA 21", 22: "FIFA 22", 23: "FIFA 23", 24: "FIFA 24",
    25: "EA FC 25"
}

# Premier League'in SoFIFA'daki lig ID'si 13'tür.
PREMIER_LEAGUE_ID = 13

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# options.add_argument("--headless=new") # Test ederken kapalı tutun

driver = None
try:
    # Selenium 4'ün kendi sürücü yöneticisini kullanıyoruz, en stabil yöntem.
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 10)

    # Adım 1: Her bir FIFA sürümü için ana döngüyü başlat
    for version_code, version_name in FIFA_VERSIONS.items():
        # Sezonu hesapla (örn: FIFA 15 = 2014-2015 sezonu)
        season_start = 2000 + version_code - 1
        season_end = season_start + 1
        season_str = f"{season_start}-{season_end}"

        print(f"\n{'=' * 60}\n--- Veri Çekiliyor: {version_name} ({season_str} Sezonu) ---\n{'=' * 60}")

        offset = 0  # Sayfalama için başlangıç noktası

        # Adım 2: Bir sürümdeki tüm sayfaları gezmek için döngü
        while True:
            # URL'yi oluştur: Sürüm kodu, lig ID'si ve sayfa offset'i ile
            url = f"{BASE_URL}?v={version_code}&league={PREMIER_LEAGUE_ID}&offset={offset}"

            print(f"  -> Sayfa işleniyor: {url}")
            driver.get(url)

            # Oyuncu tablosunun yüklenmesini bekle
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-players")))
            except:
                print("  -> Sayfa zaman aşımına uğradı veya tablo bulunamadı. Bu sürüm atlanıyor.")
                break  # Bir sonraki FIFA sürümüne geç

            soup = BeautifulSoup(driver.page_source, "html.parser")
            player_rows = soup.select("table.table-players tbody tr")

            # Eğer sayfada hiç oyuncu yoksa, o FIFA sürümü için işlem bitmiştir.
            if not player_rows:
                print(" -> Bu sürüm için daha fazla oyuncu bulunamadı.")
                break  # While döngüsünü kır ve bir sonraki FIFA sürümüne geç

            # Adım 3: Sayfadaki her bir oyuncu satırını işle
            for row in player_rows:
                try:
                    player_name = row.select_one("td.col-name a div").get_text(strip=True)
                    player_age = int(row.select_one("td.col-ae").get_text(strip=True))
                    overall_rating = int(row.select_one("td.col-oa span").get_text(strip=True))
                    potential_rating = int(row.select_one("td.col-pt span").get_text(strip=True))

                    # Kulüp ismi, ismin altındaki küçük linkte yer alır
                    club_element = row.select_one("td.col-name .subtitle a")
                    club_name = club_element.get_text(strip=True) if club_element else "Unknown"

                    # Çekilen veriyi listeye ekle
                    all_players_data.append({
                        "GameVersion": version_name,
                        "Season": season_str,
                        "PlayerName": player_name,
                        "Club": club_name,
                        "Age": player_age,
                        "Overall": overall_rating,
                        "Potential": potential_rating
                    })
                except Exception as e:
                    # Bir satırda hata olursa atla ve devam et
                    print(f"    - Bir oyuncu satırı işlenirken hata oluştu: {e}")
                    continue

            print(f"  -> Bu sayfadan {len(player_rows)} oyuncu çekildi. Toplam: {len(all_players_data)}")

            # Sonraki sayfaya geçmek için offset'i artır (SoFIFA sayfa başına 60 oyuncu gösterir)
            offset += 60
            time.sleep(random.uniform(1, 2.5))  # Siteye yük bindirmemek için bekle

finally:
    if driver:
        driver.quit()

# Adım 4: Tüm verileri bir DataFrame'e dönüştür ve CSV dosyasına kaydet
if all_players_data:
    df = pd.DataFrame(all_players_data)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ İşlem tamamlandı! {len(df)} oyuncu kaydı '{OUTPUT_FILE}' dosyasına başarıyla kaydedildi.")
else:
    print("\n❌ Hiçbir veri çekilemedi. Bir sorun oluştu.")