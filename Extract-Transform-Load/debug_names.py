import pandas as pd
import os

# --- YOL AYARLARI (DÜZELTİLDİ) ---
# Şu anki dosyanın olduğu yer: .../Extract-Transform-Load/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Bir üst klasöre (Proje Kök Dizini) çık: .../Football_Simulation/
BASE_DIR = os.path.dirname(CURRENT_DIR)

PLAYER_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'MASTER_PLAYER_STATS.csv')
MATCH_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'MASTER_MATCH_STATS.csv')


def check_mismatches():
    print("🔍 Takım İsimleri Karşılaştırılıyor...")

    if not os.path.exists(PLAYER_FILE):
        print(f"❌ HATA: Oyuncu dosyası bulunamadı:\n   {PLAYER_FILE}")
        return
    if not os.path.exists(MATCH_FILE):
        print(f"❌ HATA: Maç dosyası bulunamadı:\n   {MATCH_FILE}")
        return

    # Verileri Oku
    df_players = pd.read_csv(PLAYER_FILE)
    df_matches = pd.read_csv(MATCH_FILE)

    # Benzersiz Takım İsimlerini Al (string olarak)
    fifa_teams = set(df_players['Team'].astype(str).unique())
    match_teams = set(df_matches['HomeTeam'].astype(str).unique())

    # Eşleşmeyenleri Bul (Maçlarda var ama FIFA'da yok)
    missing_in_fifa = match_teams - fifa_teams

    print(f"\nFref (Maç) Takım Sayısı: {len(match_teams)}")
    print(f"FIFA (Stat) Takım Sayısı: {len(fifa_teams)}")
    print(f"⚠️ Eşleşmeyen (Kayıp) Takım Sayısı: {len(missing_in_fifa)}")

    print("\n--- İŞTE SORUNLU TAKIMLAR (FBref İsimleri) ---")
    print("Bu isimler FIFA veritabanında bulunamadı:")
    print("-" * 50)

    # Alfabetik sırala
    for i, team in enumerate(sorted(list(missing_in_fifa))):
        # İpucu: İsmin ilk 4 harfi FIFA listesinde geçiyor mu?
        guess = [t for t in fifa_teams if str(team)[:4] in str(t)]
        print(f"{i + 1}. {team:<25} ---> Olası: {guess}")

        if i > 100:  # Çok uzunsa kes
            print("... ve daha fazlası.")
            break


if __name__ == "__main__":
    check_mismatches()