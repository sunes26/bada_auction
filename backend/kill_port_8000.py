import psutil
import time

# 포트 8000을 사용하는 프로세스 찾기
for proc in psutil.process_iter(['pid', 'name']):
    try:
        for conn in proc.connections():
            if conn.laddr.port == 8000:
                print(f"Killing PID {proc.pid} ({proc.name()})")
                proc.kill()
                time.sleep(0.5)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print("All processes using port 8000 have been terminated")
