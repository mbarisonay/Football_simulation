import pandas as pd
import os
import sys
from difflib import get_close_matches

# --- YOL AYARLARI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_PATH = os.path.join(PROCESSED_DATA_DIR, 'training_data_v2.csv')

PLAYER_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_PLAYER_STATS.csv")
MATCH_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_MATCH_STATS.csv")

# --- MANUEL EŞLEŞTİRME LİSTESİ (Bildiğimiz kesin hatalar) ---
TEAM_MAPPING = {
    "AVS Futebol": "AVS Futebol SAD", "Alavés": "Deportivo Alavés", "Amiens": "Amiens SC",
    "Angers": "Angers SCO", "Ankaragücü": "MKE Ankaragücü", "Arminia": "DSC Arminia Bielefeld",
    "Arouca": "FC Arouca", "Augsburg": "FC Augsburg", "Auxerre": "AJ Auxerre", "Aves": "CD Aves",
    "Barcelona": "FC Barcelona", "Bastia": "Sporting Club Bastia", "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Bayern Munich": "FC Bayern München", "Benfica": "SL Benfica", "Beşiktaş": "Beşiktaş JK",
    "Boavista": "Boavista FC", "Bochum": "VfL Bochum 1848", "Bordeaux": "FC Girondins de Bordeaux",
    "Bournemouth": "AFC Bournemouth", "Braga": "Sporting Clube de Braga", "Brest": "Stade Brestois 29",
    "Caen": "Stade Malherbe Caen", "Celta Vigo": "RC Celta", "Chaves": "GD Chaves",
    "Chievo": "AC ChievoVerona", "Clermont Foot": "Clermont Foot 63", "Cádiz": "Cádiz CF",
    "Darmstadt 98": "SV Darmstadt 98", "Deportivo La Coruña": "RC Deportivo de La Coruña", "Dijon": "Dijon FCO",
    "Dortmund": "Borussia Dortmund", "Düsseldorf": "Fortuna Düsseldorf", "Eibar": "SD Eibar",
    "Eintracht Braunschweig": "Eintracht Braunschweig", "Eint Frankfurt": "Eintracht Frankfurt", "Elche": "Elche CF",
    "Erzurum BB": "Erzurumspor FK", "Espanyol": "RCD Espanyol", "Estoril": "GD Estoril Praia",
    "Estrela": "Estrela da Amadora", "Feirense": "CD Feirense", "Fenerbahçe": "Fenerbahçe SK",
    "Freiburg": "SC Freiburg", "Fulham": "Fulham FC", "Galatasaray": "Galatasaray SK",
    "Gençlerbirliği": "Gençlerbirliği SK", "Getafe": "Getafe CF", "Girona": "Girona FC", "Granada": "Granada CF",
    "Greuther Fürth": "SpVgg Greuther Fürth", "Guingamp": "En Avant Guingamp", "Göztepe": "Göztepe SK",
    "Heidenheim": "1. FC Heidenheim 1846", "Hellas Verona": "Hellas Verona FC", "Hoffenheim": "TSG 1899 Hoffenheim",
    "Huesca": "SD Huesca", "Ingolstadt 04": "FC Ingolstadt 04", "Internazionale": "Inter", "Inter": "Inter",
    "Kasımpaşa": "Kasımpaşa SK", "Köln": "1. FC Köln", "Las Palmas": "UD Las Palmas", "Le Havre": "Le Havre AC",
    "Leganés": "CD Leganés", "Lens": "RC Lens", "Levante": "Levante UD", "Lille": "Lille OSC",
    "Lorient": "FC Lorient", "Luton Town": "Luton Town", "Lyon": "Olympique Lyonnais", "Mainz 05": "1. FSV Mainz 05",
    "Mallorca": "RCD Mallorca", "Marseille": "Olympique de Marseille", "Metz": "FC Metz", "Milan": "AC Milan",
    "Monaco": "AS Monaco", "Montpellier": "Montpellier HSC", "Moreirense": "Moreirense FC", "Málaga": "Málaga CF",
    "Mönchengladbach": "Borussia Mönchengladbach", "Gladbach": "Borussia Mönchengladbach", "Nacional": "CD Nacional",
    "Nancy": "AS Nancy Lorraine", "Nantes": "FC Nantes", "Nice": "OGC Nice", "Nîmes": "Nîmes Olympique",
    "Nürnberg": "1. FC Nürnberg", "Osasuna": "CA Osasuna", "Paderborn 07": "SC Paderborn 07", "Palermo": "Palermo FC",
    "Paços de Ferreira": "FC Paços de Ferreira", "Portimonense": "Portimonense SC", "Porto": "FC Porto",
    "Real Betis": "Real Betis Balompié", "Real Madrid": "Real Madrid CF", "Real Sociedad": "Real Sociedad",
    "Rennes": "Stade Rennais FC", "Rio Ave": "Rio Ave FC", "Roma": "AS Roma", "Saint-Étienne": "AS Saint-Étienne",
    "Santa Clara": "CD Santa Clara", "Sassuolo": "US Sassuolo Calcio", "Schalke 04": "FC Schalke 04",
    "Sevilla": "Sevilla FC", "Sivasspor": "Sivasspor", "Sporting CP": "Sporting CP",
    "Strasbourg": "RC Strasbourg Alsace",
    "Stuttgart": "VfB Stuttgart", "Sunderland": "Sunderland", "Tondela": "CD Tondela", "Torino": "Torino FC",
    "Toulouse": "Toulouse FC", "Trabzonspor": "Trabzonspor", "Troyes": "ESTAC Troyes", "Udinese": "Udinese Calcio",
    "Union Berlin": "1. FC Union Berlin", "Valencia": "Valencia CF", "Valladolid": "Real Valladolid CF",
    "Vallecano": "Rayo Vallecano", "Villarreal": "Villarreal CF", "Vitória": "Vitória Guimarães", "Vizela": "FC Vizela",
    "Werder Bremen": "SV Werder Bremen", "West Ham": "West Ham United", "Wolfsburg": "VfL Wolfsburg",
    "Wolves": "Wolverhampton Wanderers", "Yeni Malatyaspor": "Yeni Malatyaspor", "Çaykur Rizespor": "Çaykur Rizespor",
    "Ümraniyespor": "Ümraniyespor", "İstanbulspor": "İstanbulspor", "İst Başakşehir": "Medipol Başakşehir FK",
    "Basaksehir": "Medipol Başakşehir FK", "Man City": "Manchester City", "Man Utd": "Manchester United",
    "Nott'ham Forest": "Nottingham Forest", "Nott'm Forest": "Nottingham Forest", "Sheffield Utd": "Sheffield United",
    "Spurs": "Tottenham Hotspur", "Tottenham": "Tottenham Hotspur", "Newcastle Utd": "Newcastle United",
    "Leicester": "Leicester City", "Leeds": "Leeds United", "Paris S-G": "Paris Saint-Germain",
    "Athletic Club": "Athletic Club de Bilbao", "Karagümrük": "VavaCars Fatih Karagümrük",
    "Gaziantep FK": "Gaziantep FK", "Hatayspor": "Atakaş Hatayspor", "Kayserispor": "Mondihome Kayserispor",
    "Konyaspor": "Tümosan Konyaspor", "Samsunspor": "Yılport Samsunspor", "Antalyaspor": "Bitexen Antalyaspor",
    "Alanyaspor": "Corendon Alanyaspor", "Adana Demirspor": "Yukatel Adana Demirspor",
    "İstanbul Başakşehir": "Medipol Başakşehir FK"
}


def get_smart_match(name, possibilities):
    """
    İsim eşleşmiyorsa, listedeki en benzer ismi bulmaya çalışır.
    Örn: "Karagümrük" -> "VavaCars Fatih Karagümrük"
    """
    if name in possibilities:
        return name

    # En yakın 1 eşleşmeyi bul (Benzerlik oranı %60 üzeri olanlar)
    matches = get_close_matches(name, possibilities, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return name  # Bulamazsa orijinalini döndür


def calculate_team_power():
    print("📊 Takım güçleri hesaplanıyor...")

    if not os.path.exists(PLAYER_FILE):
        print("❌ Hata: Oyuncu dosyası bulunamadı.")
        return None

    df_players = pd.read_csv(PLAYER_FILE)

    # Takım istatistiklerini grupla
    team_stats = df_players.groupby(['Season', 'Team', 'League']).agg({
        'Overall': 'mean', 'Finishing': 'mean', 'ShortPassing': 'mean',
        'StandingTackle': 'mean', 'SprintSpeed': 'mean', 'Stamina': 'mean'
    }).reset_index()

    team_stats.rename(columns={
        'Overall': 'Team_Overall', 'Finishing': 'Team_Attack', 'ShortPassing': 'Team_Midfield',
        'StandingTackle': 'Team_Defense', 'SprintSpeed': 'Team_Pace', 'Stamina': 'Team_Fitness'
    }, inplace=True)

    return team_stats


def create_training_set():
    print("🚀 Eğitim seti oluşturuluyor...")

    if not os.path.exists(MATCH_FILE):
        print("❌ Hata: Maç dosyası bulunamadı.")
        return

    df_matches = pd.read_csv(MATCH_FILE)
    print(f"  -> Başlangıç: {len(df_matches)} maç.")

    # --- 1. MANUEL DÜZELTME ---
    df_matches['HomeTeam'] = df_matches['HomeTeam'].replace(TEAM_MAPPING)
    df_matches['AwayTeam'] = df_matches['AwayTeam'].replace(TEAM_MAPPING)

    if 'MatchURL' in df_matches.columns:
        df_matches.drop(columns=['MatchURL'], inplace=True)

    df_team_stats = calculate_team_power()
    if df_team_stats is None: return

    # FIFA'daki Mevcut Takım İsimleri Listesi
    fifa_teams = df_team_stats['Team'].unique().tolist()

    # --- 2. AKILLI EŞLEŞTİRME (AUTO-FIX) ---
    print("🤖 Akıllı isim eşleştirme çalışıyor... (Bu biraz sürebilir)")

    # Henüz eşleşmeyen (FIFA listesinde olmayan) takımları bul
    match_teams = set(df_matches['HomeTeam'].unique()) | set(df_matches['AwayTeam'].unique())
    unknown_teams = [t for t in match_teams if t not in fifa_teams]

    # Bilinmeyenler için bir sözlük oluştur
    smart_mapping = {}
    for team in unknown_teams:
        best_match = get_smart_match(team, fifa_teams)
        if best_match != team:
            smart_mapping[team] = best_match
            # print(f"    🔗 Eşleştirildi: {team} -> {best_match}") # Merak edersen aç

    # Akıllı düzeltmeleri uygula
    df_matches['HomeTeam'] = df_matches['HomeTeam'].replace(smart_mapping)
    df_matches['AwayTeam'] = df_matches['AwayTeam'].replace(smart_mapping)

    # --- 3. BİRLEŞTİRME (MERGE) ---

    # Home Merge
    df_final = pd.merge(
        df_matches, df_team_stats,
        left_on=['Season', 'HomeTeam'], right_on=['Season', 'Team'],
        how='inner'
    )

    rename_map_home = {
        'Team_Overall': 'Home_Overall', 'Team_Attack': 'Home_Attack', 'Team_Midfield': 'Home_Midfield',
        'Team_Defense': 'Home_Defense', 'Team_Pace': 'Home_Pace', 'Team_Fitness': 'Home_Fitness'
    }
    df_final.rename(columns=rename_map_home, inplace=True)
    df_final.drop(columns=['Team', 'League_y'], axis=1, inplace=True, errors='ignore')
    if 'League_x' in df_final.columns: df_final.rename(columns={'League_x': 'League'}, inplace=True)

    # Away Merge
    df_final = pd.merge(
        df_final, df_team_stats,
        left_on=['Season', 'AwayTeam'], right_on=['Season', 'Team'],
        how='inner'
    )

    rename_map_away = {
        'Team_Overall': 'Away_Overall', 'Team_Attack': 'Away_Attack', 'Team_Midfield': 'Away_Midfield',
        'Team_Defense': 'Away_Defense', 'Team_Pace': 'Away_Pace', 'Team_Fitness': 'Away_Fitness'
    }
    df_final.rename(columns=rename_map_away, inplace=True)
    df_final.drop(columns=['Team', 'League_y'], axis=1, inplace=True, errors='ignore')
    if 'League_x' in df_final.columns: df_final.rename(columns={'League_x': 'League'}, inplace=True)

    # One Hot Encoding
    df_final = pd.get_dummies(df_final, columns=['League'], prefix='Lg')

    # Son Sütunlar
    target_cols = [
        'Season', 'Date', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG',
        'Home_Overall', 'Home_Attack', 'Home_Midfield', 'Home_Defense', 'Home_Pace',
        'Away_Overall', 'Away_Attack', 'Away_Midfield', 'Away_Defense', 'Away_Pace'
    ]
    league_cols = [c for c in df_final.columns if c.startswith('Lg_')]
    target_cols.extend(league_cols)

    final_data = df_final[target_cols].dropna()

    # Kaydet
    final_data.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ EĞİTİM VERİSİ HAZIRLANDI: {len(final_data)} maç.")
    print(f"   (Önceki: 17.307 -> Yeni: {len(final_data)})")


if __name__ == "__main__":
    create_training_set()