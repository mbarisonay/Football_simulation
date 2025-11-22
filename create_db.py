import sqlite3
import pandas as pd
import os

# --- DOSYA İSİMLERİ ---
FILE_PLAYER_STATS = "ALL_FIFA_STATS_FINAL.csv"
FILE_MATCHES = "fbref_premier_league_stats_2014-2025_COMPLETE.csv"
FILE_SQUADS = "premier_league_squads_2000_2025.csv"

DB_NAME = "football_sim.db"


def create_connection():
    return sqlite3.connect(DB_NAME)


def clean_team_names(team_name):
    """
    İki farklı kaynaktan gelen takım isimlerini standartlaştırır.
    Böylece tablolar arasında bağlantı kurulabilir.
    """
    if not isinstance(team_name, str): return "Unknown"
    name = team_name.strip()

    replacements = {
        "Manchester Utd": "Manchester United",
        "Man United": "Manchester United",
        "Man City": "Manchester City",
        "Spurs": "Tottenham Hotspur",
        "Tottenham": "Tottenham Hotspur",
        "Newcastle": "Newcastle United",
        "Leicester": "Leicester City",
        "West Ham": "West Ham United",
        "QPR": "Queens Park Rangers",
        "Wolves": "Wolverhampton Wanderers"
    }
    return replacements.get(name, name)


def import_player_stats(conn):
    if not os.path.exists(FILE_PLAYER_STATS):
        print(f"⚠️ {FILE_PLAYER_STATS} bulunamadı.")
        return

    print("--- 1. Oyuncu Statları (SoFIFA) Yükleniyor ---")
    df = pd.read_csv(FILE_PLAYER_STATS)

    # --- İSTEĞİN: FifaVersion Sütununu Kaldır ---
    if 'FifaVersion' in df.columns:
        df.drop(columns=['FifaVersion'], inplace=True)
        print("  -> 'FifaVersion' sütunu kaldırıldı.")

    # Takım isimlerini standartlaştır (Bağlantı için şart)
    if 'Team' in df.columns:
        df['Team'] = df['Team'].apply(clean_team_names)

    # Tabloyu oluştur
    df.to_sql('player_stats', conn, if_exists='replace', index=False)

    # İndeksler (Performans ve Bağlantı için)
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_p_key ON player_stats (Name, Team, Season)")
    conn.commit()
    print(f"✅ {len(df)} satır 'player_stats' tablosuna eklendi.")


def import_squad_details(conn):
    if not os.path.exists(FILE_SQUADS):
        print(f"⚠️ {FILE_SQUADS} bulunamadı.")
        return

    print("--- 2. Kadro Detayları (Transfermarkt) Yükleniyor ---")
    df = pd.read_csv(FILE_SQUADS)

    # Takım isimlerini standartlaştır
    if 'Team' in df.columns:
        df['Team'] = df['Team'].apply(clean_team_names)

    # Tabloyu oluştur
    df.to_sql('squad_details', conn, if_exists='replace', index=False)

    # İndeksler
    cursor = conn.cursor()
    # Transfermarkt dosyasında oyuncu ismi sütunu 'Player' ise ona göre indeks atıyoruz
    player_col = 'Player' if 'Player' in df.columns else 'Name'
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_s_key ON squad_details ({player_col}, Team, Season)")
    conn.commit()
    print(f"✅ {len(df)} satır 'squad_details' tablosuna eklendi.")


def import_matches(conn):
    if not os.path.exists(FILE_MATCHES):
        print(f"⚠️ {FILE_MATCHES} bulunamadı.")
        return

    print("--- 3. Maç Geçmişi Yükleniyor ---")
    df = pd.read_csv(FILE_MATCHES)

    # Takım isimlerini standartlaştır
    if 'HomeTeam' in df.columns: df['HomeTeam'] = df['HomeTeam'].apply(clean_team_names)
    if 'AwayTeam' in df.columns: df['AwayTeam'] = df['AwayTeam'].apply(clean_team_names)

    df.to_sql('matches', conn, if_exists='replace', index=False)

    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_m_season ON matches (Season)")
    conn.commit()
    print(f"✅ {len(df)} maç eklendi.")


def create_unified_view(conn):
    """
    İŞTE BAĞLANTI BURADA KURULUYOR!
    İki tabloyu (stats ve details) birleştiren sanal bir tablo (VIEW) oluşturuyoruz.
    """
    print("--- 4. Tablolar Arası Bağlantı (View) Oluşturuluyor ---")
    cursor = conn.cursor()

    # Eski view varsa sil
    cursor.execute("DROP VIEW IF EXISTS v_full_player_data")

    # SQL Sorgusu: İki tabloyu Takım ve Sezon üzerinden, İsimleri de benzeterek birleştirir.
    # Not: SoFIFA'da 'E. Hazard', Transfermarkt'ta 'Eden Hazard' olduğu için
    # tam eşleşme zor olabilir. Burada 'Team' ve 'Season' ana bağlayıcıdır.
    query = """
    CREATE VIEW v_full_player_data AS
    SELECT 
        p.*, 
        s.Nationality, 
        s.Position as DetailedPosition
    FROM player_stats p
    LEFT JOIN squad_details s 
      ON p.Team = s.Team 
      AND p.Season = s.Season
      AND (s.Player LIKE '%' || p.Name || '%' OR p.Name LIKE '%' || s.Player || '%')
    """
    # Not: LIKE eşleşmesi yavaştır ama isim farklarını (E. Hazard vs Eden Hazard) yakalamaya çalışır.

    cursor.execute(query)
    conn.commit()
    print("✅ 'v_full_player_data' adında birleşik sanal tablo oluşturuldu.")


# --- ÇALIŞTIR ---
if __name__ == "__main__":
    conn = create_connection()

    import_player_stats(conn)
    import_squad_details(conn)
    import_matches(conn)

    create_unified_view(conn)

    conn.close()
    print("\n🎉 Veritabanı hazır! 'FifaVersion' silindi ve tablolar bağlandı.")