# merge_data.py (Squads ve FIFA Reytinglerini Birleştiren Kod)

import pandas as pd
import os
from unidecode import unidecode

# --- AYARLAR ---
# Ana kadro dosyanızın adı
SQUADS_FILE = 'premier_league_squads_2000_2025.csv'

# SoFIFA scraper'ının oluşturduğu ana klasör
RATINGS_FOLDER = 'FIFA_Ratings'

# Birleştirilmiş verinin kaydedileceği dosya adı
OUTPUT_FILE = 'final_merged_player_database.csv'

# Farklı kaynaklardan gelen takım isimlerini eşleştirmek için harita
# SOL TARAF: premier_league_squads.csv'deki isim, SAĞ TARAF: SoFIFA'daki isim
TEAM_NAME_MAP = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Tottenham": "Tottenham Hotspur",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "West Ham": "West Ham United",
    "Bournemouth": "AFC Bournemouth",
    "Sheffield Utd": "Sheffield United",
    # Eklenecek diğer takımlar buraya...
}


def normalize_name(name):
    """Oyuncu isimlerini eşleştirme için standart bir formata getirir."""
    if not isinstance(name, str):
        return ""
    # Küçük harfe çevir, aksanları kaldır, noktalama işaretlerini sil
    name = unidecode(name).lower()
    name = name.replace('.', '').replace('-', ' ').strip()
    return name


def run_merge_process():
    """Tüm veri birleştirme sürecini yönetir."""

    # 1. SoFIFA verilerini tek bir DataFrame'de topla
    all_ratings_df = []
    print(f"'{RATINGS_FOLDER}' klasöründeki SoFIFA verileri okunuyor...")
    for root, _, files in os.walk(RATINGS_FOLDER):
        for file in files:
            if file.endswith('.csv'):
                try:
                    file_path = os.path.join(root, file)
                    df = pd.read_csv(file_path)
                    all_ratings_df.append(df)
                except Exception as e:
                    print(f"Hata: {file_path} okunurken sorun oluştu - {e}")

    if not all_ratings_df:
        print("HATA: Hiç SoFIFA reyting verisi bulunamadı. Lütfen scraper'ı çalıştırdığınızdan emin olun.")
        return

    ratings_df = pd.concat(all_ratings_df, ignore_index=True)
    print(f"-> Toplam {len(ratings_df)} oyuncu reytingi bulundu.")

    # 2. Ana kadro dosyasını oku
    try:
        squads_df = pd.read_csv(SQUADS_FILE)
        print(f"'{SQUADS_FILE}' dosyasından {len(squads_df)} kadro kaydı okundu.")
    except FileNotFoundError:
        print(f"HATA: '{SQUADS_FILE}' dosyası bulunamadı.")
        return

    # 3. Eşleştirme için hazırlık yap

    # Takım isimlerini standartlaştır
    squads_df['Team_Normalized'] = squads_df['Team'].replace(TEAM_NAME_MAP)
    ratings_df['Team_Normalized'] = ratings_df['Club']  # SoFIFA'da sütun adı 'Club'

    # Oyuncu isimlerini standartlaştırarak "merge_key" oluştur
    squads_df['merge_key'] = squads_df['Player'].apply(normalize_name)
    ratings_df['merge_key'] = ratings_df['PlayerName'].apply(normalize_name)

    # Sezon sütunlarını eşleştir
    squads_df.rename(columns={'Season': 'Season_squad'}, inplace=True)
    ratings_df.rename(columns={'Season': 'Season_rating'}, inplace=True)
    squads_df['Season'] = squads_df['Season_squad']
    ratings_df['Season'] = ratings_df['Season_rating']

    # 4. İki DataFrame'i birleştir (merge)
    print("Veri setleri birleştiriliyor...")

    # 'left' merge kullanarak ana kadro listesindeki tüm oyuncuları koru
    merged_df = pd.merge(
        squads_df,
        ratings_df[['Season', 'Team_Normalized', 'merge_key', 'Overall', 'Potential'] + list(STATS_MAP.keys())[6:]],
        # Sadece istediğimiz sütunları alalım
        on=['Season', 'Team_Normalized', 'merge_key'],
        how='left'
    )

    # 5. Sonuçları temizle ve kaydet

    # Geçici sütunları kaldır
    merged_df.drop(columns=['Team_Normalized', 'merge_key', 'Season_squad', 'Season_rating'], inplace=True)

    # Eşleşme oranını kontrol et
    successful_matches = merged_df['Overall'].notna().sum()
    total_players = len(merged_df)
    match_percentage = (successful_matches / total_players) * 100

    print(f"\nBirleştirme Tamamlandı!")
    print(f"Toplam {total_players} oyuncudan {successful_matches} tanesi için reyting verisi başarıyla eşleştirildi.")
    print(f"Eşleşme Oranı: {match_percentage:.2f}%")

    merged_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ Nihai birleştirilmiş veri seti '{OUTPUT_FILE}' dosyasına kaydedildi.")


if __name__ == '__main__':
    # STATS_MAP sözlüğünü scraper'dan kopyalayıp buraya da eklememiz gerekiyor.
    STATS_MAP = {
        'PlayerName': 'name', 'Positions': 'positions', 'Age': 'ae', 'Overall': 'oa', 'Potential': 'pt', 'Club': 'club',
        'Crossing': 'cr', 'Finishing': 'fi', 'HeadingAccuracy': 'he', 'ShortPassing': 'sh', 'Volleys': 'vo',
        'Dribbling': 'dr', 'Curve': 'cu', 'FKAccuracy': 'fr', 'LongPassing': 'lo', 'BallControl': 'bl',
        'Acceleration': 'ac', 'SprintSpeed': 'sp', 'Agility': 'ag', 'Reactions': 're', 'Balance': 'ba',
        'ShotPower': 'so', 'Jumping': 'ju', 'Stamina': 'st', 'Strength': 'sr', 'LongShots': 'ln',
        'Aggression': 'ar', 'Interceptions': 'in', 'Positioning': 'po', 'Vision': 'vi', 'Penalties': 'pe',
        'Composure': 'cm', 'Marking': 'ma', 'StandingTackle': 'sa', 'SlidingTackle': 'sl',
        'GKDiving': 'gd', 'GKHandling': 'gh', 'GKKicking': 'gc', 'GKPositioning': 'gp', 'GKReflexes': 'gr'
    }
    run_merge_process()