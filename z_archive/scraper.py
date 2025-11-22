# import_transfermarkt.py (Geliştirilmiş Teşhis Versiyonu)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import sys
import os

# Proje kök dizinini sisteme tanıt
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# --------------------------------------
# Ayarlar
# --------------------------------------
BASE_URL = "https://www.transfermarkt.com"
SEASONS = list(range(2000, 2025))  # Test için sadece 1 sezon çalıştıralım
OUTPUT_FILE = "premier_league_squads_2000_2025.csv"
all_data = []

# --- TAKIM EŞLEŞTİRME SÖZLÜĞÜ (EN ÖNEMLİ KISIM) ---
# Transfermarkt'taki ismi, bizim veritabanımızdaki isme çevirir
TAKIM_ESLESTIRME = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham",
    "Nottingham Forest": "Nott'm Forest",
    "Wolverhampton Wanderers": "Wolves",
    "West Ham United": "West Ham",
    "AFC Bournemouth": "Bournemouth",
    "Sheffield United": "Sheffield Utd"  # Örnek: Belki 'Sheffield United' yerine 'Sheffield Utd' yazıyordur
    # Eşleşmeyen diğer takımları buraya ekleyeceğiz
}

# --------------------------------------
# Selenium Başlat
# --------------------------------------
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new") # Test ederken kapalı kalsın
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = None
try:
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    for season in SEASONS:
        print(f"\n--- {season}-{season + 1} sezonu işleniyor ---")

        league_url = f"{BASE_URL}/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={season}"
        driver.get(league_url)

        # Çerezleri kabul et
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_1056579")))
            accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="ACCEPT ALL"]')))
            accept_button.click()
            print("  [✓] Çerezler kabul edildi.")
            driver.switch_to.default_content()
        except Exception:
            print("  [!] Çerez penceresi bulunamadı, devam ediliyor.")
            driver.switch_to.default_content()

        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        team_links = soup.select("table.items tbody tr.odd, table.items tbody tr.even")

        print(f"\nSezon sayfasında {len(team_links)} takım satırı bulundu. Kontrol ediliyor...")

        for team_row in team_links:
            team_link_tag = team_row.select_one("td.hauptlink a")
            if not team_link_tag: continue

            tm_team_name = team_link_tag.get_text(strip=True)  # Transfermarkt'taki isim

            # --- YENİ EŞLEŞTİRME VE KONTROL MANTIĞI ---
            # Önce eşleştirme sözlüğünü kullanarak ismi standart hale getir
            db_team_name = TAKIM_ESLESTIRME.get(tm_team_name, tm_team_name)

            print(f"  - Bulunan takım: '{tm_team_name}' -> Dönüştürülen isim: '{db_team_name}'")
            # Bu takımın kadrosunu çekmeye gerek var mı, yok mu diye burada karar verebiliriz
            # Şimdilik tümünü çekelim
            # ------------------------------------------------

            team_squad_url = f"{BASE_URL}{team_link_tag['href'].replace('/startseite/', '/kader/')}/plus/0/galerie/0?saison_id={season}"

            driver.get(team_squad_url)
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.items tbody tr")))
                squad_soup = BeautifulSoup(driver.page_source, "html.parser")
                player_rows = squad_soup.select("table.items tbody tr.odd, table.items tbody tr.even")
                print(f"    → {db_team_name} kadrosu alınıyor... ({len(player_rows)} oyuncu bulundu)")

                for row in player_rows:
                    cells = row.find_all('td', recursive=False)
                    if len(cells) < 3: continue

                    name_cell = cells[1].select_one('table.inline-table td.hauptlink a')
                    if not name_cell: continue

                    name = name_cell.get_text(strip=True)
                    position = row.select_one('td:nth-of-type(4)').get_text(strip=True)
                    nationality_tags = cells[5].select('img.flaggenrahmen') if len(cells) > 5 else []
                    nationalities = ", ".join([img['title'] for img in nationality_tags])

                    all_data.append({
                        "Season": f"{season}-{season + 1}",
                        "Team": db_team_name,  # Standardize edilmiş ismi kullan
                        "Player": name,
                        "Position": position,
                        "Nationality": nationalities
                    })
                time.sleep(1)
            except Exception as e:
                print(f"    ⚠️ {db_team_name} kadrosu alınırken hata: {e}")
                continue
finally:
    if driver:
        driver.quit()

if all_data:
    df = pd.DataFrame(all_data)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(
        f"\n✅ İşlem tamamlandı! {len(df['Team'].unique())} takımdan {len(df)} kayıt '{OUTPUT_FILE}' dosyasına kaydedildi.")
else:
    print("\nHiçbir veri çekilemedi.")