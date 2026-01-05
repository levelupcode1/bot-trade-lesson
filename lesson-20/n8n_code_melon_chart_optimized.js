/**
 * n8n Code 노드용 멜론 차트 크롤링 스크립트 (최적화 버전)
 * 제공된 실제 HTML 구조에 최적화
 */

// HTML 추출
const html = $input.first().json.data || $input.first().json.body || '';

if (!html) {
  throw new Error('HTML 데이터가 없습니다.');
}

const songs = [];
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

// 텍스트 추출 함수
function cleanText(text) {
  return (text || '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}

// 테이블 행 추출
const rows = html.match(/<tr[^>]*>[\s\S]*?<\/tr>/gi) || [];

rows.forEach((row, index) => {
  // 체크박스가 없는 행은 스킵 (헤더 등)
  if (!row.includes('input_check')) return;
  
  try {
    // 1. 순위: <span class="rank ">2</span>
    const rankMatch = row.match(/<span[^>]*class="rank[^"]*"[^>]*>(\d+)<\/span>/i);
    const rank = rankMatch ? parseInt(rankMatch[1]) : (index + 1);
    
    // 2. 곡 ID: 체크박스 value 또는 playSong에서
    const songIdMatch = row.match(/value="(\d+)"[^>]*input_check/i) || 
                        row.match(/playSong\([^,]+,\s*(\d+)\)/i);
    const songId = songIdMatch ? songIdMatch[1] : '';
    
    // 3. 곡명: playSong 링크의 title 또는 텍스트
    const songMatch = row.match(/<a[^>]*playSong[^>]*title="([^"]+) 재생"[^>]*>([\s\S]*?)<\/a>/i) ||
                      row.match(/<div[^>]*ellipsis rank01[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)<\/a>/i);
    
    if (!songMatch) return; // 곡명이 없으면 스킵
    
    const songTitle = songMatch[1] ? songMatch[1] : cleanText(songMatch[2] || songMatch[3]);
    if (!songTitle) return;
    
    // 4. 아티스트: goArtistDetail 링크들
    const artistLinks = row.match(/<a[^>]*goArtistDetail[^>]*>([\s\S]*?)<\/a>/gi) || [];
    const artists = [...new Set(artistLinks.map(link => cleanText(link)))].filter(a => a);
    const artist = artists.join(', ');
    
    // 5. 앨범: goAlbumDetail 링크의 title 또는 텍스트
    const albumMatch = row.match(/<a[^>]*goAlbumDetail[^>]*title="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i) ||
                       row.match(/<div[^>]*ellipsis rank03[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)<\/a>/i);
    const album = albumMatch ? (albumMatch[1] || cleanText(albumMatch[2] || albumMatch[3])) : '';
    
    // 6. 앨범 ID
    const albumIdMatch = row.match(/goAlbumDetail\(['"](\d+)['"]\)/i);
    const albumId = albumIdMatch ? albumIdMatch[1] : '';
    
    // 7. 앨범 이미지
    const imgMatch = row.match(/<img[^>]*src=["']([^"']+)["']/i);
    let albumImage = imgMatch ? imgMatch[1] : '';
    if (albumImage.startsWith('//')) albumImage = 'https:' + albumImage;
    
    // 8. 좋아요 수
    const likeMatch = row.match(/<span[^>]*class="cnt"[^>]*>[\s\S]*?(\d+)/i);
    const likeCount = likeMatch ? parseInt(likeMatch[1]) : 0;
    
    songs.push({
      rank: rank,
      song_title: songTitle,
      artist: artist,
      album: album,
      album_image: albumImage,
      song_id: songId,
      album_id: albumId,
      like_count: likeCount,
      snapshot_date: today,
      crawled_at: now
    });
    
  } catch (e) {
    console.warn(`행 ${index} 처리 오류:`, e.message);
  }
});

// 순위별 정렬
songs.sort((a, b) => a.rank - b.rank);

if (songs.length === 0) {
  throw new Error('추출된 곡이 없습니다.');
}

return songs.map(song => ({ json: song }));

