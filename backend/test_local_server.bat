@echo off
echo ============================================================
echo 로컬 백엔드 서버 시작 (테스트)
echo ============================================================
echo.
echo [INFO] 백엔드 서버를 시작합니다...
echo [INFO] API 주소: http://localhost:8000
echo [INFO] 10초 후 자동으로 스케줄러 상태를 확인합니다
echo.

start /B python main.py > server_output.log 2>&1

echo 서버 시작 중... 10초 대기
timeout /t 10 /nobreak

echo.
echo ============================================================
echo 스케줄러 상태 확인
echo ============================================================
curl -s http://localhost:8000/api/scheduler/status

echo.
echo.
echo ============================================================
echo 서버를 중지하려면 아무 키나 누르세요
echo ============================================================
pause

echo 서버 종료 중...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq main.py"
