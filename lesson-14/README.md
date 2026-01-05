# 사용자 맞춤형 자동매매 시스템

사용자의 투자 경험과 리스크 성향에 따라 자동으로 맞춤화되는 암호화폐 자동매매 시스템입니다.

## 🎯 주요 특징

### 1. 사용자 유형별 맞춤화
- **🌱 초보자**: 안전한 거래 환경과 단순한 인터페이스
- **📊 중급자**: 균형잡힌 기능과 유연한 설정
- **🎯 고급자**: 완전한 제어와 고급 기능

### 2. 동적 기능 로딩
- 사용자 프로필에 따라 자동으로 기능 활성화/비활성화
- 전략 레지스트리를 통한 동적 전략 로딩
- 플러그인 방식의 확장 가능한 구조

### 3. 권한 기반 접근 제어
- 세분화된 권한 관리 시스템
- 기능별 접근 제어
- 안전한 액션 검증

### 4. 설정 기반 커스터마이징
- YAML 기반 설정 관리
- 프로필별 독립적인 설정
- 동적 설정 변경 지원

### 5. 사용자별 인터페이스
- 프로필에 최적화된 UI/UX
- 반응형 웹 인터페이스
- 직관적인 대시보드

### 6. 🎨 개인화 시스템 (NEW!)
- **사용자 행동 분석**: 행동 패턴 분석 및 인사이트 제공
- **맞춤 추천**: 전략, 코인, 교육 콘텐츠 추천
- **학습 알고리즘**: 머신러닝 기반 선호도 학습
- **피드백 수집**: 체계적인 피드백 수집 및 반영
- **개인화된 대시보드**: 사용자 맞춤 대시보드 자동 생성

## 📁 프로젝트 구조

```
lesson-14/
├── src/
│   ├── user/                  # 사용자 관리
│   │   ├── profile/          # 프로필 시스템
│   │   │   ├── user_profile.py
│   │   │   ├── beginner_profile.py
│   │   │   ├── intermediate_profile.py
│   │   │   ├── advanced_profile.py
│   │   │   └── profile_manager.py
│   │   └── auth/             # 권한 관리
│   │       └── authorization.py
│   │
│   ├── personalization/      # 개인화 시스템 (NEW!)
│   │   ├── behavior_analyzer.py      # 행동 분석
│   │   ├── recommendation_engine.py   # 추천 시스템
│   │   ├── learning_engine.py         # 학습 알고리즘
│   │   ├── feedback_collector.py     # 피드백 수집
│   │   ├── dashboard_generator.py     # 대시보드 생성
│   │   ├── personalization_system.py  # 통합 시스템
│   │   └── user_preferences.py        # 선호도 관리
│   │
│   ├── strategy/              # 전략 시스템
│   │   ├── basic/            # 기본 전략
│   │   ├── advanced/         # 고급 전략
│   │   ├── expert/           # 전문 전략
│   │   ├── strategy_registry.py
│   │   └── strategy_loader.py
│   │
│   ├── config/                # 설정 관리
│   │   └── config_manager.py
│   │
│   └── ui/                    # 사용자 인터페이스
│       └── web/              # 웹 인터페이스
│           ├── app.py
│           └── templates/
│
├── config/                    # 설정 파일
│   ├── profiles/             # 프로필별 설정
│   │   ├── beginner.yaml
│   │   ├── intermediate.yaml
│   │   └── advanced.yaml
│   └── features/             # 기능 플래그
│       └── feature_flags.yaml
│
├── tests/                     # 테스트
│   ├── unit/                 # 단위 테스트
│   └── integration/          # 통합 테스트
│
├── examples/                  # 예제 코드
│   ├── basic_usage.py
│   └── personalization_example.py  # 개인화 시스템 예제
│
└── data/                      # 데이터
    ├── user_profiles/        # 사용자 프로필 저장소
    ├── user_preferences/     # 사용자 선호도 저장소
    ├── user_feedback/        # 피드백 저장소
    └── learning_models/      # 학습 모델 저장소
```

## 🚀 시작하기

### 1. 설치

```bash
# 프로젝트 디렉토리로 이동
cd lesson-14

# 의존성 설치
pip install -r requirements.txt
```

### 2. 기본 사용 예제 실행

```bash
# 기본 사용 예제
python examples/basic_usage.py

# 개인화 시스템 예제 (NEW!)
python examples/personalization_example.py
```

### 3. 웹 인터페이스 실행

```bash
# Flask 웹 서버 시작
python -m src.ui.web.app

# 브라우저에서 접속
# http://localhost:5000
```

## 📖 사용 방법

### 프로필 생성 및 관리

```python
from src.user.profile.profile_manager import ProfileManager
from src.user.profile.user_profile import UserType

# 프로필 관리자 생성
profile_manager = ProfileManager()

# 초보자 프로필 생성
beginner = profile_manager.create_profile(
    user_id="user001",
    user_type=UserType.BEGINNER,
    investment_amount=1000000  # 100만원
)

# 프로필 로드
profile = profile_manager.load_profile("user001")

# 프로필 업그레이드 (초보 -> 중급 -> 고급)
upgraded = profile_manager.upgrade_profile("user001")
```

### 권한 확인

```python
from src.user.auth.authorization import Authorization

authorization = Authorization()

# 기능 접근 가능 여부 확인
can_access = authorization.check_permission(profile, "create_custom_strategy")

# 사용 가능한 기능 목록
available_features = authorization.get_available_features(profile)
```

### 전략 로딩 및 사용

```python
from src.strategy.strategy_loader import StrategyLoader

# 전략 로더 생성
strategy_loader = StrategyLoader()

# 모든 전략 로드
strategy_loader.load_all_strategies()

# 프로필에 허용된 전략 목록
strategies = strategy_loader.get_strategies_for_profile(profile)

# 전략 인스턴스 생성
strategy = strategy_loader.create_strategy_instance(
    strategy_name="simple_buy_hold",
    profile=profile,
    target_return=0.05
)
```

### 거래 검증

```python
# 거래 정보
trade_info = {
    "coin": "KRW-BTC",
    "position_size": 0.10  # 10%
}

# 거래 유효성 검증
is_valid, error_msg = profile.validate_trade(trade_info)

if is_valid:
    print("거래 가능!")
else:
    print(f"거래 불가: {error_msg}")
```

## 📊 사용자 유형별 특징

### 🌱 초보자 (Beginner)

**거래 제한:**
- 최대 포지션: 15%
- 일일 거래 한도: 3회
- 손절 라인: -3% (고정)
- 현금 보유: 최소 50%

**허용 기능:**
- 기본 거래
- 백테스트
- 모의 거래

**허용 코인:**
- BTC, ETH만

**UI 특징:**
- 단순하고 큰 글자
- 모든 항목에 툴팁
- 튜토리얼 모드

---

### 📊 중급자 (Intermediate)

**거래 제한:**
- 최대 포지션: 30%
- 일일 거래 한도: 10회
- 손절 라인: -7% (조정 가능)
- 현금 보유: 최소 30%

**허용 기능:**
- 기본 거래
- 커스텀 전략
- 고급 분석
- 포트폴리오 관리

**허용 코인:**
- TOP 30 코인

**UI 특징:**
- 다중 컬럼 레이아웃
- 기술적 지표
- 성과 차트

---

### 🎯 고급자 (Advanced)

**거래 제한:**
- 최대 포지션: 80% (사용자 정의 가능)
- 일일 거래 한도: 무제한
- 손절 라인: 사용자 정의
- 현금 보유: 최소 10%

**허용 기능:**
- 모든 기본/고급 기능
- API 직접 접근
- ML 모델 사용
- 코드 실행
- 커스텀 전략 업로드

**허용 코인:**
- 모든 KRW 마켓

**UI 특징:**
- 전문가용 레이아웃
- 코드 에디터
- 터미널 접근
- 다중 모니터 지원

## 🧪 테스트

### 빠른 테스트 실행

```bash
# 전체 테스트
python run_tests.py

# 단위 테스트만
python run_tests.py unit

# 통합 테스트만
python run_tests.py integration

# 개인화 시스템 테스트만
python run_tests.py personalization

# 커버리지 포함
python run_tests.py coverage
```

### 상세 테스트 실행

```bash
# 단위 테스트 실행
pytest tests/unit/ -v

# 통합 테스트 실행
pytest tests/integration/ -v

# 개인화 시스템 단위 테스트
pytest tests/unit/test_personalization.py -v

# 개인화 시스템 통합 테스트
pytest tests/integration/test_personalization_integration.py -v

# 전체 테스트 실행 (커버리지 포함)
pytest tests/ -v --cov=src --cov-report=html
```

### 테스트 가이드

자세한 테스트 방법은 [테스트 가이드](./tests/README.md)를 참고하세요.

## ⚙️ 설정

### 프로필별 설정 수정

`config/profiles/{user_type}.yaml` 파일을 편집하여 프로필별 기본 설정을 변경할 수 있습니다.

```yaml
# config/profiles/beginner.yaml

trading:
  max_position_size: 0.15
  stop_loss: -0.03
  
ui:
  complexity_level: simple
  show_tooltips: true
  
notifications:
  all_trades: true
```

### 기능 플래그 설정

`config/features/feature_flags.yaml` 파일에서 전체 시스템의 기능을 활성화/비활성화할 수 있습니다.

```yaml
# config/features/feature_flags.yaml

basic_trading: true
custom_strategies: true
api_access: true
ml_models: false  # ML 기능 비활성화
```

## 🔧 확장

### 커스텀 전략 추가

1. 새 전략 클래스 생성:

```python
from src.strategy.strategy_registry import BaseStrategy, register_strategy

@register_strategy(
    name="my_custom_strategy",
    level="advanced",
    description="나만의 전략"
)
class MyCustomStrategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        # 전략 로직 구현
        pass
```

2. 전략 파일을 `src/strategy/advanced/` 또는 `src/strategy/expert/`에 저장

3. 시스템 재시작 시 자동 로드

### 새로운 프로필 유형 추가

1. `UserType` enum에 새 타입 추가
2. 새 프로필 클래스 생성 (`UserProfile` 상속)
3. `ProfileManager.PROFILE_CLASSES`에 등록
4. 설정 파일 생성 (`config/profiles/{type}.yaml`)

## 📈 성과 지표

시스템은 다음 지표를 추적합니다:

- **수익률**: 일간/주간/월간 수익률
- **승률**: 전체 거래 중 수익 거래 비율
- **최대 낙폭(MDD)**: 최고점 대비 최저점
- **샤프 비율**: 위험 대비 수익률
- **거래 횟수**: 일간/주간/월간 거래 횟수

## 🔒 보안

### API 키 관리
- 환경변수 또는 암호화된 설정 파일 사용
- 절대 코드에 직접 입력하지 마세요

### 권한 관리
- 최소 권한 원칙 적용
- 프로필별 접근 제어
- 모든 액션 검증

## 📚 참고 자료

- [사용자 가이드](./USER_GUIDE.md)
- [API 문서](./API_DOCUMENTATION.md)
- [개발자 가이드](./DEVELOPER_GUIDE.md)
- [개인화 시스템 문서](./docs/PERSONALIZATION_SYSTEM.md) (NEW!)

## 🤝 기여

이 프로젝트는 교육 목적으로 만들어졌습니다. 
개선 사항이나 버그 발견 시 이슈를 등록해주세요.

## ⚠️ 면책 조항

이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 
실제 자금을 사용한 거래는 높은 위험을 수반하며, 
투자 손실에 대한 책임은 사용자 본인에게 있습니다.

## 📝 라이선스

MIT License

---

**Made with ❤️ for crypto traders**

