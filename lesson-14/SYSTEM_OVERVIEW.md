# 시스템 개요

사용자 맞춤형 자동매매 시스템의 전체 아키텍처와 핵심 컴포넌트 설명입니다.

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 인터페이스 계층                      │
│  ┌─────────┬─────────┬─────────┬───────────────────┐        │
│  │초보자 UI│중급자 UI│고급자 UI│  REST API Gateway │        │
│  └─────────┴─────────┴─────────┴───────────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 권한 & 프로필 관리 계층                       │
│  ┌────────────┬────────────┬─────────────────────┐          │
│  │사용자 프로필│ 권한 관리자 │  기능 게이트웨이    │          │
│  └────────────┴────────────┴─────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    비즈니스 로직 계층                         │
│  ┌──────────────────────────────────────────────┐           │
│  │         코어 서비스 (공통)                    │           │
│  │  ┌──────┬──────┬──────┬──────┐              │           │
│  │  │거래  │데이터│리스크│알림  │              │           │
│  │  └──────┴──────┴──────┴──────┘              │           │
│  └──────────────────────────────────────────────┘           │
│  ┌──────────────────────────────────────────────┐           │
│  │       사용자별 서비스 (맞춤형)                │           │
│  │  ┌──────┬──────┬──────┬──────┐              │           │
│  │  │전략  │포트폴│분석  │학습  │              │           │
│  │  └──────┴──────┴──────┴──────┘              │           │
│  └──────────────────────────────────────────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                   데이터 접근 계층                            │
│  ┌──────┬──────┬──────┬──────────────┐                     │
│  │거래소│데이터│캐시  │파일 시스템    │                     │
│  │ API  │베이스│(Redis)│(Config/Logs) │                     │
│  └──────┴──────┴──────┴──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 핵심 컴포넌트

### 1. 사용자 프로필 시스템

#### UserProfile (추상 베이스 클래스)
- 모든 프로필의 기본 인터페이스
- 공통 속성 및 메서드 정의
- 확장 가능한 구조

#### BeginnerProfile (초보자)
- 보수적 거래 제한
- 단순한 기능
- 높은 안전성

#### IntermediateProfile (중급자)
- 균형잡힌 제한
- 고급 기능 일부 제공
- 유연한 설정

#### AdvancedProfile (고급자)
- 최소한의 제한
- 모든 기능 접근
- 완전한 커스터마이징

#### ProfileManager
- 프로필 생성, 로드, 저장
- 프로필 업그레이드
- 프로필 캐싱

### 2. 권한 관리 시스템

#### Permission (Enum)
```python
class Permission(Enum):
    # 기본 권한
    VIEW_DASHBOARD = "view_dashboard"
    PLACE_ORDER = "place_order"
    VIEW_HISTORY = "view_history"
    
    # 중급 권한
    CUSTOM_STRATEGY = "custom_strategy"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    
    # 고급 권한
    API_ACCESS = "api_access"
    ML_MODELS = "ml_models"
    CODE_EXECUTION = "code_execution"
```

#### FeatureGate
- 기능별 권한 매핑
- 사용자 유형별 권한 정의
- 접근 제어 데코레이터

#### Authorization
- 권한 확인
- 사용 가능한 기능 목록
- 액션 검증

### 3. 동적 기능 로딩 시스템

#### StrategyRegistry
- 전략 등록 및 관리
- 메타데이터 저장
- 레벨별 전략 분류

#### StrategyLoader
- 디렉토리 기반 자동 로드
- 동적 모듈 임포트
- 프로필별 전략 필터링
- 커스텀 전략 로드

#### BaseStrategy
- 모든 전략의 인터페이스
- 표준화된 실행 메서드
- 전략 등록 데코레이터

### 4. 설정 관리 시스템

#### ConfigManager
- YAML 기반 설정 관리
- 프로필별 설정 로드
- 기능 플래그 관리
- 동적 설정 업데이트

#### ProfileConfig
- 설정 값 읽기/쓰기
- 중첩 키 지원
- 딕셔너리 변환

### 5. 사용자 인터페이스

#### Flask Web Application
- 프로필별 라우팅
- 세션 관리
- REST API 엔드포인트

#### Templates
- 초보자용 템플릿 (단순)
- 중급자용 템플릿 (균형)
- 고급자용 템플릿 (전문)

## 데이터 흐름

### 1. 프로필 생성 흐름

```
사용자 입력
    ↓
ProfileManager.create_profile()
    ↓
UserType에 따라 프로필 클래스 선택
    ↓
프로필 인스턴스 생성
    ↓
설정 초기화
    ↓
JSON 파일로 저장
    ↓
캐시에 저장
    ↓
프로필 반환
```

### 2. 권한 확인 흐름

```
액션 요청
    ↓
Authorization.check_permission()
    ↓
FeatureGate.can_access_feature()
    ↓
필요한 권한 조회
    ↓
사용자 권한 확인
    ↓
결과 반환 (True/False)
```

### 3. 전략 로딩 흐름

```
시스템 시작
    ↓
StrategyLoader.load_all_strategies()
    ↓
각 디렉토리 스캔 (basic, advanced, expert)
    ↓
Python 파일 동적 임포트
    ↓
BaseStrategy 상속 클래스 찾기
    ↓
StrategyRegistry에 등록
    ↓
메타데이터 저장
```

### 4. 거래 실행 흐름

```
거래 요청
    ↓
profile.validate_trade()
    ↓
포지션 크기 확인
    ↓
허용 코인 확인
    ↓
일일 거래 한도 확인
    ↓
authorization.validate_action()
    ↓
권한 확인
    ↓
거래 실행 or 거부
```

## 확장 포인트

### 1. 새 프로필 유형 추가

```python
class ExpertProfile(UserProfile):
    def __init__(self, user_id, investment_amount):
        super().__init__(
            user_id, UserType.EXPERT,
            RiskLevel.VERY_AGGRESSIVE,
            investment_amount
        )
    
    # 모든 추상 메서드 구현
```

### 2. 새 전략 추가

```python
@register_strategy(
    name="my_new_strategy",
    level="advanced",
    description="새로운 전략"
)
class MyNewStrategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        # 전략 로직
        pass
```

### 3. 새 권한 추가

```python
class Permission(Enum):
    # ... 기존 권한 ...
    NEW_FEATURE = "new_feature"

# FeatureGate.FEATURE_PERMISSIONS에 추가
FEATURE_PERMISSIONS = {
    "use_new_feature": [Permission.NEW_FEATURE]
}

# FeatureGate.USER_TYPE_PERMISSIONS에 추가
USER_TYPE_PERMISSIONS = {
    UserType.ADVANCED: [
        # ... 기존 권한 ...
        Permission.NEW_FEATURE
    ]
}
```

### 4. 새 설정 추가

```yaml
# config/profiles/beginner.yaml
new_feature:
  enabled: true
  parameter1: value1
  parameter2: value2
```

## 성능 고려사항

### 캐싱
- 프로필 캐싱 (메모리)
- 설정 캐싱
- 전략 레지스트리 캐싱

### 최적화
- 지연 로딩 (Lazy Loading)
- 동적 임포트
- 효율적인 데이터 구조

### 확장성
- 모듈화된 구조
- 플러그인 아키텍처
- 느슨한 결합

## 보안 고려사항

### 입력 검증
- 모든 사용자 입력 검증
- 타입 체크
- 범위 제한

### 권한 관리
- 최소 권한 원칙
- 역할 기반 접근 제어
- 액션 검증

### 데이터 보호
- API 키 암호화
- 민감한 데이터 보호
- 안전한 세션 관리

## 테스트 전략

### 단위 테스트
- 각 클래스 개별 테스트
- 메서드별 테스트
- 엣지 케이스 테스트

### 통합 테스트
- 컴포넌트 간 상호작용
- 전체 워크플로우
- 시나리오 기반 테스트

### E2E 테스트
- 사용자 시나리오
- 웹 인터페이스
- API 엔드포인트

---

**시스템 버전: 1.0.0**
**최종 업데이트: 2025-10-08**

