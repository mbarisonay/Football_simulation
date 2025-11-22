import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import os
import re
import sys

# --- AYARLAR ---
BASE_URL_TEMPLATE = "https://sofifa.com/players?type=all&lg%5B0%5D=13&showCol%5B0%5D=ae&showCol%5B1%5D=oa&showCol%5B2%5D=pt&showCol%5B3%5D=vl&showCol%5B4%5D=wg&showCol%5B5%5D=ta&showCol%5B6%5D=cr&showCol%5B7%5D=fi&showCol%5B8%5D=he&showCol%5B9%5D=sh&showCol%5B10%5D=vo&showCol%5B11%5D=ts&showCol%5B12%5D=dr&showCol%5B13%5D=cu&showCol%5B14%5D=fr&showCol%5B15%5D=lo&showCol%5B16%5D=bl&showCol%5B17%5D=to&showCol%5B18%5D=ac&showCol%5B19%5D=sp&showCol%5B20%5D=ag&showCol%5B21%5D=re&showCol%5B22%5D=ba&showCol%5B23%5D=tp&showCol%5B24%5D=so&showCol%5B25%5D=ju&showCol%5B26%5D=st&showCol%5B27%5D=sr&showCol%5B28%5D=ln&showCol%5B29%5D=te&showCol%5B30%5D=ar&showCol%5B31%5D=in&showCol%5B32%5D=po&showCol%5B33%5D=vi&showCol%5B34%5D=pe&showCol%5B35%5D=cm&showCol%5B36%5D=td&showCol%5B37%5D=ma&showCol%5B38%5D=sa&showCol%5B39%5D=sl&showCol%5B40%5D=tg&showCol%5B41%5D=gd&showCol%5B42%5D=gh&showCol%5B43%5D=gc&showCol%5B44%5D=gp&showCol%5B45%5D=gr"

# --- 1. TABLO GÖRÜNÜMÜ İÇİN HARİTA (data-col kodları) ---
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

# --- 2. LİSTE GÖRÜNÜMÜ İÇİN HARİTA (İngilizce Etiketler) ---
STATS_MAP_LIST = {
    'Overall rating': 'Overall', 'Potential': 'Potential',
    'Crossing': 'Crossing', 'Finishing': 'Finishing', 'Heading accuracy': 'HeadingAccuracy',
    'Short passing': 'ShortPassing', 'Volleys': 'Volleys', 'Dribbling': 'Dribbling',
    'Curve': 'Curve', 'FK Accuracy': 'FKAccuracy', 'Long passing': 'LongPassing',
    'Ball control': 'BallControl', 'Acceleration': 'Acceleration', 'Sprint speed': 'SprintSpeed',
    'Agility': 'Agility', 'Reactions': 'Reactions', 'Balance': 'Balance',
    'Shot power': 'ShotPower', 'Jumping': 'Jumping', 'Stamina': 'Stamina',
    'Strength': 'Strength', 'Long shots': 'LongShots', 'Aggression': 'Aggression',
    'Interceptions': 'Interceptions', 'Attack position': 'Positioning', 'Vision': 'Vision',
    'Penalties': 'Penalties', 'Composure': 'Composure', 'Marking': 'Marking',
    'Standing tackle': 'StandingTackle', 'Sliding tackle': 'SlidingTackle',
    'GK Diving': 'GKDiving', 'GK Handling': 'GKHandling', 'GK Kicking': 'GKKicking',
    'GK Positioning': 'GKPositioning', 'GK Reflexes': 'GKReflexes'
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
    clean_val = str(value).strip()
    match = re.search(r'^\d+', clean_val)
    return match.group(0) if match else clean_val


# --- PARSER FONKSİYONLARI ---

def parse_via_table(soup, version_name, season_str):
    """ Tablo görünümü (Grid) varsa burası çalışır """
    players_data = []
    table = soup.find('table')
    tbody = table.find('tbody')
    if not tbody: return []

    for row in tbody.find_all('tr'):
        try:
            name_col = row.find('td', {'class': 'col-name'})
            if not name_col: continue

            # İsim ve Takım
            name_link = name_col.find('a', {'role': 'tooltip'})
            player_name = name_link.div.text.strip() if name_link and name_link.div else name_col.text.strip()

            team_link = row.find_all('a', href=re.compile(r'/team/'))
            team_name = team_link[-1].text.strip() if team_link else "Unknown"

            p_data = {
                "Season": season_str,
                "FifaVersion": version_name,
                "Name": player_name,
                "Team": team_name
            }

            # Statları Çek
            for code, header in STATS_MAP_TABLE.items():
                col = row.find('td', {'data-col': code})
                val = col.text.strip() if col else "0"
                p_data[header] = clean_stat(val)

            players_data.append(p_data)
        except:
            continue
    return players_data


def parse_via_list(soup, version_name, season_str):
    """ Liste görünümü (Card) varsa burası çalışır """
    players_data = []
    list_container = soup.find('ul', {'class': 'list'})
    if not list_container: return []

    items = list_container.find_all('li', class_=lambda x: x and 'pure-g' in x and 'player-' in x)

    for li in items:
        try:
            p_data = {
                "Season": season_str,
                "FifaVersion": version_name,
                "Name": "Unknown",
                "Team": "Unknown",
                "Age": "0"
            }

            # İsim
            name_div = li.find('div', class_='pure-u-12-24')
            if name_div and name_div.a: p_data["Name"] = name_div.a.text.strip()

            # Takım
            team_link = li.find('a', href=re.compile(r'/team/'))
            if team_link: p_data["Team"] = team_link.text.strip()

            # Yaş
            text_content = li.get_text(" ", strip=True)
            age_match = re.search(r'(\d+)y\.o\.', text_content)
            if age_match: p_data["Age"] = age_match.group(1)

            # Statlar
            label_divs = li.find_all('div', class_='pure-u-7-24')
            for label_div in label_divs:
                abbr = label_div.find('abbr')
                label_text = abbr.text.strip() if abbr else label_div.text.strip()

                if label_text in STATS_MAP_LIST:
                    csv_header = STATS_MAP_LIST[label_text]
                    value_div = label_div.find_next_sibling('div', class_='pure-u-17-24')
                    if value_div:
                        val = value_div.text.strip()
                        p_data[csv_header] = clean_stat(val)

            # Overall özel kontrol
            if "Overall" not in p_data:
                oa = li.find('em', title=True)
                if oa: p_data["Overall"] = clean_stat(oa.text)

            players_data.append(p_data)
        except:
            continue
    return players_data


# --- ANA AKIŞ ---
driver = None
tum_veriler_toplam = []

try:
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), "sofifa_profile")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--lang=en-US")
    # Pencereyi genişletiyoruz ki site Tablo versiyonuna geçmeye daha meyilli olsun (Parse etmesi daha kolay)
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--disable-blink-features=AutomationControlled')

    print("Tarayıcı başlatılıyor...")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    print("SoFIFA ana sayfasına gidiliyor...")
    driver.get("https://sofifa.com")
    print("\n--- Manuel Doğrulama Bekleniyor ---")
    print("Lütfen tarayıcıdaki 'Accept All' butonuna basıp Captcha'yı geçin.")
    input("Hazır olduğunuzda ENTER tuşuna basın...")

    for version_name, (season_str, roster_id) in FIFA_ROSTERS.items():
        print(f"\n{'=' * 70}\n--- BAŞLATILIYOR: {version_name} ({season_str}) ---\n{'=' * 70}")
        all_season_players = []
        offset = 0

        while True:
            target_url = f"{BASE_URL_TEMPLATE}&r={roster_id}&set=true&offset={offset}"
            try:
                driver.get(target_url)
                time.sleep(random.uniform(2.5, 4))
            except Exception as e:
                print(f"Sayfa yükleme hatası (Retrying): {e}")
                time.sleep(5)
                continue

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # --- HİBRİT PARSER KONTROLÜ ---
            page_players = []
            view_type = "Unknown"

            if soup.find('table', {'class': 'table'}):
                view_type = "TABLE"
                page_players = parse_via_table(soup, version_name, season_str)
            elif soup.find('ul', {'class': 'list'}):
                view_type = "LIST"
                page_players = parse_via_list(soup, version_name, season_str)

            if not page_players:
                print(f"  -> Offset {offset}: Veri bulunamadı (View: {view_type}). Sezon bitmiş olabilir.")
                break

            print(f"  -> Offset {offset}: {len(page_players)} oyuncu çekildi. (Mod: {view_type})")
            all_season_players.extend(page_players)

            # Pagination Kontrolü
            if len(page_players) < 60:
                print("  -> Sayfa sonuna gelindi.")
                break

            offset += 60

        # Sezonu Kaydet
        if all_season_players:
            season_df = pd.DataFrame(all_season_players)
            filename = f"stats_{season_str.replace('-', '_')}.csv"
            season_df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"✅ {version_name} tamamlandı. {len(season_df)} oyuncu kaydedildi.")
            tum_veriler_toplam.extend(all_season_players)
        else:
            print(f"⚠️ {version_name} için veri bulunamadı.")

except KeyboardInterrupt:
    print("\nİşlem kullanıcı tarafından durduruldu.")

except Exception as e:
    print(f"Kritik Hata: {e}")
    import traceback

    traceback.print_exc()

finally:
    if tum_veriler_toplam:
        total_df = pd.DataFrame(tum_veriler_toplam)
        total_df.to_csv("ALL_FIFA_STATS_FINAL_V2.csv", index=False, encoding="utf-8-sig")
        print("\n🎉 TÜM YILLAR BİRLEŞTİRİLDİ: 'ALL_FIFA_STATS_FINAL_V2.csv'")

    if driver:
        try:
            driver.quit()
        except:
            pass