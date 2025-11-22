import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Yollar
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_PATH = os.path.join(ROOT_DIR, 'data', 'processed', 'training_data.csv')
MODEL_DIR = os.path.join(CURRENT_DIR, 'saved_models')

# Model klasörü yoksa oluştur
os.makedirs(MODEL_DIR, exist_ok=True)


def train_ai_brain():
    print("🧠 Yapay Zeka Eğitimi Başlıyor...")

    if not os.path.exists(DATA_PATH):
        print(f"❌ HATA: {DATA_PATH} bulunamadı. Önce 'feature_engineer.py' çalıştırın.")
        return

    # 1. Veriyi Yükle
    df = pd.read_csv(DATA_PATH)

    # 2. Girdileri (Features) ve Çıktıları (Targets) Belirle
    # X: Yapay zekaya vereceğimiz ipuçları (Takım güçleri)
    X = df[[
        'Home_Overall', 'Home_Att', 'Home_Mid', 'Home_Def', 'Home_Pace',
        'Away_Overall', 'Away_Att', 'Away_Mid', 'Away_Def', 'Away_Pace'
    ]]

    # y: Tahmin etmesini istediğimiz şeyler (Ev sahibi golü ve Deplasman golü)
    y_home = df['FTHG']  # Full Time Home Goals
    y_away = df['FTAG']  # Full Time Away Goals

    # 3. Veriyi Böl (Eğitim ve Test)
    # Verinin %80'i ile ders çalışacak, %20'si ile sınav olacak
    X_train, X_test, y_home_train, y_home_test, y_away_train, y_away_test = train_test_split(
        X, y_home, y_away, test_size=0.2, random_state=42
    )

    # 4. Modelleri Oluştur (Random Forest)
    print("🤖 Modeller öğreniyor (Bu işlem birkaç saniye sürebilir)...")

    # Ev Sahibi Gol Modeli
    model_home = RandomForestRegressor(n_estimators=100, random_state=42)
    model_home.fit(X_train, y_home_train)

    # Deplasman Gol Modeli
    model_away = RandomForestRegressor(n_estimators=100, random_state=42)
    model_away.fit(X_train, y_away_train)

    # 5. Test Et (Sınav Sonuçları)
    home_preds = model_home.predict(X_test)
    away_preds = model_away.predict(X_test)

    mae_home = mean_absolute_error(y_home_test, home_preds)
    mae_away = mean_absolute_error(y_away_test, away_preds)

    print(f"\n📊 Model Performansı (Ortalama Hata Payı):")
    print(f"   🏠 Ev Sahibi Gol Hatası: ±{mae_home:.2f} gol")
    print(f"   ✈️ Deplasman Gol Hatası: ±{mae_away:.2f} gol")
    print("   (Not: Futbol kaotiktir, 1.0 altı hata payı gayet iyidir!)")

    # 6. Modelleri Kaydet (.pkl dosyası olarak)
    joblib.dump(model_home, os.path.join(MODEL_DIR, 'home_goals_model.pkl'))
    joblib.dump(model_away, os.path.join(MODEL_DIR, 'away_goals_model.pkl'))

    print(f"\n✅ Başarılı! Modeller '{MODEL_DIR}' klasörüne kaydedildi.")


if __name__ == "__main__":
    train_ai_brain()