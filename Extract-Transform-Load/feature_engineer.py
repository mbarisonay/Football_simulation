import sqlite3
import pandas as pd
import os
import sys

# Yolları ayarla
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(ROOT_DIR, 'database', 'football_sim.db')
OUTPUT_PATH = os.path.join(ROOT_DIR, 'data', 'processed', 'training_data.csv')

# Klasör yoksa oluştur
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def get_db_connection():
    return sqlite3.connect(DB_PATH)


def calculate_team_stats_per_season():
    """
    Her sezon için takımların ortalama özelliklerini (Hız, Şut, Defans vb.) hesaplar.
    """
    conn = get_db_connection()

    # Oyuncu istatistiklerini çek
    query = """
    SELECT Season, Team, 
           AVG(Overall) as Avg_Overall,
           AVG(Finishing) as Avg_Attack,
           AVG(ShortPassing) as Avg_Midfield,
           AVG(StandingTackle) as Avg_Defense,
           AVG(SprintSpeed) as Avg_Pace
    FROM player_stats
    GROUP BY Season, Team
    """

    print("📊 Takım güçleri hesaplanıyor...")
    team_stats = pd.read_sql(query, conn)

    # Sezon formatını FBref maç verileriyle eşleşecek şekilde düzenle (Örn: 2014-2015)
    # Veritabanında zaten uyumluysa dokunmaya gerek yok, kontrol edelim.
    conn.close()
    return team_stats


def create_training_dataset():
    conn = get_db_connection()

    # 1. Maç Sonuçlarını Çek
    print("matches tablosu okunuyor...")
    matches_df = pd.read_sql("SELECT * FROM matches", conn)

    # 2. Takım Güçlerini Hesapla
    team_stats = calculate_team_stats_per_season()

    conn.close()

    if matches_df.empty or team_stats.empty:
        print("❌ HATA: Veri bulunamadı! Lütfen önce veritabanını doldurun.")
        return

    print(f"📈 Toplam {len(matches_df)} maç ve {len(team_stats)} sezonluk takım verisi işleniyor...")

    # 3. Maçlar ile Takım Güçlerini Birleştir (Merge)

    # Ev Sahibi Takım Güçlerini Ekle
    df = pd.merge(
        matches_df,
        team_stats,
        left_on=['Season', 'HomeTeam'],
        right_on=['Season', 'Team'],
        how='inner'
    )
    # Sütun isimlerini güncelle (Home)
    df.rename(columns={
        'Avg_Overall': 'Home_Overall',
        'Avg_Attack': 'Home_Att',
        'Avg_Midfield': 'Home_Mid',
        'Avg_Defense': 'Home_Def',
        'Avg_Pace': 'Home_Pace'
    }, inplace=True)
    df.drop(columns=['Team'], inplace=True)  # Tekrar eden sütunu sil

    # Deplasman Takım Güçlerini Ekle
    df = pd.merge(
        df,
        team_stats,
        left_on=['Season', 'AwayTeam'],
        right_on=['Season', 'Team'],
        how='inner'
    )
    # Sütun isimlerini güncelle (Away)
    df.rename(columns={
        'Avg_Overall': 'Away_Overall',
        'Avg_Attack': 'Away_Att',
        'Avg_Midfield': 'Away_Mid',
        'Avg_Defense': 'Away_Def',
        'Avg_Pace': 'Away_Pace'
    }, inplace=True)
    df.drop(columns=['Team'], inplace=True)

    # 4. Temizle ve Kaydet
    # Sadece ML için gerekli sütunları seç
    final_columns = [
        'Season', 'HomeTeam', 'AwayTeam',
        'Home_Overall', 'Home_Att', 'Home_Mid', 'Home_Def', 'Home_Pace',
        'Away_Overall', 'Away_Att', 'Away_Mid', 'Away_Def', 'Away_Pace',
        'FTHG', 'FTAG'  # Hedef değişkenler (Skorlar)
    ]

    # Eksik veri varsa (Eşleşmeyen takım isimleri yüzünden olabilir)
    df_final = df[final_columns].dropna()

    print(f"✅ İşlem tamam! {len(matches_df)} maçtan {len(df_final)} tanesi eşleştirildi ve hazırlandı.")
    print(f"💾 Kaydediliyor: {OUTPUT_PATH}")

    df_final.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    create_training_dataset()