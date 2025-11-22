import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time
import random
import os
import re
import sys

# --- URL AYARLARI ---
# Tüm özellikleri (Agility, Balance, vb.) getiren uzun URL
BASE_URL_TEMPLATE = "https://sofifa.com/players?type=all&lg%5B0%5D=13&showCol%5B0%5D=ae&showCol%5B1%5D=oa&showCol%5B2%5D=pt&showCol%5B3%5D=vl&showCol%5B4%5D=wg&showCol%5B5%5D=ta&showCol%5B6%5D=cr&showCol%5B7%5D=fi&showCol%5B8%5D=he&showCol%5B9%5D=sh&showCol%5B10%5D=vo&showCol%5B11%5D=ts&showCol%5B12%5D=dr&showCol%5B13%5D=cu&showCol%5B14%5D=fr&showCol%5B15%5D=lo&showCol%5B16%5D=bl&showCol%5B17%5D=to&showCol%5B18%5D=ac&showCol%5B19%5D=sp&showCol%5B20%5D=ag&showCol%5B21%5D=re&showCol%5B22%5D=ba&showCol%5B23%5D=tp&showCol%5B24%5D=so&showCol%5B25%5D=ju&showCol%5B26%5D=st&showCol%5B27%5D=sr&showCol%5B28%5D=ln&showCol%5B29%5D=te&showCol%5B30%5D=ar&showCol%5B31%5D=in&showCol%5B32%5D=po&showCol%5B33%5D=vi&showCol%5B34%5D=pe&showCol%5B35%5D=cm&showCol%5B36%5D=td&showCol%5B37%5D=ma&showCol%5B38%5D=sa&showCol%5B39%5D=sl&showCol%5B40%5D=tg&showCol%5B41%5D=gd&showCol%5B42%5D=gh&showCol%5B43%5D=gc&showCol%5B44%5D=gp&showCol%5B45%5D=gr"

# HTML 'data-col' kodları -> CSV Başlıkları
STATS_MAP_TABLE = {
    'ae': 'Age', 'oa': 'Overall', 'pt': 'Potential',
    'cr': 'Crossing', 'fi': 'Finishing', 'he': 'HeadingAccuracy', 'sh': 'ShortPassing',
    'vo': 'Volleys', 'dr': 'Dribbling', 'cu': 'Curve', 'fr': 'FKAccuracy', 'lo': 'LongPassing',
    'bl': 'BallControl', 'ac': 'Acceleration', 'sp': 'SprintSpeed', 'ag': 'Agility', 're': 'Reactions',
    'ba': 'Balance', 'so': 'ShotPower', 'ju': 'Jumping', 'st': 'Stamina', 'sr': 'Strength', 'ln': 'LongShots',
    'ar': 'Aggression', 'in': 'Interceptions', 'po': 'Positioning', 'vi': 'Vision', 'pe': 'Penalties',
    'cm': 'Composure', 'ma': 'Marking', 'sa': 'StandingTackle', 'sl': 'SlidingTackle',
    'gd': 'GKDiving', 'gh': 'GKHandling', 'gc': 'GKKicking', 'gp': 'GKPositioning', 'gr': 'GKReflexes'
}

FIFA_ROSTERS = {
    "FIFA 15": ("2014-2015", "150059"),
    "FIFA 16": ("2015-2016", "160058"),
    "FIFA 17": ("2016-2017", "170099"),
    "FIFA 18": ("2017-2018", "180084"),
    "FIFA 19": ("2018-2019", "190075"),
    "FIFA 20": ("2019-2020", "200061"),
    "FIFA 21": ("2020-2021", "210064"),
    "FIFA 22": ("2021-2022", "220069"),
    "FIFA 23": ("2022-2023", "230069"),
    "FC 24": ("2023-2024", "240053"),
    "FC 25": ("2024-2025", "250001")
}


def clean_stat(value):
    if not value: return "0"
    # Sayısal değeri al (85+2 -> 85)
    match = re.search(r'^\d+', str(value).strip())
    return match.group(0) if match else str(value).strip()


# --- PARSER (VERİ AYIKLAYICI) ---
def parse_via_table(soup, version_name, season_str):
    players_data = []
    # Tabloyu bul
    table = soup.find('table')
    if not table: return []

    tbody = table.find('tbody')
    if not tbody: return []

    # Satırları gez
    for row in tbody.find_all('tr'):
        try:
            # -- İSİM BULMA (GÜÇLENDİRİLMİŞ YÖNTEM) --
            # Class ismine bakmaksızın, satırdaki ilk oyuncu linkini alıyoruz.
            name_link = row.select_one("a[href*='/player/']")

            if not name_link:
                # Eğer link yoksa, bu bir başlık satırı olabilir, geçiyoruz.
                continue

            player_name = name_link.get_text(strip=True)  # Linkin içindeki yazıyı (E. Hazard) al

            # -- TAKIM BULMA --
            team_link = row.select_one("a[href*='/team/']")
            team_name = team_link.get_text(strip=True) if team_link else "Unknown"

            p_data = {
                "Season": season_str,
                "FifaVersion": version_name,
                "Name": player_name,
                "Team": team_name
            }

            # -- İSTATİSTİKLERİ ÇEKME --
            # data-col="oa" gibi öznitelikleri arıyoruz
            for code, header in STATS_MAP_TABLE.items():
                col = row.find('td', {'data-col': code})
                if col:
                    # Bazen değer <span> içinde olur, bazen direkt text
                    val = col.get_text(strip=True)
                    p_data[header] = clean_stat(val)
                else:
                    p_data[header] = "0"

            players_data.append(p_data)

        except Exception as e:
            # Tek bir satırda hata olursa tüm programı durdurma, o satırı atla
            # print(f"Satır hatası: {e}")
            continue

    return players_data


# --- ANA PROGRAM ---
driver = None
tum_veriler_toplam = []

try:
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), "sofifa_profile")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--lang=en-US")
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--disable-blink-features=AutomationControlled')

    print("Tarayıcı başlatılıyor...")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    print("SoFIFA'ya gidiliyor...")
    driver.get("https://sofifa.com")
    print("\n--- DOĞRULAMA ---")
    print("Lütfen tarayıcıdaki kontrolleri geçin (Accept All / Captcha).")
    input("Hazırsanız ENTER'a basın...")

    for version_name, (season_str, roster_id) in FIFA_ROSTERS.items():
        print(f"\n{'=' * 60}\n--- {version_name} ({season_str}) İşleniyor ---\n{'=' * 60}")
        all_season_players = []
        offset = 0

        while True:
            # URL oluştur
            target_url = f"{BASE_URL_TEMPLATE}&r={roster_id}&set=true&offset={offset}"

            try:
                driver.get(target_url)
                time.sleep(random.uniform(3, 5))  # Bekleme süresi
            except:
                print("Sayfa yüklenemedi, tekrar deneniyor...")
                time.sleep(5)
                continue

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Veriyi çek
            page_players = parse_via_table(soup, version_name, season_str)

            if not page_players:
                print(f"  -> Offset {offset}: Oyuncu bulunamadı. Sezon bitmiş olabilir.")
                break

            print(f"  -> Offset {offset}: {len(page_players)} oyuncu başarıyla çekildi.")
            all_season_players.extend(page_players)

            # Pagination (Sayfalama) Kontrolü
            # Eğer çekilen oyuncu sayısı 60'tan azsa son sayfadayız demektir.
            if len(page_players) < 60:
                print("  -> Sezon sonuna gelindi.")
                break

            offset += 60

        # Kaydet
        if all_season_players:
            season_df = pd.DataFrame(all_season_players)
            filename = f"stats_{season_str.replace('-', '_')}.csv"
            season_df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"✅ {version_name} tamamlandı! '{filename}' dosyasına kaydedildi.")
            tum_veriler_toplam.extend(all_season_players)
        else:
            print(f"⚠️ {version_name} için hiç veri çekilemedi.")

except Exception as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")

finally:
    if tum_veriler_toplam:
        total_df = pd.DataFrame(tum_veriler_toplam)
        total_df.to_csv("ALL_FIFA_STATS_FINAL.csv", index=False, encoding="utf-8-sig")
        print("\n🎉 MÜKEMMEL! Tüm sezonlar 'ALL_FIFA_STATS_FINAL.csv' içinde birleştirildi.")

    if driver:
        print("Tarayıcı kapatılıyor...")
        driver.quit()