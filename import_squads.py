# import_squads.py

import pandas as pd
import sqlite3
import os
import sys

# Proje kök dizinini sisteme tanıt
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.db_manager import DATABASE_NAME  # Sabit veritabanı yolunu alıyoruz

# --- AYARLAR ---
SQUADS_CSV_FILE = 'premier_league_squads_2000_2025.csv'


def import_squad_data():
    """
    Çekilen kadro verilerini içeren CSV dosyasını okur ve veritabanındaki
    'Oyuncular' ve 'SezonKadrolari' tablolarını doldurur.
    """
    try:
        df = pd.read_csv(SQUADS_CSV_FILE, encoding='utf-8-sig')
        # Boş satırları veya eksik oyuncu adı olanları temizle
        df.dropna(subset=['Player', 'Team', 'Season'], inplace=True)
        print(f"'{SQUADS_CSV_FILE}' başarıyla okundu. {len(df)} oyuncu/sezon kaydı bulundu.")
    except FileNotFoundError:
        print(f"HATA: '{SQUADS_CSV_FILE}' bulunamadı. Lütfen dosya adını ve konumunu kontrol edin.")
        return
    except Exception as e:
        print(f"CSV okunurken bir hata oluştu: {e}")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 1. Adım: Tüm benzersiz oyuncuları 'Oyuncular' tablosuna ekle
    unique_players = df['Player'].unique()
    players_to_insert = [(player,) for player in unique_players]

    cursor.executemany("INSERT OR IGNORE INTO Oyuncular (oyuncu_tam_adi) VALUES (?)", players_to_insert)
    print(f"{len(unique_players)} benzersiz oyuncu 'Oyuncular' tablosuna eklendi/kontrol edildi.")
    conn.commit()

    # 2. Adım: Sezon Kadrolarını 'SezonKadrolari' tablosuna ekle
    # Hızlı işlem için önce tüm oyuncuların ID'lerini bir sözlüğe çekelim
    cursor.execute("SELECT oyuncu_tam_adi, oyuncu_id FROM Oyuncular")
    player_id_map = {name: id for name, id in cursor.fetchall()}

    squads_to_insert = []
    for index, row in df.iterrows():
        player_name = row['Player']
        team_name = row['Team']
        season = row['Season']

        # Oyuncu ID'sini haritadan bul
        player_id = player_id_map.get(player_name)

        if player_id:
            squads_to_insert.append((season, team_name, player_id))

    cursor.executemany("""
        INSERT INTO SezonKadrolari (sezon_araligi, takim_adi, oyuncu_id) 
        VALUES (?, ?, ?)
    """, squads_to_insert)

    print(f"{len(squads_to_insert)} kadro kaydı 'SezonKadrolari' tablosuna eklendi.")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Veritabanında ilgili tabloların olduğundan emin olmak için bu fonksiyonu çağırabiliriz
    # ama ana kurulumda zaten yapıldığı için şimdilik gerek yok.

    print("----- Kadro Verileri Veritabanına Aktarılıyor -----")
    import_squad_data()
    print("\n----- Kadro Aktarımı Tamamlandı! -----")