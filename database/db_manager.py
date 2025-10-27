# database/db_manager.py (Doğru ve Tam Versiyon)

import sqlite3

DATABASE_NAME = 'futbol_veritabani.db'


def create_database():
    """Veritabanını ve projenin ihtiyaç duyduğu TÜM tabloları oluşturur."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # --- TABLO 1: Takimlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Takimlar (
        api_takim_id INTEGER PRIMARY KEY,
        takim_adi TEXT NOT NULL UNIQUE,
        ulke TEXT
    )
    ''')

    # --- TABLO 2: Sezonlar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sezonlar (
        sezon_yili INTEGER PRIMARY KEY,
        lig_adi TEXT NOT NULL
    )
    ''')

    # --- TABLO 3: Maclar ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Maclar (
        api_mac_id INTEGER PRIMARY KEY,
        sezon_yili INTEGER,
        hafta INTEGER,
        mac_tarihi TEXT,
        ev_sahibi_takim_id INTEGER,
        deplasman_takim_id INTEGER,
        ev_sahibi_gol INTEGER,
        deplasman_gol INTEGER,
        ev_sahibi_sut INTEGER,
        deplasman_sut INTEGER,
        ev_sahibi_isabetli_sut INTEGER,
        deplasman_isabetli_sut INTEGER,
        ev_sahibi_korner INTEGER,
        deplasman_korner INTEGER,
        ev_sahibi_xg REAL,
        deplasman_xg REAL,
        FOREIGN KEY (sezon_yili) REFERENCES Sezonlar (sezon_yili),
        FOREIGN KEY (ev_sahibi_takim_id) REFERENCES Takimlar (api_takim_id),
        FOREIGN KEY (deplasman_takim_id) REFERENCES Takimlar (api_takim_id)
    )
    ''')

    # --- TABLO 4: Oyuncular ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Oyuncular (
        api_oyuncu_id INTEGER PRIMARY KEY,
        oyuncu_tam_adi TEXT NOT NULL,
        mevki TEXT
    )
    ''')

    # --- TABLO 5: OyuncuMacIstatistikleri ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OyuncuMacIstatistikleri (
        istatistik_id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_mac_id INTEGER,
        api_oyuncu_id INTEGER,
        api_takim_id INTEGER,
        oynadigi_dakika INTEGER,
        gol INTEGER,
        asist INTEGER,
        sut INTEGER,
        isabetli_sut INTEGER,
        kurtaris INTEGER,
        puan REAL,
        FOREIGN KEY (api_mac_id) REFERENCES Maclar (api_mac_id),
        FOREIGN KEY (api_oyuncu_id) REFERENCES Oyuncular (api_oyuncu_id),
        FOREIGN KEY (api_takim_id) REFERENCES Takimlar (api_takim_id)
    )
    ''')

    # --- TABLO 6: SezonKadrolari --- (DOĞRU YERE TAŞINDI)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SezonKadrolari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sezon_yili INTEGER,
        api_takim_id INTEGER,
        api_oyuncu_id INTEGER,
        FOREIGN KEY (sezon_yili) REFERENCES Sezonlar (sezon_yili),
        FOREIGN KEY (api_takim_id) REFERENCES Takimlar (api_takim_id),
        FOREIGN KEY (api_oyuncu_id) REFERENCES Oyuncular (api_oyuncu_id)
    )
    ''')

    print("'futbol_veritabani.db' veritabanı ve tüm tablolar başarıyla kontrol edildi/oluşturuldu.")

    # Tüm işlemler bittikten SONRA kaydet ve kapat
    connection.commit()
    connection.close()


def insert_seasons(seasons_data):
    """Sezon listesini veritabanına ekler."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    seasons_to_insert = [(s['sezon_yili'], s['lig_adi']) for s in seasons_data]

    cursor.executemany('''
    INSERT OR IGNORE INTO Sezonlar (sezon_yili, lig_adi) VALUES (?, ?)
    ''', seasons_to_insert)

    print(f"{cursor.rowcount} yeni sezon veritabanına eklendi.")
    connection.commit()
    connection.close()


def insert_teams(teams_data):
    """Takım listesini veritabanındaki Takimlar tablosuna ekler."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    teams_to_insert = []
    for team in teams_data:
        teams_to_insert.append(
            (team['api_takim_id'], team['takim_adi'], team['ulke'])
        )

    cursor.executemany('''
    INSERT OR IGNORE INTO Takimlar (api_takim_id, takim_adi, ulke) VALUES (?, ?, ?)
    ''', teams_to_insert)

    print(f"{cursor.rowcount} yeni takım veritabanına eklendi.")
    connection.commit()
    connection.close()


def insert_matches(matches_data):
    """Maç listesini ve istatistiklerini Maclar tablosuna ekler."""
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    matches_to_insert = []
    for match in matches_data:
        matches_to_insert.append(
            (
                match.get('api_mac_id'),
                match.get('sezon_yili'),
                match.get('hafta'),
                match.get('mac_tarihi'),
                match.get('ev_sahibi_takim_id'),
                match.get('deplasman_takim_id'),
                match.get('ev_sahibi_gol'),
                match.get('deplasman_gol'),
                # --- YENİ EKLENEN SÜTUNLAR ---
                match.get('ev_sahibi_sut', 0),
                match.get('deplasman_sut', 0),
                match.get('ev_sahibi_isabetli_sut', 0),
                match.get('deplasman_isabetli_sut', 0),
                match.get('ev_sahibi_korner', 0),
                match.get('deplasman_korner', 0)
            )
        )

    # SQL sorgusunu yeni sütunları içerecek şekilde güncelle
    cursor.executemany('''
    INSERT OR IGNORE INTO Maclar (
        api_mac_id, sezon_yili, hafta, mac_tarihi, ev_sahibi_takim_id, 
        deplasman_takim_id, ev_sahibi_gol, deplasman_gol,
        ev_sahibi_sut, deplasman_sut, ev_sahibi_isabetli_sut, deplasman_isabetli_sut,
        ev_sahibi_korner, deplasman_korner
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', matches_to_insert)

    print(f"-> {cursor.rowcount} yeni maç ve istatistikleri veritabanına eklendi.")
    connection.commit()
    connection.close()


def get_matches_missing_stats(limit=50):
    """
    İstatistikleri eksik olan maçların ID'lerini veritabanından çeker.
    :param limit: API limitlerini aşmamak için tek seferde en fazla kaç maç ID'si çekileceğini belirtir.
    :return: Maç ID'lerini içeren bir liste.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # ev_sahibi_sut sütununun boş (NULL) olduğu maçları seçiyoruz.
    # Bu, o maçın istatistiklerinin henüz işlenmediği anlamına gelir.
    # Sadece belirtilen limit kadar sonuç alıyoruz.
    query = """
    SELECT api_mac_id
    FROM Maclar
    WHERE ev_sahibi_sut IS NULL
    LIMIT ?
    """

    cursor.execute(query, (limit,))

    # Gelen sonuç [(123,), (456,), ...] gibi bir tuple listesi olacağı için,
    # bunu [123, 456, ...] gibi basit bir listeye çeviriyoruz.
    match_ids = [row[0] for row in cursor.fetchall()]

    connection.close()

    return match_ids


def update_match_statistics(stats_data):
    """
    API'den çekilen istatistik verisiyle veritabanındaki bir maçı günceller.
    :param stats_data: get_statistics_by_fixture'dan dönen istatistik sözlüğü.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    query = """
    UPDATE Maclar
    SET
        ev_sahibi_sut = ?,
        deplasman_sut = ?,
        ev_sahibi_isabetli_sut = ?,
        deplasman_isabetli_sut = ?,
        ev_sahibi_korner = ?,
        deplasman_korner = ?
    WHERE
        api_mac_id = ?
    """

    # Sorgudaki soru işaretlerine karşılık gelecek değerleri doğru sırada bir tuple olarak hazırlıyoruz.
    data_tuple = (
        stats_data.get('ev_sahibi_sut'),
        stats_data.get('deplasman_sut'),
        stats_data.get('ev_sahibi_isabetli_sut'),
        stats_data.get('deplasman_isabetli_sut'),
        stats_data.get('ev_sahibi_korner'),
        stats_data.get('deplasman_korner'),
        stats_data.get('api_mac_id')
    )

    cursor.execute(query, data_tuple)

    connection.commit()
    connection.close()


# Bu dosya doğrudan çalıştırıldığında veritabanını oluşturması için:
if __name__ == '__main__':
    create_database()