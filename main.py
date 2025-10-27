# main.py (Orijinal Hali)

import sys
import os

# Projenin ana (root) dizininin yolunu al
project_root = os.path.dirname(os.path.abspath(__file__))
# Python'a modülleri araması için bu yolu göster
sys.path.insert(0, project_root)

# Artık importlar sorunsuz çalışacaktır
from data_ingestion.api_client import get_teams_by_league_and_season
from database.db_manager import create_database, insert_teams

# --- Ayarlar ---
# Simüle etmek istediğimiz lig ve sezon
LEAGUE_ID = 39  # İngiltere Premier Ligi
SEASON = 2023  # 2023-2024 Sezonu


def setup_teams():
    """Belirtilen lig ve sezondaki takımları API'den alıp veritabanına yazar."""

    create_database()
    teams = get_teams_by_league_and_season(LEAGUE_ID, SEASON)

    if teams:
        insert_teams(teams)
    else:
        print("API'den takım verisi alınamadığı için işlem durduruldu.")


if __name__ == '__main__':
    print("----- PROJE BAŞLATILIYOR -----")
    setup_teams()
    print("----- İŞLEM TAMAMLANDI -----")