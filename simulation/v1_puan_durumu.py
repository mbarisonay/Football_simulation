import sys
import os
from collections import defaultdict

# Proje kök dizinini Python'un arama yoluna ekleyerek diğer dosyalardaki
# fonksiyonları import etmemizi sağlıyoruz.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Artık db_manager'daki fonksiyonu çağırabiliriz
from database.db_manager import get_matches_for_table


def calculate_league_table(season_year):
    """Belirtilen sezonun puan durumunu veritabanındaki maçlara göre hesaplar ve yazdırır."""

    # 1. Adım: Veritabanından ilgili sezonun tüm maçlarını çek
    matches = get_matches_for_table(season_year)

    if not matches:
        print(
            f"{season_year} sezonu için veritabanında maç bulunamadı. Lütfen önce main.py'yi çalıştırdığınızdan emin olun.")
        return

    # 2. Adım: Puan tablosunu tutacak bir sözlük yapısı oluştur
    # defaultdict sayesinde bir takım tabloya ilk kez eklendiğinde,
    # içindeki tüm değerler otomatik olarak 0 (sıfır) olur.
    table = defaultdict(lambda: {
        'OM': 0, 'G': 0, 'B': 0, 'M': 0,
        'AG': 0, 'YG': 0, 'Av.': 0, 'P': 0
    })

    # 3. Adım: Her bir maçı döngüye al ve tabloyu güncelle
    for match in matches:
        home_team = match['ev_sahibi']
        away_team = match['deplasman']
        home_goals = match['ev_sahibi_gol']
        away_goals = match['deplasman_gol']

        # Her iki takım için de Oynanan Maç (OM), Atılan Gol (AG) ve Yenilen Gol (YG) sayılarını artır
        table[home_team]['OM'] += 1
        table[away_team]['OM'] += 1
        table[home_team]['AG'] += home_goals
        table[away_team]['AG'] += away_goals
        table[home_team]['YG'] += away_goals
        table[away_team]['YG'] += home_goals

        # Maçın sonucuna göre Galibiyet, Beraberlik, Mağlubiyet ve Puanları işle
        if home_goals > away_goals:  # Ev sahibi kazandı
            table[home_team]['G'] += 1
            table[home_team]['P'] += 3
            table[away_team]['M'] += 1
        elif away_goals > home_goals:  # Deplasman takımı kazandı
            table[away_team]['G'] += 1
            table[away_team]['P'] += 3
            table[home_team]['M'] += 1
        else:  # Beraberlik
            table[home_team]['B'] += 1
            table[away_team]['B'] += 1
            table[home_team]['P'] += 1
            table[away_team]['P'] += 1

    # 4. Adım: Tüm maçlar bittikten sonra her takım için averajı hesapla
    for team, stats in table.items():
        stats['Av.'] = stats['AG'] - stats['YG']

    # 5. Adım: Tabloyu sırala (Önce Puana, sonra Averaja, sonra Atılan Gole göre büyükten küçüğe)
    # lambda item: (...) ifadesi, her bir takım için sıralama kriterlerini bir demet olarak belirtir.
    sorted_table = sorted(table.items(), key=lambda item: (item[1]['P'], item[1]['Av.'], item[1]['AG']), reverse=True)

    # 6. Adım: Sıralanmış tabloyu ekrana güzel bir formatta yazdır
    print(f"\n--- SÜPER LİG {season_year}-{season_year + 1} SEZONU PUAN DURUMU ---")
    print("-" * 85)
    print(f"{'#':<3} {'Takım':<25} {'OM':>4} {'G':>4} {'B':>4} {'M':>4} {'AG':>4} {'YG':>4} {'Av.':>5} {'P':>5}")
    print("-" * 85)

    for i, (team_name, stats) in enumerate(sorted_table, 1):
        # Her bir satırı formatlayarak yazdırıyoruz
        print(
            f"{i:<3} {team_name:<25} {stats['OM']:>4} {stats['G']:>4} {stats['B']:>4} {stats['M']:>4} {stats['AG']:>4} {stats['YG']:>4} {stats['Av.']:>5} {stats['P']:>5}")

    print("-" * 85)


if __name__ == '__main__':
    # Hangi sezonun puan durumunu görmek istediğimizi burada belirtiyoruz.
    # Elimizdeki veriler: 2021, 2022, 2023. Değiştirerek diğer sezonlara da bakabilirsiniz.
    TARGET_SEASON = 2022
    calculate_league_table(TARGET_SEASON)