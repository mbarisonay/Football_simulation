# scraper_modern.py (Tüm İstatistikleri Çeken Nihai Versiyon)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import os
import re

# --- AYARLAR ---
BASE_URL = "https://fbref.com"
OUTPUT_FILE = "fbref_stats_MODERN_2014_2024_FULL.csv"  # Dosya adını değiştirdim
all_matches_data = []

SEASONS_TO_SCRAPE = list(range(2014, 2024))

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = None
try:
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    for year in SEASONS_TO_SCRAPE:
        season_year_str = f"{year}-{year + 1}"
        print(f"\n--- {season_year_str} Sezonu Başlatılıyor ---")

        try:
            fixture_page_url = f"{BASE_URL}/en/comps/9/{season_year_str}/schedule/{season_year_str}-Premier-League-Scores-and-Fixtures"
            driver.get(fixture_page_url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table tbody tr")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            match_links = [BASE_URL + a['href'] for a in soup.select("td[data-stat='match_report'] a")]
            print(f"  → {len(match_links)} maç linki bulundu.")

            # Her sezon için veri listesini sıfırla
            season_data = []

            for i, url in enumerate(match_links, 1):
                try:
                    driver.get(url)
                    wait.until(EC.presence_of_element_located((By.ID, "content")))
                    match_soup = BeautifulSoup(driver.page_source, "html.parser")

                    content_div = match_soup.select_one("#content")
                    if not content_div:
                        print(f"    ⚠️ Maç {i} ({url}) için ana içerik (#content) bulunamadı. Atlanıyor.")
                        continue

                    scorebox = content_div.select_one("div.scorebox")
                    if not scorebox:
                        print(f"    ⚠️ Maç {i} ({url}) için skor kutusu bulunamadı. Atlanıyor.")
                        continue

                    team_links = scorebox.select("a[href*='/squads/']")
                    scores = scorebox.select("div.score")
                    date_element = scorebox.select_one("div.scorebox_meta span.venuetime")

                    if len(team_links) < 2 or len(scores) < 2 or not date_element:
                        print(f"    ⚠️ Maç {i} ({url}) için takım/skor bilgisi eksik. Atlanıyor.")
                        continue

                    home_team = team_links[0].get_text(strip=True)
                    away_team = team_links[1].get_text(strip=True)
                    home_goals = scores[0].get_text(strip=True)
                    away_goals = scores[1].get_text(strip=True)
                    date = date_element['data-venue-date']

                    # --- İSTATİSTİK BÖLÜMÜ (GÜNCELLENMİŞ VE TAMAMLANMIŞ) ---
                    data = {}

                    # İstatistik tablosu bazen yorum içinde olabilir, onu da bulalım
                    stats_container = content_div.find("div", id="all_matchstats")
                    if not stats_container:
                        comment = content_div.find(string=lambda text: "id=\"matchstats\"" in str(text))
                        if comment:
                            comment_soup = BeautifulSoup(str(comment), 'html.parser')
                            stats_container = comment_soup.select_one("#matchstats")

                    if stats_container:
                        def get_stat_from_columns(container, stat_name):
                            header = container.find("th", string=lambda text: text and stat_name in text)
                            if not header: return '0', '0'

                            home_td = header.find_previous_sibling('td')
                            away_td = header.find_next_sibling('td')

                            home_val = home_td.get_text(strip=True) if home_td else '0'
                            away_val = away_td.get_text(strip=True) if away_td else '0'
                            return home_val, away_val


                        # Tüm Sütun İstatistikleri
                        data["HomeFouls"], data["AwayFouls"] = get_stat_from_columns(stats_container, "Fouls")
                        data["HomeCorners"], data["AwayCorners"] = get_stat_from_columns(stats_container, "Corners")
                        data["HomeCrosses"], data["AwayCrosses"] = get_stat_from_columns(stats_container, "Crosses")
                        data["HomeTouches"], data["AwayTouches"] = get_stat_from_columns(stats_container, "Touches")
                        data["HomeTackles"], data["AwayTackles"] = get_stat_from_columns(stats_container, "Tackles")
                        data["HomeInterceptions"], data["AwayInterceptions"] = get_stat_from_columns(stats_container,
                                                                                                     "Interceptions")
                        data["HomeAerialsWon"], data["AwayAerialsWon"] = get_stat_from_columns(stats_container,
                                                                                               "Aerials Won")
                        data["HomeClearances"], data["AwayClearances"] = get_stat_from_columns(stats_container,
                                                                                               "Clearances")
                        data["HomeOffsides"], data["AwayOffsides"] = get_stat_from_columns(stats_container, "Offsides")
                        data["HomeGoalKicks"], data["AwayGoalKicks"] = get_stat_from_columns(stats_container,
                                                                                             "Goal Kicks")
                        data["HomeThrowIns"], data["AwayThrowIns"] = get_stat_from_columns(stats_container, "Throw Ins")
                        data["HomeLongBalls"], data["AwayLongBalls"] = get_stat_from_columns(stats_container,
                                                                                             "Long Balls")

                        # Tüm Bar Grafiği İstatistikleri
                        possession_div = stats_container.find("th", string="Possession")
                        if possession_div and possession_div.find_next_sibling("td"):
                            pos_values = possession_div.find_next_sibling("td").get_text(strip=True).split('%')
                            if len(pos_values) >= 2: data["HomePossession"], data["AwayPossession"] = pos_values[0], \
                            pos_values[1]

                        passing_div = stats_container.find("th", string="Passing Accuracy")
                        if passing_div and passing_div.find_next_sibling("td"):
                            parts = re.findall(r'(\d+)\s+of\s+(\d+)', passing_div.find_next_sibling("td").get_text())
                            if len(parts) == 2:
                                data["HomePassesCompleted"], data["HomePassesAttempted"] = parts[0]
                                data["AwayPassesCompleted"], data["AwayPassesAttempted"] = parts[1]

                        sot_div = stats_container.find("th", string="Shots on Target")
                        if sot_div and sot_div.find_next_sibling("td"):
                            parts = re.findall(r'(\d+)\s+of\s+(\d+)', sot_div.find_next_sibling("td").get_text())
                            if len(parts) == 2:
                                data["HomeSOT"], data["HomeShots"] = parts[0]
                                data["AwaySOT"], data["AwayShots"] = parts[1]

                        saves_div = stats_container.find("th", string="Saves")
                        if saves_div and saves_div.find_next_sibling("td"):
                            parts = re.findall(r'(\d+)\s+of\s+(\d+)', saves_div.find_next_sibling("td").get_text())
                            if len(parts) == 2:
                                data["HomeSaves"], data["HomeSavesAllowed"] = parts[0]
                                data["AwaySaves"], data["AwaySavesAllowed"] = parts[1]

                    # Kart Bilgileri
                    home_summary = content_div.select_one(f"#stats_{home_team.replace(' ', '')}_summary")
                    away_summary = content_div.select_one(f"#stats_{away_team.replace(' ', '')}_summary")

                    data["HomeYellowCards"] = home_summary.select_one("tfoot td[data-stat='cards_yellow']").get_text(
                        strip=True) if home_summary and home_summary.select_one(
                        "tfoot td[data-stat='cards_yellow']") else '0'
                    data["HomeRedCards"] = home_summary.select_one("tfoot td[data-stat='cards_red']").get_text(
                        strip=True) if home_summary and home_summary.select_one(
                        "tfoot td[data-stat='cards_red']") else '0'
                    data["AwayYellowCards"] = away_summary.select_one("tfoot td[data-stat='cards_yellow']").get_text(
                        strip=True) if away_summary and away_summary.select_one(
                        "tfoot td[data-stat='cards_yellow']") else '0'
                    data["AwayRedCards"] = away_summary.select_one("tfoot td[data-stat='cards_red']").get_text(
                        strip=True) if away_summary and away_summary.select_one(
                        "tfoot td[data-stat='cards_red']") else '0'

                    # Tüm veriyi birleştir
                    match_final_data = {
                        "Season": season_year_str, "Date": date, "HomeTeam": home_team, "AwayTeam": away_team,
                        "FTHG": home_goals, "FTAG": away_goals, **data
                    }
                    season_data.append(match_final_data)
                    print(f"    {i}/{len(match_links)}: {home_team} vs {away_team} [OK]")
                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    print(f"    ⚠️ Maç {i} ({url}) işlenirken HATA: {e}. Atlanıyor.")
                    continue

            # Her sezon sonunda o sezona ait veriyi ana listeye ekle
            all_matches_data.extend(season_data)

            # Her sezon sonunda veriyi kaydetmek, bir hata durumunda ilerlemeyi kaybetmemeyi sağlar
            if all_matches_data:
                df_to_save = pd.DataFrame(all_matches_data)
                df_to_save.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
                print(
                    f"  --- {season_year_str} sezonu tamamlandı ve toplam {len(df_to_save)} maç '{OUTPUT_FILE}' dosyasına kaydedildi. ---")

        except Exception as e:
            print(f"  [!] {season_year_str} sezonu işlenirken ana bir hata oluştu: {e}.")
            continue
finally:
    if driver:
        driver.quit()
    if all_matches_data:
        print(f"\n✅ İşlem tamamlandı! Toplam {len(all_matches_data)} kayıt kaydedildi.")
    else:
        print("\nHiçbir veri çekilemedi. Lütfen bağlantınızı veya web sitesi yapısını kontrol edin.")