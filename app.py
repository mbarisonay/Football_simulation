# app.py (Tam Sezon Simülasyonu Entegre Edilmiş Nihai Hali)

import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from simulation.v1_puan_durumu import calculate_league_table, is_valid_season_format
from simulation.takim_analizi import calculate_team_profiles
from simulation.mac_simulatoru import simulate_match
from simulation.sezon_simulatoru import run_season_simulation  # YENİ
from database.db_manager import get_matches_by_season


# Diğer menü fonksiyonları (show_team_strength_menu, show_league_table_menu) aynı kalıyor...
# ... (Kodun uzun olmaması için buraya eklemiyorum, dosyanızda kalsınlar)
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

        # --- DÜZELTME 1: Gelen 3 değeri doğru şekilde karşılıyoruz ---
        profiles, _, error = calculate_team_profiles(season_input)
        if error:
            print(f"\nHATA: {error}")
            continue

        team_list = sorted(profiles.keys())
        print("\n--- O SEZONDAKİ TAKIMLAR ---")
        for i, team in enumerate(team_list, 1):
            print(f"{i}. {team}")

        while True:
            team_input = input(
                "\nGücünü görmek istediğiniz takımın adını veya sıra numarasını yazın (geri dönmek için 'g'): ")
            if team_input.lower() == 'g':
                break

            found_team = None
            if team_input.isdigit():
                if 1 <= int(team_input) <= len(team_list):
                    found_team = team_list[int(team_input) - 1]
            if not found_team:
                for team in team_list:
                    if team_input.lower() == team.lower():
                        found_team = team
                        break

            if found_team:
                # --- DÜZELTME 2: Yeni ve daha detaylı veri yapısını kullanıyoruz ---
                values = profiles[found_team]
                print(f"\n--- {found_team} ({season_input}) Güç Skorları ---")
                print(f"  Ev Sahibi Hücum (Gol): {values['home_attack_strength']['goals']:.2f}")
                print(f"  Ev Sahibi Savunma (Gol): {values['home_defense_strength']['goals']:.2f}")
                print(f"  Deplasman Hücum (Gol): {values['away_attack_strength']['goals']:.2f}")
                print(f"  Deplasman Savunma (Gol): {values['away_defense_strength']['goals']:.2f}")
                print(f"  (Not: 1'den büyük hücum, 1'den küçük savunma skoru daha iyidir)")
            else:
                print(f"\nHATA: '{team_input}' adında veya sırasında bir takım bulunamadı.")

def show_league_table_menu():
    while True:
        season_input = input(
            "\nPuan durumunu görmek istediğiniz sezonu girin (Örn: 2003-2004) veya geri dönmek için 'g' yazın: ")
        if season_input.lower() == 'g': break
        if is_valid_season_format(season_input):
            calculate_league_table(season_input)
        else:
            print("\nHATA: Geçersiz format! Lütfen '2003-2004' gibi YYYY-YYYY formatında girin.")


def show_single_match_simulation_menu():
    """Tek maç simülasyonu menüsünü yönetir."""
    print("\n--- Tek Maç Simülasyonu ---")
    season_input = input("Simülasyon için referans alınacak sezonu seçin (Örn: 2018-2019): ")

    if not is_valid_season_format(season_input):
        print("\nHATA: Geçersiz sezon formatı!")
        return

    profiles, league_averages, error = calculate_team_profiles(season_input)
    if error:
        print(f"\nHATA: {error}");
        return

    team_list = sorted(profiles.keys())
    print("\n--- O SEZONDAKİ TAKIMLAR ---")
    for i, team in enumerate(team_list, 1): print(f"{i}. {team}")

    home_team_name = input("\nEv sahibi takımı seçin (isim veya numara): ")
    away_team_name = input("Deplasman takımını seçin (isim veya numara): ")

    def find_team(user_input, teams):
        if user_input.isdigit() and 1 <= int(user_input) <= len(teams): return teams[int(user_input) - 1]
        for team in teams:
            if user_input.lower() == team.lower(): return team
        return None

    home_team = find_team(home_team_name, team_list)
    away_team = find_team(away_team_name, team_list)

    if not home_team or not away_team:
        print("\nHATA: Takım adlarından biri veya her ikisi de geçersiz. Ana menüye dönülüyor.")
        return

    # Simülasyonu çalıştır
    simulated_stats = simulate_match(profiles[home_team], profiles[away_team], league_averages)

    # --- YENİ VE GÜZEL ÇIKTI FORMATI ---
    print("\n" + "=" * 40)
    print(" " * 12 + "SİMÜLASYON SONUCU")
    print("=" * 40)
    print(f"SEZON: {season_input}")
    print(f"{'':<15} | {'EV SAHİBİ':<12} | {'DEPLASMAN':<12}")
    print(f"{'-' * 15} | {'-' * 12} | {'-' * 12}")
    print(f"{'TAKIM':<15} | {home_team:<12} | {away_team:<12}")
    print(f"{'GOL':<15} | {simulated_stats['ev_sahibi_gol']:<12} | {simulated_stats['deplasman_gol']:<12}")
    print(f"{'ŞUT':<15} | {simulated_stats['ev_sahibi_sut']:<12} | {simulated_stats['deplasman_sut']:<12}")
    print(f"{'KORNER':<15} | {simulated_stats['ev_sahibi_korner']:<12} | {simulated_stats['deplasman_korner']:<12}")
    print("=" * 40)

# --- YENİ SEZON SİMÜLASYON MENÜSÜ ---
def show_full_season_simulation_menu():
    """Tam sezon simülasyonu menüsünü yönetir."""
    print("\n--- Tam Sezon Simülasyonu ---")
    season_input = input("Simülasyon için referans alınacak sezonu seçin (Örn: 2018-2019): ")

    if not is_valid_season_format(season_input):
        print("\nHATA: Geçersiz sezon formatı!")
        return

    # 1. Referans sezonun güçlerini ve lig ortalamalarını hesapla
    strengths, error = calculate_team_strengths(season_input)
    if error:
        print(f"\nHATA: {error}");
        return

    matches = get_matches_by_season(season_input)
    if not matches:
        print(f"\nHATA: {season_input} için maç verisi bulunamadı.");
        return

    league_averages = {
        'avg_home_goals': sum(m['ev_sahibi_gol'] for m in matches) / len(matches),
        'avg_away_goals': sum(m['deplasman_gol'] for m in matches) / len(matches)
    }

    # 2. Simülasyonu çalıştır
    final_table, error = run_season_simulation(strengths, league_averages)
    if error:
        print(f"\nHATA: {error}");
        return

    # 3. Simülasyon sonucunu (nihai puan durumu) ekrana yazdır
    print(f"\n--- SİMÜLASYON SONUCU: {season_input} GÜÇLERİNE GÖRE OLUŞAN PUAN DURUMU ---")
    print("-" * 85)
    print(f"{'#':<3} {'Takım':<25} {'OM':>4} {'G':>4} {'B':>4} {'M':>4} {'AG':>4} {'YG':>4} {'Av.':>5} {'P':>5}")
    print("-" * 85)
    for i, (team_name, stats) in enumerate(final_table, 1):
        print(
            f"{i:<3} {team_name:<25} {stats['OM']:>4} {stats['G']:>4} {stats['B']:>4} {stats['M']:>4} {stats['AG']:>4} {stats['YG']:>4} {stats['Av.']:>5} {stats['P']:>5}")
    print("-" * 85)
    print(f"\nŞampiyon: {final_table[0][0]}")


def main_menu():
    """Programın ana menüsünü gösterir ve kullanıcı seçimlerini yönetir."""
    while True:
        print("\n===== ANA MENÜ =====")
        print("1. Puan Tablosu İncele")
        print("2. Takım Gücü Analizi")
        print("3. Tek Maç Simülasyonu")
        print("4. Tam Sezon Simülasyonu")  # YENİ
        print("q. Çıkış")

        choice = input("Lütfen yapmak istediğiniz işlemi seçin: ")

        if choice == '1':
            show_league_table_menu()
        elif choice == '2':
            show_team_strength_menu()
        elif choice == '3':
            show_single_match_simulation_menu()
        elif choice == '4':
            show_full_season_simulation_menu()  # YENİ
        elif choice.lower() == 'q':
            print("Programdan çıkılıyor. Hoşça kalın!")
            break
        else:
            print("\nGeçersiz seçim. Lütfen menüden bir seçenek girin.")


if __name__ == '__main__':
    main_menu()