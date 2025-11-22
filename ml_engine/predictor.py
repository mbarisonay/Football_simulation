import joblib
import os
import pandas as pd
import numpy as np


class MatchPredictor:
    def __init__(self):
        # Model dosyalarının yerini bul
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, 'saved_models')

        home_model_path = os.path.join(model_dir, 'home_goals_model.pkl')
        away_model_path = os.path.join(model_dir, 'away_goals_model.pkl')

        # Modelleri yükle (Yüklenemezse hata verir)
        if os.path.exists(home_model_path) and os.path.exists(away_model_path):
            self.model_home = joblib.load(home_model_path)
            self.model_away = joblib.load(away_model_path)
            print("🧠 Yapay Zeka motoru başarıyla yüklendi.")
        else:
            raise FileNotFoundError("Model dosyaları bulunamadı! Önce 'train_model.py' çalıştırın.")

    def predict_match(self, home_team_stats, away_team_stats):
        """
        İki takımın istatistiklerini alır ve tahmini gol sayılarını döndürür.
        """
        # Modelin beklediği formatta bir DataFrame oluştur
        # Sütun sırası train_model.py ile AYNI olmalı!
        input_data = pd.DataFrame([{
            'Home_Overall': home_team_stats['Overall'],
            'Home_Att': home_team_stats['Attack'],
            'Home_Mid': home_team_stats['Midfield'],
            'Home_Def': home_team_stats['Defense'],
            'Home_Pace': home_team_stats['Pace'],

            'Away_Overall': away_team_stats['Overall'],
            'Away_Att': away_team_stats['Attack'],
            'Away_Mid': away_team_stats['Midfield'],
            'Away_Def': away_team_stats['Defense'],
            'Away_Pace': away_team_stats['Pace']
        }])

        # Tahmin yap (Sonuç 1.76 gibi küsuratlı çıkabilir)
        exp_home_goals = self.model_home.predict(input_data)[0]
        exp_away_goals = self.model_away.predict(input_data)[0]

        # --- SİMÜLASYON VARYASYONU ---
        # Yapay zeka her zaman aynı sonucu vermesin diye (Örn: 1.8 gol)
        # bunu bir olasılık havuzuna atıyoruz (Poisson Dağılımı).
        # Böylece bazen 1, bazen 2, nadiren 3 gol olur. Gerçekçilik artar.

        final_home_goals = np.random.poisson(exp_home_goals)
        final_away_goals = np.random.poisson(exp_away_goals)

        return {
            'score': (final_home_goals, final_away_goals),
            'expected_goals': (round(exp_home_goals, 2), round(exp_away_goals, 2))  # xG (Gol Beklentisi)
        }