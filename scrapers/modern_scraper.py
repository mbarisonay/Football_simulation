import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import re
import pprint

# --- AYARLAR ---
BASE_URL = "https://fbref.com"
OUTPUT_FILE = "ALL_LEAGUES_MATCHES_2000_2025.csv"  # Tek büyük dosya
all_matches_data = []

SEASONS_TO_SCRAPE = list(range(2014, 2025))  # 2014-2025 arası (FIFA verinle eşleşsin diye)

# --- LİGLER (FBref ID'leri) ---
COMPETITIONS = [
    {"id": "9",  "name": "Premier-League", "league_tag": "Premier League"},
    {"id": "12", "name": "La-Liga",        "league_tag": "La Liga"},
    {"id": "20", "name": "Bundesliga",     "league_tag": "Bundesliga"},
    {"id": "11", "name": "Serie-A",        "league_tag": "Serie A"},
    {"id": "13", "name": "Ligue-1",        "league_tag": "Ligue 1"},
    {"id": "26", "name": "Super-Lig",      "league_tag": "Süper Lig"},
    {"id": "32", "name": "Primeira-Liga",  "league_tag": "Liga Portugal"}
]

options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")

driver = None
try:
    driver = uc.Chrome(options=options, use_subprocess=True)
    print("Cloudflare kontrolü için bekleniyor (15sn)...")
    driver.get(BASE_URL)
    time.sleep(15)
    wait = WebDriverWait(driver, 30)

    # --- DÖNGÜ 1: LİGLER ---
    for comp in COMPETITIONS:
        print(f"\n\n🏆 ŞAMPİYONA BAŞLIYOR: {comp['league_tag']} 🏆")

        # --- DÖNGÜ 2: SEZONLAR ---
        for year in SEASONS_TO_SCRAPE:
            season_year_str = f"{year}-{year + 1}"
            print(f"\n  -> Sezon: {season_year_str}")

            try:
                # Fikstür URL'si
                fixture_url = f"{BASE_URL}/en/comps/{comp['id']}/{season_year_str}/schedule/{season_year_str}-{comp['name']}-Scores-and-Fixtures"
                driver.get(fixture_url)
                time.sleep(4)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                match_links_tags = soup.select("td[data-stat='match_report'] a")

                if not match_links_tags:
                    print("    Maç linki bulunamadı. Atlanıyor.")
                    continue

                match_links = [BASE_URL + a['href'] for a in match_links_tags]
                print(f"    {len(match_links)} maç bulundu.")

                # --- DÖNGÜ 3: MAÇLAR ---
                for i, url in enumerate(match_links, 1):
                    try:
                        driver.get(url)
                        # Rastgele bekleme (FBref çok hassastır)
                        time.sleep(random.uniform(3, 6))

                        match_soup = BeautifulSoup(driver.page_source, "html.parser")
                        content = match_soup.select_one("#content")
                        if not content: continue

                        # Skor ve Takımlar
                        scorebox = content.select_one("div.scorebox")
                        if not scorebox: continue

                        teams = scorebox.select("a[href*='/squads/']")
                        scores = scorebox.select("div.score")

                        if len(teams) < 2 or len(scores) < 2: continue

                        home = teams[0].get_text(strip=True)
                        away = teams[1].get_text(strip=True)
                        h_goal = scores[0].get_text(strip=True)
                        a_goal = scores[1].get_text(strip=True)

                        # Basit Veri Paketi
                        match_data = {
                            "League": comp['league_tag'],  # Lig adını ekliyoruz
                            "Season": season_year_str,
                            "HomeTeam": home,
                            "AwayTeam": away,
                            "FTHG": h_goal,
                            "FTAG": a_goal
                        }

                        # (İsteğe bağlı: Detaylı istatistikleri de buraya ekleyebilirsin
                        # ama sadece skor tahmini için yukarıdakiler temel olarak yeterli.
                        # Eğer önceki kodundaki 'modern parser' detaylarını istiyorsan
                        # o bloğu buraya kopyalayabilirsin.)

                        all_matches_data.append(match_data)
                        print(f"    {i}: {home} {h_goal}-{a_goal} {away}")

                    except Exception as e:
                        print(f"    Hata: {e}")
                        continue

            except Exception as e:
                print(f"  Sezon Hatası: {e}")
                continue

            # Her sezon sonu kaydet (Veri kaybını önlemek için)
            pd.DataFrame(all_matches_data).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            print(f"  💾 Kaydedildi: {len(all_matches_data)} maç.")

finally:
    if driver: driver.quit()
    print("\nBitti!")