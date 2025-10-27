# database/db_manager.py

import sqlite3

DATABASE_NAME = 'futbol_veritabani.db'


def create_database():
    """Veritabanını ve projenin ihtiyaç duyduğu TÜM tabloları oluşturur."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Takimlar tablosunu oluştur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        api_takim_id INTEGER PRIMARY KEY,
        takim_adi TEXT NOT NULL,
        ulke TEXT
    )
    ''')

    # Sezonlar tablosunu oluştur (BU YENİ EKLENDİ)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_id INTEGER PRIMARY KEY,
        lig_adi TEXT NOT NULL,
        sezon_araligi INTEGER NOT NULL UNIQUE
    )
    ''')

    # Maclar tablosunu oluştur (BU YENİ EKLENDİ)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Maclar (
        mac_id INTEGER PRIMARY KEY,
        api_mac_id INTEGER UNIQUE NOT NULL,
        sezon_id INTEGER,
        hafta INTEGER,
        mac_tarihi TEXT,
        ev_sahibi_takim_id INTEGER,
        deplasman_takim_id INTEGER,
        ev_sahibi_gol INTEGER,
        deplasman_gol INTEGER,
        FOREIGN KEY (sezon_id) REFERENCES Sezonlar (sezon_araligi),
        FOREIGN KEY (ev_sahibi_takim_id) REFERENCES Takimlar (api_takim_id),
        FOREIGN KEY (deplasman_takim_id) REFERENCES Takimlar (api_takim_id)
    )
    ''')

    print("'futbol_veritabani.db' veritabanı ve tablolar başarıyla kontrol edildi/oluşturuldu.")

    connection.commit()
    connection.close()

def insert_teams(teams_data):
    """
    Takım listesini veritabanındaki Takimlar tablosuna ekler.
    Eğer takım zaten varsa, es geçer.
    :param teams_data: İçinde takım bilgilerini barındıran sözlüklerin listesi.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Veriyi SQL'e uygun formata (tuple listesi) çevirelim
    teams_to_insert = []
    for team in teams_data:
        teams_to_insert.append(
            (team['api_takim_id'], team['takim_adi'], team['ulke'])
        )

    # INSERT OR IGNORE: Eğer api_takim_id zaten varsa, bu satırı görmezden gel.
    # Bu, aynı takımı tekrar tekrar eklemeye çalıştığımızda hata almamızı engeller.
    cursor.executemany('''
    INSERT OR IGNORE INTO Takimlar (api_takim_id, takim_adi, ulke) VALUES (?, ?, ?)
    ''', teams_to_insert)

    print(f"{cursor.rowcount} yeni takım veritabanına eklendi.")

    connection.commit()
    connection.close()


def insert_matches(matches_data):
    """
    Maç listesini veritabanındaki Maclar tablosuna ekler.
    Eğer maç zaten varsa, es geçer.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    matches_to_insert = []
    for match in matches_data:
        matches_to_insert.append(
            (
                match['api_mac_id'],
                match['sezon_araligi'],  # Geçici olarak sezon aralığını buraya alıyoruz
                match['hafta'],
                match['mac_tarihi'],
                match['ev_sahibi_takim_id'],
                match['deplasman_takim_id'],
                match['ev_sahibi_gol'],
                match['deplasman_gol']
            )
        )

    cursor.executemany('''
    INSERT OR IGNORE INTO Maclar (
        api_mac_id, sezon_id, hafta, mac_tarihi, ev_sahibi_takim_id, 
        deplasman_takim_id, ev_sahibi_gol, deplasman_gol
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', matches_to_insert)

    print(f"-> {cursor.rowcount} yeni maç veritabanına eklendi.")

    connection.commit()
    connection.close()

# Bu dosya doğrudan çalıştırıldığında veritabanını oluşturması için:
if __name__ == '__main__':
    create_database()