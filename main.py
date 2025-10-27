# main.py (Sadece 2024 sezonunu çekmek için güncellendi)

import sys
import os
import time

# Projenin ana (root) dizininin yolunu al
project_root = os.path.dirname(os.path.abspath(__file__))
# Python'a modülleri araması için bu yolu göster
sys.path.insert(0, project_root)

from data_ingestion.api_client import get_teams_by_league_and_season, get_fixtures_by_league_and_season
from database.db_manager import create_database, insert_teams, insert_matches

# --- Ayarlar ---
LEAGUE_ID = 39  # İngiltere Premier Ligi
# Sadece 2024-2025 sezonunu çek
SEZONLAR = [2024]


def ingest_past_data():
    """Belirtilen ligin geçmiş sezon verilerini API'den alıp veritabanına yazar."""

    create_database()

    for sezon in SEZONLAR:
        print(f"\n===== {sezon} SEZONU İŞLENİYOR =====\n")

        teams = get_teams_by_league_and_season(LEAGUE_ID, sezon)
        if teams:
            insert_teams(teams)
        else:
            print(f"{sezon} için takım verisi alınamadı. Sonraki sezona geçiliyor.")
            continue

        print("API rate limitini aşmamak için 7 saniye bekleniyor...")
        time.sleep(7)

        matches = get_fixtures_by_league_and_season(LEAGUE_ID, sezon)
        if matches:
            insert_matches(matches)
        else:
            print(f"{sezon} için maç verisi alınamadı.")

        print("API rate limitini aşmamak için 7 saniye bekleniyor...")
        time.sleep(7)


if __name__ == '__main__':
    print("----- GEÇMİŞ VERİLERİ ÇEKME İŞLEMİ BAŞLATILIYOR -----")
    ingest_past_data()
    print("\n----- TÜM İŞLEMLER TAMAMLANDI -----")