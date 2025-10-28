# simulation/v1_puan_durumu.py (Geniş Veri Seti İçin Nihai Versiyon)

import sys
import os
import re
from collections import defaultdict

# Proje kök dizinini Python'un arama yoluna ekleyerek diğer modülleri import etmeyi sağlıyoruz.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# db_manager'ı import etmeden önce veritabanı yolunun doğru ayarlandığından emin olmalıyız.
# db_manager.py dosyasının kendisi zaten bu ayarı yapıyor.
from database.db_manager import DATABASE_NAME
import sqlite3


def get_matches_by_season(season_range):
    """Belirtilen sezondaki tüm maçları veritabanından çeker."""

    # Veritabanı bağlantısı artık db_manager'dan alınan tam yolu kullanıyor.
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
    SELECT ev_sahibi_takim, deplasman_takim, ev_sahibi_gol, deplasman_gol
    FROM Maclar
    WHERE sezon_araligi = ?
    """

    cursor.execute(query, (season_range,))
    matches = [dict(row) for row in cursor.fetchall()]
    connection.close()

    print(f"\n{season_range} sezonu için veritabanından {len(matches)} maç çekildi.")
    return matches


def is_valid_season_format(input_str):
    """Girilen metnin 'YYYY-YYYY' formatında olup olmadığını kontrol eder."""
    pattern = re.compile(r"^\d{4}-\d{4}$")
    if not pattern.match(input_str):
        return False

    try:
        start_year, end_year = map(int, input_str.split('-'))
        if end_year != start_year + 1:
            return False
    except:
        return False

    return True


def calculate_league_table(season_range):
    """Belirtilen sezonun puan durumunu hesaplar ve yazdırır."""

    matches = get_matches_by_season(season_range)

    if not matches:
        print(f"\nUYARI: '{season_range}' sezonu için veritabanında maç bulunamadı.")
        print("Lütfen eldeki veri aralığında bir sezon girdiğinizden emin olun (Örn: 2000-2001'den 2024-2025'e kadar).")
        return

    table = defaultdict(lambda: {'OM': 0, 'G': 0, 'B': 0, 'M': 0, 'AG': 0, 'YG': 0, 'Av.': 0, 'P': 0})

    for match in matches:
        home_team = match['ev_sahibi_takim']
        away_team = match['deplasman_takim']
        home_goals = match['ev_sahibi_gol']
        away_goals = match['deplasman_gol']

        table[home_team]['OM'] += 1;
        table[away_team]['OM'] += 1
        table[home_team]['AG'] += home_goals;
        table[away_team]['AG'] += away_goals
        table[home_team]['YG'] += away_goals;
        table[away_team]['YG'] += home_goals

        if home_goals > away_goals:
            table[home_team]['G'] += 1;
            table[home_team]['P'] += 3;
            table[away_team]['M'] += 1
        elif away_goals > home_goals:
            table[away_team]['G'] += 1;
            table[away_team]['P'] += 3;
            table[home_team]['M'] += 1
        else:
            table[home_team]['B'] += 1;
            table[away_team]['B'] += 1
            table[home_team]['P'] += 1;
            table[away_team]['P'] += 1

    for team, stats in table.items():
        stats['Av.'] = stats['AG'] - stats['YG']

    sorted_table = sorted(table.items(), key=lambda item: (item[1]['P'], item[1]['Av.'], item[1]['AG']), reverse=True)

    print(f"\n--- PREMIER LEAGUE {season_range} SEZONU PUAN DURUMU ---")
    print("-" * 85)
    print(f"{'#':<3} {'Takım':<25} {'OM':>4} {'G':>4} {'B':>4} {'M':>4} {'AG':>4} {'YG':>4} {'Av.':>5} {'P':>5}")
    print("-" * 85)

    for i, (team_name, stats) in enumerate(sorted_table, 1):
        print(
            f"{i:<3} {team_name:<25} {stats['OM']:>4} {stats['G']:>4} {stats['B']:>4} {stats['M']:>4} {stats['AG']:>4} {stats['YG']:>4} {stats['Av.']:>5} {stats['P']:>5}")

    print("-" * 85)


def main_loop():
    """Programın ana döngüsünü yönetir."""
    while True:
        target_season_input = input("\nGörmek istediğiniz sezonu girin (Örn: 2003-2004) veya çıkmak için 'q' yazın: ")

        if target_season_input.lower() == 'q':
            print("Programdan çıkılıyor. Hoşça kalın!")
            break

        if is_valid_season_format(target_season_input):
            # --- DÜZELTME BURADA ---
            # Kullanıcının girdiği '2003-2004' formatını, veritabanının anladığı '2003/2004' formatına çeviriyoruz.
            db_season_format = target_season_input

            # Veritabanı sorgusunu bu yeni formatla yapıyoruz.
            calculate_league_table(db_season_format)
            # -------------------------
        else:
            print("\nHATA: Geçersiz format!")
            print("Lütfen sezonu '2003-2004' gibi YYYY-YYYY formatında girin.")


if __name__ == '__main__':
    main_loop()