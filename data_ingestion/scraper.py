# data-ingestion/scraper.py (İnsansı Davranış Modu)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


def scrape_mackolik_season():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless=new') # GÖZLEMLEMEK İÇİN BU SATIRI KAPALI TUTUYORUZ
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    print("Maçkolik'ten veri çekiliyor (İnsansı Mod)...")

    try:
        # 1. Adım: Ana sayfaya git
        driver.get("https://www.mackolik.com")
        print("Ana sayfaya gidildi.")

        # 2. Adım: Çerezleri kabul et
        try:
            wait = WebDriverWait(driver, 10)
            # Maçkolik'in çerez butonu ID'si 'accept-all-cookies-button'
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "accept-all-cookies-button")))
            accept_button.click()
            print("[BİLGİ] Çerez butonu bulundu ve tıklandı.")
        except Exception:
            print("[BİLGİ] Çerez butonu bulunamadı, zaman aşımına uğradı veya gerekli değil.")

        time.sleep(2)  # Sayfanın oturması için kısa bir bekleme

        # 3. Adım: Hedef URL'ye doğrudan git (Tıklama yerine daha güvenilir)
        season_url = "https://www.mackolik.com/futbol/türkiye/süper-lig/2022-2023/fikstür/1r097lpxe0xn03ihb7wi98kao"
        driver.get(season_url)
        print("Fikstür sayfasına gidildi.")

        # Maç kartlarının yüklenmesini bekle
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "widget-match-card__container")))
        print("[OK] Maç kartları sayfada belirdi.")

        # Sayfanın sonuna kadar yavaşça in
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        print("[OK] Sayfanın sonuna kadar inildi.")
        html_content = driver.page_source

    except Exception as e:
        print(f"Selenium ile işlem sırasında bir hata oluştu: {e}")
        driver.quit()
        return None
    finally:
        driver.quit()
        print("Selenium tarayıcısı kapatıldı.")

    # Buradan sonrası aynı...
    soup = BeautifulSoup(html_content, 'html.parser')
    match_cards = soup.find_all('div', class_='widget-match-card__container')

    if not match_cards:
        print("[HATA] Maç kartları ayrıştırılamadı.")
        return None

    matches = []

    for card in match_cards:
        try:
            status = card.find('div', class_='widget-match-card__status').get_text(strip=True)
            if status != 'Final':
                continue
            home_team = card.find('div', class_='widget-match-card__team--home').find('div',
                                                                                      class_='widget-match-card__team-name').get_text(
                strip=True)
            away_team = card.find('div', class_='widget-match-card__team--away').find('div',
                                                                                      class_='widget-match-card__team-name').get_text(
                strip=True)
            score_container = card.find('div', class_='widget-match-card__score-container')
            home_score = score_container.find('span', class_='widget-match-card__score--home').get_text(strip=True)
            away_score = score_container.find('span', class_='widget-match-card__score--away').get_text(strip=True)

            match_data = {
                'ev_sahibi': home_team,
                'deplasman': away_team,
                'ev_sahibi_gol': int(home_score),
                'deplasman_gol': int(away_score)
            }
            matches.append(match_data)
        except (AttributeError, ValueError, IndexError):
            continue

    print(f"\n{len(matches)} adet geçerli maç başarıyla ayrıştırıldı.")
    return matches


if __name__ == '__main__':
    scraped_matches = scrape_mackolik_season()

    if scraped_matches:
        print("\n--- İLK 5 MAÇIN SONUCU ---")
        for match in scraped_matches[:5]:
            print(match)
    else:
        print("\n[SONUÇ] Fonksiyon veri döndürmedi veya boş liste döndürdü.")