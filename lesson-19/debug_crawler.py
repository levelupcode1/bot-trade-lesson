"""
디버깅용 크롤러 - HTML 구조 확인
"""

import requests
from bs4 import BeautifulSoup
import json


def debug_html_structure():
    """HTML 구조를 분석하여 실제 선택자를 찾습니다."""
    url = "https://www.melon.com/new/index.htm"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.melon.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HTML 저장
        with open('debug_html.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("✅ HTML을 debug_html.html에 저장했습니다.")
        
        # 테이블 찾기
        print("\n=== 테이블 찾기 ===")
        tables = soup.find_all('table')
        print(f"총 {len(tables)}개의 테이블을 찾았습니다.")
        
        for i, table in enumerate(tables):
            print(f"\n테이블 {i+1}:")
            print(f"  class: {table.get('class')}")
            print(f"  id: {table.get('id')}")
            rows = table.find_all('tr')
            print(f"  행 개수: {len(rows)}")
            
            # 첫 번째 데이터 행 확인
            data_rows = [r for r in rows if not r.find('th')]
            if data_rows:
                first_row = data_rows[0]
                tds = first_row.find_all('td')
                print(f"  첫 번째 데이터 행의 td 개수: {len(tds)}")
                for j, td in enumerate(tds):
                    text = td.get_text(strip=True)
                    print(f"    td[{j}]: {text[:60]}")
                    
                    # 링크 확인
                    links = td.find_all('a')
                    for link in links:
                        href = link.get('href', '') or link.get('onclick', '')
                        link_text = link.get_text(strip=True)
                        if 'goSongDetail' in str(href) or 'goArtistDetail' in str(href) or 'goAlbumDetail' in str(href):
                            print(f"      -> 링크: {link_text[:40]} | href: {str(href)[:60]}")
        
        # 곡 링크 직접 찾기
        print("\n=== 곡 링크 직접 찾기 ===")
        song_links = soup.find_all('a', href=lambda x: x and 'goSongDetail' in str(x))
        if not song_links:
            song_links = soup.find_all('a', onclick=lambda x: x and 'goSongDetail' in str(x))
        
        print(f"총 {len(song_links)}개의 곡 링크를 찾았습니다.")
        for i, link in enumerate(song_links[:5]):  # 처음 5개만
            text = link.get_text(strip=True)
            href = link.get('href', '') or link.get('onclick', '')
            print(f"  {i+1}. {text[:50]} | {str(href)[:80]}")
        
        # 아티스트 링크
        print("\n=== 아티스트 링크 ===")
        artist_links = soup.find_all('a', href=lambda x: x and 'goArtistDetail' in str(x))
        if not artist_links:
            artist_links = soup.find_all('a', onclick=lambda x: x and 'goArtistDetail' in str(x))
        print(f"총 {len(artist_links)}개의 아티스트 링크를 찾았습니다.")
        
        # 앨범 링크
        print("\n=== 앨범 링크 ===")
        album_links = soup.find_all('a', href=lambda x: x and 'goAlbumDetail' in str(x))
        if not album_links:
            album_links = soup.find_all('a', onclick=lambda x: x and 'goAlbumDetail' in str(x))
        print(f"총 {len(album_links)}개의 앨범 링크를 찾았습니다.")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_html_structure()

