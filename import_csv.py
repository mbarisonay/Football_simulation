# import_csv.py (Zengin CSV için Nihai Aktarım Scripti)

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime

# --- AYARLAR ---
CSV_DOSYA_ADI = 'epl_final.csv'
DATABASE_NAME = 'futbol_veritabani.db'


def import_all_data_from_csv():
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Eski '{DATABASE_NAME}' dosyası silindi.")

    from database.db_manager import create_database_structure
    create_database_structure()

    try:
        df = pd.read_csv(CSV_DOSYA_ADI, encoding='ISO-8859-1')
        print(f"'{CSV_DOSYA_ADI}' başarıyla okundu. Toplam {len(df)} maç bulundu.")
    except Exception as e:
        print(f"HATA: CSV okunurken bir hata oluştu: {e}")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Takımları ve Sezonları Ekle
    all_teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
    teams_to_insert = [(team,) for team in all_teams if pd.notna(team)]
    cursor.executemany('INSERT INTO Takimlar (takim_adi) VALUES (?)', teams_to_insert)
    print(f"{len(teams_to_insert)} benzersiz takım eklendi.")

    all_seasons = df['Season'].unique()
    seasons_to_insert = [(season, 'Premier League') for season in all_seasons if pd.notna(season)]
    cursor.executemany('INSERT INTO Sezonlar (sezon_araligi, lig_adi) VALUES (?)', seasons_to_insert)
    print(f"{len(seasons_to_insert)} benzersiz sezon eklendi.")
    conn.commit()

    # Maç verilerini hazırlarken sütunları doğru şekilde yeniden adlandır
    matches_df = df.rename(columns={
        'Season': 'sezon_araligi',
        'MatchDate': 'mac_tarihi',
        'HomeTeam': 'ev_sahibi_takim',
        'AwayTeam': 'deplasman_takim',
        'FullTimeHomeGoals': 'ev_sahibi_gol',
        'FullTimeAwayGoals': 'deplasman_gol',
        'FullTimeResult': 'sonuc',
        'HomeShots': 'ev_sahibi_sut',
        'AwayShots': 'deplasman_sut',
        'HomeShotsOnTarget': 'ev_sahibi_isabetli_sut',
        'AwayShotsOnTarget': 'deplasman_isabetli_sut',
        'HomeFouls': 'ev_sahibi_faul',
        'AwayFouls': 'deplasman_faul',
        'HomeCorners': 'ev_sahibi_korner',
        'AwayCorners': 'deplasman_korner',
        'HomeYellowCards': 'ev_sahibi_sari_kart',
        'AwayYellowCards': 'deplasman_sari_kart',
        'HomeRedCards': 'ev_sahibi_kirmizi_kart',
        'AwayRedCards': 'deplasman_kirmizi_kart'
    })

    # Veritabanımızdaki sütunlarla eşleşen bir liste oluşturalım
    final_columns = [
        'sezon_araligi', 'mac_tarihi', 'ev_sahibi_takim', 'deplasman_takim', 'ev_sahibi_gol',
        'deplasman_gol', 'sonuc', 'ev_sahibi_sut', 'deplasman_sut', 'ev_sahibi_isabetli_sut',
        'deplasman_isabetli_sut', 'ev_sahibi_faul', 'deplasman_faul', 'ev_sahibi_korner',
        'deplasman_korner', 'ev_sahibi_sari_kart', 'deplasman_sari_kart',
        'ev_sahibi_kirmizi_kart', 'deplasman_kirmizi_kart'
    ]

    # Sadece bu sütunları alarak DataFrame'i temizle
    matches_df = matches_df[final_columns]

    matches_df.to_sql('Maclar', conn, if_exists='append', index=False)
    print(f"{len(matches_df)} maç detayı 'Maclar' tablosuna eklendi.")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    import_all_data_from_csv()
    print("\nVeri aktarımı tamamlandı!")