# database/db_manager.py (Nihai Kurulum Versiyonu)

import sqlite3

DATABASE_NAME = 'futbol_veritabani.db'


def create_final_database_structure():
    """
    Hem CSV'den gelen zengin maç verilerini hem de gelecekteki oyuncu verilerini
    barındıracak nihai veritabanı yapısını oluşturur.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # --- TABLO 1: Takimlar ---
    # Sadece benzersiz takım isimlerini tutar.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        takim_adi TEXT PRIMARY KEY
    )
    ''')

    # --- TABLO 2: Sezonlar ---
    # Sezon bilgilerini tutar (örn: '2000-2001', 'Premier League')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_araligi TEXT UNIQUE,
        lig_adi TEXT
    )
    ''')

    # --- TABLO 3: Maclar ---
    # CSV'den gelen tüm zengin maç istatistiklerini içerir.
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
        ev_sahibi_sut INTEGER,
        deplasman_sut INTEGER,
        ev_sahibi_isabetli_sut INTEGER,
        deplasman_isabetli_sut INTEGER,
        ev_sahibi_faul INTEGER,
        deplasman_faul INTEGER,
        ev_sahibi_korner INTEGER,
        deplasman_korner INTEGER,
        ev_sahibi_sari_kart INTEGER,
        deplasman_sari_kart INTEGER,
        ev_sahibi_kirmizi_kart INTEGER,
        deplasman_kirmizi_kart INTEGER,
        FOREIGN KEY (sezon_araligi) REFERENCES Sezonlar (sezon_araligi),
        FOREIGN KEY (ev_sahibi_takim) REFERENCES Takimlar (takim_adi),
        FOREIGN KEY (deplasman_takim) REFERENCES Takimlar (takim_adi)
    )
    ''')

    # --- GELECEK İÇİN HAZIRLIK (BU TABLOLAR BOŞ KALACAK) ---

    # --- TABLO 4: Oyuncular ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Oyuncular (
        oyuncu_id INTEGER PRIMARY KEY AUTOINCREMENT,
        oyuncu_tam_adi TEXT NOT NULL UNIQUE
    )
    ''')

    # --- TABLO 5: SezonKadrolari ---
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

    # --- TABLO 6: OyuncuMacIstatistikleri ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OyuncuMacIstatistikleri (
        istatistik_id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac_id INTEGER,
        oyuncu_id INTEGER,
        takim_adi TEXT,
        oynadigi_dakika INTEGER,
        gol INTEGER,
        asist INTEGER,
        puan REAL,
        FOREIGN KEY (mac_id) REFERENCES Maclar (mac_id),
        FOREIGN KEY (oyuncu_id) REFERENCES Oyuncular (oyuncu_id),
        FOREIGN KEY (takim_adi) REFERENCES Takimlar (takim_adi)
    )
    ''')

    print(f"'{DATABASE_NAME}' için nihai veritabanı yapısı başarıyla kontrol edildi/oluşturuldu.")

    connection.commit()
    connection.close()


if __name__ == '__main__':
    create_final_database_structure()