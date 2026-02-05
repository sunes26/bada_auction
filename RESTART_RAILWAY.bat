@echo off
echo ============================================================
echo Railway 서버 재시작 (Git Push 방식)
echo ============================================================
echo.
echo [정보] PlayAuto 자동 동기화를 활성화하기 위해
echo        Railway 서버를 재시작합니다.
echo.
echo [1단계] Git 상태 확인...
git status
echo.

echo [2단계] 빈 커밋 생성...
git commit --allow-empty -m "Restart Railway to enable PlayAuto auto-sync"
echo.

echo [3단계] Railway에 푸시...
git push
echo.

echo [완료] Railway가 자동으로 재배포를 시작합니다.
echo        약 2-3분 소요됩니다.
echo.
echo [확인] 재배포 상태:
echo        https://railway.app (대시보드에서 확인)
echo.
echo [테스트] 30초 후 설정을 확인하시겠습니까? (y/n)
set /p choice=

if /i "%choice%"=="y" (
    echo.
    echo 30초 대기 중...
    timeout /t 30 /nobreak
    echo.
    echo [확인] PlayAuto 설정 조회...
    curl https://badaauction-production.up.railway.app/api/playauto/settings
    echo.
    echo.
    echo [확인] 스케줄러 상태 조회...
    curl https://badaauction-production.up.railway.app/api/scheduler/status
    echo.
)

echo.
pause
