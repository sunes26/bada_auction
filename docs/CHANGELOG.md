# 업데이트 히스토리

## 2026-02-09: 쿠팡 기능 완성 + 상세페이지 이미지 개선 🛒🎨

### 쿠팡 판매자 관리코드(c_sale_cd_coupang) 수집 기능 추가

쿠팡 채널이 지마켓/옥션/스마트스토어와 동일하게 작동하도록 완성했습니다.

**수정된 파일:**
- `backend/api/products.py` - 3곳 수정
  - 개별 상품 마켓플레이스 코드 동기화 (`/api/products/{id}/sync-marketplace-codes`)
  - 전체 상품 일괄 동기화 (`/api/products/sync-all-marketplace-codes`)
  - 상품 등록 시 c_sale_cd_coupang 저장
- `backend/playauto/scheduler.py` - 스케줄러에서 쿠팡 코드 수집

**코드 변경:**
```python
# 쿠팡 c_sale_cd 수집 추가
if shop_cd == "B378":  # 쿠팡
    c_sale_cd_coupang = code.get("c_sale_cd")
```

### ol_shop_no_coupang 필드 추가

지마켓/옥션/스마트스토어와 동일하게 쿠팡용 온라인 쇼핑몰 번호를 저장합니다.

**수정된 파일:**
- `backend/database/schema.sql` - ol_shop_no_coupang 컬럼 추가
- `backend/database/schema_postgresql.sql` - ol_shop_no_coupang 컬럼 추가
- `backend/database/models.py` - SQLAlchemy 모델에 컬럼 추가
- `backend/database/db_wrapper.py` - update_selling_product 파라미터 추가
- `backend/api/products.py` - B378(쿠팡) 채널 감지 및 저장 로직

**마이그레이션 필요:**
```sql
ALTER TABLE my_selling_products ADD COLUMN IF NOT EXISTS ol_shop_no_coupang TEXT;
```

### 상세페이지 + 버튼 이미지 가로 크기 조절

+ 버튼으로 추가한 이미지의 컨테이너 가로 크기를 조절할 수 있고, 세로는 이미지 비율에 맞춰 자동 조정됩니다.

**수정된 파일:**
- `components/templates/EditableImage.tsx` - autoFitHeight 모드 추가
- `components/ui/PropertiesPanel.tsx` - 가로 크기 슬라이더 추가
- `components/templates/DetailPage.tsx` - containerWidths 상태 관리
- 모든 템플릿 파일 (Simple, Daily, Food, Fresh, Additional, Additional2)

**기능:**
- 가로 크기: 30% ~ 100% 조절 가능
- 세로 크기: 이미지 비율에 따라 자동 계산

---

## 2026-02-09: Selenium 제거 + FlareSolverr 전환 + 품절 오감지 수정 🚀🔧

### Selenium → FlareSolverr 완전 전환

모든 Selenium 코드를 FlareSolverr 기반으로 전환하여 서버 리소스를 대폭 절감했습니다.

| 파일 | 변경 내용 |
|------|----------|
| `monitor/product_monitor.py` | Selenium 제거 → FlareSolverr + BeautifulSoup |
| `api/monitoring.py` | Selenium 제거 → FlareSolverr 기반 |
| `scrapers/cjthemarket_scraper.py` | Selenium 제거 → FlareSolverr + requests |
| `scrapers/ssg_scraper_selenium.py` | Selenium 제거 → FlareSolverr + requests |
| `sourcing/smartstore.py` | Selenium 제거 → requests 기반 |
| `requirements.txt` | selenium, webdriver-manager, undetected-chromedriver 제거 |
| `Dockerfile` | Chrome/ChromeDriver 설치 제거 |

**이점:**
- Docker 이미지 크기 ~500MB 감소
- Railway 메모리 사용량 감소 (Chrome 프로세스 제거)
- "tab crashed" 오류 해결
- 빌드 시간 단축

### 품절 오감지 문제 수정

페이지 전체에서 "품절" 키워드를 찾던 방식에서, 구매 버튼 영역만 확인하도록 변경했습니다.

```python
# 변경 전 (문제)
page_text = soup.get_text().lower()
if '품절' in page_text:  # 리뷰, 다른 옵션 등에서도 감지됨
    return 'out_of_stock'

# 변경 후 (수정)
buy_button_selectors = ['.btn_buy', '.btn_cart', ...]
for selector in buy_button_selectors:
    elem = soup.select_one(selector)
    if elem and '품절' in elem.get_text():
        status = 'out_of_stock'
```

- 적용 소싱처: 11번가, SSG, 홈플러스, 롯데ON, G마켓, 옥션, GS샵, CJ더마켓
- 가격이 정상 추출되면 판매중으로 재판정하는 로직 추가

### CJ제일제당 더마켓 소싱처 추가

- `cjthemarket.com` URL 자동 인식
- 상품명, 가격, 썸네일 자동 추출
- 품절/판매종료 상태 체크

### 상세페이지 편집 기능 개선

- 외부 클릭 시 편집 모드 자동 해제
- 이미지 크기 조정 시 레이아웃 자연스럽게 확장
- 이미지 정렬 기능 추가 (왼쪽/가운데/오른쪽)

---

## 2026-02-08: 쿠팡 상품 등록 이슈 디버깅 + shop_cd 수정 🔍🛒

### 쿠팡 shop_cd 문제 발견 및 수정

- **실제 쿠팡 shop_cd 확인**: `B378` (기존 코드에서는 A027, CPM만 인식)
- **coupang_codes에 B378 추가** (`products.py`):
  ```python
  coupang_codes = ["A027", "a027", "CPM", "cpm", "COUPANG", "coupang", "B378", "b378"]
  ```

### 쿠팡 추천옵션 적용

- **쿠팡 필수 추천옵션 확인**: 옵션명 `수량`, 추천단위 `개`
- **옵션 설정 변경** (`product_registration.py`):
  - 변경 전: `opt_sort1 = "상품선택"`, `opt_sort1_desc = 상품명`
  - 변경 후: `opt_sort1 = "수량"`, `opt_sort1_desc = "1개"`

### 디버깅 로그 추가

- **프론트엔드 콘솔 디버깅**: F12에서 채널 분류 및 옵션 정보 확인 가능
- **채널 분류 디버깅**: site_list, coupang_sites, smartstore_sites 출력
- **쿠팡 옵션 디버깅**: opt_type, std_ol_yn, opts 배열 출력

---

## 2026-02-08: PlayAuto 카테고리 재매핑 + 채널별 옵션 분리 🏷️⚙️

### PlayAuto 카테고리 매핑 업데이트

- **sol_cate_no 전면 재매핑**: 81개 카테고리 → 47개 고유 코드
- **매핑 업데이트 스크립트 생성**: `update_category_mapping.sql`
- **로컬 + 프로덕션(Supabase) 동기화 완료**

### 채널별 상품 등록 방식 분리

```
┌─────────────────┬─────────────┬────────────┐
│ 채널            │ opt_type    │ std_ol_yn  │
├─────────────────┼─────────────┼────────────┤
│ 옥션/지마켓     │ 옵션없음    │ Y (단일)   │
│ 쿠팡            │ 조합형      │ N          │
│ 스마트스토어 등 │ 독립형      │ N          │
└─────────────────┴─────────────┴────────────┘
```

---

## 2026-02-06: FlareSolverr 연동 + 소싱 사이트 확장 🔓🛒

### FlareSolverr 연동 (Cloudflare 우회)

- **모든 소싱 사이트 지원**: FlareSolverr로 Cloudflare 보호 우회
- **FlareSolverr 클라이언트** (`backend/utils/flaresolverr.py`)
- **HTML 직접 파싱**: FlareSolverr 응답에서 BeautifulSoup으로 데이터 추출

### 소싱 사이트 지원 현황

| 사이트 | 방식 | 상품명 | 가격 | 썸네일 |
|--------|------|--------|------|--------|
| G마켓 | FlareSolverr | ✅ | ✅ | ✅ |
| 옥션 | FlareSolverr | ✅ | ✅ | ✅ |
| 11번가 | FlareSolverr | ✅ | ✅ | ✅ |
| SSG | FlareSolverr | ✅ | ✅ | ✅ |
| 홈플러스 | FlareSolverr | ✅ | ✅ | ✅ |
| 롯데ON | FlareSolverr | ✅ | ✅ | ✅ |
| CJ더마켓 | FlareSolverr | ✅ | ✅ | ✅ |
| ~~스마트스토어~~ | - | ❌ | ❌ | ❌ |

### 스마트스토어 지원 중단

- **네이버 CAPTCHA 차단**: FlareSolverr로도 우회 불가
- **권장**: 스마트스토어 대신 롯데ON 사용

---

## 2026-02-06: 자동가격조정 버그 수정 + 알림 시스템 개선 🔧💰🔔

### 자동가격조정 시스템 수정

- **SQLAlchemy ORM 호환성 수정** (`dynamic_pricing_service.py`)
- **모니터링 스케줄러 활성화** (`main.py`)
- **불필요한 기능 비활성화**

### 송장 업로드 스케줄러 수정

- **SQLAlchemy 호환성 수정** (`tracking_scheduler.py`)

### 알림 테스트 엔드포인트 수정

- **직접 발송 방식으로 변경** (`/api/notifications/test`)
- **누락 메서드 추가** (`db_wrapper.py`): `add_webhook_log()`

---

## 2026-02-06: 주문-회계 자동 연동 + 주문 처리 시스템 📦💰✅

### 회계 시스템 자동 연동 구현

```
PlayAuto 주문 수집 → MarketOrderRaw → Order 테이블 생성
                                            ↓
                  MySellingProduct 매칭 → OrderItem 테이블 생성
                  (sourcing_price 가져오기)   (selling_price, sourcing_price, profit)
                                            ↓
                                     회계 자동 계산!
```

### 주문 상태별 탭 분리

- **주문 목록 탭**: 미처리 주문만 표시 (신규주문, 출고대기 등)
- **송장 관리 탭**: 출고완료된 주문 표시
- 송장 관리 탭에 통계 카드 추가
- 송장 관리 탭 검색 기능

### 송장 입력 및 출고완료 처리

- **출고지시 API 구현**: `PUT /api/order/instruction`
- **송장 업데이트 시 자동 상태 변경**
- 배송사 선택 (CJ대한통운, 한진택배, 롯데택배, 우체국택배, 로젠택배)

### 주문 처리 워크플로우 완성

```
1. PlayAuto 신규주문 수신 → 주문 목록에 표시
         ↓
2. [🛒 구매하기] 버튼 → 소싱처에서 상품 구매
         ↓
3. [📝 송장 입력] 버튼 → 배송사 선택 + 송장번호 입력
         ↓
4. 🤖 자동 처리:
   - 신규주문 → 출고대기 (PUT /order/instruction)
   - 송장 업데이트 → 출고완료 (PUT /order/setInvoice)
         ↓
5. ✅ 완료! → 송장 관리 탭으로 이동
```

---

## 2026-02-04: PlayAuto 채널별 판매자 관리코드 분리 + 자동 가격 조정 수정 🔧💰

### PlayAuto 채널별 c_sale_cd 분리 구현

- **DB 스키마 변경**:
  - `c_sale_cd_gmk` 컬럼 추가 (지마켓/옥션용)
  - `c_sale_cd_smart` 컬럼 추가 (스마트스토어용)
- **상품 등록 자동화**: 채널별로 자동 저장
- **UI 개선** (EditProductModal): 채널별 관리코드 표시

### 자동 가격 조정 API 수정

- **500 에러 수정** (`/api/auto-pricing/settings`)
- PostgreSQL 호환성 보장

---

## 이전 버전

더 이전 업데이트 내역은 [GitHub 커밋 히스토리](https://github.com/sunes26/bada_auction/commits/main)를 참고하세요.
