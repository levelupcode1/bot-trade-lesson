/**
 * n8n Code 노드용 멜론 차트 크롤링 (간단 버전 - 정규표현식만 사용)
 * Cheerio 없이 순수 JavaScript로 HTML 파싱
 */

// HTML 추출
const html = $input.first().json.data || $input.first().json.body || '';

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
  return html
    .replace(/<[^>]+>/g, '') // HTML 태그 제거
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, ' ')
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

// 테이블 행 찾기
const rowPattern = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
let rowMatch;
let rankCounter = 1;

while ((rowMatch = rowPattern.exec(html)) !== null) {
  const row = rowMatch[1];
  
  // 헤더 스킵
  if (row.includes('<th')) continue;
  
  // 순위 찾기
  let rank = 0;
  const rankPatterns = [
    /<td[^>]*class="rank"[^>]*>[\s\S]*?(\d+)/i,
    /<td[^>]*>[\s\S]*?(\d+)[\s\S]*?위/i,
    /(\d+)위/i
  ];
  
  for (const pattern of rankPatterns) {
    const match = row.match(pattern);
    if (match) {
      rank = parseInt(match[1]);
      break;
    }
  }
  
  // 순위를 찾지 못했지만 곡명이 있으면 카운터 사용
  if (rank === 0) {
    rank = rankCounter;
  }
  
  // 곡명 찾기
  const songLinkPattern = /<a[^>]*href[^>]*goSongDetail[^>]*>([\s\S]*?)<\/a>/i;
  const songMatch = row.match(songLinkPattern);
  
  if (!songMatch) continue;
  
  const songTitle = extractText(songMatch[1]);
  if (!songTitle) continue;
  
  // 곡 ID
  const songIdMatch = row.match(/goSongDetail\(['"](\d+)['"]\)/i) || 
                      row.match(/songId=(\d+)/i);
  const songId = songIdMatch ? songIdMatch[1] : '';
  
  // 아티스트 찾기
  const artistPattern = /<a[^>]*href[^>]*goArtistDetail[^>]*>([\s\S]*?)<\/a>/gi;
  const artistMatches = [];
  let artistMatch;
  
  while ((artistMatch = artistPattern.exec(row)) !== null) {
    const artistText = extractText(artistMatch[1]);
    if (artistText) {
      artistMatches.push(artistText);
    }
  }
  const artist = artistMatches.join(', ');
  
  // 앨범 찾기
  const albumPattern = /<a[^>]*href[^>]*goAlbumDetail[^>]*>([\s\S]*?)<\/a>/i;
  const albumMatch = row.match(albumPattern);
  const album = albumMatch ? extractText(albumMatch[1]) : '';
  
  // 앨범 ID
  const albumIdMatch = row.match(/goAlbumDetail\(['"](\d+)['"]\)/i) ||
                       row.match(/albumId=(\d+)/i);
  const albumId = albumIdMatch ? albumIdMatch[1] : '';
  
  // 앨범 이미지
  const imgMatch = row.match(/<img[^>]*src=["']([^"']+)["']/i);
  let albumImage = imgMatch ? imgMatch[1] : '';
  if (albumImage && albumImage.startsWith('//')) {
    albumImage = 'https:' + albumImage;
  }
  
  // 순위 변동
  let rankChange = 0;
  const changeMatch = row.match(/(상승|하락|진입|동일)[\s\S]*?(\d+)/i);
  if (changeMatch) {
    const type = changeMatch[1];
    const value = parseInt(changeMatch[2] || '0');
    if (type.includes('상승')) rankChange = value;
    else if (type.includes('하락')) rankChange = -value;
    else if (type.includes('진입')) rankChange = 999;
  }
  
  songs.push({
    rank: rank,
    song_title: songTitle,
    artist: artist,
    album: album,
    album_image: albumImage,
    song_id: songId,
    album_id: albumId,
    rank_change: rankChange,
    snapshot_date: today,
    crawled_at: now
  });
  
  rankCounter++;
}

// 정렬
songs.sort((a, b) => a.rank - b.rank);

// 결과 반환
return songs.map(song => ({ json: song }));

