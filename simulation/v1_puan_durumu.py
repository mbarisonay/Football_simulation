# simulation/v1_puan_durumu.py (Sürekli Çalışan ve Hata Kontrollü Versiyon)

import sys
import os
import re
from collections import defaultdict

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.db_manager import get_matches_by_season


def is_valid_season_format(input_str):
    """Girilen metnin 'YYYY-YYYY' formatında olup olmadığını kontrol eder."""
    # ^: başlangıç, \d{4}: 4 rakam, -: tire, $: bitiş
    pattern = re.compile(r"^\d{4}-\d{4}$")
    if not pattern.match(input_str):
        return False

    # Yılların mantıksal olarak doğru olup olmadığını kontrol et (örn: 2004-2003 gibi olamaz)
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
        print("Lütfen eldeki veri aralığında bir sezon girdiğinizden emin olun (2000-2001 ile 2018-2019 arası).")
        return

    # ... (Puan durumu hesaplama mantığı tamamen aynı, hiç değiştirmeye gerek yok)
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


# --- ANA PROGRAM DÖNGÜSÜ ---
def main_loop():
    """Programın ana döngüsünü yönetir."""
    while True:
        target_season_input = input("\nGörmek istediğiniz sezonu girin (Örn: 2003-2004) veya çıkmak için 'quit' yazın: ")

        # Kullanıcı 'q' veya 'Q' girerek çıkmak isterse döngüyü kır
        if target_season_input.lower() == 'quit':
            print("Programdan çıkılıyor. Hoşça kalın!")
            break

        # Girilen formatın doğru olup olmadığını kontrol et
        if is_valid_season_format(target_season_input):
            calculate_league_table(target_season_input)
        else:
            print("\nHATA: Geçersiz format!")
            print("Lütfen sezonu '2003-2004' gibi YYYY-YYYY formatında girin.")


if __name__ == '__main__':
    main_loop()