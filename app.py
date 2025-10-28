# app.py (Tek Maç Simülasyonu Entegre Edilmiş Hali)

import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from simulation.v1_puan_durumu import calculate_league_table, is_valid_season_format
from simulation.takim_analizi import calculate_team_strengths
# Yeni simülatörümüzü import ediyoruz
from simulation.mac_simulatoru import simulate_match
# Lig ortalamalarını da hesaplamamız gerekecek, bu yüzden bu fonksiyonu da alıyoruz
from database.db_manager import get_matches_by_season


def show_team_strength_menu():
    # ... (Bu fonksiyon aynı kalıyor, değişiklik yok)
    while True:
        season_input = input(
            "\nTakım gücünü analiz etmek istediğiniz sezonu girin (Örn: 2018-2019) veya geri dönmek için 'g' yazın: ")
        if season_input.lower() == 'g': break
        if not is_valid_season_format(season_input):
            print("\nHATA: Geçersiz sezon formatı! Lütfen 'YYYY-YYYY' formatında girin.")
            continue
        strengths, error = calculate_team_strengths(season_input)
        if error:
            print(f"\nHATA: {error}");
            continue
        team_list = sorted(strengths.keys())
        print("\n--- O SEZONDAKİ TAKIMLAR ---")
        for i, team in enumerate(team_list, 1): print(f"{i}. {team}")
        while True:
            team_input = input(
                "\nGücünü görmek istediğiniz takımın adını veya sıra numarasını yazın (geri dönmek için 'g'): ")
            if team_input.lower() == 'g': break
            found_team = None
            if team_input.isdigit():
                try:
                    if 1 <= int(team_input) <= len(team_list): found_team = team_list[int(team_input) - 1]
                except:
                    pass
            if not found_team:
                for team in team_list:
                    if team_input.lower() == team.lower(): found_team = team; break
            if found_team:
                values = strengths[found_team]
                print(f"\n--- {found_team} ({season_input}) Güç Skorları ---")
                print(f"  Ev Sahibi Hücum Gücü: {values['home_attack']:.2f}");
                print(f"  Ev Sahibi Savunma Gücü: {values['home_defense']:.2f}")
                print(f"  Deplasman Hücum Gücü: {values['away_attack']:.2f}");
                print(f"  Deplasman Savunma Gücü: {values['away_defense']:.2f}")
            else:
                print(f"\nHATA: '{team_input}' adında veya sırasında bir takım bulunamadı.")


def show_league_table_menu():
    # ... (Bu fonksiyon aynı kalıyor, değişiklik yok)
    while True:
        season_input = input(
            "\nPuan durumunu görmek istediğiniz sezonu girin (Örn: 2003-2004) veya geri dönmek için 'g' yazın: ")
        if season_input.lower() == 'g': break
        if is_valid_season_format(season_input):
            calculate_league_table(season_input.replace('-', '/'))
        else:
            print("\nHATA: Geçersiz format! Lütfen '2003-2004' gibi YYYY-YYYY formatında girin.")


# --- YENİ EKLENEN FONKSİYON ---
def show_single_match_simulation_menu():
    """Tek maç simülasyonu menüsünü yönetir."""
    print("\n--- Tek Maç Simülasyonu ---")
    season_input = input("Simülasyon için sezon seçin (Örn: 2018-2019): ")

    if not is_valid_season_format(season_input):
        print("\nHATA: Geçersiz sezon formatı!")
        return

    # 1. Seçilen sezon için güç skorlarını ve lig ortalamalarını hesapla
    strengths, error = calculate_team_strengths(season_input)
    if error:
        print(f"\nHATA: {error}");
        return

    # Lig ortalamalarını almak için maç verisini tekrar çekiyoruz
    matches = get_matches_by_season(season_input)
    league_averages = {
        'avg_home_goals': sum(m['ev_sahibi_gol'] for m in matches) / len(matches),
        'avg_away_goals': sum(m['deplasman_gol'] for m in matches) / len(matches)
    }

    team_list = sorted(strengths.keys())
    print("\n--- O SEZONDAKİ TAKIMLAR ---")
    for i, team in enumerate(team_list, 1): print(f"{i}. {team}")

    # 2. Kullanıcıdan takımları al
    home_team_name = input("\nEv sahibi takımı seçin (isim veya numara): ")
    away_team_name = input("Deplasman takımını seçin (isim veya numara): ")

    # 3. Girdileri gerçek takım isimlerine çevir
    def find_team(user_input, teams):
        if user_input.isdigit() and 1 <= int(user_input) <= len(teams):
            return teams[int(user_input) - 1]
        for team in teams:
            if user_input.lower() == team.lower():
                return team
        return None

    home_team = find_team(home_team_name, team_list)
    away_team = find_team(away_team_name, team_list)

    if not home_team or not away_team:
        print("\nHATA: Takım adlarından biri veya her ikisi de geçersiz. Ana menüye dönülüyor.")
        return

    # 4. Simülasyonu çalıştır ve sonucu göster
    simulated_score = simulate_match(strengths[home_team], strengths[away_team], league_averages)

    print("\n--- SİMÜLASYON SONUCU ---")
    print(
        f"  {home_team} (Ev) {simulated_score['ev_sahibi_gol']} - {simulated_score['deplasman_gol']} {away_team} (Deplasman)")


# --- ANA MENÜ GÜNCELLENDİ ---
def main_menu():
    """Programın ana menüsünü gösterir ve kullanıcı seçimlerini yönetir."""
    while True:
        print("\n===== ANA MENÜ =====")
        print("1. Puan Tablosu İncele")
        print("2. Takım Gücü Analizi")
        print("3. Tek Maç Simülasyonu")  # Yeni seçenek
        print("q. Çıkış")

        choice = input("Lütfen yapmak istediğiniz işlemi seçin: ")

        if choice == '1':
            show_league_table_menu()
        elif choice == '2':
            show_team_strength_menu()
        elif choice == '3':
            show_single_match_simulation_menu()  # Yeni fonksiyonu çağır
        elif choice.lower() == 'q':
            print("Programdan çıkılıyor. Hoşça kalın!")
            break
        else:
            print("\nGeçersiz seçim. Lütfen menüden bir seçenek girin.")


if __name__ == '__main__':
    main_menu()