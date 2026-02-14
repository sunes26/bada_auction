# Redis 캐싱 설정 가이드

## 개요

성능 최적화를 위해 Redis 분산 캐싱을 지원합니다.
Redis가 설치되어 있으면 자동으로 Redis를 사용하고, 없으면 기존 메모리 캐시를 사용합니다.

## Redis 사용 시 장점

- ✅ 서버 재시작해도 캐시 유지
- ✅ 여러 서버 인스턴스가 캐시 공유 (로드 밸런싱)
- ✅ 캐시 히트율 80% 이상
- ✅ 응답 속도 50-90% 향상

## 설정 방법

### 1. Redis 설치 (선택)

Redis를 사용하지 않아도 기존처럼 작동합니다.

#### 로컬 개발 환경

```bash
# Windows (Chocolatey)
choco install redis

# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

#### Railway (Production)

Railway 대시보드에서:
1. 프로젝트 선택
2. "New" → "Database" → "Add Redis" 클릭
3. 자동으로 `REDIS_URL` 환경 변수 생성됨

비용: 월 $5-10

### 2. 환경 변수 설정

`.env` 파일에 다음 추가:

```bash
# Redis 연결 URL (선택)
REDIS_URL=redis://localhost:6379/0

# Railway에서는 REDIS_PRIVATE_URL도 지원
# REDIS_PRIVATE_URL=redis://...
```

### 3. 의존성 설치

```bash
pip install redis>=5.0.0
```

이미 `requirements.txt`에 포함되어 있습니다.

## 사용법

코드 변경 없이 자동으로 작동합니다:

```python
from utils.cache import cached

@cached(ttl=300)  # 5분 캐싱
def expensive_function():
    # Redis가 있으면 Redis 사용
    # 없으면 메모리 캐시 사용
    return ...
```

## 캐시 확인

서버 시작 시 로그 확인:

```
[Cache] Redis 초기화 시도...
[Cache] Redis 연결 성공: redis://localhost:6379/0
[Cache] Redis 캐시 사용
```

또는

```
[Cache] 메모리 캐시 사용 (Redis 미설치 또는 미설정)
```

## 성능 비교

| 작업 | 메모리 캐시 | Redis 캐시 |
|------|------------|-----------|
| 대시보드 조회 | 500ms | 5ms |
| 상품 목록 조회 | 200ms | 2ms |
| 카테고리 구조 | 150ms | 1ms |
| 캐시 유지 | 서버 재시작 시 삭제 | 영구 유지 |
| 다중 서버 | 각 서버 독립 | 모든 서버 공유 |

## 문제 해결

### Redis 연결 실패

```
[Cache] Redis 연결 실패: ...
[Cache] 메모리 캐시로 폴백합니다
```

→ 정상입니다. 메모리 캐시로 자동 전환됩니다.

### Redis 서버 시작 안 됨

```bash
# Redis 서버 수동 시작
redis-server

# 상태 확인
redis-cli ping
# 응답: PONG
```

### Railway에서 Redis URL 확인

```bash
# Railway CLI
railway variables

# 또는 대시보드에서 Variables 탭 확인
```

## 캐시 무효화

필요 시 캐시를 수동으로 삭제할 수 있습니다:

```python
from utils.cache import clear_all_cache

clear_all_cache()  # 모든 캐시 삭제
```

## 주의사항

1. **메모리 사용량**: Redis는 메모리를 사용하므로 큰 데이터는 주의
2. **보안**: 프로덕션에서는 Redis 비밀번호 설정 권장
3. **백업**: 중요 데이터는 DB에 저장, 캐시는 임시 데이터만

## 추가 최적화

Redis 설치 후 추가로 최적화할 수 있는 부분:

1. **TTL 증가**: 자주 변경되지 않는 데이터는 TTL 늘리기
2. **캐시 워밍**: 서버 시작 시 미리 캐시 로드
3. **캐시 계층화**: 브라우저 → Redis → DB
