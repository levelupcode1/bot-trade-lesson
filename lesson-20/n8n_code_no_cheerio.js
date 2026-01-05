/**
 * n8n Code 노드용 멜론 차트 크롤링 스크립트 (Cheerio 없이)
 * 순수 JavaScript로 HTML 파싱
 */

// 입력 데이터에서 HTML 추출
const inputData = $input.first().json;
const html = inputData.data || inputData.body || inputData.html || '';

if (!html) {
  throw new Error('HTML 데이터가 없습니다.');
}

// 결과 배열
const songs = [];
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

/**
 * 정규표현식을 사용하여 HTML에서 데이터 추출
 */

// 테이블 행 추출 (tbody tr 태그)
const trRegex = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
const rows = [];
let trMatch;

while ((trMatch = trRegex.exec(html)) !== null) {
  const rowHtml = trMatch[1];
  
  // 헤더 행 스킵 (th 태그가 있으면 스킵)
  if (rowHtml.includes('<th')) {
    continue;
  }
  
  rows.push(rowHtml);
}

// 각 행에서 데이터 추출
rows.forEach((rowHtml, index) => {
  try {
    // 순위 추출
    const rankMatch = rowHtml.match(/<td[^>]*class="rank"[^>]*>[\s\S]*?(\d+)[\s\S]*?<\/td>/i) ||
                     rowHtml.match(/<td[^>]*>[\s\S]*?(\d+)[\s\S]*?위[\s\S]*?<\/td>/i) ||
                     rowHtml.match(/<td[^>]*>[\s\S]*?(\d+)[\s\S]*?<\/td>/);
    
    if (!rankMatch) {
      return; // 순위를 찾을 수 없으면 스킵
    }
    
    const rank = parseInt(rankMatch[1]);
    if (rank === 0 || rank > 100) {
      return; // 유효하지 않은 순위
    }
    
    // 곡명 추출 (goSongDetail 링크)
    const songLinkMatch = rowHtml.match(/<a[^>]*href[^>]*goSongDetail[^>]*>([\s\S]*?)<\/a>/i);
    if (!songLinkMatch) {
      return; // 곡명을 찾을 수 없으면 스킵
    }
    
    // HTML 태그 제거하여 텍스트만 추출
    const songTitle = songLinkMatch[1]
      .replace(/<[^>]+>/g, '') // HTML 태그 제거
      .replace(/&nbsp;/g, ' ') // &nbsp; 제거
      .replace(/\s+/g, ' ') // 여러 공백을 하나로
      .trim();
    
    if (!songTitle || songTitle.length === 0) {
      return;
    }
    
    // 곡 ID 추출
    const songHrefMatch = rowHtml.match(/goSongDetail\(['"](\d+)['"]\)/i) ||
                          rowHtml.match(/songId=(\d+)/i);
    const songId = songHrefMatch ? songHrefMatch[1] : '';
    
    // 아티스트 추출 (goArtistDetail 링크)
    const artistMatches = rowHtml.match(/<a[^>]*href[^>]*goArtistDetail[^>]*>([\s\S]*?)<\/a>/gi);
    let artist = '';
    if (artistMatches) {
      const artists = artistMatches.map(match => {
        return match.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim();
      }).filter(a => a.length > 0);
      artist = artists.join(', ');
    }
    
    // 앨범 추출 (goAlbumDetail 링크)
    const albumMatch = rowHtml.match(/<a[^>]*href[^>]*goAlbumDetail[^>]*>([\s\S]*?)<\/a>/i);
    let album = '';
    if (albumMatch) {
      album = albumMatch[1]
        .replace(/<[^>]+>/g, '')
        .replace(/&nbsp;/g, ' ')
        .trim();
    }
    
    // 앨범 ID 추출
    const albumHrefMatch = rowHtml.match(/goAlbumDetail\(['"](\d+)['"]\)/i) ||
                           rowHtml.match(/albumId=(\d+)/i);
    const albumId = albumHrefMatch ? albumHrefMatch[1] : '';
    
    // 앨범 이미지 추출
    const imgMatch = rowHtml.match(/<img[^>]*src=["']([^"']+)["'][^>]*>/i);
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
    
    // 순위 변동 추출
    let rankChange = 0;
    const changeMatch = rowHtml.match(/순위\s*(상승|하락|진입|동일)[\s\S]*?(\d+)/i) ||
                        rowHtml.match(/(상승|하락|진입)[\s\S]*?(\d+)/i);
    
    if (changeMatch) {
      const changeType = changeMatch[1];
      const changeValue = parseInt(changeMatch[2] || '0');
      
      if (changeType.includes('상승')) {
        rankChange = changeValue;
      } else if (changeType.includes('하락')) {
        rankChange = -changeValue;
      } else if (changeType.includes('진입')) {
        rankChange = 999; // 신규 진입 표시
      }
    }
    
    // 데이터 객체 생성
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
    
  } catch (error) {
    // 개별 행 처리 중 에러 발생 시 로그만 남기고 계속 진행
    console.warn(`행 ${index + 1} 처리 중 에러:`, error.message);
  }
});

// 순위별로 정렬
songs.sort((a, b) => a.rank - b.rank);

if (songs.length === 0) {
  throw new Error('추출된 곡이 없습니다. HTML 구조를 확인하세요.');
}

// n8n 형식으로 반환
return songs.map(song => ({ json: song }));

