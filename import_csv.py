# import_csv.py (Nihai Veri Aktarım Scripti)

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime

# --- AYARLAR ---
# Lütfen CSV dosyanızın adını ve uzantısını tam olarak buraya yazın.
CSV_DOSYA_ADI = 'final_dataset.csv'
DATABASE_NAME = 'futbol_veritabani.db'


def import_all_data_from_csv():
    """CSV dosyasındaki tüm veriyi okur ve nihai yapıdaki SQLite veritabanına aktarır."""

    # 1. Adım: Başlamadan önce eski veritabanını sil ve yenisini oluştur
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Eski '{DATABASE_NAME}' dosyası silindi.")

    # db_manager'dan GÜNCEL fonksiyonu çağırıyoruz
    from database.db_manager import create_final_database_structure
    create_final_database_structure()

    # 2. Adım: CSV dosyasını Pandas ile oku
    try:
        df = pd.read_csv(CSV_DOSYA_ADI, encoding='ISO-8859-1')
        print(f"'{CSV_DOSYA_ADI}' başarıyla okundu. Toplam {len(df)} maç bulundu.")
    except Exception as e:
        print(f"HATA: CSV okunurken bir hata oluştu: {e}")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 3. Adım: Tarih formatını düzelt ve Sezon bilgisini oluştur
    def parse_date(date_str):
        for fmt in ('%d/%m/%y', '%d/%m/%Y'):
            try:
                return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
            except:
                continue
        return None

    df['mac_tarihi'] = df['Date'].apply(parse_date)
    df.dropna(subset=['mac_tarihi'], inplace=True)  # Tarihi bozuk olan satırları at
    df['sezon_araligi'] = df['mac_tarihi'].apply(
        lambda x: f"{int(x[:4]) - 1}-{x[:4]}" if int(x[5:7]) < 8 else f"{x[:4]}-{int(x[:4]) + 1}")

    # 4. Adım: Benzersiz Takım ve Sezon listelerini oluştur ve veritabanına yaz
    all_teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
    teams_to_insert = [(team,) for team in all_teams if pd.notna(team)]
    cursor.executemany('INSERT OR IGNORE INTO Takimlar (takim_adi) VALUES (?)', teams_to_insert)
    print(f"{len(teams_to_insert)} benzersiz takım 'Takimlar' tablosuna eklendi.")

    all_seasons = df['sezon_araligi'].unique()
    seasons_to_insert = [(season, 'Premier League') for season in all_seasons if pd.notna(season)]
    cursor.executemany('INSERT OR IGNORE INTO Sezonlar (sezon_araligi, lig_adi) VALUES (?, ?)', seasons_to_insert)
    print(f"{len(seasons_to_insert)} benzersiz sezon 'Sezonlar' tablosuna eklendi.")
    conn.commit()

    # 5. Adım: Maç verilerini 'Maclar' tablosuna yazmak için DataFrame'i hazırla
    matches_df = df.rename(columns={
        'HomeTeam': 'ev_sahibi_takim', 'AwayTeam': 'deplasman_takim',
        'FTHG': 'ev_sahibi_gol', 'FTAG': 'deplasman_gol', 'FTR': 'sonuc',
        'HS': 'ev_sahibi_sut', 'AS': 'deplasman_sut',
        'HST': 'ev_sahibi_isabetli_sut', 'AST': 'deplasman_isabetli_sut',
        'HF': 'ev_sahibi_faul', 'AF': 'deplasman_faul',
        'HC': 'ev_sahibi_korner', 'AC': 'deplasman_korner',
        'HY': 'ev_sahibi_sari_kart', 'AY': 'deplasman_sari_kart',
        'HR': 'ev_sahibi_kirmizi_kart', 'AR': 'deplasman_kirmizi_kart'
    })

    # Sadece veritabanımızda olan sütunları seçelim
    final_columns = [
        'sezon_araligi', 'mac_tarihi', 'ev_sahibi_takim', 'deplasman_takim',
        'ev_sahibi_gol', 'deplasman_gol', 'sonuc', 'ev_sahibi_sut', 'deplasman_sut',
        'ev_sahibi_isabetli_sut', 'deplasman_isabetli_sut', 'ev_sahibi_faul',
        'deplasman_faul', 'ev_sahibi_korner', 'deplasman_korner',
        'ev_sahibi_sari_kart', 'deplasman_sari_kart',
        'ev_sahibi_kirmizi_kart', 'deplasman_kirmizi_kart'
    ]
    matches_df = matches_df[final_columns]

    # DataFrame'i doğrudan SQLite tablosuna yaz
    matches_df.to_sql('Maclar', conn, if_exists='append', index=False)
    print(f"{len(matches_df)} maç detayı 'Maclar' tablosuna eklendi.")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Proje kök dizinini sisteme tanıt
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    import_all_data_from_csv()
    print("\nVeri aktarımı tamamlandı!")