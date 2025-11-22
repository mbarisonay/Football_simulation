import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
import os
import re

# --- TEŞHİS AYARLARI ---
# URL'yi çok basitleştirdik. Sadece Premier League (lg=13) ve Sezon ID'si.
# Eğer bu çalışırsa, sorun senin "showCol" parametrelerindedir.
BASE_URL_TEMPLATE = "https://sofifa.com/players?type=all&lg=13"

# Test etmek için sadece ilk 2 yılı kullanacağız, hepsini beklemeyelim.
FIFA_ROSTERS = {
    "FIFA 15": ("2014-2015", "150059"),
    "FC 25": ("2024-2025", "250001")
}


def take_debug_snapshot(driver, filename_prefix):
    """ Hata anında fotoğraf ve HTML kaydeder """
    try:
        screenshot_name = f"{filename_prefix}_screenshot.png"
        html_name = f"{filename_prefix}_source.html"

        driver.save_screenshot(screenshot_name)
        with open(html_name, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        print(f"  [!!!] HATA AYIKLAMA: Botun ne gördüğü '{screenshot_name}' ve '{html_name}' dosyalarına kaydedildi.")
        print(f"  [!!!] Lütfen '{screenshot_name}' dosyasına bakıp botun sayfayı açıp açamadığını kontrol et.")
    except Exception as e:
        print(f"  Snapshot hatası: {e}")


# --- ANA KOD ---
driver = None

try:
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), "sofifa_profile")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--lang=en-US")
    options.add_argument("--window-size=1920,1080")

    print("Tarayıcı başlatılıyor...")
    driver = uc.Chrome(options=options)

    print("SoFIFA ana sayfasına gidiliyor...")
    driver.get("https://sofifa.com")
    print("\n--- DOĞRULAMA ---")
    print("1. Tarayıcı açıldı mı?")
    print("2. Cloudflare / Robot kontrolü varsa geç.")
    print("3. 'Accept All' çerez uyarısı varsa tıkla.")
    input("Her şey tamamsa ve ana sayfa görünüyorsa ENTER'a bas...")

    for version_name, (season_str, roster_id) in FIFA_ROSTERS.items():
        print(f"\n--- TEST EDİLİYOR: {version_name} ---")

        # Basit URL
        target_url = f"{BASE_URL_TEMPLATE}&r={roster_id}&set=true"
        print(f"Gidiliyor: {target_url}")

        driver.get(target_url)
        time.sleep(5)  # Sayfanın tam yüklenmesi için cömert bir süre

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Kontrol 1: Oyuncu Tablosu var mı?
        table = soup.find('table')
        # Kontrol 2: Liste görünümü var mı?
        list_view = soup.find('ul', {'class': 'list'})
        # Kontrol 3: "No results found" yazısı var mı?
        no_results = soup.find(string=re.compile("No results found"))

        if table:
            print(f"✅ BAŞARILI! Tablo bulundu. {len(table.find_all('tr'))} satır var.")
            # Örnek veri yazdıralım
            print(f"İlk Oyuncu: {table.find('td', {'class': 'col-name'}).text.strip()}")

        elif list_view:
            print(f"✅ BAŞARILI! Liste görünümü bulundu.")

        elif no_results:
            print(f"❌ BAŞARISIZ: Sayfa 'No results found' (Sonuç yok) döndürdü.")
            print("Sebebi: ID yanlış olabilir veya o sezon için Premier League ID'si (lg=13) farklı olabilir.")
            take_debug_snapshot(driver, f"error_{version_name}")

        else:
            print(f"❌ BAŞARISIZ: Ne tablo ne liste bulundu. (View: Unknown)")
            # Burası senin yaşadığın hata. Şimdi fotoğrafını çekeceğiz.
            take_debug_snapshot(driver, f"error_{version_name}")

except Exception as e:
    print(f"Kod hatası: {e}")

finally:
    if driver:
        print("\nTarayıcı açık kalacak, inceleyebilirsin. Kapatmak için manuel kapat.")
        # driver.quit() # Otomatik kapanmasın, sen incele