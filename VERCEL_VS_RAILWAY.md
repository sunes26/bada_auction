# Vercel vs Railway - 백엔드 배포 비교

## 🤔 Vercel로 백엔드 배포가 가능한가?

**답변: 가능하지만 제한이 많습니다.**

---

## 📊 비교표

| 항목 | Vercel | Railway |
|-----|--------|---------|
| **타입** | Serverless Functions | 컨테이너 (전용 서버) |
| **실행 시간 제한** | 10초 (Hobby) / 60초 (Pro) | 무제한 |
| **메모리** | 1024MB (Hobby) | 512MB~32GB |
| **가격** | $0 / $20/월 | $5/월부터 |
| **스케줄러** | 외부 서비스 필요 | 내장 Cron 지원 |
| **WebSocket** | 제한적 | 완전 지원 |
| **상태 유지** | 불가능 (Stateless) | 가능 (Stateful) |
| **Python 지원** | 제한적 | 완전 지원 |
| **PostgreSQL** | 외부 (Supabase) | 내장 제공 가능 |
| **FastAPI** | 제한적 동작 | 완전 지원 |

---

## 🚨 온백AI 프로젝트에서 Vercel이 문제가 되는 이유

### 1. **실행 시간 제한**

우리 백엔드의 주요 작업들:

```python
# AI 상세페이지 생성 - 10-30초 소요
@router.post("/detail-page/{product_id}/generate")
async def generate_detail_page():
    response = await openai.ChatCompletion.create(...)  # 10-30초
    # Vercel Hobby: ❌ 10초 초과로 타임아웃
    # Vercel Pro: ✅ 가능 (하지만 $20/월)
```

```python
# 상품 모니터링 - 1-5분 소요
@router.post("/cron/monitor-products")
async def monitor_products():
    for product in products:  # 100개 상품
        price = await scrape_price(product.url)  # 각 1-3초
    # Vercel: ❌ 60초 초과로 타임아웃
```

```python
# 플레이오토 주문 동기화 - 2-10분 소요
@router.post("/playauto/orders/sync")
async def sync_orders():
    orders = await playauto_client.get_orders()  # 수천 건
    # Vercel: ❌ 60초 초과로 타임아웃
```

---

### 2. **스케줄러 (Cron Jobs) 문제**

**우리가 필요한 스케줄러**:
- 10분마다: 상품 가격 모니터링
- 1시간마다: 플레이오토 주문 동기화
- 매일 새벽 2시: 데이터베이스 백업
- 6시간마다: 송장 업로드 체크

**Vercel의 한계**:
```
❌ Vercel 자체에는 Cron 기능 없음
→ 외부 서비스 필요 (Vercel Cron은 Pro 플랜만)
→ 추가 비용 발생
```

**Railway의 장점**:
```
✅ 내장 Cron Jobs
✅ 무료 티어에서도 사용 가능
✅ 설정 간단 (railway.json에 schedule만 추가)
```

---

### 3. **상태 유지 (Stateful) 불가**

**APScheduler 같은 백그라운드 작업**:
```python
# 현재 코드 (main.py)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(check_prices, 'interval', minutes=10)
scheduler.start()
```

**Vercel Serverless**:
```
❌ 각 요청마다 새로운 인스턴스 생성
❌ 요청 끝나면 인스턴스 종료
❌ 백그라운드 작업 불가능
→ 스케줄러가 매번 초기화됨 (동작 안 함)
```

**Railway**:
```
✅ 서버가 계속 실행됨
✅ 스케줄러가 계속 동작
✅ 상태 유지 가능
```

---

### 4. **메모리 제한**

```python
# Excel 대량 내보내기
@router.get("/products/export")
async def export_excel():
    products = get_all_products()  # 1000개
    workbook = create_excel_with_images(products)  # 메모리 많이 사용
    # Vercel: ❌ 1024MB 제한으로 OOM (Out of Memory)
```

---

## 💡 그래도 Vercel을 사용하고 싶다면?

### 옵션 1: 하이브리드 접근 (권장)

**Vercel (프론트엔드 + 간단한 API)**:
```typescript
// app/api/health/route.ts (Next.js API Route)
export async function GET() {
  return Response.json({ status: 'ok' });
}

// app/api/products/route.ts
export async function GET() {
  // Supabase에서 직접 조회 (빠르고 간단)
  const { data } = await supabase.from('products').select('*');
  return Response.json(data);
}
```

**Railway (무거운 작업)**:
- AI 상세페이지 생성
- 상품 모니터링
- 플레이오토 동기화
- 스케줄러

**비용**: Vercel $0 + Railway $5 = **$5/월**

---

### 옵션 2: Vercel Pro + 외부 Cron 서비스

**구성**:
- Vercel Pro ($20/월) - 60초 타임아웃
- Upstash QStash ($10/월) - Cron 서비스
- Supabase ($0) - 데이터베이스

**비용**: **$30/월**

**문제점**:
- 여전히 긴 작업(모니터링 5분)은 60초 제한으로 불가능
- Railway보다 6배 비쌈

---

### 옵션 3: Vercel만 사용 (최소 기능)

**가능한 것**:
```typescript
// Next.js API Routes로 간단한 CRUD만
// app/api/products/[id]/route.ts
export async function GET(request, { params }) {
  const product = await supabase
    .from('products')
    .select('*')
    .eq('id', params.id)
    .single();
  return Response.json(product);
}
```

**불가능한 것**:
- ❌ AI 상세페이지 생성 (10초 초과)
- ❌ 자동 가격 모니터링 (스케줄러 없음)
- ❌ 플레이오토 주문 동기화 (긴 실행 시간)
- ❌ 대량 데이터 처리 (타임아웃)

**결론**: 핵심 기능의 80%를 포기해야 함

---

## 🎯 추천 방안

### 시나리오별 추천

#### 1. **비용 최소화 + 모든 기능 필요** (추천)
```
프론트엔드: Vercel ($0)
백엔드: Railway ($5)
DB: Supabase ($0)
총: $5/월
```

#### 2. **Vercel만 사용하고 싶음**
```
프론트엔드 + 간단한 API: Vercel ($0)
무거운 작업: Railway ($5)
총: $5/월
```

#### 3. **돈 상관없이 Vercel만**
```
Vercel Pro ($20)
+ Upstash QStash ($10)
+ 기능 포기 (긴 작업 불가)
총: $30/월 (기능 제한됨)
```

---

## 📋 실제 배포 시나리오

### 현재 로드맵 (Railway 사용)

```
Frontend (Vercel)
    ↓ API Call
Backend (Railway) ← 여기서 모든 무거운 작업
    ↓
Database (Supabase)
```

**장점**:
- ✅ 모든 기능 동작
- ✅ 비용 최소 ($5/월)
- ✅ 확장 가능
- ✅ 타임아웃 걱정 없음

---

### 대안 1: Vercel API Routes (일부만)

```
Frontend (Vercel)
    ↓
간단한 API (Vercel API Routes)
    ↓
Database (Supabase)

무거운 작업 (Railway)
    ↓
Database (Supabase)
```

**코드 예시**:

```typescript
// app/api/products/route.ts (Vercel)
// 간단한 조회만 - Vercel에서 처리
export async function GET() {
  const { data } = await supabase.from('products').select('*');
  return Response.json(data);
}
```

```python
# Railway 백엔드
# 무거운 작업 - Railway에서 처리
@router.post("/generate-detail-page")
async def generate(product_id: int):
    # AI 생성 (30초)
    content = await openai_generate(product_id)
    return content
```

**프론트엔드에서 호출**:
```typescript
// 간단한 조회 - Vercel API
const products = await fetch('/api/products');

// 무거운 작업 - Railway API
const detailPage = await fetch('https://api.railway.app/generate-detail-page', {
  method: 'POST',
  body: JSON.stringify({ product_id: 1 })
});
```

---

## 💰 최종 비용 비교

| 구성 | 월 비용 | 기능 | 비고 |
|-----|--------|-----|-----|
| **Vercel + Railway** | $5 | 100% | ⭐ **추천** |
| Vercel Pro + Upstash | $30 | 70% | 긴 작업 불가 |
| Vercel만 (Hobby) | $0 | 30% | 핵심 기능 불가 |
| Railway만 | $5 | 100% | 프론트엔드도 Railway |

---

## 🚀 결론

**Q: Vercel로 백엔드 배포가 안되나요?**

**A: 가능하지만 우리 프로젝트에는 부적합합니다.**

**이유**:
1. AI 생성, 모니터링 등 10초 이상 작업이 많음
2. 스케줄러가 필수인데 Vercel은 지원 안 함 (Pro는 비쌈)
3. 상태 유지가 필요한데 Serverless는 불가능
4. 비용도 Railway가 더 저렴 ($5 vs $30)

**추천**:
- ✅ Vercel (프론트엔드) + Railway (백엔드) = **$5/월**
- ✅ 모든 기능 100% 동작
- ✅ 확장 가능
- ✅ 관리 편함

**Vercel만 사용하고 싶으면**:
- Next.js API Routes로 간단한 CRUD만 구현
- 무거운 작업(AI, 모니터링)은 포기 또는 Railway 병행

---

## 📞 다음 단계

현재 로드맵대로 진행하시면:
1. Vercel: 프론트엔드 배포 (무료)
2. Railway: 백엔드 배포 ($5)
3. **총 $5/월로 모든 기능 사용 가능**

궁금한 점 있으시면 언제든 질문하세요!
