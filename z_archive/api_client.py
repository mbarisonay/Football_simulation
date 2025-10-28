import configparser
import requests
import os
import json


def get_api_key():
    """Projenin ana dizinindeki config.ini dosyasından API anahtarını okur."""

    # Bu dosyanın (api_client.py) tam yolunu al: C:/.../data_ingestion/api_client.py
    current_file_path = os.path.abspath(__file__)

    # Bir üst dizine çık (data_ingestion): C:/.../data_ingestion
    data_ingestion_dir = os.path.dirname(current_file_path)

    # Bir üst dizine daha çık (projenin ana dizini): C:/.../
    project_root = os.path.dirname(data_ingestion_dir)

    # config.ini dosyasının tam yolunu oluştur: C:/.../config.ini
    config_path = os.path.join(project_root, 'config.ini')

    # Şimdi tam yol ile oku
    config = configparser.ConfigParser()
    config.read(config_path)

    if 'api' in config and 'api_key' in config['api']:
        return config['api']['api_key']
    else:
        raise Exception(f"config.ini dosyasında [api] bölümü veya api_key bulunamadı. Kontrol edin: {config_path}")

# API'nin ana adresi ve gerekli başlık (header) bilgisi
API_URL = "https://v3.football.api-sports.io"
API_KEY = get_api_key()

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}


def test_api_connection():
    """API bağlantısını basit bir istekle test eder."""

    # API'nin durumunu kontrol eden bir endpoint'e (uç nokta) istek atalım.
    response = requests.get(f"{API_URL}/status", headers=HEADERS)

    if response.status_code == 200:
        print("API bağlantısı başarılı!")
        print("Hesap Bilgileri:", response.json()['response'])
    else:
        print("API bağlantısı başarısız. Durum Kodu:", response.status_code)
        print("Gelen Cevap:", response.text)


def get_teams_by_league_and_season(league_id, season):
    """
    Belirtilen lig ve sezondaki tüm takımların bilgilerini API'den çeker.
    :param league_id: API'nin lig için belirlediği ID (Örn: Premier League için 39)
    :param season: Sezon yılı (Örn: 2023)
    :return: Takım bilgilerini içeren bir liste veya hata durumunda None
    """
    endpoint = "/teams"
    params = {'league': league_id, 'season': season}

    print(f"{league_id} ID'li ligin {season} sezonu için takımlar çekiliyor...")

    response = requests.get(API_URL + endpoint, headers=HEADERS, params=params)

    if response.status_code == 200:
        print("Takım verileri başarıyla çekildi.")
        api_response = response.json()['response']

        # API'den gelen karmaşık veriyi basitleştirelim
        teams_list = []
        for item in api_response:
            team_info = {
                'api_takim_id': item['team']['id'],
                'takim_adi': item['team']['name'],
                'ulke': item['team']['country']
            }
            teams_list.append(team_info)
        return teams_list
    else:
        print(f"Hata! Veri çekilemedi. Durum Kodu: {response.status_code}")
        print("Gelen Cevap:", response.text)
        return None


def get_fixtures_by_league_and_season(league_id, season):
    """
    Belirtilen lig ve sezondaki tüm maçların TEMEL sonuçlarını çeker.
    """
    endpoint = "/fixtures"
    params = {'league': league_id, 'season': season}

    print(f"-> {season} sezonu için temel maç verileri çekiliyor...")

    response = requests.get(API_URL + endpoint, headers=HEADERS, params=params)

    if response.status_code == 200:
        api_response = response.json()['response']

        matches_list = []
        for fixture in api_response:
            # Sadece bitmiş maçları alalım
            if fixture['fixture']['status']['short'] == 'FT':
                match_info = {
                    'api_mac_id': fixture['fixture']['id'],
                    'hafta': int(fixture['league']['round'].split(' - ')[-1]),
                    'mac_tarihi': fixture['fixture']['date'],
                    'ev_sahibi_takim_id': fixture['teams']['home']['id'],
                    'deplasman_takim_id': fixture['teams']['away']['id'],
                    'ev_sahibi_gol': fixture['goals']['home'],
                    'deplasman_gol': fixture['goals']['away']
                }
                matches_list.append(match_info)

        print(f"-> {len(matches_list)} adet tamamlanmış maç bulundu.")
        return matches_list
    else:
        print(f"Hata! Maç verisi çekilemedi. Durum Kodu: {response.status_code}")
        return None


def get_statistics_by_fixture(fixture_id):
    """
    Tek bir maçın ID'sini kullanarak o maça ait detaylı istatistikleri çeker.
    :param fixture_id: API'nin maça verdiği benzersiz ID.
    :return: İstatistikleri içeren bir sözlük veya hata durumunda None.
    """
    endpoint = "/fixtures/statistics"
    params = {'fixture': fixture_id}

    # Bu fonksiyon çok sık çağrılacağı için print mesajı eklemiyoruz, ana script yönetecek.
    response = requests.get(API_URL + endpoint, headers=HEADERS, params=params)

    if response.status_code == 200:
        api_response = response.json()['response']

        # API bazen boş yanıt dönebilir, kontrol edelim
        if not api_response:
            return None

        home_team_id = api_response[0]['team']['id']
        home_stats = api_response[0]['statistics']
        away_stats = api_response[1]['statistics']

        # Veriyi ayıklayıp temiz bir sözlük formatında döndürelim
        stats_data = {
            'api_mac_id': fixture_id,
            'ev_sahibi_sut': next((s.get('value') for s in home_stats if s.get('type') == 'Total Shots'), None),
            'deplasman_sut': next((s.get('value') for s in away_stats if s.get('type') == 'Total Shots'), None),
            'ev_sahibi_isabetli_sut': next((s.get('value') for s in home_stats if s.get('type') == 'Shots on Goal'),
                                           None),
            'deplasman_isabetli_sut': next((s.get('value') for s in away_stats if s.get('type') == 'Shots on Goal'),
                                           None),
            'ev_sahibi_korner': next((s.get('value') for s in home_stats if s.get('type') == 'Corner Kicks'), None),
            'deplasman_korner': next((s.get('value') for s in away_stats if s.get('type') == 'Corner Kicks'), None)
        }
        return stats_data
    else:
        # Hata durumunda, hatayı ve hangi maç ID'sinde olduğunu belirtelim
        print(f"Hata! {fixture_id} ID'li maç için istatistik çekilemedi. Durum Kodu: {response.status_code}")
        return None

# Bu dosya doğrudan çalıştırıldığında bağlantıyı test etmesi için:
if __name__ == '__main__':
    test_api_connection()