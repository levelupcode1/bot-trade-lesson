"""
멜론 최신곡 크롤링 스크립트
https://www.melon.com/new/index.htm 페이지에서 최신곡 순위 리스트를 가져옵니다.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict
import time


class MelonNewSongsCrawler:
    """멜론 최신곡 크롤러 클래스"""
    
    def __init__(self):
        self.base_url = "https://www.melon.com/new/index.htm"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.melon.com/'
        }
    
    def get_page(self) -> BeautifulSoup:
        """멜론 최신곡 페이지를 가져옵니다."""
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"페이지 요청 오류: {e}")
            raise
    
    def extract_song_data(self, row) -> Dict:
        """테이블 행에서 곡 데이터를 추출합니다."""
        import re
        try:
            # NO (순위) - 여러 방법 시도
            rank = 0
            
            # 방법 1: td.no 클래스
            no_cell = row.find('td', class_='no')
            if no_cell:
                rank_text = no_cell.get_text(strip=True)
                rank_match = re.search(r'(\d+)', rank_text)
                if rank_match:
                    rank = int(rank_match.group(1))
            
            # 방법 2: 첫 번째 td에서 추출
            if rank == 0:
                first_td = row.find('td')
                if first_td:
                    rank_text = first_td.get_text(strip=True)
                    # "1위", "1", "NO 1" 등 다양한 형식 처리
                    rank_match = re.search(r'(\d+)', rank_text)
                    if rank_match:
                        rank = int(rank_match.group(1))
            
            # 방법 3: 모든 td를 확인하여 숫자만 있는 셀 찾기
            if rank == 0:
                tds = row.find_all('td')
                for td in tds[:3]:  # 처음 3개만 확인
                    text = td.get_text(strip=True)
                    # 숫자만 있는 경우 (1~100 사이)
                    if re.match(r'^\d+$', text):
                        num = int(text)
                        if 1 <= num <= 100:
                            rank = num
                            break
            
            # 순위가 없어도 곡명이 있으면 계속 진행 (순위는 나중에 카운터로 설정)
            
            # 곡명 - goSongDetail 링크에서 추출
            song_title = ""
            song_id = ""
            
            # 방법 1: href에 goSongDetail이 있는 링크
            song_links = row.find_all('a', href=lambda x: x and 'goSongDetail' in str(x))
            if not song_links:
                # 방법 2: onclick에 goSongDetail이 있는 경우
                song_links = row.find_all('a', onclick=lambda x: x and 'goSongDetail' in str(x))
            
            if song_links:
                # 첫 번째 링크가 곡명일 가능성이 높음
                song_link = song_links[0]
                song_title = song_link.get_text(strip=True)
                
                # 곡 ID 추출 - href 또는 onclick에서
                href = song_link.get('href', '') or song_link.get('onclick', '')
                song_id_match = re.search(r"goSongDetail\('(\d+)'\)", str(href))
                if song_id_match:
                    song_id = song_id_match.group(1)
            
            # 곡명이 없으면 None 반환
            if not song_title:
                return None
            
            # 아티스트 - goArtistDetail 링크에서 추출
            artist = ""
            artist_links = row.find_all('a', href=lambda x: x and 'goArtistDetail' in str(x))
            if not artist_links:
                artist_links = row.find_all('a', onclick=lambda x: x and 'goArtistDetail' in str(x))
            
            if artist_links:
                # 첫 번째 아티스트 링크
                artist = artist_links[0].get_text(strip=True)
                # 여러 아티스트인 경우 처리
                if len(artist_links) > 1:
                    artists = [link.get_text(strip=True) for link in artist_links if link.get_text(strip=True)]
                    artist = ", ".join(artists)
            
            # 앨범명 - goAlbumDetail 링크에서 추출
            album = ""
            album_id = ""
            album_links = row.find_all('a', href=lambda x: x and 'goAlbumDetail' in str(x))
            if not album_links:
                album_links = row.find_all('a', onclick=lambda x: x and 'goAlbumDetail' in str(x))
            
            if album_links:
                album_link = album_links[0]
                album = album_link.get_text(strip=True)
                # 앨범 ID 추출
                href = album_link.get('href', '') or album_link.get('onclick', '')
                album_id_match = re.search(r"goAlbumDetail\('(\d+)'\)", str(href))
                if album_id_match:
                    album_id = album_id_match.group(1)
            
            # 앨범 이미지
            album_image = ""
            img_tag = row.find('img')
            if img_tag:
                album_image = img_tag.get('src', '')
                # 상대 경로를 절대 경로로 변환
                if album_image.startswith('//'):
                    album_image = 'https:' + album_image
                elif album_image.startswith('/'):
                    album_image = 'https://www.melon.com' + album_image
            
            return {
                'rank': rank,  # 0일 수 있음 (나중에 카운터로 설정)
                'song_title': song_title,
                'artist': artist,
                'album': album,
                'album_image': album_image,
                'song_id': song_id,
                'album_id': album_id
            }
        except Exception as e:
            print(f"데이터 추출 오류: {e}")
            return None
    
    def crawl(self) -> List[Dict]:
        """최신곡 리스트를 크롤링합니다."""
        print(f"멜론 최신곡 페이지 크롤링 시작: {self.base_url}")
        
        soup = self.get_page()
        songs = []
        
        # 디버깅: HTML 구조 확인용 (필요시 주석 해제)
        # with open('debug_html.html', 'w', encoding='utf-8') as f:
        #     f.write(soup.prettify())
        
        # 테이블에서 곡 리스트 찾기
        # 멜론 최신곡 페이지의 테이블 구조에 맞게 선택자 수정
        table = soup.find('table', class_='list')
        if not table:
            # 대체 선택자 시도
            table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            print(f"총 {len(rows)}개의 행을 찾았습니다.")
            
            # 디버깅: 첫 번째 데이터 행 확인
            data_rows = [r for r in rows if not r.find('th')]
            if data_rows:
                print(f"데이터 행 {len(data_rows)}개 발견")
                # 첫 번째 행 구조 확인
                first_row = data_rows[0]
                tds = first_row.find_all('td')
                print(f"첫 번째 행의 td 개수: {len(tds)}")
                for i, td in enumerate(tds[:5]):  # 처음 5개만
                    print(f"  td[{i}]: {td.get_text(strip=True)[:50]}")
            
            rank_counter = 1  # 순위 카운터 (순위를 찾지 못할 경우 사용)
            
            for row in rows:
                # 헤더 행 스킵
                if row.find('th'):
                    continue
                
                song_data = self.extract_song_data(row)
                
                # 순위를 찾지 못한 경우 카운터 사용
                if song_data:
                    if song_data.get('rank', 0) == 0:
                        song_data['rank'] = rank_counter
                        rank_counter += 1
                    
                    # 곡명이 있으면 추가
                    if song_data.get('song_title'):
                        # 타임스탬프 추가
                        song_data['crawled_at'] = datetime.now().isoformat()
                        song_data['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
                        songs.append(song_data)
                        rank_counter += 1
        else:
            # 테이블이 없을 경우 다른 방법 시도
            print("테이블을 찾을 수 없습니다. 대체 방법을 시도합니다...")
            songs = self._extract_alternative_method(soup)
        
        print(f"총 {len(songs)}개의 곡을 추출했습니다.")
        return songs
    
    def _extract_alternative_method(self, soup: BeautifulSoup) -> List[Dict]:
        """대체 방법으로 데이터 추출"""
        import re
        songs = []
        
        # 곡 링크로 직접 추출
        song_links = soup.find_all('a', href=lambda x: x and 'goSongDetail' in str(x))
        if not song_links:
            song_links = soup.find_all('a', onclick=lambda x: x and 'goSongDetail' in str(x))
        
        rank = 1
        for link in song_links:
            song_title = link.get_text(strip=True)
            if song_title:
                # 곡 ID 추출
                href = link.get('href', '') or link.get('onclick', '')
                song_id_match = re.search(r"goSongDetail\('(\d+)'\)", str(href))
                song_id = song_id_match.group(1) if song_id_match else ''
                
                # 같은 행에서 다른 정보 찾기
                row = link.find_parent('tr')
                artist = ''
                album = ''
                album_id = ''
                album_image = ''
                
                if row:
                    # 아티스트
                    artist_link = row.find('a', href=lambda x: x and 'goArtistDetail' in str(x))
                    if artist_link:
                        artist = artist_link.get_text(strip=True)
                    
                    # 앨범
                    album_link = row.find('a', href=lambda x: x and 'goAlbumDetail' in str(x))
                    if album_link:
                        album = album_link.get_text(strip=True)
                        href = album_link.get('href', '') or album_link.get('onclick', '')
                        album_id_match = re.search(r"goAlbumDetail\('(\d+)'\)", str(href))
                        if album_id_match:
                            album_id = album_id_match.group(1)
                    
                    # 이미지
                    img = row.find('img')
                    if img:
                        album_image = img.get('src', '')
                
                songs.append({
                    'rank': rank,
                    'song_title': song_title,
                    'artist': artist,
                    'album': album,
                    'album_image': album_image,
                    'song_id': song_id,
                    'album_id': album_id,
                    'crawled_at': datetime.now().isoformat(),
                    'snapshot_date': datetime.now().strftime('%Y-%m-%d')
                })
                rank += 1
        
        return songs
    
    def save_to_json(self, songs: List[Dict], filename: str = None):
        """결과를 JSON 파일로 저장합니다."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'melon_new_songs_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)
        
        print(f"결과를 {filename}에 저장했습니다.")
    
    def print_results(self, songs: List[Dict], limit: int = 10):
        """결과를 출력합니다."""
        print(f"\n{'='*80}")
        print(f"멜론 최신곡 TOP {min(limit, len(songs))}")
        print(f"{'='*80}")
        print(f"{'순위':<5} {'곡명':<30} {'아티스트':<20} {'앨범':<25}")
        print(f"{'-'*80}")
        
        for song in songs[:limit]:
            print(f"{song['rank']:<5} {song['song_title']:<30} {song['artist']:<20} {song['album']:<25}")
        
        if len(songs) > limit:
            print(f"\n... 외 {len(songs) - limit}개")


def main():
    """메인 함수"""
    crawler = MelonNewSongsCrawler()
    
    try:
        # 크롤링 실행
        songs = crawler.crawl()
        
        if songs:
            # 결과 출력
            crawler.print_results(songs, limit=20)
            
            # JSON 파일로 저장
            crawler.save_to_json(songs)
            
            print(f"\n✅ 크롤링 완료: 총 {len(songs)}개 곡")
        else:
            print("❌ 추출된 곡이 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

