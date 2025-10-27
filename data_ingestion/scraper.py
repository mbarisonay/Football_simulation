# data_ingestion/scraper.py (Yorum Temizleme ve Çalışan Son Versiyon)

import requests
from bs4 import BeautifulSoup, Comment
import time


def scrape_fbref_season(season_start_year):
    """
    FBref.com'dan belirtilen sezonun Premier Lig maç sonuçlarını çeker.
    Bu versiyon, JavaScript tarafından gizlenen yorumlanmış HTML'i temizler.
    :param season_start_year: Sezonun başlangıç yılı (örn: 2022-2023 sezonu için 2022)
    """

    season_str = f"{season_start_year}-{season_start_year + 1}"
    url = f"https://fbref.com/en/comps/9/{season_str}/schedule/{season_str}-Premier-League-Scores-and-Fixtures"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    print(f"{season_str} sezonu için FBref'ten veri çekiliyor...")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"URL çekilemedi: {e}")
        return None

    # BeautifulSoup'u kullanarak tüm HTML'i ayrıştır
    soup = BeautifulSoup(response.text, 'html.parser')

    # Sayfa içindeki tüm yorumları (Comment) bul
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    table_html = ""
    # Aradığımız tabloyu içeren yorumu bul
    for comment in comments:
        if "Scores & Fixtures" in comment:
            # Yorumu temizleyip içindeki HTML'i al
            table_html = comment
            break

    if not table_html:
        print("Maç tablosunu içeren yorum bloğu bulunamadı.")
        return None

    # Sadece yorumun içindeki HTML'i tekrar BeautifulSoup ile ayrıştır
    table_soup = BeautifulSoup(table_html, 'html.parser')

    # Şimdi tabloyu bu temizlenmiş HTML içinde arayabiliriz
    # ID değişmiş olabilir, bu yüzden daha genel bir arama yapalım: class='stats_table'
    table = table_soup.find('table', class_='stats_table')

    if not table or not table.tbody:
        print("Maç tablosu veya tbody bölümü bulunamadı.")
        return None

    matches = []

    for row in table.tbody.find_all('tr'):
        cells = row.find_all('td')

        if len(cells) < 5 or not cells[3].get_text(strip=True):
            continue

        home_team = cells[2].get_text(strip=True)
        score_text = cells[3].get_text(strip=True)
        away_team = cells[4].get_text(strip=True)

        if '–' in score_text:
            score = score_text.split('–')
            try:
                match_data = {
                    'hafta': cells[0].get_text(strip=True),
                    'ev_sahibi': home_team,
                    'deplasman': away_team,
                    'ev_sahibi_gol': int(score[0]),
                    'deplasman_gol': int(score[1])
                }
                matches.append(match_data)
            except (ValueError, IndexError):
                print(f"Hatalı skor formatı, atlanıyor: {score_text}")
                continue

    print(f"{len(matches)} adet maç başarıyla çekildi.")
    return matches


if __name__ == '__main__':
    scraped_matches = scrape_fbref_season(2022)
    if scraped_matches:
        for match in scraped_matches[:5]:
            print(match)