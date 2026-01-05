/**
 * n8n Code 노드용 멜론 차트 크롤링 스크립트
 * 실제 HTML 구조에 맞춘 버전 (Cheerio 없이)
 */

// HTML 추출
const html = $input.first().json.data || $input.first().json.body || $input.first().json.html || '';

if (!html) {
  throw new Error('HTML 데이터가 없습니다.');
}

const songs = [];
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

/**
 * HTML에서 텍스트 추출 헬퍼 함수
 */
function extractText(html) {
  if (!html) return '';
  return html
    .replace(/<[^>]+>/g, '') // HTML 태그 제거
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ') // 여러 공백을 하나로
    .trim();
}

/**
 * 속성 값 추출 헬퍼 함수
 */
function extractAttribute(html, attrName) {
  const regex = new RegExp(`${attrName}=["']([^"']+)["']`, 'i');
  const match = html.match(regex);
  return match ? match[1] : '';
}

// 테이블 행 찾기 (<tr> 태그)
const trPattern = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
let trMatch;
let rankCounter = 1;

while ((trMatch = trPattern.exec(html)) !== null) {
  const row = trMatch[1];
  
  try {
    // 헤더 행 스킵 (th 태그가 있거나 체크박스가 없는 경우)
    if (row.includes('<th') || !row.includes('input_check')) {
      continue;
    }
    
    // 1. 순위 추출
    let rank = 0;
    
    // 방법 1: <span class="rank ">2</span> 패턴
    const rankMatch1 = row.match(/<span[^>]*class="rank[^"]*"[^>]*>(\d+)<\/span>/i);
    if (rankMatch1) {
      rank = parseInt(rankMatch1[1]);
    }
    
    // 방법 2: 체크박스 value에서 곡 ID 추출 후 순위 카운터 사용
    if (rank === 0) {
      rank = rankCounter;
    }
    
    // 2. 곡 ID 추출
    // 체크박스 value에서 추출
    const checkboxMatch = row.match(/<input[^>]*value="(\d+)"[^>]*input_check/i);
    const songId = checkboxMatch ? checkboxMatch[1] : '';
    
    // 또는 playSong에서 추출
    const playSongMatch = row.match(/playSong\([^,]+,\s*(\d+)\)/i);
    const songIdFromPlay = playSongMatch ? playSongMatch[1] : '';
    const finalSongId = songId || songIdFromPlay;
    
    // 3. 곡명 추출
    // <a href="javascript:melon.play.playSong(...)" title="... 재생">곡명</a>
    const songTitleMatch = row.match(/<a[^>]*playSong[^>]*title="([^"]+) 재생"[^>]*>([\s\S]*?)<\/a>/i);
    let songTitle = '';
    if (songTitleMatch) {
      // title 속성에서 추출 시도
      songTitle = songTitleMatch[1] || extractText(songTitleMatch[2]);
    } else {
      // ellipsis rank01에서 추출
      const rank01Match = row.match(/<div[^>]*class="ellipsis rank01"[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)<\/a>/i);
      if (rank01Match) {
        songTitle = extractText(rank01Match[1]);
      }
    }
    
    if (!songTitle) {
      continue; // 곡명이 없으면 스킵
    }
    
    // 4. 아티스트 추출
    // <a href="javascript:melon.link.goArtistDetail('510556');" title="...">아티스트</a>
    const artistPattern = /<a[^>]*goArtistDetail[^>]*>([\s\S]*?)<\/a>/gi;
    const artists = [];
    let artistMatch;
    
    while ((artistMatch = artistPattern.exec(row)) !== null) {
      const artistText = extractText(artistMatch[1]);
      if (artistText && artistText.length > 0) {
        artists.push(artistText);
      }
    }
    
    // 중복 제거
    const uniqueArtists = [...new Set(artists)];
    const artist = uniqueArtists.join(', ');
    
    // 5. 앨범명 추출
    // <a href="javascript:melon.link.goAlbumDetail('12121264');" title="...">앨범명</a>
    const albumMatch = row.match(/<a[^>]*goAlbumDetail[^>]*title="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
    let album = '';
    if (albumMatch) {
      album = albumMatch[1] || extractText(albumMatch[2]);
    } else {
      // ellipsis rank03에서 추출
      const rank03Match = row.match(/<div[^>]*class="ellipsis rank03"[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)<\/a>/i);
      if (rank03Match) {
        album = extractText(rank03Match[1]);
      }
    }
    
    // 6. 앨범 ID 추출
    const albumIdMatch = row.match(/goAlbumDetail\(['"](\d+)['"]\)/i);
    const albumId = albumIdMatch ? albumIdMatch[1] : '';
    
    // 7. 앨범 이미지 추출
    // <img ... src="https://cdnimg.melon.co.kr/...">
    const imgMatch = row.match(/<img[^>]*src=["']([^"']+)["']/i);
    let albumImage = '';
    if (imgMatch) {
      albumImage = imgMatch[1];
      // 상대 경로를 절대 경로로 변환
      if (albumImage.startsWith('//')) {
        albumImage = 'https:' + albumImage;
      } else if (albumImage.startsWith('/')) {
        albumImage = 'https://www.melon.com' + albumImage;
      }
    }
    
    // 8. 좋아요 수 추출 (선택사항)
    const likeMatch = row.match(/<span[^>]*class="cnt"[^>]*>[\s\S]*?(\d+)[\s\S]*?<\/span>/i);
    const likeCount = likeMatch ? parseInt(likeMatch[1]) : 0;
    
    // 9. 순위 변동 추출 (있는 경우)
    // 이 HTML에는 순위 변동 정보가 없으므로 0으로 설정
    let rankChange = 0;
    
    // 순위 변동 정보가 있는 경우 (다른 페이지 구조)
    const changeMatch = row.match(/(상승|하락|진입|동일)[\s\S]*?(\d+)/i);
    if (changeMatch) {
      const type = changeMatch[1];
      const value = parseInt(changeMatch[2] || '0');
      if (type.includes('상승')) rankChange = value;
      else if (type.includes('하락')) rankChange = -value;
      else if (type.includes('진입')) rankChange = 999;
    }
    
    // 데이터 객체 생성
    songs.push({
      rank: rank,
      song_title: songTitle,
      artist: artist,
      album: album,
      album_image: albumImage,
      song_id: finalSongId,
      album_id: albumId,
      like_count: likeCount,
      rank_change: rankChange,
      snapshot_date: today,
      crawled_at: now
    });
    
    rankCounter++;
    
  } catch (error) {
    // 개별 행 처리 중 에러 발생 시 로그만 남기고 계속 진행
    console.warn(`행 처리 중 에러:`, error.message);
  }
}

// 순위별로 정렬
songs.sort((a, b) => a.rank - b.rank);

if (songs.length === 0) {
  throw new Error('추출된 곡이 없습니다. HTML 구조를 확인하세요.');
}

// n8n 형식으로 반환
return songs.map(song => ({ json: song }));

