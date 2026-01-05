"""
멜론 최신곡 크롤링 사용 예시
"""

from melon_new_songs_crawler import MelonNewSongsCrawler
import json


def example_basic_usage():
    """기본 사용 예시"""
    print("=" * 80)
    print("예시 1: 기본 크롤링")
    print("=" * 80)
    
    crawler = MelonNewSongsCrawler()
    songs = crawler.crawl()
    
    # TOP 10 출력
    crawler.print_results(songs, limit=10)
    
    # JSON 저장
    crawler.save_to_json(songs, 'example_output.json')


def example_filter_by_artist():
    """특정 아티스트 필터링 예시"""
    print("\n" + "=" * 80)
    print("예시 2: 특정 아티스트 필터링")
    print("=" * 80)
    
    crawler = MelonNewSongsCrawler()
    songs = crawler.crawl()
    
    # 특정 아티스트만 필터링
    target_artists = ['조째즈', 'SKINZ']
    filtered = [s for s in songs if any(artist in s['artist'] for artist in target_artists)]
    
    print(f"\n'{', '.join(target_artists)}' 아티스트의 곡:")
    for song in filtered:
        print(f"  {song['rank']}위: {song['song_title']} - {song['artist']}")


def example_top_n():
    """TOP N만 추출 예시"""
    print("\n" + "=" * 80)
    print("예시 3: TOP 5만 추출")
    print("=" * 80)
    
    crawler = MelonNewSongsCrawler()
    songs = crawler.crawl()
    
    # TOP 5만 추출
    top5 = songs[:5]
    
    print("\nTOP 5:")
    for song in top5:
        print(f"  {song['rank']}위: {song['song_title']} - {song['artist']}")


def example_export_to_csv():
    """CSV로 내보내기 예시"""
    print("\n" + "=" * 80)
    print("예시 4: CSV로 내보내기")
    print("=" * 80)
    
    import csv
    from datetime import datetime
    
    crawler = MelonNewSongsCrawler()
    songs = crawler.crawl()
    
    # CSV 파일로 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'melon_new_songs_{timestamp}.csv'
    
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'rank', 'song_title', 'artist', 'album', 
            'song_id', 'album_id', 'snapshot_date'
        ])
        writer.writeheader()
        writer.writerows(songs)
    
    print(f"CSV 파일로 저장 완료: {filename}")


def example_get_song_details():
    """곡 상세 정보 가져오기 예시"""
    print("\n" + "=" * 80)
    print("예시 5: 곡 ID로 상세 정보 확인")
    print("=" * 80)
    
    crawler = MelonNewSongsCrawler()
    songs = crawler.crawl()
    
    # 첫 번째 곡의 상세 정보
    if songs:
        first_song = songs[0]
        print(f"\n첫 번째 곡 상세 정보:")
        print(f"  순위: {first_song['rank']}")
        print(f"  곡명: {first_song['song_title']}")
        print(f"  아티스트: {first_song['artist']}")
        print(f"  앨범: {first_song['album']}")
        print(f"  곡 ID: {first_song['song_id']}")
        print(f"  앨범 ID: {first_song['album_id']}")
        print(f"  앨범 이미지: {first_song['album_image']}")
        print(f"  크롤링 시간: {first_song['crawled_at']}")


if __name__ == "__main__":
    try:
        # 예시 1: 기본 사용
        example_basic_usage()
        
        # 예시 2: 아티스트 필터링
        example_filter_by_artist()
        
        # 예시 3: TOP N
        example_top_n()
        
        # 예시 4: CSV 내보내기
        example_export_to_csv()
        
        # 예시 5: 상세 정보
        example_get_song_details()
        
        print("\n" + "=" * 80)
        print("✅ 모든 예시 실행 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

