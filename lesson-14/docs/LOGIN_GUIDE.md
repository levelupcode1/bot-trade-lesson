# 프로필별 로그인 가이드

## 로그인 방법

### 1. 웹 인터페이스를 통한 로그인

#### 기본 로그인 절차

1. **웹 서버 실행**
   ```bash
   cd lesson-14
   python -m src.ui.web.app
   ```

2. **브라우저에서 접속**
   ```
   http://localhost:5000/login
   ```

3. **로그인 정보 입력**
   - **사용자 ID**: 원하는 사용자 ID 입력 (예: `user001`, `beginner_user`)
   - **사용자 유형**: 카드를 클릭하여 선택
     - 🌱 초보자: 안전하고 단순한 거래
     - 📊 중급자: 균형잡힌 거래 전략
     - 🎯 고급자: 완전한 제어와 커스터마이징
   - **투자 금액**: 투자할 금액 입력 (최소 100,000원)

4. **시작하기 버튼 클릭**

#### 프로필별 로그인 예제

**초보자로 로그인:**
```
사용자 ID: beginner001
사용자 유형: 🌱 초보자 선택
투자 금액: 1,000,000원
```

**중급자로 로그인:**
```
사용자 ID: intermediate001
사용자 유형: 📊 중급자 선택
투자 금액: 5,000,000원
```

**고급자로 로그인:**
```
사용자 ID: advanced001
사용자 유형: 🎯 고급자 선택
투자 금액: 10,000,000원
```

### 2. 기존 프로필로 로그인

이미 생성된 프로필이 있는 경우:
- 동일한 사용자 ID로 로그인하면 기존 프로필이 로드됩니다
- 프로필 타입은 변경되지 않습니다 (업그레이드 API 사용 필요)

### 3. 프로그래밍 방식 로그인

```python
from src.user.profile.profile_manager import ProfileManager, UserType
from src.personalization import PersonalizationSystem

# 프로필 관리자
profile_manager = ProfileManager()

# 프로필 생성 또는 로드
user_id = "user001"
profile = profile_manager.load_profile(user_id)

if not profile:
    # 새 프로필 생성
    profile = profile_manager.create_profile(
        user_id=user_id,
        user_type=UserType.BEGINNER,  # 또는 INTERMEDIATE, ADVANCED
        investment_amount=1000000
    )

# 개인화 시스템 초기화
personalization = PersonalizationSystem()
preferences = personalization.initialize_user(user_id)

print(f"로그인 완료: {user_id} ({profile.user_type.value})")
```

## 프로필별 차이점

### 🌱 초보자 프로필

**로그인 후 제공되는 기능:**
- 기본 거래 기능
- 단순한 대시보드 (3개 위젯)
- 제한된 전략 선택
- 안전한 거래 제한

**대시보드 위젯:**
- 포트폴리오 가치
- 손익 현황
- 최근 거래

**거래 제한:**
- 최대 포지션: 15%
- 일일 거래 한도: 3회
- 허용 코인: BTC, ETH만

### 📊 중급자 프로필

**로그인 후 제공되는 기능:**
- 고급 거래 기능
- 확장된 대시보드 (4개 이상 위젯)
- 다양한 전략 선택
- 분석 도구

**대시보드 위젯:**
- 포트폴리오 가치
- 손익 현황
- 최근 거래
- 리스크 지표
- 시장 개요 (선택)
- 성과 차트 (선택)

**거래 제한:**
- 최대 포지션: 30%
- 일일 거래 한도: 10회
- 허용 코인: TOP 30 코인

### 🎯 고급자 프로필

**로그인 후 제공되는 기능:**
- 모든 기능 접근
- 전문가용 대시보드 (모든 위젯 사용 가능)
- 커스텀 전략
- API 직접 접근

**대시보드 위젯:**
- 모든 기본 위젯
- 통계 위젯 (고급 전용)
- 리스크 지표
- 시장 개요
- 성과 차트
- 기타 고급 위젯

**거래 제한:**
- 최대 포지션: 80% (사용자 정의)
- 일일 거래 한도: 무제한
- 허용 코인: 모든 KRW 마켓

## 개인화 시스템과 통합

로그인 후 개인화 시스템을 사용하려면:

```python
from src.personalization import PersonalizationSystem

# 개인화 시스템 초기화
personalization = PersonalizationSystem()

# 사용자 초기화 (로그인 시 자동으로 수행됨)
preferences = personalization.initialize_user(user_id)

# 개인화된 대시보드 가져오기
dashboard = personalization.get_personalized_dashboard(user_id)

# 맞춤 추천 받기
recommendations = personalization.get_recommendations(user_id)
```

## 로그아웃

웹 인터페이스에서:
```
http://localhost:5000/logout
```

또는 프로그래밍 방식:
```python
# 세션 클리어 (웹 애플리케이션에서)
session.clear()
```

## 프로필 업그레이드

초보자 → 중급자 → 고급자로 업그레이드:

**웹 인터페이스:**
```
POST /api/upgrade_profile
```

**프로그래밍 방식:**
```python
from src.user.profile.profile_manager import ProfileManager

profile_manager = ProfileManager()
new_profile = profile_manager.upgrade_profile(user_id)

if new_profile:
    print(f"업그레이드 완료: {new_profile.user_type.value}")
```

## 문제 해결

### 기존 프로필이 로드되지 않는 경우

```python
# 프로필 파일 확인
import os
from pathlib import Path

profile_file = Path("data/user_profiles") / f"{user_id}.json"
if profile_file.exists():
    print(f"프로필 파일 존재: {profile_file}")
else:
    print("프로필 파일이 없습니다. 새로 생성합니다.")
```

### 프로필 타입 변경

기존 프로필의 타입을 변경하려면:
1. 프로필 파일 삭제 또는 백업
2. 새로운 타입으로 재로그인

또는 업그레이드 API 사용:
```python
profile_manager.upgrade_profile(user_id)
```

## 보안 고려사항

1. **프로덕션 환경에서는:**
   - 비밀번호 인증 추가
   - 세션 암호화
   - HTTPS 사용
   - SECRET_KEY 환경변수로 설정

2. **개발 환경:**
   - 현재는 간단한 사용자 ID 기반 인증
   - 프로덕션 배포 전 보안 강화 필요

## 예제 시나리오

### 시나리오 1: 초보자가 처음 로그인

```
1. 웹 브라우저에서 http://localhost:5000/login 접속
2. 사용자 ID: "newbie001" 입력
3. 🌱 초보자 카드 클릭
4. 투자 금액: 1,000,000원 입력
5. 시작하기 클릭
6. 초보자용 대시보드 표시 (3개 위젯)
```

### 시나리오 2: 중급자가 재로그인

```
1. 웹 브라우저에서 http://localhost:5000/login 접속
2. 기존 사용자 ID: "intermediate001" 입력
3. 📊 중급자 카드 클릭 (기존 프로필 유지)
4. 시작하기 클릭
5. 중급자용 대시보드 표시 (4개 이상 위젯)
6. 이전 설정 및 선호도 유지
```

### 시나리오 3: 고급자로 업그레이드

```
1. 기존 중급자로 로그인
2. 프로필 설정 페이지에서 업그레이드 요청
3. POST /api/upgrade_profile 호출
4. 고급자 프로필로 업그레이드
5. 고급자용 대시보드 및 기능 활성화
```

## 참고 자료

- [사용자 가이드](./USER_GUIDE.md)
- [개인화 시스템 문서](./PERSONALIZATION_SYSTEM.md)
- [API 문서](./API_DOCUMENTATION.md)





