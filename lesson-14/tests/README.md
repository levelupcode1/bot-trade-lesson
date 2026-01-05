# 테스트 가이드

개인화 시스템의 테스트 방법을 안내합니다.

## 테스트 구조

```
tests/
├── unit/                          # 단위 테스트
│   ├── test_profile.py           # 프로필 테스트
│   └── test_personalization.py   # 개인화 시스템 단위 테스트
└── integration/                   # 통합 테스트
    ├── test_system.py            # 시스템 통합 테스트
    └── test_personalization_integration.py  # 개인화 통합 테스트
```

## 테스트 실행 방법

### 1. 전체 테스트 실행

```bash
# 프로젝트 루트에서
cd lesson-14

# 모든 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=src --cov-report=html
```

### 2. 단위 테스트만 실행

```bash
# 개인화 시스템 단위 테스트
pytest tests/unit/test_personalization.py -v

# 특정 테스트 클래스만
pytest tests/unit/test_personalization.py::TestBehaviorAnalyzer -v

# 특정 테스트 메서드만
pytest tests/unit/test_personalization.py::TestBehaviorAnalyzer::test_analyze_behavior_patterns -v
```

### 3. 통합 테스트만 실행

```bash
# 개인화 시스템 통합 테스트
pytest tests/integration/test_personalization_integration.py -v

# 전체 워크플로우 테스트만
pytest tests/integration/test_personalization_integration.py::TestPersonalizationWorkflow::test_complete_personalization_workflow -v
```

### 4. 특정 패턴의 테스트 실행

```bash
# 이름에 "feedback"이 포함된 테스트만
pytest tests/ -k feedback -v

# 이름에 "dashboard"가 포함된 테스트만
pytest tests/ -k dashboard -v
```

## 테스트 커버리지 확인

```bash
# HTML 리포트 생성
pytest tests/ --cov=src/personalization --cov-report=html

# 브라우저에서 htmlcov/index.html 열기
```

## 주요 테스트 시나리오

### 1. 행동 분석 테스트
- 빈 행동 데이터 분석
- 행동 패턴 분석
- 거래 패턴 분석
- 참여도 메트릭 계산

### 2. 추천 시스템 테스트
- 전략 추천
- 코인 추천
- 교육 콘텐츠 추천
- 설정 추천

### 3. 학습 엔진 테스트
- 모델 훈련
- 선호도 예측
- 신뢰도 계산

### 4. 피드백 수집 테스트
- 평점 피드백
- 기능 피드백
- 피드백 요약

### 5. 대시보드 생성 테스트
- 기본 대시보드 생성
- 선호도 기반 대시보드
- 위젯 커스터마이징

### 6. 통합 워크플로우 테스트
- 완전한 개인화 워크플로우
- 시간에 따른 학습 개선
- 추천 품질 검증
- 피드백 통합

## 테스트 데이터

테스트는 자동으로 임시 데이터를 생성하며, 테스트 후 정리됩니다.

- 사용자 ID: `test_user_{timestamp}` 형식
- 데이터 디렉토리: `data/` 하위에 생성
- 테스트 후 정리: pytest fixture를 사용하여 자동 정리

## 디버깅

### 상세 출력

```bash
# 매우 상세한 출력
pytest tests/ -v -s

# 특정 테스트의 print 출력 보기
pytest tests/unit/test_personalization.py::TestBehaviorAnalyzer::test_analyze_behavior_patterns -v -s
```

### 실패한 테스트만 재실행

```bash
# 이전 실행에서 실패한 테스트만 재실행
pytest tests/ --lf

# 실패한 테스트와 이전 실패와 관련된 테스트 실행
pytest tests/ --ff
```

## CI/CD 통합

GitHub Actions 등에서 사용할 수 있는 예제:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ -v --cov=src --cov-report=xml
```

## 문제 해결

### ImportError 발생 시

```bash
# 프로젝트 루트에서 실행 확인
cd lesson-14
pytest tests/ -v
```

### 데이터 디렉토리 권한 오류

```bash
# 데이터 디렉토리 생성
mkdir -p data/user_preferences data/user_feedback data/learning_models
```

### 캐시 문제

```bash
# pytest 캐시 삭제
pytest --cache-clear
```

## 참고 자료

- [pytest 문서](https://docs.pytest.org/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
- [개인화 시스템 문서](../docs/PERSONALIZATION_SYSTEM.md)





