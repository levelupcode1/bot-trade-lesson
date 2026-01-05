/**
 * n8n Code 노드용 멜론 최신곡 크롤링 스크립트
 * https://www.melon.com/new/index.htm
 * 
 * 사용 방법:
 * 1. HTTP Request 노드에서 멜론 최신곡 페이지 가져오기
 * 2. Code 노드에서 이 스크립트 실행
 * 3. 결과를 Set 노드나 Database 노드로 전달
 */

const cheerio = require('cheerio');

try {
  // 입력 데이터에서 HTML 추출
  const inputData = $input.first().json;
  const html = inputData.data || inputData.body || inputData.html || '';
  
  if (!html) {
    throw new Error('HTML 데이터가 없습니다.');
  }
  
  // HTML 파싱
  const $ = cheerio.load(html);
  
  // 결과 배열
  const songs = [];
  const today = new Date().toISOString().split('T')[0];
  const now = new Date().toISOString();
  
  // 테이블에서 곡 리스트 추출
  // 멜론 최신곡 페이지의 테이블 구조
  const table = $('table.list, table').first();
  
  if (table.length === 0) {
    throw new Error('테이블을 찾을 수 없습니다.');
  }
  
  // 테이블 행 추출
  table.find('tbody tr, tr').each((index, element) => {
    const $row = $(element);
    
    // 헤더 행 스킵
    if ($row.find('th').length > 0) {
      return;
    }
    
    // NO (순위) 추출
    const noText = $row.find('td.no').text().trim() || 
                   $row.find('td:first-child').text().trim();
    const rankMatch = noText.match(/(\d+)/);
    const rank = rankMatch ? parseInt(rankMatch[1]) : 0;
    
    if (rank === 0) {
      return; // 순위가 없으면 스킵
    }
    
    // 곡명 추출
    const songLink = $row.find('a[href*="goSongDetail"]').first();
    const songTitle = songLink.text().trim();
    
    if (!songTitle) {
      return; // 곡명이 없으면 스킵
    }
    
    // 곡 ID 추출
    const songHref = songLink.attr('href') || '';
    const songIdMatch = songHref.match(/goSongDetail\('(\d+)'\)/);
    const songId = songIdMatch ? songIdMatch[1] : '';
    
    // 아티스트 추출
    const artistLink = $row.find('a[href*="goArtistDetail"]').first();
    const artist = artistLink.text().trim();
    
    // 앨범명 추출
    const albumLink = $row.find('a[href*="goAlbumDetail"]').first();
    const album = albumLink.text().trim();
    
    // 앨범 ID 추출
    const albumHref = albumLink.attr('href') || '';
    const albumIdMatch = albumHref.match(/goAlbumDetail\('(\d+)'\)/);
    const albumId = albumIdMatch ? albumIdMatch[1] : '';
    
    // 앨범 이미지 추출
    const albumImage = $row.find('img').attr('src') || '';
    
    songs.push({
      rank: rank,
      song_title: songTitle,
      artist: artist,
      album: album,
      album_image: albumImage,
      song_id: songId,
      album_id: albumId,
      snapshot_date: today,
      crawled_at: now
    });
  });
  
  // 대체 방법: 테이블을 찾지 못한 경우
  if (songs.length === 0) {
    console.log('테이블 방법 실패, 대체 방법 시도...');
    
    // 곡 링크로 직접 추출
    $('a[href*="goSongDetail"]').each((index, element) => {
      const $link = $(element);
      const songTitle = $link.text().trim();
      
      if (songTitle) {
        const href = $link.attr('href') || '';
        const songIdMatch = href.match(/goSongDetail\('(\d+)'\)/);
        const songId = songIdMatch ? songIdMatch[1] : '';
        
        // 같은 행에서 아티스트 찾기
        const $row = $link.closest('tr');
        const artist = $row.find('a[href*="goArtistDetail"]').first().text().trim();
        const album = $row.find('a[href*="goAlbumDetail"]').first().text().trim();
        
        songs.push({
          rank: index + 1,
          song_title: songTitle,
          artist: artist,
          album: album,
          album_image: '',
          song_id: songId,
          album_id: '',
          snapshot_date: today,
          crawled_at: now
        });
      }
    });
  }
  
  if (songs.length === 0) {
    throw new Error('추출된 곡이 없습니다.');
  }
  
  // 순위별로 정렬
  songs.sort((a, b) => a.rank - b.rank);
  
  // n8n 형식으로 반환
  return songs.map(song => ({ json: song }));
  
} catch (error) {
  console.error('크롤링 에러:', error.message);
  return [{
    json: {
      error: true,
      error_message: error.message,
      timestamp: new Date().toISOString()
    }
  }];
}

