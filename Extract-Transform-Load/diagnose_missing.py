import pandas as pd
import os

# --- YOL AYARLARI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

PLAYER_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_PLAYER_STATS.csv")
MATCH_FILE = os.path.join(PROCESSED_DATA_DIR, "MASTER_MATCH_STATS.csv")

# --- MEVCUT EŞLEŞTİRME SÖZLÜĞÜ (Aynısını buraya da koyuyoruz ki simülasyon doğru olsun) ---
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


def diagnose():
    print("🕵️‍♀️ KAYIP VERİLER ARANIYOR...\n")

    # Verileri Yükle
    df_players = pd.read_csv(PLAYER_FILE)
    df_matches = pd.read_csv(MATCH_FILE)

    # Manuel Eşleştirmeyi Uygula
    df_matches['HomeTeam'] = df_matches['HomeTeam'].replace(TEAM_MAPPING)

    # Takım ve Sezon Bazında FIFA Verisi Var mı?
    # FIFA veritabanındaki (Takım, Sezon) çiftlerini bir sete atıyoruz
    fifa_keys = set(zip(df_players['Team'], df_players['Season']))

    # Kayıp Maçları Bul
    missing_stats = []

    for index, row in df_matches.iterrows():
        team = row['HomeTeam']
        season = row['Season']

        # Bu Takım+Sezon kombinasyonu FIFA dosyasında var mı?
        if (team, season) not in fifa_keys:
            missing_stats.append({'Team': team, 'Season': season})

    if not missing_stats:
        print("✅ Müjde! Hiçbir eksik takım yok. Kodda birleştirme (merge) mantığını kontrol etmeliyiz.")
        return

    df_missing = pd.DataFrame(missing_stats)

    # Özet Rapor
    print(f"Toplam {len(df_missing)} maç, takımların FIFA verisi olmadığı için siliniyor.")
    print("-" * 60)
    print("EN ÇOK VERİSİ EKSİK OLAN TAKIMLAR (Ve Sezonları):")

    # Hangi takımlar en çok eksik?
    missing_counts = df_missing['Team'].value_counts().head(30)
    for team, count in missing_counts.items():
        seasons = df_missing[df_missing['Team'] == team]['Season'].unique()
        print(f"❌ {team:<25} -> {count} Maç Kayıp | Sezonlar: {', '.join(seasons)}")

    print("-" * 60)
    print("NEDEN OLABİLİR?")
    print("1. Takım ismi hala eşleşmiyor olabilir (FIFA'da farklı yazılıyordur).")
    print("2. O sezon takım FIFA oyununda lisanslı değildir (Örn: Serie A'da Juventus -> Piemonte Calcio).")
    print("3. Takım o sezon FIFA veritabanında yoktur (Alt ligden yeni çıkmıştır vs).")


if __name__ == "__main__":
    diagnose()