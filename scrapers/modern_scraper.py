import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
import re
import sys
import os
import subprocess

# --- AYARLAR ---
BASE_URL = "https://fbref.com"
OUTPUT_FILE = "ALL_LEAGUES_DETAILED_MATCHES.csv"

# Kaldığın yerden devam etmesi için 2019 yapıldı
SEASONS_TO_SCRAPE = list(range(2016, 2025))

COMPETITIONS = [
    {"id": "20", "name": "Bundesliga", "league_tag": "Bundesliga"},
    {"id": "11", "name": "Serie-A", "league_tag": "Serie A"},
    {"id": "13", "name": "Ligue-1", "league_tag": "Ligue-1"},
    {"id": "26", "name": "Super-Lig", "league_tag": "Süper Lig"},
    {"id": "32", "name": "Primeira-Liga", "league_tag": "Liga Portugal"}
]


# --- DRIVER YÖNETİMİ ---
def kill_chrome():
    """Arkada kalan chrome işlemlerini temizler"""
    try:
        subprocess.call("taskkill /F /IM chrome.exe /T", shell=True, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        subprocess.call("taskkill /F /IM chromedriver.exe /T", shell=True, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass


def init_driver():
    kill_chrome()
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # --- KRİTİK DÜZELTME: EAGER STRATEGY ---
    # Sayfanın resimlerinin/reklamlarının yüklenmesini bekleme, HTML gelince başla.
    options.page_load_strategy = 'eager'

    try:
        d = uc.Chrome(options=options, use_subprocess=True)
        d.set_page_load_timeout(90)  # Süreyi uzattık
        return d
    except:
        time.sleep(5)
        return init_driver()


# --- BAŞLANGIÇTA MEVCUT VERİYİ OKU ---
scraped_urls = set()
if os.path.exists(OUTPUT_FILE):
    try:
        # Sadece URL sütununu okuyarak hafızayı yormayalım
        df_existing = pd.read_csv(OUTPUT_FILE, usecols=['MatchURL'])
        scraped_urls = set(df_existing['MatchURL'].tolist())
        print(f"📥 Mevcut dosya bulundu. {len(scraped_urls)} maç zaten çekilmiş, bunlar atlanacak.")
    except Exception as e:
        print(f"ℹ️ Dosya var ama okunamadı veya boş ({e}). Sıfırdan başlanıyor.")

driver = init_driver()


# --- PARSER FONKSİYONLARI ---
def extract_stat_row(soup_obj, stat_name):
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
    h_succ, h_att, a_succ, a_att = '0', '0', '0', '0'
    label = soup_obj.find(lambda tag: tag.name in ["div", "th"] and stat_name in tag.text)
    if label:
        if label.name == "th":
            row = label.find_parent("tr").find_next_sibling("tr")
            if row:
                tds = row.find_all("td")
                if len(tds) >= 2:
                    parts_h = re.findall(r'(\d+)\s+of\s+(\d+)', tds[0].text)
                    if parts_h: h_succ, h_att = parts_h[0]
                    parts_a = re.findall(r'(\d+)\s+of\s+(\d+)', tds[1].text)
                    if parts_a: a_succ, a_att = parts_a[0]
        elif label.name == "div" or label.parent.name == "div":
            container = label.find_parent("div").parent
            if container:
                text = container.get_text(" ")
                matches = re.findall(r'(\d+)\s+of\s+(\d+)', text)
                if len(matches) >= 2:
                    h_succ, h_att = matches[0]
                    a_succ, a_att = matches[1]
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
            strongs = poss_header.find_parent("table").find_all("strong") if poss_header.find_parent("table") else []
            percents = [s.text.strip().replace('%', '') for s in strongs if '%' in s.text]
            if len(percents) >= 2:
                return percents[0], percents[1]
    return '50', '50'


# --- ANA DÖNGÜ ---
try:
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

                try:
                    driver.get(fixture_url)
                except:
                    print("    ⚠️ Sezon sayfası hatası. Driver yenileniyor...")
                    driver = init_driver();
                    driver.get(fixture_url)

                # Eager load olduğu için elementin gelmesini beklemek şart
                time.sleep(3)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                match_links_tags = soup.select("td[data-stat='match_report'] a")

                if not match_links_tags:
                    print("    ⚠️ Maç linki bulunamadı.")
                    continue

                match_links = [BASE_URL + a['href'] for a in match_links_tags]
                print(f"    -> {len(match_links)} adet maç bulundu.")

                for i, url in enumerate(match_links, 1):
                    if url in scraped_urls:
                        if i % 50 == 0: print(f"    ℹ️ {i}. Maç zaten var, atlanıyor...")
                        continue

                    success = False;
                    retry_count = 0
                    while not success and retry_count < 3:
                        try:
                            driver.get(url)
                            # İçeriğin yüklenmesi için biraz bekle
                            time.sleep(random.uniform(2, 4))

                            match_soup = BeautifulSoup(driver.page_source, "html.parser")
                            content_div = match_soup.select_one("#content")

                            if not content_div: raise Exception("Boş sayfa")
                            scorebox = content_div.select_one("div.scorebox")
                            if not scorebox:
                                print(f"    {i}. Maç atlanıyor (Scorebox yok).");
                                success = True;
                                continue

                            team_links = scorebox.select("a[href*='/squads/']")
                            scores = scorebox.select("div.score")
                            date_elem = scorebox.select_one("div.scorebox_meta span.venuetime")

                            if len(team_links) < 2 or len(scores) < 2: success = True; continue

                            home_team = team_links[0].get_text(strip=True)
                            away_team = team_links[1].get_text(strip=True)
                            home_goals = scores[0].get_text(strip=True)
                            away_goals = scores[1].get_text(strip=True)
                            match_date = date_elem['data-venue-date'] if date_elem else "Unknown"

                            data = {
                                "League": comp['league_tag'], "Season": season_year_str, "Date": match_date,
                                "HomeTeam": home_team, "AwayTeam": away_team,
                                "FTHG": home_goals, "FTAG": away_goals,
                                "MatchURL": url
                            }

                            # --- PARSER ---
                            main_stats_source = match_soup.find("div", id="team_stats")
                            extra_stats_source = match_soup.find("div", id="team_stats_extra")

                            if not main_stats_source or not extra_stats_source:
                                wrapper = match_soup.find("div", id="all_matchstats")
                                if wrapper:
                                    for comment in wrapper.find_all(
                                            string=lambda t: isinstance(t, str) and "matchstats" in t):
                                        comment_soup = BeautifulSoup(comment, 'html.parser')
                                        if not main_stats_source: main_stats_source = comment_soup.find("div",
                                                                                                        id="team_stats")
                                        if not extra_stats_source: extra_stats_source = comment_soup.find("div",
                                                                                                          id="team_stats_extra")

                            if main_stats_source:
                                data["HomePossession"], data["AwayPossession"] = extract_possession(main_stats_source)
                                data["HomePassesCompleted"], data["HomePassesAttempted"], data["AwayPassesCompleted"], \
                                data["AwayPassesAttempted"] = extract_bar_stat(main_stats_source, "Passing Accuracy")
                                data["HomeSOT"], data["HomeShots"], data["AwaySOT"], data[
                                    "AwayShots"] = extract_bar_stat(main_stats_source, "Shots on Target")
                                data["HomeSaves"], data["HomeSavesAllowed"], data["AwaySaves"], data[
                                    "AwaySavesAllowed"] = extract_bar_stat(main_stats_source, "Saves")
                            else:
                                for k in ["HomePossession", "AwayPossession", "HomeSOT", "HomeShots", "AwaySOT",
                                          "AwayShots",
                                          "HomePassesCompleted", "HomePassesAttempted", "AwayPassesCompleted",
                                          "AwayPassesAttempted",
                                          "HomeSaves", "HomeSavesAllowed", "AwaySaves", "AwaySavesAllowed"]:
                                    data[k] = '0'

                            if extra_stats_source:
                                for stat in ["Fouls", "Corners", "Crosses", "Touches", "Tackles", "Interceptions",
                                             "Aerials Won", "Clearances", "Offsides", "Goal Kicks", "Throw Ins",
                                             "Long Balls"]:
                                    h, a = extract_stat_row(extra_stats_source, stat)
                                    data[f"Home{stat.replace(' ', '')}"] = h
                                    data[f"Away{stat.replace(' ', '')}"] = a
                            else:
                                for stat in ["Fouls", "Corners", "Crosses", "Touches", "Tackles", "Interceptions",
                                             "Aerials Won", "Clearances", "Offsides", "Goal Kicks", "Throw Ins",
                                             "Long Balls"]:
                                    data[f"Home{stat.replace(' ', '')}"] = '0'
                                    data[f"Away{stat.replace(' ', '')}"] = '0'

                            # Kartlar 0
                            data["HomeYellowCards"], data["HomeRedCards"] = '0', '0'
                            data["AwayYellowCards"], data["AwayRedCards"] = '0', '0'

                            # --- ANLIK KAYIT ---
                            df_single = pd.DataFrame([data])
                            header_mode = not os.path.exists(OUTPUT_FILE)
                            df_single.to_csv(OUTPUT_FILE, mode='a', header=header_mode, index=False,
                                             encoding="utf-8-sig")
                            scraped_urls.add(url)

                            print(
                                f"\n✅ {i}/{len(match_links)}: {home_team} {home_goals}-{away_goals} {away_team} [KAYDEDİLDİ]")
                            print(
                                f"   📊 Top: %{data['HomePossession']}-%{data['AwayPossession']} | Şut(SOT): {data['HomeShots']}({data['HomeSOT']}) | Pas: {data['HomePassesCompleted']}-{data['AwayPassesCompleted']}")
                            print(
                                f"   🚩 Korner: {data['HomeCorners']} | Faul: {data['HomeFouls']} | Ofsayt: {data['HomeOffsides']}")
                            print("-" * 40)

                            success = True

                        except Exception as e:
                            print(f"    ⚠️ Hata (Deneme {retry_count + 1}): {e}")
                            retry_count += 1
                            if "HTTPConnectionPool" in str(e) or "timed out" in str(e) or "refused" in str(e):
                                print("    🚨 Driver kilitlendi! Yenileniyor...")
                                driver = init_driver()

            except Exception as e:
                print(f"  🚨 Sezon Hatası: {e}")
                continue

except KeyboardInterrupt:
    print("\n🛑 İşlem kullanıcı tarafından durduruldu.")

finally:
    if driver: kill_chrome()
    print("\n🎉 BİTTİ.")