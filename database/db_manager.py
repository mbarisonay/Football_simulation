# database/db_manager.py (Doğru ve Sade Versiyon)

import sqlite3
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
# Projenin kök dizinine çık: ../
_project_root = os.path.dirname(_current_dir)
# Veritabanının tam yolunu oluştur: ../futbol_veritabani.db
DATABASE_NAME = os.path.join(_project_root, 'futbol_veritabani.db')


def create_final_database_structure():
    """
    CSV'den gelen temel maç sonuçlarını barındıracak nihai veritabanı yapısını oluşturur.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # --- TABLO 1: Takimlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        takim_adi TEXT PRIMARY KEY
    )
    ''')

    # --- TABLO 2: Sezonlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_araligi TEXT UNIQUE,
        lig_adi TEXT
    )
    ''')

    # --- TABLO 3: Maclar (SADELEŞTİRİLDİ) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Maclar (
        mac_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_araligi TEXT,
        mac_tarihi TEXT,
        ev_sahibi_takim TEXT,
        deplasman_takim TEXT,
        ev_sahibi_gol INTEGER,
        deplasman_gol INTEGER,
        sonuc TEXT,
        FOREIGN KEY (sezon_araligi) REFERENCES Sezonlar (sezon_araligi),
        FOREIGN KEY (ev_sahibi_takim) REFERENCES Takimlar (takim_adi),
        FOREIGN KEY (deplasman_takim) REFERENCES Takimlar (takim_adi)
    )
    ''')

    print(f"'{DATABASE_NAME}' için nihai ve sadeleştirilmiş yapı başarıyla kontrol edildi/oluşturuldu.")

    connection.commit()
    connection.close()


def get_matches_by_season(season_range):
    """
    Belirtilen sezondaki tüm maçları veritabanından çeker.
    :param season_range: Sezon aralığı (Örn: '2003-2004')
    :return: Maç bilgilerini içeren bir liste.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
    SELECT ev_sahibi_takim, deplasman_takim, ev_sahibi_gol, deplasman_gol
    FROM Maclar
    WHERE sezon_araligi = ?
    """

    cursor.execute(query, (season_range,))
    matches = [dict(row) for row in cursor.fetchall()]
    connection.close()

    print(f"\n{season_range} sezonu için veritabanından {len(matches)} maç çekildi.")
    return matches

if __name__ == '__main__':
    create_final_database_structure()