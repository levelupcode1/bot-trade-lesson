@echo off
echo ================================
echo Lesson 13 패키지 설치 스크립트
echo ================================
echo.

REM pip 업그레이드
echo [1/3] pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

REM requirements.txt 설치
echo [2/3] 필수 패키지 설치 중...
pip install -r requirements.txt
echo.

REM 설치 확인
echo [3/3] 설치 확인 중...
python quick_test.py
echo.

echo ================================
echo 설치 완료!
echo ================================
echo.
echo 다음 명령으로 예제를 실행하세요:
echo   python example_usage.py
echo.
pause

