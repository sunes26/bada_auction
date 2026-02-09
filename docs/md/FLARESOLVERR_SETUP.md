# FlareSolverr 설정 가이드

## 개요
FlareSolverr는 Cloudflare 보호를 우회하기 위한 프록시 서버입니다.
G마켓, 옥션, 스마트스토어 등 Cloudflare로 보호된 사이트의 크롤링에 필요합니다.

## Railway 배포 방법

### 방법 1: Railway에서 Docker 이미지로 배포

1. **Railway 대시보드에서 새 프로젝트 생성**
   - https://railway.app/dashboard 접속
   - "New Project" → "Deploy from Docker Image" 선택

2. **Docker 이미지 설정**
   ```
   ghcr.io/flaresolverr/flaresolverr:latest
   ```

3. **환경변수 설정**
   ```
   LOG_LEVEL=info
   LOG_HTML=false
   CAPTCHA_SOLVER=none
   TZ=Asia/Seoul
   ```

4. **포트 설정**
   - FlareSolverr는 기본적으로 포트 8191 사용
   - Railway에서 자동으로 포트 매핑됨

5. **배포 완료 후 URL 확인**
   - Railway에서 제공하는 URL 확인 (예: `https://flaresolverr-xxx.up.railway.app`)

### 방법 2: railway.json으로 배포

프로젝트 루트에 `railway-flaresolverr.json` 파일 생성:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "dockerfilePath": null
  },
  "deploy": {
    "image": "ghcr.io/flaresolverr/flaresolverr:latest",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

## 백엔드 연동

### 환경변수 설정

백엔드 프로젝트에 다음 환경변수 추가:

```
FLARESOLVERR_URL=https://your-flaresolverr-url.up.railway.app/v1
```

### 로컬 테스트

로컬에서 FlareSolverr 실행:

```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

환경변수:
```
FLARESOLVERR_URL=http://localhost:8191/v1
```

## 작동 방식

1. 앱에서 G마켓/옥션/스마트스토어 URL 요청
2. FlareSolverr가 Cloudflare 챌린지 자동 해결
3. 쿠키와 HTML 반환
4. 반환된 쿠키로 Selenium에서 페이지 접근

## 리소스 요구사항

- RAM: 최소 512MB (권장 1GB)
- 각 브라우저 인스턴스당 100-200MB 추가 사용

## 문제 해결

### FlareSolverr 연결 실패
- Railway 서비스가 실행 중인지 확인
- URL이 올바른지 확인 (`/v1` 포함)
- 네트워크 연결 확인

### Cloudflare 우회 실패
- FlareSolverr 버전 업데이트 확인
- CAPTCHA가 필요한 경우 수동 해결 필요

### 타임아웃
- `maxTimeout` 값 증가 (기본 60000ms)
- 네트워크 상태 확인
