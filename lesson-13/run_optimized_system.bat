@echo off
echo ================================================================
echo 최적화된 실시간 모니터링 시스템 실행
echo ================================================================
echo.

REM 필수 패키지 확인
echo [1/3] 필수 패키지 확인 중...
python -c "import flask, psutil, aiohttp" 2>nul
if errorlevel 1 (
    echo 패키지가 설치되지 않았습니다. 설치 중...
    pip install flask psutil aiohttp
)
echo.

REM 시스템 테스트
echo [2/3] 시스템 테스트 중...
python test_monitoring_system.py
if errorlevel 1 (
    echo 테스트 실패! 문제를 확인하세요.
    pause
    exit /b 1
)
echo.

REM 최적화된 시스템 실행
echo [3/3] 최적화된 모니터링 시스템 시작...
echo.
echo ================================================================
echo 웹 대시보드 접속: http://localhost:5000
echo 종료: Ctrl+C
echo ================================================================
echo.

python optimized_monitoring_system.py

pause

