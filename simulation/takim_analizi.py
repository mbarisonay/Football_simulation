# simulation/takim_analizi.py (V2.0 İstatistik Profilleri)

import sys
import os
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.db_manager import get_matches_by_season


def calculate_team_profiles(season_range):
    """
    Belirtilen sezon için her takımın gol, şut, korner vb. gibi
    istatistiksel profillerini ve göreceli güçlerini hesaplar.
    """
    matches = get_matches_by_season(season_range)
    if not matches:
        return None, None, "Belirtilen sezon için maç bulunamadı."

    df = pd.DataFrame(matches)

    # DataFrame'deki None/NaN değerlerini 0 ile doldurarak hesaplama hatalarını önle
    df.fillna(0, inplace=True)

    # 1. Adım: Ligin Genel Ortalamalarını Hesapla
    league_averages = {
        'avg_home_goals': df['ev_sahibi_gol'].mean(),
        'avg_away_goals': df['deplasman_gol'].mean(),
        'avg_home_shots': df['ev_sahibi_sut'].mean(),
        'avg_away_shots': df['deplasman_sut'].mean(),
        'avg_home_corners': df['ev_sahibi_korner'].mean(),
        'avg_away_corners': df['deplasman_korner'].mean()
    }

    team_profiles = {}
    teams = set(df['ev_sahibi_takim']) | set(df['deplasman_takim'])

    for team in teams:
        home_games = df[df['ev_sahibi_takim'] == team]
        away_games = df[df['deplasman_takim'] == team]

        # 2. Adım: Her takımın kendi ortalamalarını hesapla
        # Hücum İstatistikleri (Ürettiği)
        home_attack_avg = {
            'goals': home_games['ev_sahibi_gol'].mean(),
            'shots': home_games['ev_sahibi_sut'].mean(),
            'corners': home_games['ev_sahibi_korner'].mean()
        }
        away_attack_avg = {
            'goals': away_games['deplasman_gol'].mean(),
            'shots': away_games['deplasman_sut'].mean(),
            'corners': away_games['deplasman_korner'].mean()
        }

        # Savunma İstatistikleri (İzin Verdiği)
        home_defense_avg = {
            'goals': home_games['deplasman_gol'].mean(),
            'shots': home_games['deplasman_sut'].mean(),
            'corners': home_games['deplasman_korner'].mean()
        }
        away_defense_avg = {
            'goals': away_games['ev_sahibi_gol'].mean(),
            'shots': away_games['ev_sahibi_sut'].mean(),
            'corners': away_games['ev_sahibi_korner'].mean()
        }

        # 3. Adım: Göreceli Güç Skorlarını Hesapla
        team_profiles[team] = {
            'home_attack_strength': {
                'goals': home_attack_avg['goals'] / league_averages['avg_home_goals'],
                'shots': home_attack_avg['shots'] / league_averages['avg_home_shots'],
                'corners': home_attack_avg['corners'] / league_averages['avg_home_corners']
            },
            'away_attack_strength': {
                'goals': away_attack_avg['goals'] / league_averages['avg_away_goals'],
                'shots': away_attack_avg['shots'] / league_averages['avg_away_shots'],
                'corners': away_attack_avg['corners'] / league_averages['avg_away_corners']
            },
            'home_defense_strength': {
                'goals': home_defense_avg['goals'] / league_averages['avg_away_goals'],
                'shots': home_defense_avg['shots'] / league_averages['avg_away_shots'],
                'corners': home_defense_avg['corners'] / league_averages['avg_away_corners']
            },
            'away_defense_strength': {
                'goals': away_defense_avg['goals'] / league_averages['avg_home_goals'],
                'shots': away_defense_avg['shots'] / league_averages['avg_home_shots'],
                'corners': away_defense_avg['corners'] / league_averages['avg_home_corners']
            }
        }

    return team_profiles, league_averages, None


if __name__ == '__main__':
    TARGET_SEASON = '2018-2019'
    profiles, averages, error = calculate_team_profiles(TARGET_SEASON)

    if error:
        print(f"Hata: {error}")
    else:
        # Örnek olarak Man City'nin profilini yazdıralım
        team_name = 'Man City'
        if team_name in profiles:
            print(f"--- {team_name} ({TARGET_SEASON}) İstatistik Profili ---")
            print(f"Ligin Ortalama Ev Golü: {averages['avg_home_goals']:.2f}")
            print(f"Man City Ev Hücum Gücü (Gol): {profiles[team_name]['home_attack_strength']['goals']:.2f}")
            print(f"Man City Ev Hücum Gücü (Şut): {profiles[team_name]['home_attack_strength']['shots']:.2f}")
            print(
                f"Man City Ev Savunma Gücü (Gol): {profiles[team_name]['home_defense_strength']['goals']:.2f} (1'den küçükse iyi)")
            print(
                f"Man City Ev Savunma Gücü (Şut): {profiles[team_name]['home_defense_strength']['shots']:.2f} (1'den küçükse iyi)")