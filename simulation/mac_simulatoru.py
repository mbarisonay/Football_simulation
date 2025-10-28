# simulation/mac_simulatoru.py

import numpy as np


def predict_score(home_attack, away_defense, avg_home_goals):
    """
    Ev sahibi takımın atması beklenen gol sayısını (lambda) hesaplar ve
    bu beklentiye göre Poisson dağılımını kullanarak bir gol sayısı simüle eder.
    """
    # Beklenen gol sayısı = Ev sahibinin hücum gücü * Deplasmanın savunma gücü * Ligin ev sahibi gol ortalaması
    lambda_home = home_attack * away_defense * avg_home_goals

    # Poisson dağılımına göre rastgele bir gol sayısı üret
    # Bu, "beklenen ortalama bu ise, bu maçta kaç gol olur?" sorusunun olasılıksal cevabıdır.
    return np.random.poisson(lam=lambda_home, size=1)[0]


def simulate_match(home_team_strength, away_team_strength, league_averages):
    """
    İki takımın güç skorlarını ve lig ortalamalarını alarak tek bir maçın
    skorunu simüle eder.
    """
    # Ev sahibi takımın gollerini tahmin et
    home_goals = predict_score(
        home_attack=home_team_strength['home_attack'],
        away_defense=away_team_strength['away_defense'],
        avg_home_goals=league_averages['avg_home_goals']
    )

    # Deplasman takımının gollerini tahmin et
    away_goals = predict_score(
        home_attack=away_team_strength['away_attack'],  # Deplasman takımının DEPLASMAN hücum gücü
        away_defense=home_team_strength['home_defense'],  # Ev sahibi takımının EV savunma gücü
        avg_home_goals=league_averages['avg_away_goals']  # Ligin DEPLASMAN gol ortalaması
    )

    return {'ev_sahibi_gol': home_goals, 'deplasman_gol': away_goals}


if __name__ == '__main__':
    # Bu dosyayı doğrudan çalıştırarak basit bir test yapalım

    # Örnek: Güçlü bir ev sahibi (Man City) vs ortalama bir deplasman takımı (Everton)

    # Man City'nin 2018-2019 güç skorları (takim_analizi.py'den alınmış gibi)
    man_city_strength = {
        'home_attack': 1.81, 'home_defense': 0.72,
        'away_attack': 1.62, 'away_defense': 0.58
    }

    # Everton'ın 2018-2019 güç skorları
    everton_strength = {
        'home_attack': 1.07, 'home_defense': 0.91,
        'away_attack': 0.89, 'away_defense': 1.05
    }

    # 2018-2019 sezonu lig ortalamaları
    lig_ortalamalari = {
        'avg_home_goals': 1.54,
        'avg_away_goals': 1.25
    }

    print("--- TEK MAÇ SİMÜLASYONU TESTİ ---")
    print("Simüle edilen maç: Manchester City (Ev Sahibi) vs Everton (Deplasman)")

    # 10 farklı simülasyon yapıp sonuçları görelim
    print("\n10 farklı simülasyon sonucu:")
    for i in range(10):
        skor = simulate_match(man_city_strength, everton_strength, lig_ortalamalari)
        print(f"  Simülasyon {i + 1}: Man City {skor['ev_sahibi_gol']} - {skor['deplasman_gol']} Everton")