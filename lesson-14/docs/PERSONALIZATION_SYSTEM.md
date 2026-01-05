# 개인화 시스템 문서

## 개요

개인화 시스템은 사용자의 행동, 선호도, 피드백을 학습하여 맞춤형 경험을 제공하는 통합 시스템입니다.

## 주요 구성 요소

### 1. 사용자 행동 분석 엔진 (BehaviorAnalyzer)

사용자의 행동 패턴을 분석하여 인사이트를 제공합니다.

#### 주요 기능
- 행동 패턴 분석 (액션 빈도, 시간대, 세션 패턴)
- 거래 패턴 분석 (승률, 수익성, 선호 코인)
- 참여도 메트릭 계산
- 선호도 변화 추적

#### 사용 예제
```python
from src.personalization import BehaviorAnalyzer, UserPreferences

analyzer = BehaviorAnalyzer()
preferences = load_user_preferences(user_id)

# 종합 분석
analysis = analyzer.analyze_user_behavior(preferences, trade_history)

# 행동 인사이트
insights = analyzer.get_behavioral_insights(user_id)

# 니즈 예측
needs = analyzer.predict_user_needs(preferences, analysis)
```

### 2. 추천 시스템 (RecommendationEngine)

사용자 프로필과 행동을 기반으로 맞춤 추천을 제공합니다.

#### 추천 유형
- **전략 추천**: 리스크 성향에 맞는 거래 전략
- **코인 추천**: 투자 성향에 맞는 암호화폐
- **교육 콘텐츠 추천**: 학습 레벨에 맞는 교육 자료
- **설정 추천**: 최적화된 시스템 설정
- **액션 추천**: 수행할 작업 제안

#### 사용 예제
```python
from src.personalization import RecommendationEngine, RecommendationType

engine = RecommendationEngine()
preferences = load_user_preferences(user_id)

# 추천 받기
recommendations = engine.get_recommendations(
    preferences,
    recommendation_types=[
        RecommendationType.STRATEGY,
        RecommendationType.COIN
    ],
    limit=10
)

for rec in recommendations:
    print(f"{rec.title}: {rec.reason}")
    print(f"신뢰도: {rec.confidence:.2%}")
```

### 3. 학습 알고리즘 (LearningEngine)

머신러닝 기반으로 사용자 선호도를 학습하고 예측합니다.

#### 학습 데이터
- 행동 패턴 (액션, 시간대, 기능 사용)
- 선호도 패턴 (코인, 전략, 설정)
- 성과 패턴 (수익성 높은 전략/코인)
- 피드백 패턴 (만족도, 선호 기능)

#### 모델 특징
- 가중치 기반 학습 (행동 40%, 선호도 30%, 성과 20%, 피드백 10%)
- 신뢰도 점수 계산
- 선호도 예측

#### 사용 예제
```python
from src.personalization import LearningEngine

engine = LearningEngine()

# 모델 훈련
model = engine.train_user_model(
    user_id,
    preferences,
    trade_history,
    feedback_history
)

# 선호도 예측
predictions = engine.predict_preferences(user_id, {
    "current_hour": 14,
    "context": "trading"
})

# 학습 인사이트
insights = engine.get_learning_insights(user_id)
```

### 4. 피드백 수집 시스템 (FeedbackCollector)

사용자 피드백을 체계적으로 수집하고 분석합니다.

#### 피드백 유형
- **평점**: 항목별 1-5점 평점
- **기능 피드백**: 기능별 평가
- **추천 피드백**: 추천 수용/거부
- **개선 제안**: 시스템 개선 아이디어
- **만족도 조사**: 종합 만족도

#### 사용 예제
```python
from src.personalization import FeedbackCollector, FeedbackType

collector = FeedbackCollector()

# 평점 수집
collector.collect_rating(
    user_id="user001",
    item_type="strategy",
    item_id="volatility_breakout",
    rating=5,
    comment="매우 만족합니다!"
)

# 기능 피드백
collector.collect_feature_feedback(
    user_id="user001",
    feature="portfolio_value",
    rating=4,
    usefulness=5,
    ease_of_use=4
)

# 피드백 요약
summary = collector.get_feedback_summary(user_id)
print(f"평균 평점: {summary['average_rating']}")
```

### 5. 개인화된 대시보드 생성기 (DashboardGenerator)

사용자 선호도와 행동을 기반으로 맞춤 대시보드를 생성합니다.

#### 위젯 유형
- 포트폴리오 가치
- 손익 현황
- 최근 거래
- 시장 개요
- 가격 차트
- 성과 차트
- 추천
- 알림
- 뉴스
- 통계
- 리스크 지표
- 학습 진행도

#### 레이아웃
- **Grid**: 그리드 레이아웃 (기본)
- **List**: 리스트 레이아웃
- **Custom**: 사용자 정의 레이아웃

#### 사용 예제
```python
from src.personalization import DashboardGenerator

generator = DashboardGenerator()
preferences = load_user_preferences(user_id)

# 대시보드 생성
dashboard = generator.generate_dashboard(
    preferences,
    behavior_insights=analysis
)

print(f"위젯 수: {len(dashboard['widgets'])}")
print(f"레이아웃: {dashboard['layout']['type']}")
```

### 6. 통합 개인화 시스템 (PersonalizationSystem)

모든 개인화 기능을 통합하여 제공하는 메인 클래스입니다.

#### 주요 기능
- 사용자 초기화 및 관리
- 행동 기록 및 분석
- 맞춤 추천 제공
- 개인화된 대시보드 생성
- 피드백 수집 및 반영
- 학습 모델 관리
- 개인화 점수 계산

#### 사용 예제
```python
from src.personalization import PersonalizationSystem

# 시스템 초기화
personalization = PersonalizationSystem()

# 사용자 초기화
preferences = personalization.initialize_user("user001")

# 행동 기록
personalization.record_user_action(
    "user001",
    "view_dashboard",
    {"page": "dashboard"}
)

# 종합 분석
analysis = personalization.analyze_user("user001", trade_history)

# 추천 받기
recommendations = personalization.get_recommendations("user001")

# 대시보드 생성
dashboard = personalization.get_personalized_dashboard("user001")

# 피드백 수집
personalization.collect_feedback(
    "user001",
    FeedbackType.RATING,
    {"item_type": "strategy", "item_id": "xxx", "rating": 5}
)

# 개인화 점수
score = personalization.get_personalization_score("user001")
```

## 데이터 흐름

```
사용자 행동
    ↓
행동 기록 (record_user_action)
    ↓
행동 분석 (analyze_user)
    ↓
학습 모델 훈련 (train_user_model)
    ↓
추천 생성 (get_recommendations)
    ↓
대시보드 생성 (get_personalized_dashboard)
    ↓
피드백 수집 (collect_feedback)
    ↓
선호도 업데이트 (update_preferences)
    ↓
개인화 개선
```

## 개인화 점수

개인화 점수는 다음 요소로 계산됩니다:

1. **행동 데이터 (30점)**: 행동 기록의 충분성
2. **선호도 명확성 (25점)**: 선호 코인/전략 설정
3. **학습 모델 신뢰도 (25점)**: 모델의 신뢰도 점수
4. **피드백 참여도 (20점)**: 피드백 제공 횟수

총점에 따른 레벨:
- **Excellent (80-100)**: 매우 우수한 개인화
- **Good (60-79)**: 양호한 개인화
- **Fair (40-59)**: 보통 수준
- **Low (0-39)**: 개선 필요

## 설정 및 커스터마이징

### 선호도 설정

```python
# 투자 프로필 업데이트
personalization.update_preferences(
    user_id,
    "investment",
    risk_tolerance=RiskTolerance.HIGH,
    target_return=15.0
)

# 대시보드 설정
personalization.update_preferences(
    user_id,
    "dashboard",
    layout="grid",
    theme="dark",
    enabled_widgets=["portfolio_value", "price_chart"]
)
```

### 학습 모델 가중치 조정

```python
# 가중치 업데이트
learning_engine.update_model_weights(
    user_id,
    {
        "behavior_weight": 0.5,
        "preference_weight": 0.3,
        "performance_weight": 0.15,
        "feedback_weight": 0.05
    }
)
```

## 성능 최적화

### 캐싱
- 사용자 선호도 캐싱
- 대시보드 캐싱
- 학습 모델 캐싱

### 비동기 처리
- 학습 모델 재훈련은 비동기로 처리 가능
- 대용량 데이터 분석은 백그라운드 작업으로 처리

## 보안 및 개인정보

- 사용자 데이터는 암호화 저장
- 피드백 데이터는 익명화 가능
- 개인정보 보호 정책 준수

## 확장 가능성

### 새로운 추천 유형 추가
```python
class RecommendationType(Enum):
    # 기존 유형...
    NEWS = "news"  # 새 유형 추가

# RecommendationEngine에 새 추천 메서드 추가
def _recommend_news(self, user_preferences):
    # 구현
    pass
```

### 새로운 위젯 추가
```python
class WidgetType(Enum):
    # 기존 위젯...
    CUSTOM_ANALYTICS = "custom_analytics"  # 새 위젯 추가

# DashboardGenerator에 새 위젯 템플릿 추가
```

## 참고 자료

- [사용자 가이드](./USER_GUIDE.md)
- [API 문서](./API_DOCUMENTATION.md)
- [예제 코드](../examples/personalization_example.py)





