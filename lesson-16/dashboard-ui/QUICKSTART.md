# 🚀 빠른 시작 가이드

## 설치 및 실행

### 1. 패키지 설치

```bash
cd lesson-16/dashboard-ui
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저가 자동으로 열리며 `http://localhost:5173`에서 대시보드를 확인할 수 있습니다.

### 3. 빌드

```bash
npm run build
```

빌드된 파일은 `dist/` 폴더에 생성됩니다.

## 문제 해결

### 포트 5173이 이미 사용 중인 경우

다른 포트로 실행:

```bash
npm run dev -- --port 3000
```

### 패키지 설치 오류

캐시 삭제 후 재설치:

```bash
rm -rf node_modules package-lock.json
npm install
```

### 화면이 표시되지 않는 경우

1. 개발자 도구(F12) 열기
2. Console 탭에서 오류 확인
3. 브라우저 새로고침 (Ctrl+F5)

## 현재 구현 상태

✅ 완료:
- 네비게이션 바
- 통계 카드 (3개)
- 디자인 시스템 (CSS Variables)
- 반응형 레이아웃

🚧 진행 중:
- 가격 차트
- 호가창
- 거래 내역 테이블
- 알림 패널

## 다음 단계

1. MCP 서버 연동
2. 실시간 데이터 표시
3. 차트 컴포넌트 추가
4. 알림 시스템 구현

