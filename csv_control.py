# csv_incele.py

import pandas as pd

# Lütfen bu kısmı kendi CSV dosyanızın adıyla güncelleyin
CSV_DOSYA_ADI = 'final_dataset.csv'  # Veya sizin dosyanızın adı

try:
    # Sadece ilk satırı (başlık satırını) okumak yeterli
    df = pd.read_csv(CSV_DOSYA_ADI, nrows=1, encoding='ISO-8859-1')

    print("--- CSV DOSYASINDAKİ GERÇEK SÜTUN İSİMLERİ ---")
    print(list(df.columns))

except Exception as e:
    print(f"Bir hata oluştu: {e}")