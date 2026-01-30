# Repository 패턴 구조 및 사용법

## 📁 디렉토리 구조

```
backend/database/
├── db.py                         # DB 연결 관리만 담당 (기존)
├── schema.sql                    # 스키마 정의
├── repositories/                 # ⭐ NEW! DB 접근 전용 계층
│   ├── __init__.py
│   ├── base_repository.py        # 공통 CRUD 로직
│   ├── product_repository.py     # 상품 DB 접근
│   ├── order_repository.py       # 주문 DB 접근 (TODO)
│   ├── notification_repository.py # 알림 DB 접근 (TODO)
│   ├── webhook_repository.py     # Webhook DB 접근 (TODO)
│   └── stats_repository.py       # 통계 DB 접근 (TODO)
└── services/                     # ⭐ NEW! 비즈니스 로직 계층
    ├── __init__.py
    ├── product_service.py        # 상품 비즈니스 로직
    ├── order_service.py          # 주문 비즈니스 로직 (TODO)
    └── notification_service.py   # 알림 비즈니스 로직 (TODO)
```

## 🔄 아키텍처 계층

```
┌─────────────────────────────────────┐
│          API Layer (FastAPI)         │  # 요청/응답 처리
│      api/monitoring.py, orders.py    │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         Service Layer               │  # 비즈니스 로직
│   services/product_service.py       │  # - 가격 변동 감지
│   services/order_service.py         │  # - 알림 발송
│                                      │  # - 재고 관리
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Repository Layer              │  # DB 접근 전용
│ repositories/product_repository.py  │  # - CRUD 연산
│ repositories/order_repository.py    │  # - 쿼리 실행
│                                      │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         Database (SQLite)           │  # 데이터 저장
└─────────────────────────────────────┘
```

## 📝 사용 예시

### 1. API에서 Service 사용 (권장)

**AS-IS (기존 방식 - 비추천)**:
```python
# backend/api/monitoring.py
from database.db import get_db

@router.post("/check-price/{product_id}")
async def check_product_price(product_id: int, new_price: float):
    db = get_db()

    # 비즈니스 로직이 API에 직접 구현되어 있음 (❌)
    product = db.get_monitored_product(product_id)
    old_price = product['current_price']
    price_change = ((new_price - old_price) / old_price) * 100

    if abs(price_change) >= 1.0:
        # 알림 발송 로직...
        pass

    db.update_product_price(product_id, new_price)
    db.add_price_history(product_id, new_price, "checked")

    return {"success": True, "price_change": price_change}
```

**TO-BE (Repository 패턴 - 추천)**:
```python
# backend/api/monitoring.py
from database.services.product_service import ProductService

product_service = ProductService()

@router.post("/check-price/{product_id}")
async def check_product_price(product_id: int, new_price: float):
    """
    상품 가격 체크

    비즈니스 로직은 Service에 위임 (✅)
    """
    result = product_service.check_price_change(product_id, new_price)
    return result
```

### 2. Repository 직접 사용 (단순 CRUD만 필요할 때)

```python
# backend/api/monitoring.py
from database.repositories.product_repository import ProductRepository

product_repo = ProductRepository()

@router.get("/products")
async def get_products(source: Optional[str] = None):
    """
    상품 목록 조회

    단순 조회는 Repository 직접 사용 가능 (✅)
    """
    if source:
        products = product_repo.get_by_source(source)
    else:
        products = product_repo.get_active_products()

    return {"success": True, "products": products}

@router.get("/products/{product_id}")
async def get_product_detail(product_id: int):
    """상품 상세 조회"""
    product = product_repo.get_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

    # 가격 이력도 함께 조회
    price_history = product_repo.get_price_history(product_id, limit=30)

    return {
        "success": True,
        "product": product,
        "price_history": price_history
    }
```

### 3. Service에서 여러 Repository 조합

```python
# backend/database/services/product_service.py
from database.repositories.product_repository import ProductRepository
from database.repositories.notification_repository import NotificationRepository

class ProductService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.notification_repo = NotificationRepository()

    def check_price_change(self, product_id: int, new_price: float):
        """
        여러 Repository를 조합하여 비즈니스 로직 처리
        """
        # 1. 상품 정보 조회
        product = self.product_repo.get_by_id(product_id)

        # 2. 가격 변동 계산
        old_price = product['current_price']
        price_change_percent = ((new_price - old_price) / old_price) * 100

        # 3. 알림 발송 (1% 이상 변동 시)
        if abs(price_change_percent) >= 1.0:
            self.notification_repo.create({
                "product_id": product_id,
                "type": "price_change",
                "message": f"가격 {price_change_percent:+.1f}% 변동"
            })

        # 4. 가격 업데이트
        self.product_repo.update_price(product_id, new_price)
        self.product_repo.add_price_history(product_id, new_price, "checked")

        return {"success": True, "price_change_percent": price_change_percent}
```

## 🎯 Repository vs Service 선택 기준

### Repository 직접 사용
- ✅ **단순 CRUD 연산**만 필요한 경우
- ✅ **조회 전용** 엔드포인트
- ✅ **비즈니스 로직이 없는** 경우

**예시**:
- 상품 목록 조회
- 주문 상세 조회
- 알림 목록 조회

### Service 사용
- ✅ **비즈니스 로직**이 필요한 경우
- ✅ **여러 Repository 조합**이 필요한 경우
- ✅ **외부 서비스 호출** (알림, 결제 등)
- ✅ **복잡한 계산**이 필요한 경우

**예시**:
- 가격 변동 감지 및 알림
- 재고 자동 관리
- 주문 생성 및 재고 차감
- 마진 계산 및 경고

## 📊 마이그레이션 가이드

### 기존 코드를 Repository 패턴으로 변경하기

**1단계: Repository 생성**

```python
# backend/database/repositories/order_repository.py
from .base_repository import BaseRepository
from typing import List, Dict

class OrderRepository(BaseRepository):
    def get_table_name(self) -> str:
        return "orders"

    def get_with_items(self, order_id: int) -> Dict:
        """주문 + 주문 상품 함께 조회 (N+1 해결)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 주문 조회
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = dict(cursor.fetchone())

            # 주문 상품 조회
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
            order['items'] = [dict(row) for row in cursor.fetchall()]

            return order
```

**2단계: Service 생성 (비즈니스 로직 이동)**

```python
# backend/database/services/order_service.py
from database.repositories.order_repository import OrderRepository
from database.repositories.product_repository import ProductRepository

class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()

    def create_order_with_stock_check(self, order_data: Dict) -> Dict:
        """주문 생성 + 재고 체크 (비즈니스 로직)"""

        # 1. 재고 체크
        for item in order_data['items']:
            product = self.product_repo.get_by_id(item['product_id'])
            if not product['is_active']:
                return {"success": False, "error": f"{product['product_name']} 품절"}

        # 2. 주문 생성
        order_id = self.order_repo.create(order_data)

        # 3. 주문 상품 추가
        for item in order_data['items']:
            self.order_repo.add_item(order_id, item)

        return {"success": True, "order_id": order_id}
```

**3단계: API 수정**

```python
# backend/api/orders.py (수정 후)
from database.services.order_service import OrderService

order_service = OrderService()

@router.post("/orders")
async def create_order(order_data: CreateOrderRequest):
    """주문 생성"""
    result = order_service.create_order_with_stock_check(order_data.dict())
    return result
```

## 🧪 테스트 작성 예시

Repository 패턴을 사용하면 테스트가 쉬워집니다:

```python
# tests/test_product_service.py
from unittest.mock import Mock
from database.services.product_service import ProductService

def test_check_price_change():
    # Given
    service = ProductService()
    service.product_repo = Mock()  # Repository를 Mock으로 교체

    service.product_repo.get_by_id.return_value = {
        'id': 1,
        'product_name': '테스트 상품',
        'current_price': 10000
    }

    # When
    result = service.check_price_change(product_id=1, new_price=11000)

    # Then
    assert result['success'] == True
    assert result['price_change_percent'] == 10.0
    service.product_repo.update_price.assert_called_once_with(1, 11000)
```

## 🔄 TODO: 나머지 Repository/Service 구현

현재 **ProductRepository**와 **ProductService**만 구현되어 있습니다.

### 구현 필요 목록

1. **OrderRepository** - 주문 DB 접근
2. **OrderService** - 주문 비즈니스 로직
3. **NotificationRepository** - 알림 DB 접근
4. **NotificationService** - 알림 발송 로직
5. **WebhookRepository** - Webhook DB 접근
6. **StatsRepository** - 통계 조회
7. **PlayautoRepository** - 플레이오토 설정 DB 접근

### 구현 우선순위

1. **OrderRepository** (가장 많이 사용됨)
2. **NotificationRepository** (알림 시스템)
3. **StatsRepository** (대시보드 통계)

### 패턴 템플릿

새로운 Repository를 만들 때는 다음 템플릿을 사용하세요:

```python
# backend/database/repositories/your_repository.py
from .base_repository import BaseRepository
from typing import List, Dict

class YourRepository(BaseRepository):
    def get_table_name(self) -> str:
        return "your_table_name"

    # 테이블 특화 메서드 추가
    def your_custom_method(self, ...):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 쿼리 실행
            ...
```

## ✅ 장점 요약

| 항목 | 개선 전 (db.py 1,308줄) | 개선 후 (Repository 패턴) |
|------|------------------------|--------------------------|
| **파일 크기** | 1,308줄 (단일 파일) | 100~300줄 (파일당) |
| **책임 분리** | 하나의 클래스가 모든 역할 | Repository/Service 명확히 분리 |
| **테스트** | 전체 DB Mock 필요 | Repository만 Mock하면 됨 |
| **유지보수** | 어려움 (1,300줄에서 찾기) | 쉬움 (역할별 파일 분리) |
| **Git 충돌** | 자주 발생 | 거의 없음 (파일 분리) |
| **DB 교체** | 전체 수정 필요 | Repository만 수정 |
| **재사용성** | 낮음 | 높음 (Service 재사용 가능) |
| **비즈니스 로직** | DB와 혼재 | Service에 명확히 분리 |

## 🚀 다음 단계

1. **API 파일 수정**: 기존 API에서 Service 사용하도록 변경
2. **나머지 Repository 구현**: Order, Notification, Stats 등
3. **테스트 작성**: 각 Repository/Service에 대한 단위 테스트
4. **기존 db.py 축소**: 연결 관리만 남기고 나머지 제거

## 📚 참고 자료

- [Repository Pattern 설명](https://martinfowler.com/eaaCatalog/repository.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
