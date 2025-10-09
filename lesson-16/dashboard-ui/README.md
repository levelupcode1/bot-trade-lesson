# 🚀 CryptoAutoTrader Dashboard

Figma 디자인을 기반으로 한 암호화폐 자동매매 시스템 대시보드

## 📋 개요

이 프로젝트는 Figma MCP를 활용하여 디자인한 UI/UX를 실제 동작하는 React 웹 애플리케이션으로 구현한 것입니다.

### 주요 기능

- ✅ 실시간 가격 모니터링
- ✅ 거래 내역 추적
- ✅ 호가창 표시
- ✅ 수익률 통계
- ✅ 알림 시스템
- ✅ 반응형 디자인

## 🎨 디자인 시스템

### 색상 팔레트

| 색상 | 용도 | HEX |
|------|------|-----|
| Primary Blue | 주요 액션, 브랜드 | `#4389FA` |
| Success Green | 매수, 수익, 성공 | `#22C55E` |
| Danger Red | 매도, 손실, 경고 | `#F54336` |
| Warning Orange | 주의, 경고 | `#FF9900` |
| Background Dark | 메인 배경 | `#1C2128` |
| Background Darker | 카드 배경 | `#262C36` |

### 타이포그래피

- **Base Font**: SF Pro, -apple-system, Segoe UI
- **Mono Font**: SF Mono, Monaco
- **Font Sizes**: 10px ~ 36px (8단계)
- **Font Weights**: 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)

## 🏗️ 프로젝트 구조

```
dashboard-ui/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx          # 메인 대시보드
│   │   ├── NavigationBar.jsx      # 네비게이션 바
│   │   ├── StatsCard.jsx          # 통계 카드
│   │   ├── PriceChart.jsx         # 가격 차트
│   │   ├── OrderBook.jsx          # 호가창
│   │   ├── TradeHistory.jsx       # 거래 내역
│   │   ├── NotificationPanel.jsx  # 알림 패널
│   │   └── LoadingState.jsx       # 로딩 상태
│   ├── styles/
│   │   ├── designTokens.css       # 디자인 토큰
│   │   └── global.css             # 글로벌 스타일
│   ├── hooks/
│   │   ├── useUpbitMCP.js         # 업비트 MCP 훅
│   │   └── useWebSocket.js        # WebSocket 훅
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```

## 🚀 시작하기

### 1. 설치

```bash
cd dashboard-ui
npm install
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```env
VITE_UPBIT_ACCESS_KEY=your_access_key
VITE_UPBIT_SECRET_KEY=your_secret_key
VITE_WS_URL=wss://api.upbit.com/websocket/v1
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 열기

### 4. 빌드

```bash
npm run build
```

## 📱 반응형 디자인

### 브레이크포인트

- **Mobile**: < 768px
- **Tablet**: 768px ~ 1024px
- **Desktop**: > 1024px

### 모바일 최적화

- 터치 친화적 UI (최소 44x44px 버튼)
- 간소화된 네비게이션
- 핵심 정보 우선 표시
- 스와이프 제스처 지원

## 🎯 MCP 통합

### 업비트 MCP 연동

```jsx
import { useUpbitMCP } from './hooks/useUpbitMCP';

const Dashboard = () => {
  const { price, orderbook, loading } = useUpbitMCP('KRW-BTC');
  
  return (
    <div>
      {loading ? <LoadingState /> : <PriceDisplay price={price} />}
    </div>
  );
};
```

### MCP 서버 설정

`mcp.json`:

```json
{
  "mcpServers": {
    "upbit": {
      "command": "python",
      "args": ["../upbit_mcp_server.py"],
      "env": {
        "UPBIT_ACCESS_KEY": "...",
        "UPBIT_SECRET_KEY": "..."
      }
    }
  }
}
```

## 🎨 컴포넌트 사용법

### StatsCard

```jsx
<StatsCard
  title="총 수익률"
  value="+15.8%"
  trend="up"
  icon={<TrendingUp />}
  color="success"
/>
```

### NotificationPanel

```jsx
<NotificationPanel 
  notifications={[
    {
      type: 'success',
      title: '매수 체결 완료',
      message: 'BTC 0.015 @ 85,150,000 KRW',
      timestamp: new Date()
    }
  ]}
  onClose={() => setShowNotifications(false)}
/>
```

## 🔧 커스터마이징

### 디자인 토큰 변경

`src/styles/designTokens.css`:

```css
:root {
  --color-primary: #YOUR_COLOR;
  --font-size-base: YOUR_SIZE;
  /* ... */
}
```

### 테마 전환

```jsx
// Light Theme 활성화
document.body.classList.add('light-theme');

// Dark Theme 활성화
document.body.classList.remove('light-theme');
```

## 📊 성능 최적화

### 구현된 최적화

- ✅ React.memo를 통한 불필요한 리렌더링 방지
- ✅ Virtual Scrolling (거래 내역 테이블)
- ✅ 이미지 Lazy Loading
- ✅ Code Splitting (React.lazy)
- ✅ WebSocket 연결 풀링
- ✅ Debounced API 호출

### 성능 지표

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Lighthouse Score**: 95+

## ♿ 접근성

### WCAG 2.1 준수

- ✅ AA 등급 색상 대비 (4.5:1 이상)
- ✅ 키보드 네비게이션 지원
- ✅ Screen Reader 최적화
- ✅ Focus 상태 명확한 표시
- ✅ ARIA 레이블 적용

### 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl/Cmd + K` | 빠른 거래 |
| `Ctrl/Cmd + N` | 알림 패널 |
| `Ctrl/Cmd + ,` | 설정 |
| `Esc` | 모달/패널 닫기 |

## 🧪 테스트

### 단위 테스트

```bash
npm run test
```

### E2E 테스트

```bash
npm run test:e2e
```

### 커버리지

```bash
npm run test:coverage
```

## 📦 배포

### Vercel 배포

```bash
npm run build
vercel deploy
```

### Docker 배포

```bash
docker build -t crypto-dashboard .
docker run -p 3000:3000 crypto-dashboard
```

## 🔗 관련 링크

- [Figma 디자인](https://figma.com/file/...)
- [MCP 가이드](../MCP_GUIDE.md)
- [API 문서](../api-docs.md)
- [업비트 MCP 서버](../upbit_mcp_server.py)

## 📝 라이센스

MIT License

## 👥 기여

이슈 및 PR 환영합니다!

---

**Made with ❤️ using Figma MCP & React**

