"""
플레이오토 API Pydantic 모델

요청/응답 데이터 검증 및 타입 안전성 제공
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========================================
# 설정 관련 모델
# ========================================

class PlayautoSettingsRequest(BaseModel):
    """플레이오토 설정 요청"""
    api_key: str = Field(..., min_length=10, description="플레이오토 API 키")
    email: str = Field(..., description="플레이오토 계정 이메일")
    password: str = Field(..., min_length=1, description="플레이오토 계정 비밀번호")
    api_base_url: Optional[str] = Field("https://openapi.playauto.io/api", description="API 기본 URL")
    enabled: bool = Field(True, description="플레이오토 연동 활성화 여부")
    auto_sync_enabled: bool = Field(False, description="자동 동기화 활성화 여부")
    auto_sync_interval: int = Field(30, ge=5, le=1440, description="자동 동기화 주기 (분, 5~1440)")
    encrypt_credentials: bool = Field(True, description="자격 증명 암호화 여부")


class PlayautoSettingsResponse(BaseModel):
    """플레이오토 설정 응답"""
    api_key_masked: str = Field(..., description="마스킹된 API 키")
    api_base_url: str = Field(..., description="API 기본 URL")
    enabled: bool = Field(..., description="플레이오토 연동 활성화 여부")
    auto_sync_enabled: bool = Field(..., description="자동 동기화 활성화 여부")
    auto_sync_interval: int = Field(..., description="자동 동기화 주기 (분)")
    last_sync_at: Optional[datetime] = Field(None, description="마지막 동기화 시각")


# ========================================
# 주문 관련 모델
# ========================================

class OrderItem(BaseModel):
    """주문 상품"""
    product_name: str = Field(..., description="상품명")
    product_url: Optional[str] = Field(None, description="상품 URL")
    quantity: int = Field(1, ge=1, description="수량")
    price: float = Field(0, ge=0, description="가격")
    option: Optional[str] = Field(None, description="옵션 정보")


class OrdererInfo(BaseModel):
    """주문자 정보"""
    order_name: Optional[str] = Field(None, max_length=30, description="주문자명")
    order_id: Optional[str] = Field(None, max_length=30, description="주문자 ID")
    order_tel: Optional[str] = Field(None, max_length=20, description="주문자 전화번호")
    order_htel: Optional[str] = Field(None, max_length=20, description="주문자 휴대폰")
    order_email: Optional[str] = Field(None, max_length=50, description="주문자 이메일")


class ReceiverInfo(BaseModel):
    """수령인 정보"""
    to_name: Optional[str] = Field(None, max_length=30, description="수령인명")
    to_tel: Optional[str] = Field(None, max_length=20, description="수령인 전화번호")
    to_htel: Optional[str] = Field(None, max_length=20, description="수령인 휴대폰")
    to_zipcd: Optional[str] = Field(None, max_length=10, description="우편번호")
    to_addr1: Optional[str] = Field(None, max_length=255, description="기본 주소")
    to_addr2: Optional[str] = Field(None, max_length=255, description="상세 주소")


class DeliveryInfo(BaseModel):
    """배송 정보"""
    ship_cost: Optional[float] = Field(None, description="배송비")
    ship_method: Optional[str] = Field(None, description="배송 방법")
    ship_msg: Optional[str] = Field(None, description="배송 메시지")
    carr_name: Optional[str] = Field(None, max_length=30, description="택배사명")
    carr_no: Optional[str] = Field(None, max_length=5, description="택배사 코드")
    invoice_no: Optional[str] = Field(None, max_length=20, description="송장번호")
    invoice_send_time: Optional[datetime] = Field(None, description="송장 발송 시각")


class PaymentInfo(BaseModel):
    """결제 정보"""
    pay_amt: Optional[float] = Field(None, description="결제 금액")
    discount_amt: Optional[float] = Field(None, description="할인 금액")
    sales: Optional[float] = Field(None, description="매출")
    pay_method: Optional[str] = Field(None, description="결제 수단")
    pay_time: Optional[datetime] = Field(None, description="결제 시각")


class PlayautoOrder(BaseModel):
    """플레이오토 주문 데이터 (80+ 필드 지원)"""
    # ========================================
    # 기존 필드 (하위 호환성 유지)
    # ========================================
    playauto_order_id: str = Field(..., description="플레이오토 주문 ID")
    market: str = Field(..., description="마켓 (coupang, naver, 11st 등)")
    order_number: str = Field(..., description="마켓 주문번호")
    customer_name: str = Field(..., description="고객명")
    customer_phone: Optional[str] = Field(None, description="고객 전화번호")
    customer_address: str = Field(..., description="고객 주소")
    customer_zipcode: Optional[str] = Field(None, description="고객 우편번호")
    total_amount: float = Field(0, ge=0, description="총 주문 금액")
    order_date: Optional[datetime] = Field(None, description="주문 일시")
    order_status: Optional[str] = Field("pending", description="주문 상태")
    items: List[OrderItem] = Field(default_factory=list, description="주문 상품 목록")

    # ========================================
    # 신규 필드 (공식 API)
    # ========================================
    # 핵심 필드
    uniq: Optional[str] = Field(None, max_length=20, description="주문 고유번호")
    bundle_no: Optional[str] = Field(None, max_length=20, description="묶음 번호")
    sol_no: Optional[int] = Field(None, description="솔루션 번호")

    # 마켓 정보
    shop_cd: Optional[str] = Field(None, max_length=4, description="쇼핑몰 코드")
    shop_name: Optional[str] = Field(None, max_length=50, description="쇼핑몰명")
    shop_id: Optional[str] = Field(None, max_length=40, description="쇼핑몰 ID")
    shop_ord_no: Optional[str] = Field(None, max_length=50, description="쇼핑몰 주문번호")

    # 상태 정보
    ord_status: Optional[str] = Field(None, description="주문 상태")
    ord_time: Optional[datetime] = Field(None, description="주문 시각")
    ord_confirm_time: Optional[datetime] = Field(None, description="주문 확인 시각")

    # 중첩 객체
    orderer: Optional[OrdererInfo] = Field(None, description="주문자 정보")
    receiver: Optional[ReceiverInfo] = Field(None, description="수령인 정보")
    delivery: Optional[DeliveryInfo] = Field(None, description="배송 정보")
    payment: Optional[PaymentInfo] = Field(None, description="결제 정보")

    # 상품 정보
    shop_sale_no: Optional[str] = Field(None, max_length=40, description="쇼핑몰 상품번호")
    shop_sale_name: Optional[str] = Field(None, max_length=255, description="쇼핑몰 상품명")
    shop_opt_name: Optional[str] = Field(None, max_length=250, description="옵션명")
    sale_cnt: Optional[int] = Field(None, description="판매 수량")
    sales: Optional[float] = Field(None, description="판매 금액")
    c_sale_cd: Optional[str] = Field(None, max_length=40, description="상품 코드")

    # 매칭 정보
    map_yn: Optional[int] = Field(None, description="매칭 여부 (0/1)")
    sku_cd: Optional[str] = Field(None, max_length=40, description="SKU 코드")
    prod_name: Optional[str] = Field(None, max_length=200, description="상품명")


class OrdersFetchRequest(BaseModel):
    """주문 수집 요청 (공식 API 호환)"""
    # 페이지네이션
    start: int = Field(0, ge=0, description="시작 인덱스 (offset)")
    length: int = Field(500, ge=1, le=3000, description="조회 개수")

    # 정렬
    orderby: Optional[str] = Field("wdate desc", description="정렬 기준")

    # 날짜 필터
    date_type: str = Field("wdate", description="날짜 유형 (wdate, udate 등)")
    sdate: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    edate: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")

    # 마켓/상태 필터 (다중)
    shop_cd: Optional[str] = Field(None, description="쇼핑몰 코드")
    status: List[str] = Field(default_factory=lambda: ["ALL"], description="주문 상태 리스트")

    # 검색
    search_key: Optional[str] = Field(None, description="검색 필드 (order_name, shop_ord_no 등)")
    search_word: Optional[str] = Field(None, description="검색어")
    search_type: Optional[str] = Field("partial", description="검색 방식 (partial/exact)")

    # 묶음 주문
    bundle_yn: bool = Field(False, description="묶음 주문 그룹화")

    # 레거시 필드 (하위 호환성)
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD) - 레거시")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD) - 레거시")
    market: Optional[str] = Field(None, description="특정 마켓 필터 - 레거시")
    order_status: Optional[str] = Field(None, description="주문 상태 필터 - 레거시")
    page: int = Field(1, ge=1, description="페이지 번호 - 레거시")
    limit: int = Field(100, ge=1, le=1000, description="페이지당 항목 수 - 레거시")
    auto_sync: bool = Field(False, description="자동 동기화 여부 - 레거시")


class OrdersFetchResponse(BaseModel):
    """주문 수집 응답"""
    success: bool = Field(..., description="성공 여부")
    total: int = Field(..., description="총 주문 수")
    page: int = Field(..., description="현재 페이지")
    orders: List[PlayautoOrder] = Field(..., description="주문 목록")
    synced_count: Optional[int] = Field(0, description="동기화된 주문 수")


# ========================================
# 송장 관련 모델
# ========================================

class TrackingItem(BaseModel):
    """송장 정보"""
    playauto_order_id: Optional[str] = Field(None, description="플레이오토 주문 ID")
    order_number: str = Field(..., description="마켓 주문번호")
    tracking_number: str = Field(..., min_length=10, description="송장번호")
    courier_code: str = Field(..., description="택배사 코드")
    courier_name: Optional[str] = Field(None, description="택배사명")


class UploadTrackingRequest(BaseModel):
    """송장 업로드 요청"""
    tracking_data: List[TrackingItem] = Field(..., min_items=1, description="송장 정보 목록")


class UploadTrackingResponse(BaseModel):
    """송장 업로드 응답"""
    success: bool = Field(..., description="성공 여부")
    total_count: int = Field(..., description="총 업로드 시도 수")
    success_count: int = Field(..., description="성공 수")
    fail_count: int = Field(..., description="실패 수")
    failed_items: List[dict] = Field(default_factory=list, description="실패 항목 목록")


# ========================================
# 로그 및 통계 모델
# ========================================

class SyncLog(BaseModel):
    """동기화 로그"""
    id: int
    sync_type: str = Field(..., description="동기화 유형")
    status: str = Field(..., description="상태")
    items_count: int = Field(0, description="항목 수")
    success_count: int = Field(0, description="성공 수")
    fail_count: int = Field(0, description="실패 수")
    error_message: Optional[str] = Field(None, description="에러 메시지")
    execution_time: Optional[float] = Field(None, description="실행 시간 (초)")
    created_at: datetime = Field(..., description="생성 시각")


class PlayautoStats(BaseModel):
    """플레이오토 통계"""
    total_orders: int = Field(0, description="총 수집 주문 수")
    synced_orders: int = Field(0, description="동기화된 주문 수")
    uploaded_tracking: int = Field(0, description="업로드된 송장 수")
    today_synced: int = Field(0, description="오늘 동기화 수")
    recent_trend: List[dict] = Field(default_factory=list, description="최근 7일 추이")


# ========================================
# 연결 테스트 모델
# ========================================

class ConnectionTestResponse(BaseModel):
    """연결 테스트 응답"""
    success: bool = Field(..., description="연결 성공 여부")
    message: str = Field(..., description="결과 메시지")
    api_key_masked: Optional[str] = Field(None, description="마스킹된 API 키")
    base_url: Optional[str] = Field(None, description="API 기본 URL")
