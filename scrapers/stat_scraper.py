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
# lg parametresini dinamik yapacağız, şablondan çıkardık.
BASE_URL_TEMPLATE = "https://sofifa.com/players?type=all&showCol%5B0%5D=ae&showCol%5B1%5D=oa&showCol%5B2%5D=pt&showCol%5B3%5D=vl&showCol%5B4%5D=wg&showCol%5B5%5D=ta&showCol%5B6%5D=cr&showCol%5B7%5D=fi&showCol%5B8%5D=he&showCol%5B9%5D=sh&showCol%5B10%5D=vo&showCol%5B11%5D=ts&showCol%5B12%5D=dr&showCol%5B13%5D=cu&showCol%5B14%5D=fr&showCol%5B15%5D=lo&showCol%5B16%5D=bl&showCol%5B17%5D=to&showCol%5B18%5D=ac&showCol%5B19%5D=sp&showCol%5B20%5D=ag&showCol%5B21%5D=re&showCol%5B22%5D=ba&showCol%5B23%5D=tp&showCol%5B24%5D=so&showCol%5B25%5D=ju&showCol%5B26%5D=st&showCol%5B27%5D=sr&showCol%5B28%5D=ln&showCol%5B29%5D=te&showCol%5B30%5D=ar&showCol%5B31%5D=in&showCol%5B32%5D=po&showCol%5B33%5D=vi&showCol%5B34%5D=pe&showCol%5B35%5D=cm&showCol%5B36%5D=td&showCol%5B37%5D=ma&showCol%5B38%5D=sa&showCol%5B39%5D=sl&showCol%5B40%5D=tg&showCol%5B41%5D=gd&showCol%5B42%5D=gh&showCol%5B43%5D=gc&showCol%5B44%5D=gp&showCol%5B45%5D=gr"

# --- LİG ID'LERİ (SoFIFA) ---
LEAGUES = {
    "La Liga": "53",
    "Bundesliga": "19",
    "Serie A": "31",
    "Ligue 1": "16",
    "Süper Lig": "68",
    "Liga Portugal": "308"
}

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
    match = re.search(r'^\d+', str(value).strip())
    return match.group(0) if match else str(value).strip()


def parse_via_table(soup, version_name, season_str, league_name):
    players_data = []
    table = soup.find('table')
    if not table: return []
    tbody = table.find('tbody')
    if not tbody: return []

    for row in tbody.find_all('tr'):
        try:
            name_link = row.select_one("a[href*='/player/']")
            if not name_link: continue
            player_name = name_link.get_text(strip=True)

            team_link = row.select_one("a[href*='/team/']")
            team_name = team_link.get_text(strip=True) if team_link else "Unknown"

            p_data = {
                "Season": season_str,
                "FifaVersion": version_name,
                "League": league_name,  # YENİ: Hangi ligden geldiğini kaydediyoruz
                "Name": player_name,
                "Team": team_name
            }

            for code, header in STATS_MAP_TABLE.items():
                col = row.find('td', {'data-col': code})
                if col:
                    val = col.get_text(strip=True)
                    p_data[header] = clean_stat(val)
                else:
                    p_data[header] = "0"
            players_data.append(p_data)
        except:
            continue
    return players_data


# --- ANA PROGRAM ---
driver = None
tum_veriler_toplam = []

try:
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # İstersen açabilirsin ama görsel takip daha iyi
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
    print("\n--- LÜTFEN GİRİŞ EKRANINI GEÇİN (Captcha/Cookies) ---")
    input("Hazır olduğunda ENTER'a bas...")

    # --- DIŞ DÖNGÜ: LİGLER ---
    for league_name, league_id in LEAGUES.items():
        print(f"\n{'#' * 50}")
        print(f"🌍 LİG BAŞLATILIYOR: {league_name} (ID: {league_id})")
        print(f"{'#' * 50}")

        # --- İÇ DÖNGÜ: SEZONLAR ---
        for version_name, (season_str, roster_id) in FIFA_ROSTERS.items():
            print(f"\n--- {league_name} | {version_name} ({season_str}) ---")
            all_season_players = []
            offset = 0

            while True:
                # URL'ye Lig ID'sini ekliyoruz
                target_url = f"{BASE_URL_TEMPLATE}&lg%5B0%5D={league_id}&r={roster_id}&set=true&offset={offset}"

                try:
                    driver.get(target_url)
                    time.sleep(random.uniform(3, 5))
                except:
                    time.sleep(5)
                    continue

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                page_players = parse_via_table(soup, version_name, season_str, league_name)

                if not page_players:
                    print(f"  -> Bitti veya Bulunamadı. Offset: {offset}")
                    break

                print(f"  -> {len(page_players)} oyuncu çekildi (Offset: {offset})")
                all_season_players.extend(page_players)

                if len(page_players) < 60:
                    break

                offset += 60

            # Her sezon sonunda o ligin o sezonunu kaydedelim (Veri kaybı olmasın)
            if all_season_players:
                tum_veriler_toplam.extend(all_season_players)
                # Anlık yedekleme (Opsiyonel)
                # pd.DataFrame(all_season_players).to_csv(f"backup_{league_name}_{season_str}.csv", index=False)

except Exception as e:
    print(f"Hata: {e}")

finally:
    if tum_veriler_toplam:
        total_df = pd.DataFrame(tum_veriler_toplam)
        # Dosya ismini değiştirdim, tüm ligler var
        total_df.to_csv("ALL_LEAGUES_FIFA_STATS.csv", index=False, encoding="utf-8-sig")
        print("\n🎉 MÜKEMMEL! Tüm ligler 'ALL_LEAGUES_FIFA_STATS.csv' içine kaydedildi.")

    if driver:
        driver.quit()