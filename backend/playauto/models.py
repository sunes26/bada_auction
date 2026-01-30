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


class PlayautoOrder(BaseModel):
    """플레이오토 주문 데이터"""
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


class OrdersFetchRequest(BaseModel):
    """주문 수집 요청"""
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    market: Optional[str] = Field(None, description="특정 마켓 필터")
    order_status: Optional[str] = Field(None, description="주문 상태 필터")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(100, ge=1, le=1000, description="페이지당 항목 수")
    auto_sync: bool = Field(False, description="자동 동기화 여부")


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
