import sqlite3
import pandas as pd
import os

DB_NAME = "football_sim.db"

if not os.path.exists(DB_NAME):
    print("❌ HATA: Veritabanı dosyası (football_sim.db) bulunamadı!")
    print("Lütfen önce 'create_db.py' kodunu çalıştır.")
else:
    print(f"✅ '{DB_NAME}' bulundu. Bağlanılıyor...\n")
    conn = sqlite3.connect(DB_NAME)

    # 1. Tablo Listesini Kontrol Et
    print("--- TABLOLAR VE VIEW'LAR ---")
    tables = pd.read_sql("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')", conn)
    print(tables)
    print("-" * 30)

    # 2. 'player_stats' Tablosunda FifaVersion Var mı? (Olmamalı)
    print("\n--- SÜTUN KONTROLÜ (FifaVersion silindi mi?) ---")
    player_cols = pd.read_sql("PRAGMA table_info(player_stats)", conn)
    if 'FifaVersion' not in player_cols['name'].values:
        print("✅ BAŞARILI: 'FifaVersion' sütunu temizlenmiş.")
    else:
        print("❌ HATA: 'FifaVersion' hala duruyor!")

    # 3. BAĞLANTI TESTİ (View Çalışıyor mu?)
    # Hem SoFIFA'dan gücü (Overall) hem Transfermarkt'tan uyruğu (Nationality) çekiyoruz.
    print("\n--- BİRLEŞTİRME TESTİ (v_full_player_data) ---")
    try:
        # Chelsea'den örnek bir oyuncu çekelim
        query = """
        SELECT Name, Team, Overall, Nationality, DetailedPosition 
        FROM v_full_player_data 
        WHERE Team = 'Chelsea' AND Season = '2014-2015'
        LIMIT 5
        """
        merged_data = pd.read_sql(query, conn)

        if not merged_data.empty:
            print(merged_data)
            print("\n✅ MÜKEMMEL: Hem statlar hem de uyruklar tek tabloda geliyor!")
        else:
            print("⚠️ Veri dönmedi. Takım veya Sezon ismi eşleşmiyor olabilir.")

    except Exception as e:
        print(f"❌ View hatası: {e}")

    conn.close()