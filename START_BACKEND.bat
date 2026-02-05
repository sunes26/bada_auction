@echo off
echo ============================================================
echo 물바다AI 백엔드 서버 시작
echo ============================================================
echo.

cd backend
echo [INFO] 백엔드 서버를 시작합니다...
echo [INFO] PlayAuto 자동 동기화: 30분마다
echo [INFO] API 주소: http://localhost:8000
echo.
python main.py

pause
