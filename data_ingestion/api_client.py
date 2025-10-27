import configparser
import requests
import os


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


# Bu dosya doğrudan çalıştırıldığında bağlantıyı test etmesi için:
if __name__ == '__main__':
    test_api_connection()