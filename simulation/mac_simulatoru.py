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
    İki takımın tam profillerini kullanarak maçın tüm istatistiklerini simüle eder.
    """
    # Ev sahibi takımın istatistikleri
    home_goals = predict_stat(home_team_profile['home_attack_strength']['goals'], away_team_profile['away_defense_strength']['goals'], league_averages['avg_home_goals'])
    home_shots = predict_stat(home_team_profile['home_attack_strength']['shots'], away_team_profile['away_defense_strength']['shots'], league_averages['avg_home_shots'])
    home_sot = predict_stat(home_team_profile['home_attack_strength']['sot'], away_team_profile['away_defense_strength']['sot'], league_averages['avg_home_sot'])
    home_corners = predict_stat(home_team_profile['home_attack_strength']['corners'], away_team_profile['away_defense_strength']['corners'], league_averages['avg_home_corners'])
    home_yellow = predict_stat(home_team_profile['discipline_profile']['home_yellow'], away_team_profile['discipline_profile']['away_yellow'], league_averages['avg_home_yellow'])
    home_red = predict_stat(home_team_profile['discipline_profile']['home_red'], away_team_profile['discipline_profile']['away_red'], league_averages['avg_home_red'])

    # Deplasman takımının istatistikleri
    away_goals = predict_stat(away_team_profile['away_attack_strength']['goals'], home_team_profile['home_defense_strength']['goals'], league_averages['avg_away_goals'])
    away_shots = predict_stat(away_team_profile['away_attack_strength']['shots'], home_team_profile['home_defense_strength']['shots'], league_averages['avg_away_shots'])
    away_sot = predict_stat(away_team_profile['away_attack_strength']['sot'], home_team_profile['home_defense_strength']['sot'], league_averages['avg_away_sot'])
    away_corners = predict_stat(away_team_profile['away_attack_strength']['corners'], home_team_profile['home_defense_strength']['corners'], league_averages['avg_away_corners'])
    away_yellow = predict_stat(away_team_profile['discipline_profile']['away_yellow'], home_team_profile['discipline_profile']['home_yellow'], league_averages['avg_away_yellow'])
    away_red = predict_stat(away_team_profile['discipline_profile']['away_red'], home_team_profile['discipline_profile']['home_red'], league_averages['avg_away_red'])

    # İsabetli şut sayısı, toplam şut sayısından fazla olamaz.
    if home_sot > home_shots: home_sot = home_shots
    if away_sot > away_shots: away_sot = away_shots

    # --- DÜZELTME BURADA: Eksik anahtarları return sözlüğüne ekliyoruz ---
    return {
        'ev_sahibi_gol': home_goals, 'deplasman_gol': away_goals,
        'ev_sahibi_sut': home_shots, 'deplasman_sut': away_shots,
        'ev_sahibi_isabetli_sut': home_sot, 'deplasman_isabetli_sut': away_sot,
        'ev_sahibi_korner': home_corners, 'deplasman_korner': away_corners,
        'ev_sahibi_sari_kart': home_yellow, 'deplasman_sari_kart': away_yellow,
        'ev_sahibi_kirmizi_kart': home_red, 'deplasman_kirmizi_kart': away_red,
    }