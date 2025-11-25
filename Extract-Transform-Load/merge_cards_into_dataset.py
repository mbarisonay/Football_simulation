import pandas as pd
import os

# --- DOSYA YOLLARI ---
BASE_FILE = "ALL_LEAGUES_DETAILED_MATCHES.csv"
CARDS_FILE = "MATCH_CARDS.csv"
FINAL_FILE = "ALL_LEAGUES_FINAL_WITH_CARDS.csv"


def merge_cards():
    print("🔄 Dosyalar birleştiriliyor...")

    if not os.path.exists(BASE_FILE) or not os.path.exists(CARDS_FILE):
        print("❌ Hata: Dosyalardan biri eksik.")
        return

    # 1. Dosyaları Oku
    df_base = pd.read_csv(BASE_FILE)
    df_cards = pd.read_csv(CARDS_FILE)

    print(f"  -> Ana Veri: {len(df_base)} maç")
    print(f"  -> Kart Verisi: {len(df_cards)} maç")

    # 2. Gereksiz (Boş) Kart Sütunlarını Ana Dosyadan At (Varsa)
    cols_to_drop = ['HomeYellowCards', 'HomeRedCards', 'AwayYellowCards', 'AwayRedCards']
    df_base.drop(columns=[c for c in cols_to_drop if c in df_base.columns], inplace=True)

    # 3. URL Üzerinden Birleştir (Merge)
    # 'left' merge yapıyoruz ki kart verisi çekilememiş maçlar silinmesin (onlar NaN kalır)
    df_merged = pd.merge(df_base, df_cards, on='MatchURL', how='left')

    # 4. Eksik (NaN) Kartları 0 Yap
    # (Eğer bir maçın kart verisi yoksa 0 kabul edelim)
    for col in cols_to_drop:
        df_merged[col] = df_merged[col].fillna(0).astype(int)

    # 5. Kaydet
    df_merged.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ İŞLEM TAMAMLANDI!")
    print(f"   Yeni dosya: {FINAL_FILE}")
    print("   Artık 'feature_engineer.py' dosyasında bu yeni dosyayı kullanabilirsin.")


if __name__ == "__main__":
    merge_cards()