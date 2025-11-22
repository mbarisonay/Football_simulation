import sqlite3
import pandas as pd
import os

# --- DOSYA İSİMLERİ (SENDEKİLERLE DEĞİŞTİR) ---
# 1. SoFIFA'dan gelen dosya (Statlar)
FILE_PLAYER_STATS = "ALL_FIFA_STATS_FINAL.csv"
# 2. FBref'ten gelen dosya (Maçlar)
FILE_MATCHES = "fbref_premier_league_stats_2000-2014_COMPLETE.csv"
# 3. Transfermarkt'tan gelen dosya (Uyruklar - Opsiyonel)
FILE_SQUADS = "premier_league_squads_2000_2025.csv"

DB_NAME = "football_sim.db"


def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


def clean_team_names(team_name):
    """
    Takım isimlerini standartlaştırır.
    Örn: 'Manchester United FC' -> 'Manchester United'
    Bu, tabloları birbiriyle eşleştirmek için KRİTİKTİR.
    """
    if not isinstance(team_name, str): return "Unknown"
    name = team_name.strip()

    # Basit eşleştirmeler (Gerektikçe listeyi uzatabilirsin)
    replacements = {
        "Manchester Utd": "Manchester United",
        "Man United": "Manchester United",
        "Man City": "Manchester City",
        "Spurs": "Tottenham Hotspur",
        "Tottenham": "Tottenham Hotspur",
        "Newcastle": "Newcastle United",
        "Leicester": "Leicester City",
        "West Ham": "West Ham United"
    }

    return replacements.get(name, name)


def import_player_stats(conn):
    if not os.path.exists(FILE_PLAYER_STATS):
        print(f"⚠️ {FILE_PLAYER_STATS} bulunamadı, atlanıyor.")
        return

    print("--- Oyuncu Statları Yükleniyor ---")
    df = pd.read_csv(FILE_PLAYER_STATS)

    # Sütun isimlerini temizle (Boşlukları at, vs.)
    df.columns = [c.strip().replace(' ', '_') for c in df.columns]

    # Takım isimlerini standartlaştır
    if 'Team' in df.columns:
        df['Team'] = df['Team'].apply(clean_team_names)

    # Veri Tiplerini Düzelt (Statların sayı olduğundan emin ol)
    # 85+2 gibi değerleri temizlemiştik ama garanti olsun
    stat_columns = ['Overall', 'Potential', 'Pace', 'Shooting', 'Finishing', 'SprintSpeed', 'Dribbling']  # Örnekler
    # (Senin CSV'de çok sütun var, Pandas to_sql çoğunu otomatik anlar ama kritik olanları zorlayabiliriz)

    # SQL'e Yaz
    df.to_sql('player_stats', conn, if_exists='replace', index=False)
    print(f"✅ {len(df)} oyuncu stat verisi 'player_stats' tablosuna eklendi.")

    # İndeksler (Hız için çok önemli)
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_season ON player_stats (Season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_team ON player_stats (Team)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_name ON player_stats (Name)")
    conn.commit()


def import_matches(conn):
    if not os.path.exists(FILE_MATCHES):
        print(f"⚠️ {FILE_MATCHES} bulunamadı, atlanıyor.")
        return

    print("--- Maç Verileri Yükleniyor ---")
    df = pd.read_csv(FILE_MATCHES)

    # Takım isimlerini standartlaştır (Eşleşme için)
    if 'HomeTeam' in df.columns: df['HomeTeam'] = df['HomeTeam'].apply(clean_team_names)
    if 'AwayTeam' in df.columns: df['AwayTeam'] = df['AwayTeam'].apply(clean_team_names)

    df.to_sql('matches', conn, if_exists='replace', index=False)
    print(f"✅ {len(df)} maç verisi 'matches' tablosuna eklendi.")

    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_season ON matches (Season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_teams ON matches (HomeTeam, AwayTeam)")
    conn.commit()


def import_squad_details(conn):
    if not os.path.exists(FILE_SQUADS):
        print(f"⚠️ {FILE_SQUADS} bulunamadı, atlanıyor.")
        return

    print("--- Kadro Detayları (Uyruk vb.) Yükleniyor ---")
    df = pd.read_csv(FILE_SQUADS)

    if 'Team' in df.columns: df['Team'] = df['Team'].apply(clean_team_names)

    # Bu tabloyu sadece destekleyici bilgi olarak kullanacağız
    df.to_sql('squad_details', conn, if_exists='replace', index=False)
    print(f"✅ {len(df)} kadro detayı 'squad_details' tablosuna eklendi.")


# --- ÇALIŞTIR ---
if __name__ == "__main__":
    try:
        connection = create_connection()

        import_player_stats(connection)
        import_matches(connection)
        import_squad_details(connection)

        connection.close()
        print("\n🎉 Veritabanı kurulumu başarıyla tamamlandı: football_sim.db")

    except Exception as e:
        print(f"\n❌ Bir hata oluştu: {e}")