import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import os
import sys

# Patcher'ı import ediyoruz
from undetected_chromedriver.patcher import Patcher

# --- AYARLAR ---
BASE_URL_TEMPLATE = "https://sofifa.com/players?type=all&lg%5B0%5D=13&showCol%5B0%5D=ae&showCol%5B1%5D=oa&showCol%5B2%5D=pt&showCol%5B3%5D=vl&showCol%5B4%5D=wg&showCol%5B5%5D=ta&showCol%5B6%5D=cr&showCol%5B7%5D=fi&showCol%5B8%5D=he&showCol%5B9%5D=sh&showCol%5B10%5D=vo&showCol%5B11%5D=ts&showCol%5B12%5D=dr&showCol%5B13%5D=cu&showCol%5B14%5D=fr&showCol%5B15%5D=lo&showCol%5B16%5D=bl&showCol%5B17%5D=to&showCol%5B18%5D=ac&showCol%5B19%5D=sp&showCol%5B20%5D=ag&showCol%5B21%5D=re&showCol%5B22%5D=ba&showCol%5B23%5D=tp&showCol%5B24%5D=so&showCol%5B25%5D=ju&showCol%5B26%5D=st&showCol%5B27%5D=sr&showCol%5B28%5D=ln&showCol%5B29%5D=te&showCol%5B30%5D=ar&showCol%5B31%5D=in&showCol%5B32%5D=po&showCol%5B33%5D=vi&showCol%5B34%5D=pe&showCol%5B35%5D=cm&showCol%5B36%5D=td&showCol%5B37%5D=ma&showCol%5B38%5D=sa&showCol%5B39%5D=sl&showCol%5B40%5D=tg&showCol%5B41%5D=gd&showCol%5B42%5D=gh&showCol%5B43%5D=gc&showCol%5B44%5D=gp&showCol%5B45%5D=gr"
STATS_MAP = {'PlayerName': 'name', 'Positions': 'positions', 'Age': 'ae', 'Overall': 'oa', 'Potential': 'pt',
             'Club': 'club', 'Crossing': 'cr', 'Finishing': 'fi', 'HeadingAccuracy': 'he', 'ShortPassing': 'sh',
             'Volleys': 'vo', 'Dribbling': 'dr', 'Curve': 'cu', 'FKAccuracy': 'fr', 'LongPassing': 'lo',
             'BallControl': 'bl', 'Acceleration': 'ac', 'SprintSpeed': 'sp', 'Agility': 'ag', 'Reactions': 're',
             'Balance': 'ba', 'ShotPower': 'so', 'Jumping': 'ju', 'Stamina': 'st', 'Strength': 'sr', 'LongShots': 'ln',
             'Aggression': 'ar', 'Interceptions': 'in', 'Positioning': 'po', 'Vision': 'vi', 'Penalties': 'pe',
             'Composure': 'cm', 'Marking': 'ma', 'StandingTackle': 'sa', 'SlidingTackle': 'sl', 'GKDiving': 'gd',
             'GKHandling': 'gh', 'GKKicking': 'gc', 'GKPositioning': 'gp', 'GKReflexes': 'gr'}
FIFA_ROSTERS = {"FIFA 15": ("2014-2015", "150002"), "FIFA 16": ("2015-2016", "160001"),
                "FIFA 17": ("2016-2017", "170001"), "FIFA 18": ("2017-2018", "180001"),
                "FIFA 19": ("2018-2019", "190001"), "FIFA 20": ("2019-2020", "200001"),
                "FIFA 21": ("2020-2021", "210001"), "FIFA 22": ("2021-2022", "220001"),
                "FIFA 23": ("2022-2023", "230001"), "FIFA 24": ("2023-2024", "240001"),
                "EA FC 25": ("2024-2025", "250001")}


def patch_driver():
    """undetected_chromedriver'ı en son yamalarla manuel olarak başlatır."""
    patcher = Patcher()
    patcher.auto()
    return patcher.executable_path


# --- ANA DÖNGÜ ---
for version_name, (season_str, roster_id) in FIFA_ROSTERS.items():
    print(f"\n{'=' * 70}\n--- BAŞLATILIYOR: {version_name} ({season_str} Sezonu) ---\n{'=' * 70}")

    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--lang=en-US")

        driver_executable_path = patch_driver()
        driver = uc.Chrome(driver_executable_path=driver_executable_path, options=options)

        wait = WebDriverWait(driver, 25)

        target_url = f"{BASE_URL_TEMPLATE}&r={roster_id}&set=true"
        print(f"-> URL'ye gidiliyor: {target_url}")
        driver.get(target_url)

        print("-> Bot korumasının geçmesi için 12 saniye bekleniyor...")
        time.sleep(12)

        try:
            accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            driver.execute_script("arguments[0].click();", accept_button)
            print("-> Çerezler kabul edildi.")
        except:
            pass

        all_season_players = []
        offset = 0

        while True:
            current_page_url = f"{target_url}&offset={offset}"
            # İlk sayfa zaten açık, tekrar gitmeye gerek yok
            if offset > 0:
                print(f"-> Sonraki sayfaya gidiliyor: offset={offset}")
                driver.get(current_page_url)
                time.sleep(random.uniform(4, 6))

            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "table.table-players tbody tr")))
            except Exception as e:
                print(f"  -> Tablo bulunamadı veya zaman aşımı. Sezon tamamlanmış olabilir. Hata: {e}")
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")
            player_rows = soup.select("table.table-players tbody tr")

            if not player_rows:
                print("  -> Bu sayfada oyuncu yok. Sezon tamamlandı.")
                break

            page_players = []
            for row in player_rows:
                player_data = {"GameVersion": version_name, "Season": season_str}
                try:
                    name_tag = row.select_one('a[data-tippy-content]')
                    if not name_tag: continue
                    player_data['PlayerName'] = name_tag.get('data-tippy-content')

                    club_tag = row.select_one('figure.team img')
                    player_data['Club'] = club_tag.get('alt') if club_tag else "Free Agent"

                    player_data['Positions'] = ', '.join(
                        [pos.get_text(strip=True) for pos in row.select('td:nth-of-type(2) a span.pos')])

                    for stat_name, col_code in STATS_MAP.items():
                        if col_code not in ['name', 'positions', 'club']:
                            element = row.select_one(f'td[data-col="{col_code}"] em')
                            if not element: element = row.select_one(f'td[data-col="{col_code}"]')

                            if element:
                                val_text = element.get_text(strip=True)
                                if '+' in val_text: val_text = val_text.split('+')[0]
                                if '-' in val_text: val_text = val_text.split('-')[0]
                                player_data[stat_name] = int(val_text) if val_text.isdigit() else 0
                            else:
                                player_data[stat_name] = 0

                    page_players.append(player_data)
                except Exception as e:
                    continue

            all_season_players.extend(page_players)
            print(f"  -> Offset {offset}: {len(page_players)} oyuncu çekildi. Toplam: {len(all_season_players)}")

            # Pagination'ı direkt URL ile yapmak yerine Next butonuna tıklamayı deneyelim
            try:
                next_button_container = driver.find_element(By.CSS_SELECTOR, "div.pagination")
                next_button = next_button_container.find_element(By.XPATH, ".//a[contains(text(), 'Next')]")
                # Eğer buton disabled ise, döngüyü kır
                if "disabled" in next_button.get_attribute("class"):
                    print("  -> Son sayfaya ulaşıldı (Next butonu disabled).")
                    break
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(random.uniform(3, 5))
                offset += 60  # Sadece loglama için
            except Exception as e:
                print(f"  -> 'Next' butonu bulunamadı veya tıklanamadı. Sezon tamamlandı. Hata: {e}")
                break

        if all_season_players:
            df = pd.DataFrame(all_season_players)
            clean_version_name = version_name.replace('™', '').replace(' ', '_')
            output_folder = f"FIFA_Ratings/{clean_version_name}_{season_str}"
            os.makedirs(output_folder, exist_ok=True)
            for club_name, club_data in df.groupby('Club'):
                safe_club_name = "".join(x for x in club_name if x.isalnum() or x in " _-").strip()
                file_path = os.path.join(output_folder, f"{safe_club_name}.csv")
                club_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"\n  ✅ {version_name} verileri '{output_folder}' klasörüne kaydedildi.")
        else:
            print(f"\n  ❌ {version_name} için veri bulunamadı.")

    except Exception as e:
        print(f"  [!] KRİTİK HATA ({version_name}): {e}", file=sys.stderr)

    finally:
        if driver:
            try:
                driver.quit()
                print("  -> Tarayıcı kapatıldı.")
            except:
                pass
        time.sleep(3)

print("\n🎉 TÜM SEZONLAR TAMAMLANDI!")