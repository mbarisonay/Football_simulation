import pandas as pd
import os
import sys

# --- YOL AYARLARI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# --- DOSYA LİSTELERİ ---
PLAYER_FILES = [
    "ALL_FIFA_STATS_FINAL.csv",
    "ALL_LEAGUES_FIFA_STATS.csv"
]

MATCH_FILES = [
    "fbref_premier_league_stats_2014-2025_COMPLETE.csv",
    "fbref_laLiga_stats_2016-2025_COMPLETE.csv",
    "ALL_LEAGUES_DETAILED_MATCHES.csv"
]


def merge_players():
    print("\n⚽ OYUNCU VERİLERİ BİRLEŞTİRİLİYOR...")
    df_list = []

    for filename in PLAYER_FILES:
        filepath = os.path.join(RAW_DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"  -> Okunuyor: {filename}")
            # Dtype uyarısını önlemek için low_memory=False
            df = pd.read_csv(filepath, low_memory=False)

            if 'League' not in df.columns:
                df['League'] = 'Premier League'

            df_list.append(df)
        else:
            print(f"  ⚠️ UYARI: {filename} bulunamadı.")

    if not df_list: return

    master_players = pd.concat(df_list, ignore_index=True)

    # Sayısal sütunları temizle (Overall, Potential vb.)
    numeric_cols = ['Overall', 'Potential', 'Age', 'Crossing', 'Finishing']  # Önemli olanlar
    for col in numeric_cols:
        if col in master_players.columns:
            master_players[col] = pd.to_numeric(master_players[col], errors='coerce').fillna(0).astype(int)

    master_players.drop_duplicates(subset=['Name', 'Team', 'Season'], keep='last', inplace=True)

    output_path = os.path.join(PROCESSED_DATA_DIR, "MASTER_PLAYER_STATS.csv")
    master_players.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ OYUNCU VERİTABANI HAZIR: {len(master_players)} satır.")


def merge_matches():
    print("\n🏟️ MAÇ VERİLERİ BİRLEŞTİRİLİYOR...")
    df_list = []

    for filename in MATCH_FILES:
        filepath = os.path.join(RAW_DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"  -> Okunuyor: {filename}")
            # UYARIYI ÇÖZEN KISIM: low_memory=False
            df = pd.read_csv(filepath, low_memory=False)

            # Lig yoksa ekle
            if 'League' not in df.columns:
                if "premier_league" in filename.lower():
                    df['League'] = 'Premier League'
                elif "laliga" in filename.lower():
                    df['League'] = 'La Liga'

            # Eksik sütunları doldur
            cols_to_ensure = ["HomeYellowCards", "HomeRedCards", "AwayYellowCards", "AwayRedCards", "HomeSaves",
                              "AwaySaves", "HomePossession", "AwayPossession"]
            for col in cols_to_ensure:
                if col not in df.columns: df[col] = 0

            df_list.append(df)

    if not df_list: return

    master_matches = pd.concat(df_list, ignore_index=True)

    # --- TEMİZLİK VE TİP DÖNÜŞÜMÜ ---
    # Skorları (5. ve 6. sütunlar) zorla sayıya çeviriyoruz
    for col in ['FTHG', 'FTAG']:
        if col in master_matches.columns:
            master_matches[col] = pd.to_numeric(master_matches[col], errors='coerce').fillna(0).astype(int)

    # Tarih formatı
    master_matches = master_matches.dropna(subset=['Date'])
    try:
        master_matches['Date'] = pd.to_datetime(master_matches['Date'], errors='coerce')
        master_matches = master_matches.sort_values(by='Date', ascending=False)
    except:
        pass

    # Tekilleştirme
    master_matches.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last', inplace=True)
    master_matches.fillna(0, inplace=True)

    output_path = os.path.join(PROCESSED_DATA_DIR, "MASTER_MATCH_STATS.csv")
    master_matches.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ MAÇ VERİTABANI HAZIR: {len(master_matches)} maç.")


if __name__ == "__main__":
    merge_players()
    merge_matches()
    print("\n🏁 İŞLEM TAMAMLANDI.")