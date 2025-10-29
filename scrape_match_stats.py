# scrape_match_stats.py (Doğru URL ve İstatistik Sayfası Versiyonu)

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

# --- AYARLAR ---
BASE_URL = "https://www.transfermarkt.com"
SEASONS = list(range(2011, 2012))
OUTPUT_FILE = "epl_match_stats_tm_FINAL.csv"
all_matches_data = []

# --- Selenium Başlat ---
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # Arka planda çalışması için
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--start-maximized")

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
    except:
        print("[!] Çerez penceresi bulunamadı, devam ediliyor.")
        driver.switch_to.default_content()
    time.sleep(2)

    for season in SEASONS:
        print(f"\n--- {season}-{season + 1} Sezonu Başlatılıyor ---")

        match_urls = []
        for week in range(1, 39):
            fixture_url = f"{BASE_URL}/premier-league/spieltag/wettbewerb/GB1/plus/?saison_id={season}&spieltag={week}"
            driver.get(fixture_url)
            time.sleep(random.uniform(1.5, 2.5))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.select("td.spieltagsansicht-ergebnis a")
            for link in links:
                if 'spielbericht' in link['href']:
                    # --- KRİTİK DÜZELTME BURADA ---
                    # Linki alıyoruz ama '/index/' kısmını '/statistik/' ile değiştiriyoruz
                    # Orijinal link: .../index/spielbericht/123456
                    # Yeni link:     .../statistik/spielbericht/123456
                    stats_url = BASE_URL + link['href'].replace("/index/", "/statistik/")
                    match_urls.append(stats_url)
                    # -----------------------------

        match_urls = list(dict.fromkeys(match_urls))
        print(f"  → {len(match_urls)} adet İSTATİSTİK sayfası linki bulundu.")

        season_matches = []
        for i, url in enumerate(match_urls, 1):
            try:
                driver.get(url)
                # İstatistik sayfasındaki ana tablonun yüklenmesini bekle
                # Bu sayfada genellikle 'div.box' içinde istatistikler olur
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.box")))

                match_soup = BeautifulSoup(driver.page_source, "html.parser")

                # Takım isimlerini ve skoru al (Bunlar sayfanın üst kısmında standarttır)
                home_team = match_soup.select_one("div.sb-team.sb-heim a").get_text(strip=True)
                away_team = match_soup.select_one("div.sb-team.sb-gast a").get_text(strip=True)
                score_text = match_soup.select_one("div.sb-endstand").get_text(strip=True).split('(')[0].strip()
                score = score_text.split(':')
                home_goals, away_goals = int(score[0]), int(score[1])
                date_text = match_soup.select_one("p.sb-datum a").get_text(strip=True).split(' - ')[0].strip()

                # --- İSTATİSTİKLERİ ÇEKME ---
                # İstatistikler genellikle "div.sb-statistik" yerine farklı bir yapıda olabilir bu sayfada.
                # Ancak genellikle bir tablo veya liste içindedirler.
                # Transfermarkt'ın istatistik sayfasındaki yapıya göre genel bir çekme mantığı:

                # Önce varsayılan değerler
                stats = {
                    "Total shots": (0, 0), "Shots off target": (0, 0), "Saves": (0, 0),
                    "Corners": (0, 0), "Fouls": (0, 0), "Offsides": (0, 0)
                }

                # İstatistik satırlarını bul (Genellikle 'sb-statistik-zeile' class'ına sahip div'ler)
                stat_rows = match_soup.select("div.sb-statistik-zeile")
                for row in stat_rows:
                    label = row.select_one("div.sb-statistik-label").get_text(strip=True)
                    home_val = row.select_one("div.sb-statistik-heim .sb-statistik-zahl").get_text(strip=True)
                    away_val = row.select_one("div.sb-statistik-gast .sb-statistik-zahl").get_text(strip=True)

                    # Bazı istatistiklerin adları farklı olabilir, onları eşleştirelim
                    if "Shots" in label and "Total" in label:
                        stats["Total shots"] = (home_val, away_val)
                    elif "Shots" in label and "off" in label:
                        stats["Shots off target"] = (home_val, away_val)
                    elif "Saves" in label:
                        stats["Saves"] = (home_val, away_val)
                    elif "Corners" in label:
                        stats["Corners"] = (home_val, away_val)
                    elif "Fouls" in label:
                        stats["Fouls"] = (home_val, away_val)
                    elif "Offsides" in label:
                        stats["Offsides"] = (home_val, away_val)

                # İsabetli şut genellikle doğrudan verilmez, Toplam - İsabetsiz olarak hesaplanabilir
                # veya bazen doğrudan verilir. Basitlik için şimdilik elimizdekileri kaydedelim.

                season_matches.append({
                    "Season": f"{season}-{season + 1}", "Date": date_text,
                    "HomeTeam": home_team, "AwayTeam": away_team,
                    "FTHG": home_goals, "FTAG": away_goals,
                    "HS": stats["Total shots"][0], "AS": stats["Total shots"][1],
                    # İsabetli şut = Toplam şut - İsabetsiz şut (Basit bir tahmin)
                    # "HST": int(stats["Total shots"][0]) - int(stats["Shots off target"][0]), ...
                    "HC": stats["Corners"][0], "AC": stats["Corners"][1],
                    "HF": stats["Fouls"][0], "AF": stats["Fouls"][1],
                    "HO": stats["Offsides"][0], "AO": stats["Offsides"][1]
                })
                print(f"    {i}/{len(match_urls)}: {home_team} vs {away_team} [OK]")
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                # Bazı eski maçlarda istatistik sayfası olmayabilir, normaldir.
                print(f"    ⚠️ Maç {i} ({url}) işlenirken hata veya eksik veri: {e}")
                continue

        all_matches_data.extend(season_matches)
        df_temp = pd.DataFrame(all_matches_data)
        df_temp.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"  --- {season}-{season + 1} sezonu tamamlandı. ---")

finally:
    if driver: driver.quit()
print(f"\n✅ İşlem tamamlandı! {len(all_matches_data)} kayıt kaydedildi.")