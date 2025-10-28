# import_csv.py (Gerçek Sütun Adlarıyla Çalışan Nihai Versiyon)

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime

# --- AYARLAR ---
CSV_DOSYA_ADI = 'final_dataset.csv'  # Lütfen bu adı kendi dosyanızın adıyla değiştirin.
DATABASE_NAME = 'futbol_veritabani.db'


def import_all_data_from_csv():
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Eski '{DATABASE_NAME}' dosyası silindi.")

    from database.db_manager import create_final_database_structure
    create_final_database_structure()

    try:
        df = pd.read_csv(CSV_DOSYA_ADI, encoding='ISO-8859-1')
        print(f"'{CSV_DOSYA_ADI}' başarıyla okundu. Toplam {len(df)} maç bulundu.")
    except Exception as e:
        print(f"HATA: CSV okunurken bir hata oluştu: {e}")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Takımları ve Sezonları ekle
    all_teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
    teams_to_insert = [(team,) for team in all_teams if pd.notna(team)]
    cursor.executemany('INSERT OR IGNORE INTO Takimlar (takim_adi) VALUES (?)', teams_to_insert)
    print(f"{len(teams_to_insert)} benzersiz takım 'Takimlar' tablosuna eklendi.")

    # Tarih formatını düzelt ve Sezon bilgisini oluştur
    def parse_date(date_str):
        for fmt in ('%d/%m/%y', '%d/%m/%Y'):
            try:
                return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
            except:
                continue
        return None

    df['mac_tarihi'] = df['Date'].apply(parse_date)
    df.dropna(subset=['mac_tarihi'], inplace=True)
    df['sezon_araligi'] = df['mac_tarihi'].apply(
        lambda x: f"{int(x[:4]) - 1}-{x[:4]}" if int(x[5:7]) < 8 else f"{x[:4]}-{int(x[:4]) + 1}"
    )

    all_seasons = df['sezon_araligi'].unique()
    seasons_to_insert = [(season, 'Premier League') for season in all_seasons if pd.notna(season)]
    cursor.executemany('INSERT OR IGNORE INTO Sezonlar (sezon_araligi, lig_adi) VALUES (?, ?)', seasons_to_insert)
    print(f"{len(seasons_to_insert)} benzersiz sezon 'Sezonlar' tablosuna eklendi.")
    conn.commit()

    # Maç verilerini 'Maclar' tablosuna yazmak için DataFrame'i hazırla
    # CSV'deki GERÇEK sütun adlarını kullanıyoruz
    matches_df = df.rename(columns={
        'HomeTeam': 'ev_sahibi_takim',
        'AwayTeam': 'deplasman_takim',
        'FTHG': 'ev_sahibi_gol',
        'FTAG': 'deplasman_gol',
        'FTR': 'sonuc'
    })

    # Sadece veritabanımızda olan sütunları seçelim
    final_columns = [
        'sezon_araligi', 'mac_tarihi', 'ev_sahibi_takim', 'deplasman_takim',
        'ev_sahibi_gol', 'deplasman_gol', 'sonuc'
    ]
    matches_df = matches_df[final_columns]

    # DataFrame'i doğrudan SQLite tablosuna yaz
    matches_df.to_sql('Maclar', conn, if_exists='append', index=False)
    print(f"{len(matches_df)} maç detayı 'Maclar' tablosuna eklendi.")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    import_all_data_from_csv()
    print("\nVeri aktarımı tamamlandı!")