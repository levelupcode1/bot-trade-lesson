# 📦 설치 가이드

## 빠른 설치 (권장)

### 1단계: 가상환경 활성화
```bash
cd lesson-13
..\bot-env\Scripts\activate  # Windows
```

### 2단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 3단계: 설치 확인
```bash
python quick_test.py
```

---

## 상세 설치 가이드

### Python 버전 확인
```bash
python --version
# Python 3.8 이상 필요
```

### 핵심 패키지 설치

#### 1. 기본 패키지 (필수)
```bash
pip install pandas numpy scipy scikit-learn
```

#### 2. 최적화 라이브러리 (필수)
```bash
pip install bayesian-optimization hyperopt optuna
```

#### 3. 시각화 (필수)
```bash
pip install matplotlib plotly seaborn
```

#### 4. 성능 분석 (필수)
```bash
pip install quantstats statsmodels
```

#### 5. 유틸리티 (필수)
```bash
pip install pyyaml python-dotenv tqdm joblib colorlog cerberus
```

#### 6. 기술적 지표 (필수)
```bash
pip install ta PyWavelets
```

#### 7. 기타 (선택)
```bash
pip install yfinance
```

---

## 문제 해결

### ❌ 오류: empyrical 설치 실패

**증상:**
```
AttributeError: module 'configparser' has no attribute 'SafeConfigParser'
```

**해결:**
- `empyrical`과 `pyfolio`는 제거되었습니다
- 대신 `quantstats`가 사용됩니다
- requirements.txt를 사용하면 문제없음

### ❌ 오류: TA-Lib 설치 실패

**해결:**
- TA-Lib는 **선택사항**입니다
- 설치하지 않아도 시스템이 작동합니다
- pandas로 기술적 지표를 계산할 수 있습니다

**정말 필요한 경우:**
- Windows: [whl 파일 다운로드](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
- macOS: `brew install ta-lib`
- Linux: 소스 컴파일 필요 (권장하지 않음)

### ❌ 오류: Microsoft Visual C++ 필요

**Windows에서 일부 패키지 설치 시:**
```bash
# Microsoft C++ Build Tools 설치
https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

또는:
```bash
# 미리 컴파일된 버전 설치
pip install --only-binary :all: scipy scikit-learn
```

### ❌ 오류: 메모리 부족

**해결:**
```bash
# 한 번에 하나씩 설치
pip install pandas
pip install numpy
pip install scipy
# ...
```

### ❌ 오류: 권한 문제

**Windows:**
```bash
# 관리자 권한으로 실행하거나
pip install --user -r requirements.txt
```

**Linux/macOS:**
```bash
# sudo 사용하지 말고 가상환경 사용
python3 -m venv bot-env
source bot-env/bin/activate
pip install -r requirements.txt
```

---

## 패키지 버전 확인

### 설치된 패키지 확인
```bash
pip list | grep -E "pandas|numpy|scipy|optuna|quantstats"
```

### 필수 패키지 체크리스트
```bash
python -c "import pandas; print('✅ pandas:', pandas.__version__)"
python -c "import numpy; print('✅ numpy:', numpy.__version__)"
python -c "import scipy; print('✅ scipy:', scipy.__version__)"
python -c "import sklearn; print('✅ scikit-learn:', sklearn.__version__)"
python -c "import optuna; print('✅ optuna:', optuna.__version__)"
python -c "import ta; print('✅ ta:', ta.__version__)"
python -c "import quantstats; print('✅ quantstats:', quantstats.__version__)"
```

---

## 최소 요구사항

| 패키지 | 최소 버전 | 용도 |
|--------|-----------|------|
| pandas | 1.5.0 | 데이터 처리 |
| numpy | 1.23.0 | 수치 계산 |
| scipy | 1.9.0 | 과학 계산 |
| scikit-learn | 1.1.0 | 머신러닝 |
| optuna | 3.0.0 | 최적화 |
| ta | 0.10.0 | 기술적 지표 |
| quantstats | 0.0.62 | 성능 분석 |
| matplotlib | 3.6.0 | 시각화 |

---

## 설치 스크립트

### Windows
```batch
@echo off
echo 패키지 설치 중...
pip install --upgrade pip
pip install -r requirements.txt
echo 설치 완료!
python quick_test.py
```

### Linux/macOS
```bash
#!/bin/bash
echo "패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt
echo "설치 완료!"
python quick_test.py
```

---

## 도움말

### 전체 재설치
```bash
# 모든 패키지 제거 후 재설치
pip freeze | xargs pip uninstall -y
pip install -r requirements.txt
```

### 캐시 없이 설치
```bash
pip install --no-cache-dir -r requirements.txt
```

### 특정 버전 설치
```bash
pip install pandas==1.5.0 numpy==1.23.0
```

---

## 설치 완료 후

### 1. 빠른 테스트
```bash
python quick_test.py
```

### 2. 예제 실행
```bash
python example_usage.py
```

### 3. 도움말 보기
```bash
cat README.md
cat QUICKSTART.md
```

---

**문제가 계속되면 GitHub Issues에 문의하세요!**

