# database/db_manager.py

import sqlite3

DATABASE_NAME = 'futbol_veritabani.db'


def create_database():
    """Veritabanını ve gerekli tabloları oluşturur."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Takimlar tablosunu oluştur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        takim_id INTEGER PRIMARY KEY,
        api_takim_id INTEGER UNIQUE NOT NULL,
        takim_adi TEXT NOT NULL,
        ulke TEXT
    )
    ''')

    # ... (diğer CREATE TABLE komutları buraya gelecek) ...
    # Sezonlar ve Maclar tablolarını da aynı şekilde ekleyin

    print(f"'{DATABASE_NAME}' veritabanı ve tablolar başarıyla kontrol edildi/oluşturuldu.")

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

# Bu dosya doğrudan çalıştırıldığında veritabanını oluşturması için:
if __name__ == '__main__':
    create_database()