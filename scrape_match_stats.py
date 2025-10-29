# scrape_match_stats.py (Düzeltilmiş Seçici ile Nihai Versiyon)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

# --- AYARLAR ---
BASE_URL = "https://www.transfermarkt.com"
SEASONS = list(range(2000, 2024))  # 2000'den 2023'e kadar olan tamamlanmış sezonlar
OUTPUT_FILE = "epl_match_stats_2000_2024.csv"
all_matches_data = []

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # Arka planda çalışması için
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = None
try:
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    driver.get(BASE_URL)
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_1056579")))
        accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="ACCEPT ALL"]')))
        accept_button.click()
        print("[✓] Çerezler kabul edildi.")
        driver.switch_to.default_content()
    except Exception:
        print("[!] Çerez penceresi bulunamadı, devam ediliyor.")
        driver.switch_to.default_content()
    time.sleep(2)

    for season in SEASONS:
        print(f"\n--- {season}-{season + 1} Sezonu Başlatılıyor ---")

        # Fikstür/Sonuçlar sayfasına git. URL yapısı bazen değişebiliyor. Bu daha genel bir yol.
        fixture_url = f"{BASE_URL}/premier-league/spielplan/wettbewerb/GB1/saison_id/{season}"
        driver.get(fixture_url)

        # --- DÜZELTİLMİŞ SEÇİCİ ---
        # Maç raporu linklerini içeren hücreleri bul ve içlerindeki <a> etiketlerini al
        soup = BeautifulSoup(driver.page_source, "html.parser")
        match_links = soup.select("td.ergebnis a")
        match_urls = [BASE_URL + link['href'] for link in match_links if 'spielbericht' in link['href']]

        print(f"  → {len(match_urls)} adet maç linki bulundu. İstatistikler çekiliyor...")
        if not match_urls:
            print("  [!] Bu sezon için maç linki bulunamadı, atlanıyor.")
            continue

        season_matches = []
        for i, url in enumerate(match_urls, 1):
            try:
                driver.get(url)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sb-statistik")))

                match_soup = BeautifulSoup(driver.page_source, "html.parser")

                home_team = match_soup.select_one("div.sb-team a[href*='heim']").get_text(strip=True)
                away_team = match_soup.select_one("div.sb-team a[href*='gast']").get_text(strip=True)
                score_text = match_soup.select_one("div.sb-endstand").get_text(strip=True).split('(')[0].strip()
                score = score_text.split(':')
                home_goals = int(score[0])
                away_goals = int(score[1])
                date_text = match_soup.select_one("p.sb-datum a").get_text(strip=True).split(' - ')[0].strip()

                stats_box = match_soup.find('div', class_='sb-statistik')


                def get_stat(box, stat_name):
                    stat_div = box.find('div', string=lambda text: text and stat_name in text)
                    if not stat_div: return 'N/A', 'N/A'
                    values = stat_div.find_previous_sibling('div').find_all('div')
                    return values[0].get_text(strip=True), values[2].get_text(strip=True)


                shots_home, shots_away = get_stat(stats_box, "Shots")
                sot_home, sot_away = get_stat(stats_box, "Shots on goal")
                fouls_home, fouls_away = get_stat(stats_box, "Fouls")
                corners_home, corners_away = get_stat(stats_box, "Corner kicks")

                season_matches.append({
                    "Season": f"{season}-{season + 1}", "Date": date_text,
                    "HomeTeam": home_team, "AwayTeam": away_team,
                    "FullTimeHomeGoals": home_goals, "FullTimeAwayGoals": away_goals,
                    "HomeShots": shots_home, "AwayShots": shots_away,
                    "HomeShotsOnTarget": sot_home, "AwayShotsOnTarget": sot_away,
                    "HomeFouls": fouls_home, "AwayFouls": fouls_away,
                    "HomeCorners": corners_home, "AwayCorners": corners_away
                })
                print(f"    {i}/{len(match_urls)}: {home_team} vs {away_team} [OK]")
                time.sleep(1)

            except Exception as e:
                print(f"    ⚠️ Maç {i} ({url}) işlenirken hata oluştu.")
                continue

        all_matches_data.extend(season_matches)
        df_temp = pd.DataFrame(all_matches_data)
        df_temp.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"  --- {season}-{season + 1} sezonu tamamlandı ve veriler kaydedildi. ---")

finally:
    if driver:
        driver.quit()

print(f"\n✅ İşlem tamamlandı! {len(all_matches_data)} kayıt '{OUTPUT_FILE}' dosyasına kaydedildi.")