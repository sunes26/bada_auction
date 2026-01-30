# 물바다AI 백엔드 - 상품 수집 엔진

Python/FastAPI 기반의 상품 수집 백엔드 서버입니다.

## 설치

```bash
cd backend
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 아래 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 상품 검색

```
POST /api/sourcing/search
```

**파라미터:**
- `source`: 소싱처 (traders, ssg, all)
- `category`: 카테고리 (선택)
- `keyword`: 검색 키워드 (선택)
- `page`: 페이지 번호 (기본: 1)
- `page_size`: 페이지당 항목 수 (기본: 20)

**응답:**
```json
{
  "products": [...],
  "total": 20,
  "page": 1,
  "page_size": 20
}
```

### 가격 확인

```
GET /api/sourcing/price-check
```

**파라미터:**
- `source`: 소싱처
- `product_url`: 상품 URL

**응답:**
```json
{
  "source": "traders",
  "product_url": "https://...",
  "current_price": 15000,
  "checked_at": "2026-01-07T..."
}
```

## 스크래퍼 구현 상태

- ✅ Traders 스크래퍼 (기본 구조 완성, 샘플 데이터)
- ✅ SSG 스크래퍼 (기본 구조 완성, 샘플 데이터)

## TODO

- [ ] Traders 실제 스크래핑 로직 구현
- [ ] SSG 실제 스크래핑 로직 구현
- [ ] 상품 데이터베이스 연동 (SQLite)
- [ ] 가격 동기화 스케줄러 (15분 주기)
- [ ] 마진 방어 시스템 구현
