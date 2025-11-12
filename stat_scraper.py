# scrape_sofifa_all_stats.py (Tüm Detaylı Oyuncu Statlarını Çeken Final Kodu)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import os

# --- AYARLAR ---
# Verdiğiniz URL'nin temel kısmı
BASE_URL = "https://sofifa.com/players?type=all&lg%5B0%5D=13"
# Tüm statları gösteren sütun parametreleri
COLUMNS_PARAMS = "&showCol%5B0%5D=ae&showCol%5B1%5D=oa&showCol%5B2%5D=pt&showCol%5B3%5D=vl&showCol%5B4%5D=wg&showCol%5B5%5D=ta&showCol%5B6%5D=cr&showCol%5B7%5D=fi&showCol%5B8%5D=he&showCol%5B9%5D=sh&showCol%5B10%5D=vo&showCol%5B11%5D=ts&showCol%5B12%5D=dr&showCol%5B13%5D=cu&showCol%5B14%5D=fr&showCol%5B15%5D=lo&showCol%5B16%5D=bl&showCol%5B17%5D=to&showCol%5B18%5D=ac&showCol%5B19%5D=sp&showCol%5B20%5D=ag&showCol%5B21%5D=re&showCol%5B22%5D=ba&showCol%5B23%5D=tp&showCol%5B24%5D=so&showCol%5B25%5D=ju&showCol%5B26%5D=st&showCol%5B27%5D=sr&showCol%5B28%5D=ln&showCol%5B29%5D=te&showCol%5B30%5D=ar&showCol%5B31%5D=in&showCol%5B32%5D=po&showCol%5B33%5D=vi&showCol%5B34%5D=pe&showCol%5B35%5D=cm&showCol%5B36%5D=td&showCol%5B37%5D=ma&showCol%5B38%5D=sa&showCol%5B39%5D=sl&showCol%5B40%5D=tg&showCol%5B41%5D=gd&showCol%5B42%5D=gh&showCol%5B43%5D=gc&showCol%5B44%5D=gp&showCol%5B45%5D=gr"
# Sıralama parametreleri
SORT_PARAMS = "&col=oa&sort=desc"

# Çekilecek statların SoFIFA'daki `data-col` etiketlerine göre haritası
# Bu, kodu çok daha sağlam ve okunabilir yapar.
STATS_MAP = {
    'PlayerName': 'name', 'Positions': 'positions', 'Age': 'ae', 'Overall': 'oa', 'Potential': 'pt', 'Club': 'club',
    'Crossing': 'cr', 'Finishing': 'fi', 'HeadingAccuracy': 'he', 'ShortPassing': 'sh', 'Volleys': 'vo',
    'Dribbling': 'dr', 'Curve': 'cu', 'FKAccuracy': 'fr', 'LongPassing': 'lo', 'BallControl': 'bl',
    'Acceleration': 'ac', 'SprintSpeed': 'sp', 'Agility': 'ag', 'Reactions': 're', 'Balance': 'ba',
    'ShotPower': 'so', 'Jumping': 'ju', 'Stamina': 'st', 'Strength': 'sr', 'LongShots': 'ln',
    'Aggression': 'ar', 'Interceptions': 'in', 'Positioning': 'po', 'Vision': 'vi', 'Penalties': 'pe',
    'Composure': 'cm', 'Marking': 'ma', 'StandingTackle': 'sa', 'SlidingTackle': 'sl',
    'GKDiving': 'gd', 'GKHandling': 'gh', 'GKKicking': 'gc', 'GKPositioning': 'gp', 'GKReflexes': 'gr'
}

# Hangi FIFA sürümlerini çekeceğimizi belirleyelim
FIFA_VERSIONS = {
    15: "FIFA 15", 16: "FIFA 16", 17: "FIFA 17", 18: "FIFA 18", 19: "FIFA 19",
    20: "FIFA 20", 21: "FIFA 21", 22: "FIFA 22", 23: "FIFA 23", 24: "FIFA 24",
    25: "EA FC 25", 26: "EA FC 26"
}

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
options.add_argument("--headless=new")  # Kodu test ettikten sonra açabilirsiniz, daha hızlı çalışır

driver = None
try:
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 20)

    # Her FIFA sürümü için döngü
    for version_code, version_name in FIFA_VERSIONS.items():
        season_start = 2000 + version_code - 1
        season_str = f"{season_start}-{season_start + 1}"
        print(f"\n{'=' * 60}\n--- Veri Çekiliyor: {version_name} ({season_str} Sezonu) ---\n{'=' * 60}")

        all_players_data = []  # Her sezon için verileri sıfırla
        offset = 0

        # Bir sürümdeki tüm sayfaları gezmek için döngü
        while True:
            url = f"{BASE_URL}{COLUMNS_PARAMS}&v={version_code}&offset={offset}{SORT_PARAMS}"
            print(f"  -> Sayfa işleniyor: {url}")
            driver.get(url)

            try:
                # Çerez penceresini kabul et (sadece ilk seferde gerekli olabilir)
                if offset == 0:
                    try:
                        accept_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
                        accept_button.click()
                        print("  -> Çerezler kabul edildi.")
                    except:
                        print("  -> Çerez penceresi bulunamadı.")

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-players tbody tr")))
            except:
                print("  -> Oyuncu tablosu bulunamadı. Bu sürüm için işlem tamamlanmış olabilir.")
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")
            player_rows = soup.select("table.table-players tbody tr")

            if not player_rows:
                print("  -> Bu sürüm için daha fazla oyuncu bulunamadı.")
                break

            for row in player_rows:
                player_data = {}
                try:
                    # Temel bilgileri çek
                    player_data['PlayerName'] = row.select_one('a[data-tippy-content]').get('data-tippy-content')
                    player_data['Club'] = row.select_one('figure.team img').get('alt')

                    positions = [pos.get_text(strip=True) for pos in row.select('td:nth-of-type(2) a span.pos')]
                    player_data['Positions'] = ', '.join(positions)

                    # STATS_MAP kullanarak tüm statları dinamik olarak çek
                    for stat_name, col_code in STATS_MAP.items():
                        if col_code not in ['name', 'positions', 'club']:
                            element = row.select_one(f'td[data-col="{col_code}"] em')
                            if element:
                                player_data[stat_name] = int(element.get_text(strip=True))
                            else:
                                player_data[stat_name] = 0  # Eğer bir stat bulunamazsa 0 ata

                    all_players_data.append(player_data)

                except Exception as e:
                    print(f"    - Bir satır işlenirken hata (atlandı): {e}")
                    continue

            print(f"  -> Bu sayfadan {len(player_rows)} oyuncu çekildi. Toplam {len(all_players_data)} oyuncu.")
            offset += 60
            time.sleep(random.uniform(1, 2))

        # Sezon bittiğinde, toplanan verileri kulüplere göre ayrı CSV dosyalarına kaydet
        if all_players_data:
            df = pd.DataFrame(all_players_data)

            # Kayıt için bir klasör oluştur
            output_folder = f"FIFA_Ratings/{version_name}_{season_str}"
            os.makedirs(output_folder, exist_ok=True)

            # Her bir kulüp için ayrı CSV dosyası oluştur
            for club_name, club_data in df.groupby('Club'):
                # Dosya isimlerinde geçersiz karakterleri temizle
                safe_club_name = "".join(x for x in club_name if x.isalnum() or x in " _-").strip()
                file_path = os.path.join(output_folder, f"{safe_club_name}.csv")
                club_data.to_csv(file_path, index=False, encoding='utf-8-sig')

            print(f"\n  -> {version_name} verileri '{output_folder}' klasöründeki kulüp CSV'lerine kaydedildi.")

finally:
    if driver:
        driver.quit()
    print("\n✅ Tüm işlemler tamamlandı!")