"""
Windows 환경에서 Playwright를 사용하기 위한 uvicorn 서버 시작 스크립트
"""
import asyncio
import sys

# Windows 환경에서 Playwright 실행을 위한 설정
if sys.platform == 'win32':
    # SelectorEventLoop 사용 (Playwright 호환)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[INFO] Windows SelectorEventLoop 정책 설정 완료")

if __name__ == "__main__":
    import uvicorn

    # uvicorn 실행 (reload 비활성화로 event loop 안정화)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        loop="asyncio"
    )
