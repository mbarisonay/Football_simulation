# main.py (Veritabanını Tam Doldurma Versiyonu)

import sys
import os
import time

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from data_ingestion.api_client import get_teams_by_league_and_season, get_fixtures_by_league_and_season
# db_manager'dan yeni fonksiyonlar da import edeceğiz
from database.db_manager import create_database, insert_teams, insert_matches, insert_seasons

# --- Ayarlar ---
LEAGUE_ID = 39
LEAGUE_NAME = "Premier League"
# Elimizdeki verilerle uyumlu sezon aralığı
SEZONLAR = range(2021, 2024)  # 2021, 2022, 2023 sezonlarını kapsar


def setup_database_from_scratch():
    """Veritabanını sıfırdan oluşturur, sezonları, takımları ve maçları doldurur."""

    # 1. Adım: Veritabanını ve tüm tabloları oluştur
    create_database()

    # 2. Adım: Sezonlar tablosunu doldur
    # Bu adımı döngünün dışında, en başta bir kere yapıyoruz.
    seasons_to_add = [{'sezon_yili': year, 'lig_adi': LEAGUE_NAME} for year in SEZONLAR]
    insert_seasons(seasons_to_add)  # Bu fonksiyonu db_manager'a ekleyeceğiz

    # 3. Adım: Her sezon için takımları ve maçları doldur
    for sezon in SEZONLAR:
        print(f"\n===== {sezon} SEZONU İŞLENİYOR =====\n")

        # O sezondaki takımları çek ve veritabanına ekle
        teams = get_teams_by_league_and_season(LEAGUE_ID, sezon)
        if teams:
            insert_teams(teams)
        else:
            print(f"{sezon} için takım verisi alınamadı. Sonraki sezona geçiliyor.")
            continue

        # API limitlerini aşmamak için bekle
        print("API rate limitini aşmamak için 7 saniye bekleniyor...")
        time.sleep(7)

        # O sezondaki maçları çek ve veritabanına ekle
        matches = get_fixtures_by_league_and_season(LEAGUE_ID, sezon)
        if matches:
            # ÖNEMLİ: API'den gelen sezon_araligi'ni doğru sezon_yili ile değiştiriyoruz
            for match in matches:
                match['sezon_yili'] = sezon
            insert_matches(matches)
        else:
            print(f"{sezon} için maç verisi alınamadı.")

        print("Bir sonraki sezona geçmeden önce 7 saniye bekleniyor...")
        time.sleep(7)


if __name__ == '__main__':
    print("----- VERİTABANI SIFIRDAN KURULUYOR -----")
    setup_database_from_scratch()
    print("\n----- TÜM İŞLEMLER TAMAMLANDI -----")