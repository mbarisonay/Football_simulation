# scraper_modern.py (Tüm Düzeltmeleri İçeren Final Versiyon)

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
import pprint

# --- AYARLAR ---
BASE_URL = "https://fbref.com"
OUTPUT_FILE = "fbref_premier_league_stats_2000-2014_COMPLETE.csv"
all_matches_data = []

SEASONS_TO_SCRAPE = list(range(2000, 2014))

# --- Selenium Başlat (undetected-chromedriver ile) ---
options = uc.ChromeOptions()
# options.add_argument('--headless') # Bot tespitini zorlaştırmak için ilk denemede kapalı kalsın
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
options.add_argument('--disable-blink-features=AutomationControlled')

driver = None
try:
    driver = uc.Chrome(options=options, use_subprocess=True)

    print("Cloudflare korumasını geçmek için ana sayfaya gidiliyor (15 saniye bekleme)...")
    driver.get(BASE_URL)
    time.sleep(15)
    print("Bekleme tamamlandı, veri çekme işlemi başlıyor.")

    wait = WebDriverWait(driver, 30)

    for year in SEASONS_TO_SCRAPE:
        season_year_str = f"{year}-{year + 1}"
        print(f"\n--- {season_year_str} Sezonu Başlatılıyor ---")

        try:
            fixture_page_url = f"{BASE_URL}/en/comps/9/{season_year_str}/schedule/{season_year_str}-Premier-League-Scores-and-Fixtures"
            driver.get(fixture_page_url)

            wait.until(EC.presence_of_element_located((By.ID, "content")))
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            match_links_tags = soup.select("td[data-stat='match_report'] a")

            if not match_links_tags:
                print(
                    f"  -> {season_year_str} sezonu için maç linki bulunamadı. Muhtemelen o sezon için veri yok. Atlanıyor.")
                continue

            match_links = [BASE_URL + a['href'] for a in match_links_tags]
            print(f"  → {len(match_links)} maç linki bulundu.")

            season_data = []

            for i, url in enumerate(match_links, 1):
                try:
                    driver.get(url)
                    wait.until(EC.presence_of_element_located((By.ID, "content")))
                    match_soup = BeautifulSoup(driver.page_source, "html.parser")

                    content_div = match_soup.select_one("#content")
                    if not content_div: continue

                    scorebox = content_div.select_one("div.scorebox")
                    if not scorebox: continue

                    team_links = scorebox.select("a[href*='/squads/']")
                    scores = scorebox.select("div.score")
                    date_element = scorebox.select_one("div.scorebox_meta span.venuetime")

                    if len(team_links) < 2 or len(scores) < 2 or not date_element: continue

                    home_team = team_links[0].get_text(strip=True)
                    away_team = team_links[1].get_text(strip=True)
                    home_goals = scores[0].get_text(strip=True)
                    away_goals = scores[1].get_text(strip=True)
                    date = date_element['data-venue-date']

                    data = {}

                    # --- HİBRİT PARSER MANTIĞI ---
                    stats_container = None
                    stats_wrapper = content_div.find("div", id="all_matchstats")
                    if stats_wrapper:
                        comment = stats_wrapper.find(string=lambda text: isinstance(text, str) and "matchstats" in text)
                        if comment:
                            comment_soup = BeautifulSoup(comment, 'html.parser')
                            stats_container = comment_soup.find("div", id="matchstats")
                            if stats_container:
                                print(f"    -> Modern HTML yapısı bulundu.")


                                # MODERN YAPI PARSER
                                def get_stat_from_columns(container, stat_name):
                                    header = container.find("th", string=lambda text: text and stat_name in text)
                                    if not header: return '0', '0'
                                    home_td = header.find_previous_sibling('td')
                                    away_td = header.find_next_sibling('td')
                                    return (home_td.get_text(strip=True) if home_td else '0'), (
                                        away_td.get_text(strip=True) if away_td else '0')


                                data["HomeFouls"], data["AwayFouls"] = get_stat_from_columns(stats_container, "Fouls")
                                data["HomeCorners"], data["AwayCorners"] = get_stat_from_columns(stats_container,
                                                                                                 "Corners")
                                data["HomeCrosses"], data["AwayCrosses"] = get_stat_from_columns(stats_container,
                                                                                                 "Crosses")
                                data["HomeTouches"], data["AwayTouches"] = get_stat_from_columns(stats_container,
                                                                                                 "Touches")
                                data["HomeTackles"], data["AwayTackles"] = get_stat_from_columns(stats_container,
                                                                                                 "Tackles")
                                data["HomeInterceptions"], data["AwayInterceptions"] = get_stat_from_columns(
                                    stats_container, "Interceptions")
                                data["HomeAerialsWon"], data["AwayAerialsWon"] = get_stat_from_columns(stats_container,
                                                                                                       "Aerials Won")
                                data["HomeClearances"], data["AwayClearances"] = get_stat_from_columns(stats_container,
                                                                                                       "Clearances")
                                data["HomeOffsides"], data["AwayOffsides"] = get_stat_from_columns(stats_container,
                                                                                                   "Offsides")
                                data["HomeGoalKicks"], data["AwayGoalKicks"] = get_stat_from_columns(stats_container,
                                                                                                     "Goal Kicks")
                                data["HomeThrowIns"], data["AwayThrowIns"] = get_stat_from_columns(stats_container,
                                                                                                   "Throw Ins")
                                data["HomeLongBalls"], data["AwayLongBalls"] = get_stat_from_columns(stats_container,
                                                                                                     "Long Balls")

                                possession_div = stats_container.find("th", string="Possession")
                                if possession_div and possession_div.find_next_sibling("td"):
                                    pos_values = possession_div.find_next_sibling("td").get_text(strip=True).split('%')
                                    if len(pos_values) >= 2: data["HomePossession"], data["AwayPossession"] = \
                                    pos_values[0], pos_values[1]


                                def modern_parse_bar_stat(stat_name):
                                    div = stats_container.find("th", string=stat_name)
                                    if div and div.find_next_sibling("td"):
                                        parts = re.findall(r'(\d+)\s+of\s+(\d+)',
                                                           div.find_next_sibling("td").get_text())
                                        if len(parts) == 2: return parts[0][0], parts[0][1], parts[1][0], parts[1][1]
                                    return '0', '0', '0', '0'


                                data["HomePassesCompleted"], data["HomePassesAttempted"], data["AwayPassesCompleted"], \
                                data["AwayPassesAttempted"] = modern_parse_bar_stat("Passing Accuracy")
                                data["HomeSOT"], data["HomeShots"], data["AwaySOT"], data[
                                    "AwayShots"] = modern_parse_bar_stat("Shots on Target")
                                data["HomeSaves"], data["HomeSavesAllowed"], data["AwaySaves"], data[
                                    "AwaySavesAllowed"] = modern_parse_bar_stat("Saves")

                    if not data:
                        print(f"    -> Eski HTML yapısı bulundu.")
                        main_stats_table = content_div.select_one("#team_stats table")
                        extra_stats_div = content_div.select_one("#team_stats_extra")
                        if main_stats_table:
                            # ESKİ YAPI PARSER
                            possession_row = main_stats_table.find("th", string="Possession").find_parent(
                                "tr").find_next_sibling("tr")
                            if possession_row:
                                tds = possession_row.find_all("td")
                                if len(tds) == 2:
                                    data["HomePossession"] = tds[0].get_text(strip=True).replace('%', '')
                                    data["AwayPossession"] = tds[1].get_text(strip=True).replace('%', '')


                            def legacy_parse_bar_stat(stat_name):
                                row = main_stats_table.find("th", string=stat_name)
                                if not row: return '0', '0', '0', '0'
                                row = row.find_parent("tr").find_next_sibling("tr")
                                if not row: return '0', '0', '0', '0'
                                tds = row.find_all("td")
                                if len(tds) != 2: return '0', '0', '0', '0'
                                home_parts = re.findall(r'(\d+)\s+of\s+(\d+)', tds[0].get_text())
                                away_parts = re.findall(r'(\d+)\s+of\s+(\d+)', tds[1].get_text())
                                return (home_parts[0][0] if home_parts else '0'), (
                                    home_parts[0][1] if home_parts else '0'), (
                                    away_parts[0][0] if away_parts else '0'), (away_parts[0][1] if away_parts else '0')


                            data["HomePassesCompleted"], data["HomePassesAttempted"], data["AwayPassesCompleted"], data[
                                "AwayPassesAttempted"] = legacy_parse_bar_stat("Passing Accuracy")
                            data["HomeSOT"], data["HomeShots"], data["AwaySOT"], data[
                                "AwayShots"] = legacy_parse_bar_stat("Shots on Target")
                            data["HomeSaves"], data["HomeSavesAllowed"], data["AwaySaves"], data[
                                "AwaySavesAllowed"] = legacy_parse_bar_stat("Saves")

                        if extra_stats_div:
                            def get_extra_stat(stat_name):
                                stat_div = extra_stats_div.find("div", string=stat_name)
                                if not stat_div: return '0', '0'
                                return stat_div.find_previous_sibling("div").get_text(
                                    strip=True), stat_div.find_next_sibling("div").get_text(strip=True)


                            data["HomeFouls"], data["AwayFouls"] = get_extra_stat("Fouls")
                            data["HomeCorners"], data["AwayCorners"] = get_extra_stat("Corners")
                            data["HomeCrosses"], data["AwayCrosses"] = get_extra_stat("Crosses")
                            data["HomeTouches"], data["AwayTouches"] = get_extra_stat("Touches")
                            data["HomeTackles"], data["AwayTackles"] = get_extra_stat("Tackles")
                            data["HomeInterceptions"], data["AwayInterceptions"] = get_extra_stat("Interceptions")
                            data["HomeAerialsWon"], data["AwayAerialsWon"] = get_extra_stat("Aerials Won")
                            data["HomeClearances"], data["AwayClearances"] = get_extra_stat("Clearances")
                            data["HomeOffsides"], data["AwayOffsides"] = get_extra_stat("Offsides")
                            data["HomeGoalKicks"], data["AwayGoalKicks"] = get_extra_stat("Goal Kicks")
                            data["HomeThrowIns"], data["AwayThrowIns"] = get_extra_stat("Throw Ins")
                            data["HomeLongBalls"], data["AwayLongBalls"] = get_extra_stat("Long Balls")

                    # Kart Bilgileri (Ortak)
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

                    match_final_data = {"Season": season_year_str, "Date": date, "HomeTeam": home_team,
                                        "AwayTeam": away_team, "FTHG": home_goals, "FTAG": away_goals, **data}
                    season_data.append(match_final_data)

                    print(f"    {i}/{len(match_links)}: {home_team} vs {away_team} [OK]")
                    pprint.pprint(match_final_data, indent=4, width=120)
                    print("-" * 60)

                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    print(f"    ⚠️ Maç {i} ({url}) işlenirken HATA: {e}. Atlanıyor.")
                    continue

            all_matches_data.extend(season_data)
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
        print("\nHiçbir veri çekilemedi. Cloudflare'i geçememiş olabilirsiniz veya internet bağlantınızı kontrol edin.")