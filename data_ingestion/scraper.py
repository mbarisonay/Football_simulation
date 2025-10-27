# data_ingestion/scraper.py (Selenium Manager ile Çalışan Son Versiyon)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Comment
import time


def scrape_fbref_season(season_start_year):
    """
    FBref.com'dan belirtilen sezonun Premier Lig maç sonuçlarını çeker.
    Bu versiyon, sürücü yönetimi için Selenium'un kendi mekanizmasını (Selenium Manager) kullanır.
    :param season_start_year: Sezonun başlangıç yılı (örn: 2022-2023 sezonu için 2022)
    """

    # 1. Selenium'u ayarla (Selenium 4.6.0 ve üstü sürücü yönetimini kendi yapar)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Tarayıcının görsel olarak açılmadan arka planda çalışmasını sağlar.
    options.add_argument('--log-level=3')  # Terminaldeki gereksiz logları gizler

    # Tarayıcıyı başlat (service=... parametresi olmadan)
    # Selenium Manager doğru sürücüyü otomatik olarak bulup yönetecek.
    driver = webdriver.Chrome(options=options)

    season_str = f"{season_start_year}-{season_start_year + 1}"
    url = f"https://fbref.com/en/comps/9/{season_str}/schedule/{season_str}-Premier-League-Scores-and-Fixtures"

    print(f"{season_str} sezonu için FBref'ten veri çekiliyor (Selenium Manager kullanılıyor)...")

    try:
        # 2. Sayfaya git
        driver.get(url)

        # 3. Sayfanın tam olarak yüklenmesini ve tablonun görünür olmasını bekle
        wait = WebDriverWait(driver, 10)
        # Tablonun ID'si, gizlenmiş HTML'deki ID ile aynı. Bu ID'li elementin var olmasını bekliyoruz.
        table_id = f"sched_ks_{season_str}_9"
        wait.until(EC.presence_of_element_located((By.ID, table_id)))

        # 4. Sayfanın son halinin HTML'ini al
        html_content = driver.page_source

    except Exception as e:
        print(f"Selenium ile sayfa yüklenirken bir hata oluştu: {e}")
        driver.quit()
        return None
    finally:
        # Hata olsa da olmasa da tarayıcıyı kapat
        driver.quit()
        print("Selenium tarayıcısı kapatıldı.")

    # 5. Artık elimizde tam ve işlenmiş HTML var, gerisi BeautifulSoup'un işi
    soup = BeautifulSoup(html_content, 'html.parser')

    # Bazı durumlarda veri hala yorum içinde olabilir, bu yüzden kontrol edelim.
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    table_html = ""
    for comment in comments:
        if "Scores & Fixtures" in comment:
            table_html = comment
            break

    # Eğer veri yorum içinde DEĞİLSE, doğrudan HTML'in kendisini kullan
    if not table_html:
        table_soup = soup
    else:
        table_soup = BeautifulSoup(table_html, 'html.parser')

    table = table_soup.find('table', class_='stats_table')

    if not table or not table.tbody:
        print("Maç tablosu veya tbody bölümü bulunamadı.")
        return None

    matches = []

    for row in table.tbody.find_all('tr'):
        cells = row.find_all('td')

        if len(cells) < 5 or not cells[3].get_text(strip=True):
            conti