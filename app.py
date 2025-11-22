from game_engine.team import Team
from ml_engine.predictor import MatchPredictor


def main():
    print("⚽ YAPAY ZEKA FUTBOL SİMÜLASYONU V1.0 ⚽")
    print("-" * 40)

    # 1. Yapay Zeka Motorunu Başlat
    try:
        predictor = MatchPredictor()
    except Exception as e:
        print(f"Motor başlatılamadı: {e}")
        return

    # 2. Takımları Seç
    season = "2023-2024"  # Veritabanında olan bir sezon seç
    home_team_name = "Manchester City"
    away_team_name = "Liverpool"

    print(f"\n📅 Sezon: {season}")
    print(f"🏠 Ev Sahibi: {home_team_name}")
    print(f"✈️  Deplasman: {away_team_name}")
    print("-" * 40)

    # 3. Takım Verilerini Yükle
    home_team = Team(home_team_name, season)
    away_team = Team(away_team_name, season)

    print(f"📊 {home_team.name} Güçleri: {home_team.stats['Overall']:.1f} (Hücum: {home_team.stats['Attack']:.1f})")
    print(f"📊 {away_team.name} Güçleri: {away_team.stats['Overall']:.1f} (Hücum: {away_team.stats['Attack']:.1f})")

    # 4. Maçı Oynat (Tahmin Et)
    result = predictor.predict_match(home_team.get_ml_features(), away_team.get_ml_features())

    score = result['score']
    xg = result['expected_goals']

    print("\n" + "=" * 40)
    print(f"🏁 MAÇ SONUCU: {home_team.name} {score[0]} - {score[1]} {away_team.name}")
    print("=" * 40)
    print(f"📈 Gol Beklentisi (xG): {xg[0]} - {xg[1]}")
    print(f"ℹ️  Not: xG yapay zekanın saf tahmini, skor ise bu ihtimale göre gerçekleşen simülasyondur.")


if __name__ == "__main__":
    main()