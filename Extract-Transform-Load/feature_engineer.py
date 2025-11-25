import pandas as pd
import os
import sys

# --- YOL AYARLARI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_PATH = os.path.join(PROCESSED_DATA_DIR, 'training_data_v2.csv')

# Girdi Dosyaları
PLAYER_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_PLAYER_STATS.csv")
MATCH_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_MATCH_STATS.csv")


def calculate_team_power():
    print("📊 Takım güçleri (Overall, Attack, Pace vs.) hesaplanıyor...")

    if not os.path.exists(PLAYER_FILE):
        print("❌ Hata: Oyuncu dosyası bulunamadı.")
        return None

    df_players = pd.read_csv(PLAYER_FILE)

    # Takımın o sezonki ortalama gücünü bulacağız
    # Bu istatistikler SoFIFA'dan geliyor
    team_stats = df_players.groupby(['Season', 'Team', 'League']).agg({
        'Overall': 'mean',
        'Finishing': 'mean',  # Hücum
        'ShortPassing': 'mean',  # Orta Saha
        'StandingTackle': 'mean',  # Defans
        'SprintSpeed': 'mean',  # Hız
        'Stamina': 'mean'  # Kondisyon
    }).reset_index()

    # Sütun isimlerini standartlaştıralım
    team_stats.rename(columns={
        'Overall': 'Team_Overall',
        'Finishing': 'Team_Attack',
        'ShortPassing': 'Team_Midfield',
        'StandingTackle': 'Team_Defense',
        'SprintSpeed': 'Team_Pace',
        'Stamina': 'Team_Fitness'
    }, inplace=True)

    return team_stats


def create_training_set():
    print("🚀 Eğitim seti oluşturuluyor...")

    if not os.path.exists(MATCH_FILE):
        print("❌ Hata: Maç dosyası bulunamadı.")
        return

    df_matches = pd.read_csv(MATCH_FILE)

    # --- İSTEĞİN: MatchURL'i SİL ---
    if 'MatchURL' in df_matches.columns:
        df_matches.drop(columns=['MatchURL'], inplace=True)
        # print("  -> MatchURL sütunu temizlendi.")

    print(f"  -> {len(df_matches)} maç işleniyor...")

    # 2. Takım Güçlerini Çek
    df_team_stats = calculate_team_power()
    if df_team_stats is None: return

    # 3. Eşleştirme (Merge) - EV SAHİBİ (Home)
    # Maç tablosundaki HomeTeam ile İstatistik tablosundaki Team'i eşleştir
    df_final = pd.merge(
        df_matches,
        df_team_stats,
        left_on=['Season', 'HomeTeam'],
        right_on=['Season', 'Team'],
        how='inner'
    )

    # Sütun adlarını 'Home_' ile başlat
    rename_map_home = {
        'Team_Overall': 'Home_Overall',
        'Team_Attack': 'Home_Attack',
        'Team_Midfield': 'Home_Midfield',
        'Team_Defense': 'Home_Defense',
        'Team_Pace': 'Home_Pace',
        'Team_Fitness': 'Home_Fitness'
    }
    df_final.rename(columns=rename_map_home, inplace=True)
    # Gereksizleri at
    df_final.drop(columns=['Team', 'League_y'], axis=1, inplace=True, errors='ignore')
    # League_x -> League olarak kalsın
    if 'League_x' in df_final.columns:
        df_final.rename(columns={'League_x': 'League'}, inplace=True)

    # 4. Eşleştirme (Merge) - DEPLASMAN (Away)
    df_final = pd.merge(
        df_final,
        df_team_stats,
        left_on=['Season', 'AwayTeam'],
        right_on=['Season', 'Team'],
        how='inner'
    )

    # Sütun adlarını 'Away_' ile başlat
    rename_map_away = {
        'Team_Overall': 'Away_Overall',
        'Team_Attack': 'Away_Attack',
        'Team_Midfield': 'Away_Midfield',
        'Team_Defense': 'Away_Defense',
        'Team_Pace': 'Away_Pace',
        'Team_Fitness': 'Away_Fitness'
    }
    df_final.rename(columns=rename_map_away, inplace=True)

    # Gereksizleri at
    df_final.drop(columns=['Team', 'League_y'], axis=1, inplace=True, errors='ignore')
    if 'League_x' in df_final.columns:
        df_final.rename(columns={'League_x': 'League'}, inplace=True)

    # 5. Ligi Sayısallaştır (One-Hot Encoding)
    # Yapay zeka "La Liga" yazısını matematiksel vektöre çevirir
    df_final = pd.get_dummies(df_final, columns=['League'], prefix='Lg')

    # 6. Son Sütun Seçimi (Eğitimde kullanılacaklar)
    # Modelin öğrenmesi için gerekli olan her şeyi buraya ekliyoruz
    target_cols = [
        'Season', 'Date', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG',  # Hedef: Skorlar

        # Ev Sahibi Güçleri
        'Home_Overall', 'Home_Attack', 'Home_Midfield', 'Home_Defense', 'Home_Pace',

        # Deplasman Güçleri
        'Away_Overall', 'Away_Attack', 'Away_Midfield', 'Away_Defense', 'Away_Pace'
    ]

    # Oluşan Lig Sütunlarını da ekle (Lg_La Liga, Lg_Premier League vb.)
    league_cols = [c for c in df_final.columns if c.startswith('Lg_')]
    target_cols.extend(league_cols)

    # Varsa diğer maç istatistiklerini de (Korner, Faul vs.) ekleyebiliriz
    # Ama şimdilik skor tahmini için oyuncu güçleri yeterli.

    # DataFrame'i filtrele
    final_data = df_final[target_cols].dropna()

    # Kaydet
    final_data.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ EĞİTİM VERİSİ HAZIRLANDI: {len(final_data)} maç.")
    print(f"   Dosya: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_training_set()