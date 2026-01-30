"""서버 시작 스크립트 (디버깅용)"""
import uvicorn
import sys

# 버퍼링 비활성화
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

if __name__ == "__main__":
    print("[START] Starting server without reload...", flush=True)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 리로드 비활성화
        log_level="info"
    )
