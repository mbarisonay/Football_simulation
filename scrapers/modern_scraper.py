import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time
import random
import re
import sys
import os

# --- AYARLAR ---
BASE_URL = "https://fbref.com"
OUTPUT_FILE = "ALL_LEAGUES_DETAILED_MATCHES.csv"
all_matches_data = []

# 2016'dan 2025'e kadar
SEASONS_TO_SCRAPE = list(range(2016, 2025))

COMPETITIONS = [
    {"id": "12", "name": "La-Liga", "league_tag": "La Liga"},
    {"id": "9", "name": "Premier-League", "league_tag": "Premier League"},
    {"id": "20", "name": "Bundesliga", "league_tag": "Bundesliga"},
    {"id": "11", "name": "Serie-A", "league_tag": "Serie A"},
    {"id": "13", "name": "Ligue-1", "league_tag": "Ligue 1"},
    {"id": "26", "name": "Super-Lig", "league_tag": "Süper Lig"},
    {"id": "32", "name": "Primeira-Liga", "league_tag": "Liga Portugal"}
]

options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")

driver = None

try:
    driver = uc.Chrome(options=options, use_subprocess=True)
    print("Cloudflare kontrolü için bekleniyor (15sn)...")
    driver.get(BASE_URL)
    time.sleep(15)


    # --- DATA MINING FONKSİYONLARI ---

    def extract_stat_row(soup_obj, stat_name):
        """ Düz satır verileri (Faul, Korner, Ofsayt vb.) """
        label = soup_obj.find(lambda tag: tag.name in ["div", "th"] and tag.text.strip() == stat_name)
        if label:
            if label.name == "div":
                home_val = label.find_previous_sibling("div")
                away_val = label.find_next_sibling("div")
                return (home_val.text.strip() if home_val else '0'), (away_val.text.strip() if away_val else '0')
            elif label.name == "th":
                home_val = label.find_previous_sibling("td")
                away_val = label.find_next_sibling("td")
                return (home_val.text.strip() if home_val else '0'), (away_val.text.strip() if away_val else '0')
        return '0', '0'


    def extract_bar_stat(soup_obj, stat_name):
        """ 'X of Y' formatındaki veriler (Pas, Şut, Kurtarış) """
        label = soup_obj.find(lambda tag: tag.name in ["div", "th"] and stat_name in tag.text)
        h_succ, h_att, a_succ, a_att = '0', '0', '0', '0'

        if label:
            # Metni alacağımız yer (Div yapısı için sibling, Table için sibling td)
            target_elem = None
            if label.name == "th":
                # Table yapısında
                row = label.find_parent("tr").find_next_sibling("tr")
                if row:
                    tds = row.find_all("td")
                    if len(tds) >= 2:
                        # Ev Sahibi
                        parts_h = re.findall(r'(\d+)\s+of\s+(\d+)', tds[0].text)
                        if parts_h: h_succ, h_att = parts_h[0]
                        # Deplasman
                        parts_a = re.findall(r'(\d+)\s+of\s+(\d+)', tds[1].text)
                        if parts_a: a_succ, a_att = parts_a[0]

            elif label.name == "div" or label.parent.name == "div":
                # Div yapısında (team_stats) - Genelde bir sonraki div içinde text olur
                # Bu yapı karmaşık olabilir, genel text araması yapalım
                parent = label.find_parent("div", id=re.compile("team_stats"))
                if parent:
                    # O bölümdeki metinleri tarayalım "286 of 402" gibi
                    all_text = parent.get_text(" ")
                    # Regex ile tüm "sayı of sayı" kalıplarını bul
                    matches = re.findall(r'(\d+)\s+of\s+(\d+)', all_text)
                    # Eşleşmeleri sıraya göre dağıt (Genelde sıra: Passing Home, Passing Away, Shooting Home...)
                    # Bu yöntem riskli, o yüzden spesifik elemente gidelim:

                    # Bu stat isminden sonra gelen ilk iki "div" bloğunu bulmaya çalışalım
                    # (Basit çözüm: V2.0'daki gibi güçlü bir regex parser kullanalım)
                    pass

        return h_succ, h_att, a_succ, a_att


    def extract_possession(soup_obj):
        poss_header = soup_obj.find(lambda tag: tag.name in ["div", "th"] and "Possession" in tag.text)
        if poss_header:
            if poss_header.name == "th":
                row = poss_header.find_parent("tr").find_next_sibling("tr")
                if row:
                    tds = row.find_all("td")
                    if len(tds) >= 2:
                        return tds[0].text.strip().replace('%', ''), tds[1].text.strip().replace('%', '')
            elif poss_header.name == "div" or poss_header.parent.name == "div":
                strongs = poss_header.find_parent("table").find_all("strong") if poss_header.find_parent(
                    "table") else []
                if len(strongs) >= 2:
                    return strongs[0].text.strip().replace('%', ''), strongs[1].text.strip().replace('%', '')
        return '50', '50'


    def extract_cards(soup_obj):
        cards_header = soup_obj.find(lambda tag: tag.name in ["div", "th"] and "Cards" in tag.text)
        hy, hr, ay, ar = 0, 0, 0, 0
        if cards_header:
            if cards_header.name == "th":
                row = cards_header.find_parent("tr").find_next_sibling("tr")
                if row:
                    tds = row.find_all("td")
                    if len(tds) >= 2:
                        hy = len(tds[0].select('.yellow_card'))
                        hr = len(tds[0].select('.red_card')) + len(tds[0].select('.yellow_red_card'))
                        ay = len(tds[1].select('.yellow_card'))
                        ar = len(tds[1].select('.red_card')) + len(tds[1].select('.yellow_red_card'))
            # Div yapısında kartlar (Senin attığın HTML'deki gibi)
            elif cards_header.name == "div" or cards_header.parent.name == "div":
                table = cards_header.find_parent("table")
                if table:
                    rows = table.find_all("tr")
                    # Kart satırını bul
                    for r in rows:
                        if "Cards" in r.text: continue  # Başlık satırı
                        cols = r.find_all("td")
                        if len(cols) >= 2:
                            hy = len(cols[0].select('.yellow_card'))
                            hr = len(cols[0].select('.red_card')) + len(cols[0].select('.yellow_red_card'))
                            ay = len(cols[1].select('.yellow_card'))
                            ar = len(cols[1].select('.red_card')) + len(cols[1].select('.yellow_red_card'))
                            break
        return str(hy), str(hr), str(ay), str(ar)


    # --- ANA DÖNGÜ ---
    for comp in COMPETITIONS:
        print(f"\n\n{'=' * 50}")
        print(f"🏆 ŞAMPİYONA BAŞLIYOR: {comp['league_tag']}")
        print(f"{'=' * 50}")

        comp_id = comp['id']
        comp_slug = comp['name']

        for year in SEASONS_TO_SCRAPE:
            season_year_str = f"{year}-{year + 1}"
            print(f"\n  -> Sezon: {season_year_str} işleniyor...")

            try:
                fixture_url = f"{BASE_URL}/en/comps/{comp_id}/{season_year_str}/schedule/{season_year_str}-{comp_slug}-Scores-and-Fixtures"
                driver.get(fixture_url)
                time.sleep(4)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                match_links_tags = soup.select("td[data-stat='match_report'] a")

                if not match_links_tags:
                    print("    ⚠️ Maç linki bulunamadı.")
                    continue

                match_links = [BASE_URL + a['href'] for a in match_links_tags]
                print(f"    -> {len(match_links)} adet maç bulundu. Detaylar çekiliyor...")

                season_data = []

                for i, url in enumerate(match_links, 1):
                    try:
                        driver.get(url)
                        time.sleep(random.uniform(2.5, 4.5))

                        match_soup = BeautifulSoup(driver.page_source, "html.parser")
                        content_div = match_soup.select_one("#content")
                        if not content_div: continue

                        scorebox = content_div.select_one("div.scorebox")
                        if not scorebox: continue

                        team_links = scorebox.select("a[href*='/squads/']")
                        scores = scorebox.select("div.score")
                        date_elem = scorebox.select_one("div.scorebox_meta span.venuetime")

                        if len(team_links) < 2 or len(scores) < 2: continue

                        home_team = team_links[0].get_text(strip=True)
                        away_team = team_links[1].get_text(strip=True)
                        home_goals = scores[0].get_text(strip=True)
                        away_goals = scores[1].get_text(strip=True)
                        match_date = date_elem['data-venue-date'] if date_elem else "Unknown"

                        data = {
                            "League": comp['league_tag'], "Season": season_year_str, "Date": match_date,
                            "HomeTeam": home_team, "AwayTeam": away_team,
                            "FTHG": home_goals, "FTAG": away_goals
                        }

                        # --- 1. TEMEL İSTATİSTİKLER (Pos, Cards, Passing, Shooting) ---
                        # Bu kısım genellikle 'team_stats' içindedir

                        main_stats_source = match_soup.find("div", id="team_stats")
                        if not main_stats_source:
                            # Gizli ise bul
                            wrapper = match_soup.find("div", id="all_matchstats")
                            if wrapper:
                                comment = wrapper.find(
                                    string=lambda t: isinstance(t, str) and "team_stats" in t)  # team_stats ara
                                if not comment:  # Bazen matchstats içinde olur
                                    comment = wrapper.find(string=lambda t: isinstance(t, str) and "matchstats" in t)
                                if comment: main_stats_source = BeautifulSoup(comment, 'html.parser')

                        # Varsayılanlar
                        data["HomePossession"], data["AwayPossession"] = '50', '50'
                        data["HomeSOT"], data["HomeShots"], data["AwaySOT"], data["AwayShots"] = '0', '0', '0', '0'

                        if main_stats_source:
                            # Possession
                            data["HomePossession"], data["AwayPossession"] = extract_possession(main_stats_source)
                            # Cards
                            data["HomeYellowCards"], data["HomeRedCards"], data["AwayYellowCards"], data[
                                "AwayRedCards"] = extract_cards(main_stats_source)

                            # --- ŞUTLAR ve PASLAR (Bar Stats) ---
                            # Bu kısım biraz regex büyücülüğü gerektirir
                            text_content = main_stats_source.get_text(" ")

                            # Shots on Target (Örn: 4 of 13 ... 3 of 8)
                            # "Shots on Target" yazısından sonraki sayıları yakala
                            shots_match = re.search(r'Shots on Target.*?(\d+)\s+of\s+(\d+).*?(\d+)\s+of\s+(\d+)',
                                                    text_content, re.DOTALL)
                            if shots_match:
                                data["HomeSOT"], data["HomeShots"] = shots_match.group(1), shots_match.group(2)
                                data["AwaySOT"], data["AwayShots"] = shots_match.group(3), shots_match.group(4)

                            # Passing (Opsiyonel, istersen ekleyebilirsin)
                            # pass_match = re.search(...) logic similar to above

                        # --- 2. EKSTRA İSTATİSTİKLER (Fouls, Corners, etc.) ---
                        extra_source = match_soup.find("div", id="team_stats_extra")
                        if not extra_source:
                            wrapper = match_soup.find("div", id="all_matchstats")
                            if wrapper:
                                comment = wrapper.find(string=lambda t: isinstance(t, str) and "matchstats" in t)
                                if comment: extra_source = BeautifulSoup(comment, 'html.parser')

                        if extra_source:
                            data["HomeFouls"], data["AwayFouls"] = extract_stat_row(extra_source, "Fouls")
                            data["HomeCorners"], data["AwayCorners"] = extract_stat_row(extra_source, "Corners")
                            data["HomeCrosses"], data["AwayCrosses"] = extract_stat_row(extra_source, "Crosses")
                            data["HomeTouches"], data["AwayTouches"] = extract_stat_row(extra_source, "Touches")
                            data["HomeTackles"], data["AwayTackles"] = extract_stat_row(extra_source, "Tackles")
                            data["HomeInterceptions"], data["AwayInterceptions"] = extract_stat_row(extra_source,
                                                                                                    "Interceptions")
                            data["HomeAerialsWon"], data["AwayAerialsWon"] = extract_stat_row(extra_source,
                                                                                              "Aerials Won")
                            data["HomeClearances"], data["AwayClearances"] = extract_stat_row(extra_source,
                                                                                              "Clearances")
                            data["HomeOffsides"], data["AwayOffsides"] = extract_stat_row(extra_source, "Offsides")
                            data["HomeGoalKicks"], data["AwayGoalKicks"] = extract_stat_row(extra_source, "Goal Kicks")
                            data["HomeThrowIns"], data["AwayThrowIns"] = extract_stat_row(extra_source, "Throw Ins")
                            data["HomeLongBalls"], data["AwayLongBalls"] = extract_stat_row(extra_source, "Long Balls")
                        else:
                            for k in ["HomeFouls", "HomeCorners", "HomeCrosses", "HomeTouches", "HomeTackles",
                                      "HomeInterceptions", "HomeAerialsWon", "HomeClearances", "HomeOffsides",
                                      "HomeGoalKicks", "HomeThrowIns", "HomeLongBalls"]:
                                data[k] = '0';
                                data[k.replace('Home', 'Away')] = '0'

                        season_data.append(data)

                        print(f"\n✅ {i}/{len(match_links)}: {home_team} {home_goals}-{away_goals} {away_team}")
                        print(
                            f"   📊 Top: %{data['HomePossession']}-%{data['AwayPossession']} | Şut(SOT): {data['HomeShots']}({data['HomeSOT']}) - {data['AwayShots']}({data['AwaySOT']})")
                        print(
                            f"   🚩 Korner: {data['HomeCorners']}-{data['AwayCorners']} | Faul: {data['HomeFouls']}-{data['AwayFouls']}")
                        print(
                            f"   🟨 Sarı: {data['HomeYellowCards']}-{data['AwayYellowCards']} | 🟥 Kırmızı: {data['HomeRedCards']}-{data['AwayRedCards']}")
                        print("-" * 40)

                    except Exception as e:
                        print(f"    ⚠️ Hata: {e}")
                        continue

                all_matches_data.extend(season_data)
                df_save = pd.DataFrame(all_matches_data)
                df_save.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
                print(f"  💾 SEZON KAYDEDİLDİ. Toplam Veri: {len(df_save)} maç.")

            except Exception as e:
                print(f"  🚨 Sezon Hatası: {e}")
                continue

finally:
    if driver:
        driver.quit()
        print("\n🎉 BİTTİ.")