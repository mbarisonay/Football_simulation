# database/db_manager.py (Zengin CSV için Nihai Yapı)

import sqlite3
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
DATABASE_NAME = os.path.join(_project_root, 'futbol_veritabani.db')


def create_database_structure():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute('DROP TABLE IF EXISTS Maclar')
    cursor.execute('DROP TABLE IF EXISTS Takimlar')
    cursor.execute('DROP TABLE IF EXISTS Sezonlar')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        takim_adi TEXT PRIMARY KEY
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_araligi TEXT PRIMARY KEY,
        lig_adi TEXT
    )
    ''')

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

    print(f"'{DATABASE_NAME}' için nihai veritabanı yapısı başarıyla oluşturuldu.")

    connection.commit()
    connection.close()