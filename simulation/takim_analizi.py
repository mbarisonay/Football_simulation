# simulation/takim_analizi.py (Zenginleştirilmiş Güç Modeli)

import sys
import os
from collections import defaultdict
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.db_manager import get_matches_by_season


def calculate_team_strengths(season_range):
    matches = get_matches_by_season(season_range)
    if not matches:
        return None, "Belirtilen sezon için maç bulunamadı."

    # Pandas DataFrame'i, bu tür hesaplamalar için çok daha güçlü ve pratiktir.
    df = pd.DataFrame(matches)

    # 1. Adım: Lig Ortalamalarını Hesapla
    avg_home_goals = df['ev_sahibi_gol'].mean()
    avg_away_goals = df['deplasman_gol'].mean()
    avg_home_shots = df['ev_sahibi_sut'].mean()
    avg_away_shots = df['deplasman_sut'].mean()
    avg_home_sot = df['ev_sahibi_isabetli_sut'].mean()
    avg_away_sot = df['deplasman_isabetli_sut'].mean()

    team_strengths = {}
    teams = set(df['ev_sahibi_takim']) | set(df['deplasman_takim'])

    # 2. Adım: Her Takım İçin Güçleri Hesapla
    for team in teams:
        home_games = df[df['ev_sahibi_takim'] == team]
        away_games = df[df['deplasman_takim'] == team]

        # Takımın kendi ortalamaları
        avg_goals_scored_home = home_games['ev_sahibi_gol'].mean()
        avg_shots_scored_home = home_games['ev_sahibi_sut'].mean()
        avg_sot_scored_home = home_games['ev_sahibi_isabetli_sut'].mean()

        avg_goals_conceded_home = home_games['deplasman_gol'].mean()
        avg_shots_conceded_home = home_games['deplasman_sut'].mean()
        avg_sot_conceded_home = home_games['deplasman_isabetli_sut'].mean()

        avg_goals_scored_away = away_games['deplasman_gol'].mean()
        avg_shots_scored_away = away_games['deplasman_sut'].mean()
        avg_sot_scored_away = away_games['deplasman_isabetli_sut'].mean()

        avg_goals_conceded_away = away_games['ev_sahibi_gol'].mean()
        avg_shots_conceded_away = away_games['ev_sahibi_sut'].mean()
        avg_sot_conceded_away = away_games['ev_sahibi_isabetli_sut'].mean()

        # Göreceli güç skorları (Takım Ortalaması / Lig Ortalaması)
        # Ağırlıklar: Gol %60, İsabetli Şut %30, Toplam Şut %10
        home_attack = (
                (avg_goals_scored_home / avg_home_goals) * 0.6 +
                (avg_sot_scored_home / avg_home_sot) * 0.3 +
                (avg_shots_scored_home / avg_home_shots) * 0.1
        )
        away_attack = (
                (avg_goals_scored_away / avg_away_goals) * 0.6 +
                (avg_sot_scored_away / avg_away_sot) * 0.3 +
                (avg_shots_scored_away / avg_away_shots) * 0.1
        )

        # Savunma gücü, rakibin ortalamasına göre ölçülür
        home_defense = (
                (avg_goals_conceded_home / avg_away_goals) * 0.6 +
                (avg_sot_conceded_home / avg_away_sot) * 0.3 +
                (avg_shots_conceded_home / avg_away_shots) * 0.1
        )
        away_defense = (
                (avg_goals_conceded_away / avg_home_goals) * 0.6 +
                (avg_sot_conceded_away / avg_home_sot) * 0.3 +
                (avg_shots_conceded_away / avg_home_shots) * 0.1
        )

        team_strengths[team] = {
            'home_attack': home_attack, 'home_defense': home_defense,
            'away_attack': away_attack, 'away_defense': away_defense
        }

    return team_strengths, None


if __name__ == '__main__':
    TARGET_SEASON = '2018-2019'
    strengths, error = calculate_team_strengths(TARGET_SEASON)

    if error:
        print(f"Hata: {error}")
    else:
        print(f"--- PREMIER LEAGUE {TARGET_SEASON} SEZONU ZENGİNLEŞTİRİLMİŞ GÜÇ SKORLARI ---")
        # Örnek takımların skorlarını yazdır
        for team, values in list(strengths.items())[:5]:  # İlk 5 takımı göster
            print(f"\n--- {team} ---")
            print(f"  Ev Sahibi Hücum Gücü: {values['home_attack']:.2f}")
            print(f"  Ev Sahibi Savunma Gücü: {values['home_defense']:.2f}")
            print(f"  Deplasman Hücum Gücü: {values['away_attack']:.2f}")
            print(f"  Deplasman Savunma Gücü: {values['away_defense']:.2f}")