# simulation/sezon_simulatoru.py

import sys
import os
import random
from collections import defaultdict
from itertools import combinations

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulation.mac_simulatoru import simulate_match


def create_fixture(teams):
    """
    Verilen takım listesi için basit bir çift devreli lig fikstürü oluşturur.
    Her takım her takımla bir evinde, bir deplasmanda oynar.
    """
    fixture = []
    # combinations(teams, 2) -> ['A', 'B', 'C'] listesinden ('A', 'B'), ('A', 'C'), ('B', 'C') gibi tüm ikilileri üretir
    for team1, team2 in combinations(teams, 2):
        # İlk yarı maçı (biri ev sahibi)
        fixture.append({'home': team1, 'away': team2})
        # İkinci yarı maçı (diğeri ev sahibi)
        fixture.append({'home': team2, 'away': team1})

    # Maçları rastgele karıştıralım ki her simülasyonda farklı bir sıra olsun
    random.shuffle(fixture)
    return fixture


def run_season_simulation(team_strengths, league_averages):
    """
    Verilen güç skorlarına göre tam bir sezonu simüle eder ve puan durumunu döndürür.
    """
    teams = list(team_strengths.keys())
    if len(teams) == 0:
        return None, "Güç skorları hesaplanmış takım bulunamadı."

    fixture = create_fixture(teams)

    # Sanal puan tablosunu oluştur
    table = defaultdict(lambda: {'OM': 0, 'G': 0, 'B': 0, 'M': 0, 'AG': 0, 'YG': 0, 'Av.': 0, 'P': 0})

    print(f"\n--- {len(teams)} TAKIMLI, {len(fixture)} MAÇLIK SEZON SİMÜLASYONU BAŞLATILIYOR ---")

    # Fikstürdeki her maçı tek tek simüle et
    for i, match in enumerate(fixture, 1):
        home_team_name = match['home']
        away_team_name = match['away']

        # Takımların güç skorlarını al
        home_strength = team_strengths[home_team_name]
        away_strength = team_strengths[away_team_name]

        # Maçı simüle et
        score = simulate_match(home_strength, away_strength, league_averages)
        home_goals = score['ev_sahibi_gol']
        away_goals = score['deplasman_gol']

        # Simülasyon sonucunu puan tablosuna işle (Bu mantığı v1_puan_durumu'ndan zaten biliyoruz)
        table[home_team_name]['OM'] += 1
        table[away_team_name]['OM'] += 1
        table[home_team_name]['AG'] += home_goals
        table[away_team_name]['AG'] += away_goals
        table[home_team_name]['YG'] += away_goals
        table[away_team_name]['YG'] += home_goals

        if home_goals > away_goals:
            table[home_team_name]['G'] += 1;
            table[home_team_name]['P'] += 3;
            table[away_team_name]['M'] += 1
        elif away_goals > home_goals:
            table[away_team_name]['G'] += 1;
            table[away_team_name]['P'] += 3;
            table[home_team_name]['M'] += 1
        else:
            table[home_team_name]['B'] += 1;
            table[away_team_name]['B'] += 1
            table[home_team_name]['P'] += 1;
            table[away_team_name]['P'] += 1

        # Kullanıcıya ilerlemeyi göstermek için her 38 maçta bir (yaklaşık 1 hafta) mesaj yazdır
        if i % (len(teams) / 2 * 10) == 0:
            print(f"  ... {i}/{len(fixture)} maç simüle edildi ...")

    # Tüm maçlar bitince averajları hesapla
    for team, stats in table.items():
        stats['Av.'] = stats['AG'] - stats['YG']

    # Nihai puan durumunu sırala
    sorted_table = sorted(table.items(), key=lambda item: (item[1]['P'], item[1]['Av.'], item[1]['AG']), reverse=True)

    print("--- SİMÜLASYON TAMAMLANDI! ---")
    return sorted_table, None