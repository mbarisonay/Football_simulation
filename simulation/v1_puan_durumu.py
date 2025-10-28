# simulation/v1_puan_durumu.py

import sys
import os
from collections import defaultdict

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.db_manager import get_matches_by_season


def calculate_league_table(season_range):
    """Belirtilen sezonun puan durumunu hesaplar ve yazdırır."""

    matches = get_matches_by_season(season_range)
    if not matches:
        print(f"{season_range} sezonu için maç bulunamadı.")
        return

    table = defaultdict(lambda: {'OM': 0, 'G': 0, 'B': 0, 'M': 0, 'AG': 0, 'YG': 0, 'Av.': 0, 'P': 0})

    for match in matches:
        home_team = match['ev_sahibi_takim']
        away_team = match['deplasman_takim']
        home_goals = match['ev_sahibi_gol']
        away_goals = match['deplasman_gol']

        table[home_team]['OM'] += 1
        table[away_team]['OM'] += 1
        table[home_team]['AG'] += home_goals
        table[away_team]['AG'] += away_goals
        table[home_team]['YG'] += away_goals
        table[away_team]['YG'] += home_goals

        if home_goals > away_goals:
            table[home_team]['G'] += 1
            table[home_team]['P'] += 3
            table[away_team]['M'] += 1
        elif away_goals > home_goals:
            table[away_team]['G'] += 1
            table[away_team]['P'] += 3
            table[home_team]['M'] += 1
        else:
            table[home_team]['B'] += 1
            table[away_team]['B'] += 1
            table[home_team]['P'] += 1
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


if __name__ == '__main__':
    # Hangi sezonun puan durumunu görmek istediğimizi burada belirtiyoruz
    # Örnek: '2003-2004' (Arsenal'in yenilmez şampiyon olduğu sezon)
    # Örnek: '2011-2012' (Manchester City'nin son saniye golüyle şampiyon olduğu sezon)
    TARGET_SEASON = '2003-2004'
    calculate_league_table(TARGET_SEASON)