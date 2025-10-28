# database/db_manager.py (TÜM TABLOLARI İÇEREN NİHAİ VERSİYON)

import sqlite3
import os

# Veritabanı dosyasının tam yolunu projenin ana dizini olarak ayarla
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
DATABASE_NAME = os.path.join(_project_root, 'futbol_veritabani.db')


def create_database_structure():
    """Veritabanını ve projenin ihtiyaç duyduğu TÜM tabloları (yeniden) oluşturur."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Başlamadan önce mevcut tabloları silerek temiz bir başlangıç yap
    cursor.execute('DROP TABLE IF EXISTS OyuncuMacIstatistikleri')
    cursor.execute('DROP TABLE IF EXISTS SezonKadrolari')
    cursor.execute('DROP TABLE IF EXISTS Oyuncular')
    cursor.execute('DROP TABLE IF EXISTS Maclar')
    cursor.execute('DROP TABLE IF EXISTS Takimlar')
    cursor.execute('DROP TABLE IF EXISTS Sezonlar')

    # --- TABLO 1: Takimlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        takim_adi TEXT PRIMARY KEY
    )
    ''')

    # --- TABLO 2: Sezonlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_araligi TEXT PRIMARY KEY,
        lig_adi TEXT
    )
    ''')

    # --- TABLO 3: Maclar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Maclar (
        mac_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_araligi TEXT, mac_tarihi TEXT,
        ev_sahibi_takim TEXT, deplasman_takim TEXT,
        ev_sahibi_gol INTEGER, deplasman_gol INTEGER, sonuc TEXT,
        ev_sahibi_sut INTEGER, deplasman_sut INTEGER,
        ev_sahibi_isabetli_sut INTEGER, deplasman_isabetli_sut INTEGER,
        ev_sahibi_faul INTEGER, deplasman_faul INTEGER,
        ev_sahibi_korner INTEGER, deplasman_korner INTEGER,
        ev_sahibi_sari_kart INTEGER, deplasman_sari_kart INTEGER,
        ev_sahibi_kirmizi_kart INTEGER, deplasman_kirmizi_kart INTEGER,
        FOREIGN KEY (sezon_araligi) REFERENCES Sezonlar (sezon_araligi),
        FOREIGN KEY (ev_sahibi_takim) REFERENCES Takimlar (takim_adi),
        FOREIGN KEY (deplasman_takim) REFERENCES Takimlar (takim_adi)
    )
    ''')

    # --- TABLO 4: Oyuncular (EKSİK OLAN KISIM) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Oyuncular (
        oyuncu_id INTEGER PRIMARY KEY AUTOINCREMENT,
        oyuncu_tam_adi TEXT NOT NULL UNIQUE
    )
    ''')

    # --- TABLO 5: SezonKadrolari (EKSİK OLAN KISIM) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SezonKadrolari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_araligi TEXT,
        takim_adi TEXT,
        oyuncu_id INTEGER,
        FOREIGN KEY (sezon_araligi) REFERENCES Sezonlar (sezon_araligi),
        FOREIGN KEY (takim_adi) REFERENCES Takimlar (takim_adi),
        FOREIGN KEY (oyuncu_id) REFERENCES Oyuncular (oyuncu_id)
    )
    ''')

    # --- TABLO 6: OyuncuMacIstatistikleri (Gelecek için) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OyuncuMacIstatistikleri (
        istatistik_id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac_id INTEGER, oyuncu_id INTEGER, takim_adi TEXT,
        oynadigi_dakika INTEGER, gol INTEGER, asist INTEGER, puan REAL,
        FOREIGN KEY (mac_id) REFERENCES Maclar (mac_id),
        FOREIGN KEY (oyuncu_id) REFERENCES Oyuncular (oyuncu_id),
        FOREIGN KEY (takim_adi) REFERENCES Takimlar (takim_adi)
    )
    ''')

    print(f"'{DATABASE_NAME}' için nihai veritabanı yapısı başarıyla oluşturuldu.")

    connection.commit()
    connection.close()


# --- Diğer Fonksiyonlar ---
def get_matches_by_season(season_range):
    # ... (Bu fonksiyon doğru ve aynı kalacak)
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    query = """
    SELECT 
        ev_sahibi_takim, deplasman_takim, ev_sahibi_gol, deplasman_gol,
        ev_sahibi_sut, deplasman_sut, ev_sahibi_isabetli_sut, deplasman_isabetli_sut,
        ev_sahibi_korner, deplasman_korner, ev_sahibi_sari_kart, deplasman_sari_kart,
        ev_sahibi_kirmizi_kart, deplasman_kirmizi_kart
    FROM Maclar
    WHERE sezon_araligi = ?
    """
    cursor.execute(query, (season_range,))
    matches = [dict(row) for row in cursor.fetchall()]
    connection.close()
    print(f"\n{season_range} sezonu için veritabanından {len(matches)} maç ve tüm istatistikleri çekildi.")
    return matches


def get_all_teams():
    # ... (Bu fonksiyon doğru ve aynı kalacak)
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT takim_adi FROM Takimlar")
    teams = [row[0] for row in cursor.fetchall()]
    connection.close()
    return teams