import sys
import os
import time

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from data_ingestion.api_client import get_statistics_by_fixture
from database.db_manager import get_matches_missing_stats, update_match_statistics

# --- Ayarlar ---
# Tek bir çalıştırmada kaç maçın istatistiğini çekeceğimizi belirler.
# Günlük 100 limitimiz olduğu için 50-80 arası güvenli bir sayıdır.
BATCH_SIZE = 50


def run_update_process():
    """
    Veritabanındaki istatistikleri eksik maçları bulur, API'den çeker ve veritabanını günceller.
    """
    print("----- İstatistik Güncelleme Süreci Başlatıldı -----")

    # 1. Adım: Veritabanından istatistikleri eksik olan maçların ID'lerini al
    match_ids_to_update = get_matches_missing_stats(limit=BATCH_SIZE)

    if not match_ids_to_update:
        print("İstatistikleri eksik olan hiçbir maç bulunamadı. Veritabanı güncel.")
        print("----- Süreç Tamamlandı -----")
        return

    total_matches = len(match_ids_to_update)
    print(f"{total_matches} adet maçın istatistiği çekilecek...")

    # 2. Adım: Her bir maç ID'si için döngü başlat
    for i, match_id in enumerate(match_ids_to_update, 1):
        print(f"İşleniyor: {i}/{total_matches}  (Maç ID: {match_id})")

        # 3. Adım: API'den bu maçın istatistiklerini çek
        stats = get_statistics_by_fixture(match_id)

        # 4. Adım: Gelen veri geçerliyse, veritabanını güncelle
        if stats:
            update_match_statistics(stats)
            print(f" -> Başarıyla güncellendi.")
        else:
            print(f" -> Bu maç için istatistik verisi alınamadı veya boş. Atlanıyor.")

        # 5. Adım: API limitlerine takılmamak için her istek arasında bekle (ÇOK ÖNEMLİ!)
        # Dakikada 10-15 isteğe izin verildiği için 5-7 saniye idealdir.
        time.sleep(6)

    print(f"\n{total_matches} maç işlendi.")
    print("----- Süreç Tamamlandı -----")


if __name__ == '__main__':
    run_update_process()