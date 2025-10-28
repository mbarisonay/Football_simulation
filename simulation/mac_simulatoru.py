# simulation/mac_simulatoru.py (V2.0 - Çoklu İstatistik Simülasyonu)

import numpy as np


def predict_stat(attack_strength, defense_strength, avg_league_stat):
    """
    Belirli bir istatistik (gol, şut, korner) için beklenen değeri hesaplar
    ve Poisson dağılımına göre o maçlık bir değer üretir.
    """
    # Beklenen değer = Takımın ilgili hücum gücü * Rakibin ilgili savunma gücü * Ligin ilgili ortalaması
    lambda_val = attack_strength * defense_strength * avg_league_stat

    # Negatif bir beklenti olamayacağından emin olalım
    if lambda_val < 0:
        lambda_val = 0

    return np.random.poisson(lam=lambda_val, size=1)[0]


def simulate_match(home_team_profile, away_team_profile, league_averages):
    """
    İki takımın ZENGİNLEŞTİRİLMİŞ profillerini kullanarak tek bir maçın
    skorunu ve diğer istatistiklerini simüle eder.
    """
    # Ev sahibi takımın istatistiklerini tahmin et
    home_goals = predict_stat(
        attack_strength=home_team_profile['home_attack_strength']['goals'],
        defense_strength=away_team_profile['away_defense_strength']['goals'],
        avg_league_stat=league_averages['avg_home_goals']
    )
    home_shots = predict_stat(
        attack_strength=home_team_profile['home_attack_strength']['shots'],
        defense_strength=away_team_profile['away_defense_strength']['shots'],
        avg_league_stat=league_averages['avg_home_shots']
    )
    home_corners = predict_stat(
        attack_strength=home_team_profile['home_attack_strength']['corners'],
        defense_strength=away_team_profile['away_defense_strength']['corners'],
        avg_league_stat=league_averages['avg_home_corners']
    )

    # Deplasman takımının istatistiklerini tahmin et
    away_goals = predict_stat(
        attack_strength=away_team_profile['away_attack_strength']['goals'],
        defense_strength=home_team_profile['home_defense_strength']['goals'],
        avg_league_stat=league_averages['avg_away_goals']
    )
    away_shots = predict_stat(
        attack_strength=away_team_profile['away_attack_strength']['shots'],
        defense_strength=home_team_profile['home_defense_strength']['shots'],
        avg_league_stat=league_averages['avg_away_shots']
    )
    away_corners = predict_stat(
        attack_strength=away_team_profile['away_attack_strength']['corners'],
        defense_strength=home_team_profile['home_defense_strength']['corners'],
        avg_league_stat=league_averages['avg_away_corners']
    )

    return {
        'ev_sahibi_gol': home_goals, 'deplasman_gol': away_goals,
        'ev_sahibi_sut': home_shots, 'deplasman_sut': away_shots,
        'ev_sahibi_korner': home_corners, 'deplasman_korner': away_corners
    }