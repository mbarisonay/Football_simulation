# app.py (Ana Uygulama Menüsü)

import sys
import os

# Proje kök dizinini Python'un arama yoluna ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Artık simulation klasöründeki fonksiyonları import edebiliriz
from simulation.v1_puan_durumu import calculate_league_table, is_valid_season_format
from simulation.takim_analizi import calculate_team_strengths


# app.py dosyasında sadece bu fonksiyonu güncelleyin

def show_team_strength_menu():
    """Takım gücü analiz menüsünü yönetir."""
    while True:
        season_input = input(
            "\nTakım gücünü analiz etmek istediğiniz sezonu girin (Örn: 2018-2019) veya geri dönmek için 'g' yazın: ")

        if season_input.lower() == 'g':
            break

        if not is_valid_season_format(season_input):
            print("\nHATA: Geçersiz sezon formatı! Lütfen 'YYYY-YYYY' formatında girin.")
            continue

        strengths, error = calculate_team_strengths(season_input)
        if error:
            print(f"\nHATA: {error}")
            continue

        team_list = sorted(strengths.keys())
        print("\n--- O SEZONDAKİ TAKIMLAR ---")
        for i, team in enumerate(team_list, 1):
            print(f"{i}. {team}")

        while True:
            team_input = input(
                "\nGücünü görmek istediğiniz takımın adını veya sıra numarasını yazın (geri dönmek için 'g'): ")

            if team_input.lower() == 'g':
                break

            found_team = None
            # --- YENİ EKLENEN MANTIK BURADA ---
            # 1. Adım: Girdinin bir sayı olup olmadığını kontrol et
            if team_input.isdigit():
                try:
                    team_index = int(team_input)
                    # Girilen sayının liste sınırları içinde olup olmadığını kontrol et
                    if 1 <= team_index <= len(team_list):
                        # Liste index'i 0'dan başladığı için 1 çıkarıyoruz
                        found_team = team_list[team_index - 1]
                except ValueError:
                    # Bu genellikle olmaz ama bir güvenlik kontrolü
                    pass

            # 2. Adım: Eğer sayı değilse veya geçerli bir numara değilse, isimle aramayı dene
            if not found_team:
                for team in team_list:
                    if team_input.lower() == team.lower():
                        found_team = team
                        break
            # ------------------------------------

            if found_team:
                values = strengths[found_team]
                print(f"\n--- {found_team} ({season_input}) Güç Skorları ---")
                print(f"  Ev Sahibi Hücum Gücü: {values['home_attack']:.2f} (1'den büyükse iyi)")
                print(f"  Ev Sahibi Savunma Gücü: {values['home_defense']:.2f} (1'den küçükse iyi)")
                print(f"  Deplasman Hücum Gücü: {values['away_attack']:.2f} (1'den büyükse iyi)")
                print(f"  Deplasman Savunma Gücü: {values['away_defense']:.2f} (1'den küçükse iyi)")
            else:
                print(f"\nHATA: '{team_input}' adında veya sırasında bir takım bulunamadı. Lütfen tekrar deneyin.")

def show_league_table_menu():
    """Puan durumu menüsünü yönetir."""
    while True:
        season_input = input(
            "\nPuan durumunu görmek istediğiniz sezonu girin (Örn: 2003-2004) veya geri dönmek için 'g' yazın: ")

        if season_input.lower() == 'g':
            break

        if is_valid_season_format(season_input):
            calculate_league_table(season_input)
        else:
            print("\nHATA: Geçersiz format! Lütfen '2003-2004' gibi YYYY-YYYY formatında girin.")


def main_menu():
    """Programın ana menüsünü gösterir ve kullanıcı seçimlerini yönetir."""
    while True:
        print("\n===== ANA MENÜ =====")
        print("1. Puan Tablosu İncele")
        print("2. Takım Gücü Analizi")
        print("q. Çıkış")

        choice = input("Lütfen yapmak istediğiniz işlemi seçin: ")

        if choice == '1':
            show_league_table_menu()
        elif choice == '2':
            show_team_strength_menu()
        elif choice.lower() == 'q':
            print("Programdan çıkılıyor. Hoşça kalın!")
            break
        else:
            print("\nGeçersiz seçim. Lütfen menüden bir seçenek girin.")


if __name__ == '__main__':
    main_menu()