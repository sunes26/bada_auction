/**
 * 통합 주문 관리 페이지 (Unified Order Management Page)
 *
 * 이 컴포넌트는 플레이오토 연동 주문과 수동 입력 주문을 통합하여 관리합니다.
 *
 * 주요 기능:
 * - 6개 탭: 대시보드, 주문 목록, 플레이오토 설정, 자동 가격 조정, 송장 관리, 소싱처 계정
 * - 플레이오토 API 연동 (주문 동기화, 송장 업로드)
 * - 자동 가격 조정 시스템
 * - 송장 관리 및 추적
 *
 * @author onbaek-ai
 * @version 2.0.0
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Package,
  Plus,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  RefreshCw,
  Play,
  Truck,
  BarChart3,
  Filter,
  AlertCircle,
  TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';
import AdvancedFilter, { FilterConfig } from '@/components/ui/AdvancedFilter';
import FilterPresets, { saveFilterPreset } from '@/components/ui/FilterPresets';
import ExportButton from '@/components/ui/ExportButton';
import { Trash2 } from 'lucide-react';
import { ordersApi, playautoApi, cache } from '@/lib/api';
import type { Order as OrderType, OrderItem as OrderItemType, PlayautoConfig } from '@/lib/types';
import OrderMonitorWidget from '@/components/ui/OrderMonitorWidget';
import MarketStatsGrid from '@/components/ui/MarketStatsGrid';
import OrderStatusBadges from '@/components/ui/OrderStatusBadges';
import TrackingSchedulerPage from '@/components/pages/TrackingSchedulerPage';
import { API_BASE_URL } from '@/lib/api';

// ============= TypeScript 인터페이스 정의 =============

// 주문 관련 인터페이스 (기존 로컬 타입 유지, 추후 lib/types.ts로 완전 이동)
interface Order extends OrderType {
  order_status: string;
  order_source?: string; // 'playauto' | 'manual'
}

interface OrderItem extends OrderItemType {
  profit: number;
  option?: string;
}

// 플레이오토 관련 인터페이스


interface PlayautoOrder {
  playauto_order_id: string;
  market: string;
  order_number: string;
  customer_name: string;
  customer_phone?: string;
  customer_address: string;
  customer_zipcode?: string;
  total_amount: number;
  order_date?: string;
  order_status?: string;
  items?: OrderItem[];
  synced_to_local: boolean;
  created_at: string;
}

interface PlayautoStats {
  total_orders_synced: number;
  total_items_synced: number;
  successful_tracking_uploads: number;
  failed_tracking_uploads: number;
  sync_logs_count: number;
}

interface SyncLog {
  id: number;
  sync_type: string;
  status: string;
  items_count: number;
  success_count: number;
  fail_count: number;
  error_message?: string;
  execution_time?: number;
  created_at: string;
}


// 탭 타입 정의
type TabType = 'dashboard' | 'orders' | 'tracking' | 'auto-pricing';

// 주문 필터 타입
type OrderSourceFilter = 'all' | 'playauto' | 'manual';

// ============= 메인 컴포넌트 =============

export default function UnifiedOrderManagementPage() {
  // 탭 관리
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  // 대시보드 탭 상태
  const [stats, setStats] = useState<PlayautoStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<SyncLog[]>([]);

  // 주문 탭 상태
  const [rawManualOrders, setRawManualOrders] = useState<Order[]>([]);
  const [rawPlayautoOrders, setRawPlayautoOrders] = useState<Order[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [orderSourceFilter, setOrderSourceFilter] = useState<OrderSourceFilter>('all');
  const [searchQuery, setSearchQuery] = useState<string>(''); // 검색어 상태
  const [orderFilters, setOrderFilters] = useState({
    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    market: '',
    order_status: ''
  });
  const [advancedFilters, setAdvancedFilters] = useState<FilterConfig>({});
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0
  });



  // 자동 가격 조정 설정 (항상 활성화)
  const [autoPricingSettings, setAutoPricingSettings] = useState({
    enabled: true,  // 무조건 활성화
    target_margin: 30.0,
    min_margin: 15.0,
    price_unit: 100,
    auto_disable_on_low_margin: true
  });

  // 주문 처리 상태 (송장 입력 모달)
  const [isTrackingModalOpen, setIsTrackingModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [trackingInfo, setTrackingInfo] = useState({
    carrier_code: '4', // 기본값: CJ대한통운
    tracking_number: ''
  });

  // 송장 관리 탭 상태
  const [trackingHistory, setTrackingHistory] = useState<SyncLog[]>([]);
  const [trackingStats, setTrackingStats] = useState({
    total_uploaded: 0,
    success_rate: 0,
    last_upload_at: null as string | null
  });
  const [completedOrders, setCompletedOrders] = useState<Order[]>([]); // 출고완료된 주문


  // ============= API 호출 함수 =============

  // 대시보드 관련
  const loadStats = useCallback(async () => {
    try {
      const data = await fetch(`${API_BASE_URL}/api/playauto/stats`).then(r => r.json());
      setStats(data);
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  }, []);

  const loadRecentLogs = useCallback(async () => {
    try {
      const data = await fetch(`${API_BASE_URL}/api/playauto/sync-logs?limit=10`).then(r => r.json());
      if (data.success) {
        setRecentLogs(data.logs);
      }
    } catch (error) {
      console.error('로그 로드 실패:', error);
    }
  }, []);

  /**
   * 주문 조회 (통합)
   * - 수동 주문과 플레이오토 주문을 함께 가져와서 저장
   * - 필터링은 별도 useEffect에서 처리 (클라이언트 사이드)
   */
  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true);

      // 수동 주문 가져오기 (공통 API 클라이언트 사용, 캐싱 적용)
      const manualData = await ordersApi.list(50, true);
      const manualOrders = manualData.success && manualData.orders ? manualData.orders.map((o: OrderType) => ({ ...o, source: 'manual' as const, order_status: o.status, order_source: 'manual' })) : [];

      // 플레이오토 주문 가져오기 (API 키가 없으면 스킵)
      let playautoOrders: Order[] = [];
      try {
        // 공통 API 클라이언트 사용 (캐싱 적용)
        const playautoData = await playautoApi.getOrders(50, false) as any; // 캐시 비활성화

        console.log('[DEBUG] PlayAuto API 응답:', playautoData);

        // 백엔드 응답: { success: true, orders: [...], total: 0 }
        const orders = playautoData.orders || playautoData.data || [];
        if (playautoData.success && orders.length > 0) {
          playautoOrders = orders.map((o: any) => ({
            id: o.playauto_order_id || o.id,
            order_number: o.order_number,
            market: o.market,
            customer_name: o.customer_name,
            customer_phone: o.customer_phone,
            customer_address: o.customer_address,
            total_amount: o.total_amount,
            order_date: o.ord_time || o.order_date || o.created_at,  // ord_time 우선 사용
            status: (o.order_status || o.status || 'pending') as 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled',
            order_status: o.ord_status || o.order_status || o.status || 'pending',  // ord_status 우선 사용
            source: 'playauto' as const,
            order_source: 'playauto',
            created_at: o.ord_time || o.created_at,  // ord_time 우선 사용
            updated_at: o.updated_at || o.created_at,
            // PlayAuto 전용 필드 추가
            playauto_order_id: o.playauto_order_id || o.uniq,
            bundle_no: o.bundle_no,  // 송장 업데이트에 필요한 묶음번호
            shop_cd: o.shop_cd,
            shop_sale_no: o.shop_sale_no,
            shop_sale_name: o.shop_sale_name,
            shop_opt_name: o.shop_opt_name,
            sale_cnt: o.sale_cnt,
            sales: o.sales,
            sales_unit: o.sales_unit,  // 단가
            prod_name: o.prod_name
          }));
        }
      } catch (error) {
        // 플레이오토 API 에러는 무시 (API 키가 없거나 서비스 미사용)
        console.log('플레이오토 주문 로드 스킵:', error);
      }

      // Raw 데이터 저장 (필터링 없이)
      setRawManualOrders(manualOrders);
      setRawPlayautoOrders(playautoOrders);
    } catch (error) {
      console.error('주문 조회 실패:', error);
      toast.error('주문 조회에 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [orderFilters, pagination.page, pagination.limit]);

  /**
   * 고급 필터 적용
   * @param filters - FilterConfig 객체
   */
  const applyAdvancedFilters = useCallback((filters: FilterConfig) => {
    setAdvancedFilters(filters);
    let filtered = [...orders];

    // 가격 범위 필터
    if (filters.priceRange) {
      filtered = filtered.filter(order =>
        order.total_amount >= filters.priceRange!.min &&
        order.total_amount <= filters.priceRange!.max
      );
    }

    // 날짜 범위 필터
    if (filters.dateRange?.start || filters.dateRange?.end) {
      filtered = filtered.filter(order => {
        const orderDate = new Date(order.created_at);
        const start = filters.dateRange!.start ? new Date(filters.dateRange!.start) : new Date(0);
        const end = filters.dateRange!.end ? new Date(filters.dateRange!.end) : new Date();
        return orderDate >= start && orderDate <= end;
      });
    }

    // 마켓 필터
    if (filters.markets && filters.markets.length > 0) {
      filtered = filtered.filter(order => filters.markets!.includes(order.market));
    }

    // 상태 필터
    if (filters.statuses && filters.statuses.length > 0) {
      filtered = filtered.filter(order => filters.statuses!.includes(order.order_status));
    }

    setFilteredOrders(filtered);
    setPagination(prev => ({ ...prev, total: filtered.length }));
    toast.success(`필터 적용됨: ${filtered.length}건의 주문`);
  }, [orders]);

  /**
   * 고급 필터 프리셋 저장
   */
  const handleSaveFilterPreset = useCallback((name: string, filters: FilterConfig) => {
    const success = saveFilterPreset(name, filters);
    if (success) {
      toast.success(`프리셋 "${name}"이 저장되었습니다`);
    } else {
      toast.error('프리셋 저장에 실패했습니다');
    }
  }, []);

  /**
   * 주문 삭제
   */
  const handleDeleteOrder = useCallback(async (orderId: number, orderNumber: string) => {
    // 확인 대화상자
    if (!confirm(`주문 "${orderNumber}"을(를) 정말 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, 관련된 주문 상품도 함께 삭제됩니다.`)) {
      return;
    }

    try {
      // 공통 API 클라이언트 사용
      const data = await ordersApi.delete(orderId);

      if (data.success) {
        toast.success('주문이 삭제되었습니다');
        cache.clearOrders();
        fetchOrders();
      } else {
        toast.error('주문 삭제에 실패했습니다');
      }
    } catch (error) {
      console.error('주문 삭제 실패:', error);
      toast.error('주문 삭제 중 오류가 발생했습니다');
    }
  }, [fetchOrders]);

  /**
   * 상품 매칭 (주문 상품 → 내 판매 상품 찾기)
   *
   * 우선순위:
   * 1. shop_cd + shop_sale_no로 마켓 코드 매칭
   * 2. 상품명으로 폴백 검색
   */
  const matchOrderWithProduct = async (order: Order) => {
    try {
      // PlayAuto 주문에서 shop_cd, shop_sale_no 추출
      const shopCd = (order as any).shop_cd;
      const shopSaleNo = (order as any).shop_sale_no;
      const shopSaleName = (order as any).shop_sale_name;

      // 검색 파라미터 구성
      const params = new URLSearchParams();
      if (shopCd) params.append('shop_cd', shopCd);
      if (shopSaleNo) params.append('shop_sale_no', shopSaleNo);
      if (shopSaleName) params.append('query', shopSaleName);

      const res = await fetch(`${API_BASE_URL}/api/products/search?${params.toString()}`);
      const data = await res.json();

      if (data.success && data.products && data.products.length > 0) {
        const matchedProduct = data.products[0];
        console.log(`[상품매칭] 성공: ${data.matched_by}, shop_cd=${shopCd}, shop_sale_no=${shopSaleNo}`);
        return {
          sourcing_url: matchedProduct.sourcing_url,
          sourcing_source: matchedProduct.sourcing_source,
          product_id: matchedProduct.id
        };
      }

      console.log(`[상품매칭] 실패: shop_cd=${shopCd}, shop_sale_no=${shopSaleNo}, shop_sale_name=${shopSaleName}`);
      return null;
    } catch (error) {
      console.error('상품 매칭 실패:', error);
      return null;
    }
  };

  /**
   * 구매하기 버튼 핸들러
   */
  const handlePurchase = async (order: Order) => {
    try {
      // 상품 매칭
      const productMatch = await matchOrderWithProduct(order);

      if (!productMatch) {
        const shopCd = (order as any).shop_cd;
        const shopSaleNo = (order as any).shop_sale_no;
        if (shopCd && shopSaleNo) {
          toast.error(`상품을 찾을 수 없습니다. 상품 탭에서 [쇼핑몰 상품코드 수집]을 먼저 진행해주세요.\n\n마켓: ${shopCd}\n상품코드: ${shopSaleNo}`);
        } else {
          toast.error('주문에 마켓 코드 정보가 없습니다. 플레이오토에서 주문을 다시 동기화해주세요.');
        }
        return;
      }

      if (!productMatch.sourcing_url) {
        toast.error('소싱처 URL이 등록되지 않았습니다. 상품 탭에서 소싱처 URL을 먼저 등록해주세요.');
        return;
      }

      // 배송지 정보를 로컬스토리지에 저장 (크롬 확장에서 사용)
      localStorage.setItem('current_order_address', JSON.stringify({
        name: order.customer_name,
        phone: order.customer_phone || '',
        address: order.customer_address || '',
        bundle_no: order.playauto_order_id || order.order_number
      }));

      // 소싱처 링크 열기
      window.open(productMatch.sourcing_url, '_blank');

      toast.info(`${productMatch.sourcing_source}에서 구매를 진행해주세요.\n배송지는 자동으로 입력됩니다.`);
    } catch (error) {
      console.error('구매하기 실패:', error);
      toast.error('구매 처리 중 오류가 발생했습니다');
    }
  };

  /**
   * 송장 입력 모달 열기
   */
  const openTrackingModal = (order: Order) => {
    setSelectedOrder(order);
    setTrackingInfo({
      carrier_code: '4', // 기본값: CJ대한통운
      tracking_number: ''
    });
    setIsTrackingModalOpen(true);
  };

  /**
   * 송장 입력 모달 닫기
   */
  const closeTrackingModal = () => {
    setIsTrackingModalOpen(false);
    setSelectedOrder(null);
    setTrackingInfo({
      carrier_code: '4',
      tracking_number: ''
    });
  };

  /**
   * 송장 번호 업데이트 핸들러
   */
  const handleUpdateTracking = async () => {
    if (!selectedOrder) return;

    if (!trackingInfo.tracking_number.trim()) {
      toast.error('송장번호를 입력해주세요');
      return;
    }

    try {
      setActionLoading({ ...actionLoading, 'update-tracking': true });

      // PlayAuto API 호출 (송장 업데이트)
      // bundle_no 필드 사용 (uniq가 아님!)
      const bundle_no = (selectedOrder as any).bundle_no || selectedOrder.playauto_order_id || selectedOrder.order_number;
      console.log('[DEBUG] 송장 업데이트 - bundle_no:', bundle_no);

      const res = await fetch(`${API_BASE_URL}/api/playauto/orders/invoice`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orders: [{
            bundle_no: bundle_no,
            carr_no: trackingInfo.carrier_code,
            invoice_no: trackingInfo.tracking_number
          }],
          overwrite: true,
          change_complete: true  // 출고완료로 변경
        })
      });

      const data = await res.json();

      if (data.success) {
        toast.success('송장 등록 완료! 출고완료 처리되었습니다.');
        closeTrackingModal();
        fetchOrders(); // 주문 목록 새로고침
      } else {
        throw new Error(data.message || '송장 업데이트 실패');
      }
    } catch (error) {
      console.error('송장 업데이트 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      toast.error(`송장 업데이트 실패: ${errorMessage}`);
    } finally {
      setActionLoading({ ...actionLoading, 'update-tracking': false });
    }
  };


  // 플레이오토 설정 관련

  // 자동 가격 조정 설정 관련
  const loadAutoPricingSettings = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auto-pricing/settings`);
      if (!res.ok) throw new Error('자동 가격 조정 설정 조회 실패');
      const data = await res.json();
      if (data.success && data.settings) {
        // enabled는 항상 true로 강제 설정
        setAutoPricingSettings({ ...data.settings, enabled: true });
      }
    } catch (error) {
      console.error('자동 가격 조정 설정 로드 실패:', error);
    }
  };

  const saveAutoPricingSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionLoading({ ...actionLoading, 'save-auto-pricing': true });
      const res = await fetch(`${API_BASE_URL}/api/auto-pricing/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // enabled는 항상 true로 강제 전송
        body: JSON.stringify({ ...autoPricingSettings, enabled: true })
      });
      const data = await res.json();
      if (data.success) {
        toast.success('자동 가격 조정 설정이 저장되었습니다');
        await loadAutoPricingSettings();
      } else {
        throw new Error(data.message || '설정 저장 실패');
      }
    } catch (error) {
      console.error('설정 저장 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      toast.error(`설정 저장 실패: ${errorMessage}`);
    } finally {
      setActionLoading({ ...actionLoading, 'save-auto-pricing': false });
    }
  };

  const adjustAllPrices = async () => {
    try {
      setActionLoading({ ...actionLoading, 'adjust-all-prices': true });
      const res = await fetch(`${API_BASE_URL}/api/auto-pricing/adjust-all`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        toast.success(`${data.adjusted_count}개 상품의 가격이 조정되었습니다.\n비활성화: ${data.disabled_count}개`);
      } else {
        toast.error(data.message || '가격 조정에 실패했습니다');
      }
    } catch (error) {
      console.error('가격 조정 실패:', error);
      toast.error('가격 조정 중 오류가 발생했습니다');
    } finally {
      setActionLoading({ ...actionLoading, 'adjust-all-prices': false });
    }
  };


  // 송장 관련
  const autoUploadTracking = async (days: number = 7) => {
    try {
      setActionLoading({ ...actionLoading, 'auto-upload': true });
      const res = await fetch(`${API_BASE_URL}/api/playauto/upload-tracking/auto?days=${days}`, {
        method: 'POST'
      });
      const data = await res.json();

      if (data.success) {
        toast.success(`${data.success_count || 0}개 송장이 업로드되었습니다`);
        await loadTrackingHistory();
        await loadStats();
      } else {
        throw new Error(data.message || '업로드 실패');
      }
    } catch (error) {
      console.error('송장 업로드 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      toast.error(`송장 업로드 실패: ${errorMessage}`);
    } finally {
      setActionLoading({ ...actionLoading, 'auto-upload': false });
    }
  };

  const loadTrackingHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/playauto/tracking-upload-history?limit=20`);
      if (!res.ok) throw new Error('이력 조회 실패');
      const data = await res.json();

      if (data.success) {
        setTrackingHistory(data.logs || []);

        // 통계 계산
        const totalUploaded = data.logs.reduce((sum: number, log: SyncLog) => sum + log.success_count, 0);
        const totalAttempts = data.logs.reduce((sum: number, log: SyncLog) => sum + log.items_count, 0);
        const successRate = totalAttempts > 0 ? (totalUploaded / totalAttempts * 100) : 0;
        const lastLog = data.logs[0];

        setTrackingStats({
          total_uploaded: totalUploaded,
          success_rate: successRate,
          last_upload_at: lastLog ? lastLog.created_at : null
        });
      }
    } catch (error) {
      console.error('이력 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 소싱처 계정 관련

  // ============= useEffect 훅 =============

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadStats();
      loadRecentLogs();
    } else if (activeTab === 'orders') {
      fetchOrders();
    } else if (activeTab === 'tracking') {
      loadTrackingHistory();
      fetchOrders(); // 출고완료 주문 목록을 위해 주문 데이터도 로드
    } else if (activeTab === 'auto-pricing') {
      loadAutoPricingSettings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // 출고완료 상태 확인 헬퍼 함수
  const isCompletedOrder = (order: Order) => {
    const status = (order.order_status || '').toLowerCase();
    // PlayAuto 출고완료 상태 또는 내부 completed 상태
    return status.includes('출고완료') ||
           status.includes('배송완료') ||
           status.includes('배송중') ||
           status === 'completed' ||
           status === 'shipped' ||
           status === 'delivered';
  };

  // 주문 소스 필터 변경 시 클라이언트 사이드 필터링 (API 호출 없음)
  useEffect(() => {
    let allOrders: Order[] = [];

    // 필터에 따라 주문 병합
    if (orderSourceFilter === 'all') {
      allOrders = [...rawManualOrders, ...rawPlayautoOrders];
    } else if (orderSourceFilter === 'manual') {
      allOrders = rawManualOrders;
    } else if (orderSourceFilter === 'playauto') {
      allOrders = rawPlayautoOrders;
    }

    // 날짜 기준으로 정렬 (최신순)
    allOrders.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    // 출고완료된 주문과 미처리 주문 분리
    const completed = allOrders.filter(isCompletedOrder);
    let pending = allOrders.filter(order => !isCompletedOrder(order));

    // 검색어 필터링 (미처리 주문에만 적용)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      pending = pending.filter(order => {
        return (
          order.order_number?.toLowerCase().includes(query) ||
          order.customer_name?.toLowerCase().includes(query) ||
          order.customer_phone?.includes(query) ||
          order.market?.toLowerCase().includes(query)
        );
      });
    }

    setOrders(pending);
    setFilteredOrders(pending);
    setCompletedOrders(completed);
    setPagination(prev => ({ ...prev, total: pending.length, page: 1 })); // 검색 시 1페이지로
  }, [orderSourceFilter, rawManualOrders, rawPlayautoOrders, searchQuery]);

  // 날짜/마켓/상태 필터 변경 시에만 재조회
  useEffect(() => {
    if (activeTab === 'orders') {
      fetchOrders();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderFilters]);

  // 대시보드 자동 새로고침 (1분마다)
  useEffect(() => {
    if (activeTab !== 'dashboard') return;

    const interval = setInterval(() => {
      loadStats();
      loadRecentLogs();
    }, 60000);

    return () => clearInterval(interval);
  }, [activeTab]);

  // ============= 유틸리티 함수 =============

  /**
   * 동기화 상태 뱃지 렌더링
   * @param status - success, failed, partial
   */
  const getSyncStatusBadge = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactElement; text: string }> = {
      success: { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="w-4 h-4" />, text: '성공' },
      failed: { color: 'bg-red-100 text-red-800', icon: <XCircle className="w-4 h-4" />, text: '실패' },
      partial: { color: 'bg-yellow-100 text-yellow-800', icon: <AlertCircle className="w-4 h-4" />, text: '부분성공' }
    };

    const cfg = config[status] || config.failed;
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${cfg.color}`}>
        {cfg.icon}
        {cfg.text}
      </span>
    );
  };

  /**
   * 주문 상태 뱃지 렌더링
   * @param status - pending, processing, completed, cancelled
   */
  const getOrderStatusBadge = (status?: string) => {
    const config: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: '대기' },
      processing: { color: 'bg-blue-100 text-blue-800', text: '처리중' },
      completed: { color: 'bg-green-100 text-green-800', text: '완료' },
      cancelled: { color: 'bg-red-100 text-red-800', text: '취소' }
    };

    const cfg = config[status || 'pending'] || config.pending;
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${cfg.color}`}>
        {cfg.text}
      </span>
    );
  };

  /**
   * 주문 소스 뱃지 렌더링
   * @param source - 'playauto' 또는 'manual'
   */
  const getOrderSourceBadge = (source?: string) => {
    if (source === 'playauto') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
          <Settings className="w-3 h-3" />
          플레이오토
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
          <Plus className="w-3 h-3" />
          수동입력
        </span>
      );
    }
  };

  /**
   * 날짜 포맷 (한국 로케일)
   */
  const formatDate = (dateString: string | undefined | null) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return '-';
      return date.toLocaleString('ko-KR');
    } catch {
      return '-';
    }
  };

  /**
   * 통화 포맷 (원화)
   */
  const formatCurrency = (amount: number) => {
    return amount.toLocaleString() + '원';
  };

  // ============= 렌더링 =============

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl">
            <Package className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-800">통합 주문 관리</h2>
            <p className="text-gray-600">플레이오토 연동 및 수동 주문 관리</p>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="flex gap-2 border-b border-gray-200">
          {[
            { key: 'dashboard', label: '대시보드', icon: <BarChart3 className="w-4 h-4" /> },
            { key: 'orders', label: '주문 목록', icon: <Package className="w-4 h-4" /> },
            { key: 'auto-pricing', label: '자동 가격 조정', icon: <TrendingUp className="w-4 h-4" /> },
            { key: 'tracking', label: '송장 관리', icon: <Truck className="w-4 h-4" /> }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 대시보드 탭 */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* 실시간 주문 모니터링 위젯 */}
          <OrderMonitorWidget
            enabled={true}
            interval={30000}
            showRecentOrders={true}
          />

          {/* 마켓별 통합 통계 그리드 */}
          <MarketStatsGrid
            days={7}
            onMarketClick={(market) => {
              if (market) {
                // 마켓 선택 시 주문 탭으로 이동하고 필터 적용
                setOrderFilters(prev => ({ ...prev, market }));
                setActiveTab('orders');
                toast.success(`${market} 마켓 주문으로 필터링되었습니다`);
              }
            }}
          />

          {/* 주문 상태별 카운트 뱃지 */}
          <OrderStatusBadges
            onStatusClick={(status) => {
              // 상태 선택 시 주문 탭으로 이동하고 필터 적용
              setOrderFilters(prev => ({ ...prev, order_status: status }));
              setActiveTab('orders');
              toast.success(`${status} 주문으로 필터링되었습니다`);
            }}
          />

          {/* 통계 카드 그리드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Package className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{stats?.total_orders_synced || 0}</div>
                  <div className="text-sm opacity-90">동기화된 주문</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Truck className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{stats?.successful_tracking_uploads || 0}</div>
                  <div className="text-sm opacity-90">업로드된 송장</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <CheckCircle className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{stats?.total_items_synced || 0}</div>
                  <div className="text-sm opacity-90">동기화된 상품</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <AlertCircle className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{stats?.failed_tracking_uploads || 0}</div>
                  <div className="text-sm opacity-90">업로드 실패</div>
                </div>
              </div>
            </div>
          </div>

          {/* 빠른 액션 버튼 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-4">빠른 액션</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => setActiveTab('orders')}
                className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:shadow-lg transition-all"
              >
                <Package className="w-6 h-6" />
                <div className="text-left">
                  <div className="font-semibold">주문 조회</div>
                  <div className="text-sm opacity-90">통합 주문 목록</div>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('tracking')}
                className="flex items-center gap-3 p-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all"
              >
                <Truck className="w-6 h-6" />
                <div className="text-left">
                  <div className="font-semibold">송장 업로드</div>
                  <div className="text-sm opacity-90">송장 일괄 등록</div>
                </div>
              </button>
            </div>
          </div>

          {/* 최근 동기화 로그 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">최근 동기화 로그</h3>
              <button
                onClick={() => { loadRecentLogs(); loadStats(); }}
                className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                새로고침
              </button>
            </div>

            {recentLogs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>동기화 로그가 없습니다</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentLogs.map((log) => (
                  <div key={log.id} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-semibold text-gray-800">
                          {log.sync_type === 'order_fetch' && '주문 수집'}
                          {log.sync_type === 'tracking_upload' && '송장 업로드'}
                          {log.sync_type === 'product_sync' && '상품 동기화'}
                        </span>
                        <p className="text-sm text-gray-600">{formatDate(log.created_at)}</p>
                      </div>
                      {getSyncStatusBadge(log.status)}
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm mt-3">
                      <div>
                        <span className="text-gray-600">전체:</span>
                        <p className="text-gray-800 font-bold">{log.items_count}건</p>
                      </div>
                      <div>
                        <span className="text-gray-600">성공:</span>
                        <p className="text-green-600 font-bold">{log.success_count}건</p>
                      </div>
                      <div>
                        <span className="text-gray-600">실패:</span>
                        <p className="text-red-600 font-bold">{log.fail_count}건</p>
                      </div>
                      <div>
                        <span className="text-gray-600">실행시간:</span>
                        <p className="text-gray-800 font-bold">{log.execution_time?.toFixed(2) || 0}초</p>
                      </div>
                    </div>
                    {log.error_message && (
                      <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
                        {log.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 주문 목록 탭 (통합) */}
      {activeTab === 'orders' && (
        <div className="space-y-6">
          {/* 필터 섹션 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Filter className="w-5 h-5" />
              주문 필터
            </h3>

            {/* 검색창 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">🔍 빠른 검색</label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="주문번호, 고객명, 전화번호, 마켓으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 pl-11 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                />
                <svg
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              {searchQuery && (
                <p className="mt-2 text-sm text-gray-600">
                  "{searchQuery}" 검색 결과: <span className="font-bold text-purple-600">{filteredOrders.length}개</span>
                </p>
              )}
            </div>

            {/* 주문 소스 필터 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">주문 소스</label>
              <div className="flex gap-3">
                <button
                  onClick={() => setOrderSourceFilter('all')}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    orderSourceFilter === 'all'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  전체
                </button>
                <button
                  onClick={() => setOrderSourceFilter('playauto')}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    orderSourceFilter === 'playauto'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  플레이오토
                </button>
                <button
                  onClick={() => setOrderSourceFilter('manual')}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    orderSourceFilter === 'manual'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  수동입력
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">시작 날짜</label>
                <input
                  type="date"
                  value={orderFilters.start_date}
                  onChange={(e) => setOrderFilters({ ...orderFilters, start_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">종료 날짜</label>
                <input
                  type="date"
                  value={orderFilters.end_date}
                  onChange={(e) => setOrderFilters({ ...orderFilters, end_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">마켓</label>
                <select
                  value={orderFilters.market}
                  onChange={(e) => setOrderFilters({ ...orderFilters, market: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">전체</option>
                  <option value="coupang">쿠팡</option>
                  <option value="naver">네이버</option>
                  <option value="11st">11번가</option>
                  <option value="gmarket">G마켓</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">주문 상태</label>
                <select
                  value={orderFilters.order_status}
                  onChange={(e) => setOrderFilters({ ...orderFilters, order_status: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">전체</option>
                  <option value="pending">대기</option>
                  <option value="processing">처리중</option>
                  <option value="completed">완료</option>
                  <option value="cancelled">취소</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={fetchOrders}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    조회 중...
                  </>
                ) : (
                  <>
                    <Package className="w-5 h-5" />
                    주문 조회
                  </>
                )}
              </button>
              <AdvancedFilter
                onFilterChange={applyAdvancedFilters}
                onSavePreset={handleSaveFilterPreset}
                availableMarkets={['coupang', 'naver', '11st', 'gmarket']}
                availableStatuses={['pending', 'processing', 'completed', 'cancelled']}
              />
              <ExportButton
                data={filteredOrders.map(order => ({
                  '주문번호': order.order_number,
                  '마켓': order.market,
                  '고객명': order.customer_name,
                  '전화번호': order.customer_phone || '-',
                  '배송지': order.customer_address,
                  '주문금액': order.total_amount,
                  '상태': order.order_status,
                  '소스': order.order_source === 'playauto' ? '플레이오토' : '수동입력',
                  '주문일시': new Date(order.created_at).toLocaleString('ko-KR')
                }))}
                filename="주문목록"
                buttonText="엑셀 내보내기"
              />
            </div>
          </div>

          {/* 필터 프리셋 */}
          <FilterPresets
            onLoadPreset={applyAdvancedFilters}
            currentFilters={advancedFilters}
          />

          {/* 주문 리스트 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" />
              미처리 주문 ({filteredOrders.length}건)
              {completedOrders.length > 0 && (
                <span className="text-sm font-normal text-gray-500 ml-2">
                  | 출고완료 {completedOrders.length}건은 송장관리 탭에서 확인
                </span>
              )}
            </h3>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">주문 조회 중...</p>
              </div>
            ) : filteredOrders.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>조회된 주문이 없습니다</p>
                <p className="text-sm mt-2">필터를 조정하거나 주문을 생성해보세요</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredOrders.map((order) => (
                  <div key={order.id} className="border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="text-lg font-bold text-gray-800">{order.order_number}</h4>
                        <p className="text-sm text-gray-600">
                          {order.market} | {order.customer_name}
                        </p>
                      </div>
                      <div className="flex gap-2 items-center">
                        {getOrderStatusBadge(order.order_status)}
                        {getOrderSourceBadge(order.order_source)}
                        <button
                          onClick={() => handleDeleteOrder(order.id, order.order_number)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="주문 삭제"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* 상품 정보 */}
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-medium text-gray-800">
                            {(order as any).shop_sale_name || (order as any).prod_name || '상품명 없음'}
                          </p>
                          {(order as any).shop_opt_name && (
                            <p className="text-sm text-gray-500 mt-1">옵션: {(order as any).shop_opt_name}</p>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-sm text-gray-500">
                            수량: {(order as any).sale_cnt ?? 1}개
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                      <div>
                        <span className="text-gray-600">주문 금액:</span>
                        {(() => {
                          const saleCnt = (order as any).sale_cnt ?? 1;
                          const unitPrice = (order as any).sales || order.total_amount || 0;
                          const totalAmount = saleCnt * unitPrice;
                          return (
                            <p className="text-gray-800 font-bold">
                              {saleCnt > 1
                                ? `${saleCnt}개 × ${formatCurrency(unitPrice)} = ${formatCurrency(totalAmount)}`
                                : formatCurrency(unitPrice)
                              }
                            </p>
                          );
                        })()}
                      </div>
                      <div>
                        <span className="text-gray-600">배송지:</span>
                        <p className="text-gray-800 truncate">{order.customer_address}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">연락처:</span>
                        <p className="text-gray-800">{order.customer_phone || '-'}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">주문 일시:</span>
                        <p className="text-gray-800">{formatDate(order.order_date)}</p>
                      </div>
                    </div>

                    {/* 주문 처리 버튼 */}
                    <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200">
                      <button
                        onClick={() => handlePurchase(order)}
                        className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2"
                      >
                        🛒 구매하기
                      </button>
                      <button
                        onClick={() => openTrackingModal(order)}
                        className="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-teal-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2"
                      >
                        📝 송장 입력
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 송장 관리 탭 - 출고완료된 주문 목록 */}
      {activeTab === 'tracking' && (
        <div className="space-y-6">
          {/* 출고완료 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <Truck className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{completedOrders.length}</div>
                  <div className="text-sm opacity-90">출고완료 주문</div>
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <CheckCircle className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{trackingStats.total_uploaded}</div>
                  <div className="text-sm opacity-90">업로드된 송장</div>
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <BarChart3 className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{trackingStats.success_rate}%</div>
                  <div className="text-sm opacity-90">성공률</div>
                </div>
              </div>
            </div>
          </div>

          {/* 출고완료 주문 목록 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Truck className="w-5 h-5 text-green-600" />
              출고완료 주문 목록 ({completedOrders.length}건)
            </h3>

            {completedOrders.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Truck className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>출고완료된 주문이 없습니다</p>
                <p className="text-sm mt-2">주문 목록에서 송장을 등록하면 여기에 표시됩니다</p>
              </div>
            ) : (
              <div className="space-y-3">
                {completedOrders.map((order) => (
                  <div key={order.id} className="border border-green-200 bg-green-50/50 rounded-xl p-6 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="text-lg font-bold text-gray-800">{order.order_number}</h4>
                        <p className="text-sm text-gray-600">
                          {order.market} | {order.customer_name}
                        </p>
                      </div>
                      <div className="flex gap-2 items-center">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          {order.order_status}
                        </span>
                        {order.tracking_number && (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                            <Truck className="w-4 h-4 mr-1" />
                            {order.tracking_number}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 상품 정보 */}
                    <div className="bg-white rounded-lg p-3 mb-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-medium text-gray-800">
                            {(order as any).shop_sale_name || (order as any).prod_name || '상품명 없음'}
                          </p>
                          {(order as any).shop_opt_name && (
                            <p className="text-sm text-gray-500 mt-1">옵션: {(order as any).shop_opt_name}</p>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-sm text-gray-500">
                            수량: {(order as any).sale_cnt ?? 1}개
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">주문 금액:</span>
                        {(() => {
                          const saleCnt = (order as any).sale_cnt ?? 1;
                          const unitPrice = (order as any).sales || order.total_amount || 0;
                          const totalAmount = saleCnt * unitPrice;
                          return (
                            <p className="text-gray-800 font-bold">
                              {saleCnt > 1
                                ? `${saleCnt}개 × ${formatCurrency(unitPrice)} = ${formatCurrency(totalAmount)}`
                                : formatCurrency(unitPrice)
                              }
                            </p>
                          );
                        })()}
                      </div>
                      <div>
                        <span className="text-gray-600">배송지:</span>
                        <p className="text-gray-800 truncate">{order.customer_address}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">주문일시:</span>
                        <p className="text-gray-800">{formatDate(order.order_date || order.created_at)}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">전화번호:</span>
                        <p className="text-gray-800">{order.customer_phone || '-'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 송장 업로드 이력 */}
          {trackingHistory.length > 0 && (
            <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
              <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <Clock className="w-5 h-5 text-purple-600" />
                송장 업로드 이력
              </h3>
              <div className="space-y-3">
                {trackingHistory.slice(0, 10).map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div className="flex items-center gap-4">
                      {getSyncStatusBadge(log.status)}
                      <div>
                        <p className="font-medium text-gray-800">
                          {log.success_count}건 성공 / {log.fail_count}건 실패
                        </p>
                        <p className="text-sm text-gray-500">
                          {formatDate(log.created_at)}
                        </p>
                      </div>
                    </div>
                    {log.error_message && (
                      <p className="text-sm text-red-600 max-w-md truncate">{log.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 자동 가격 조정 탭 */}
      {activeTab === 'auto-pricing' && (
        <div className="space-y-6">
          {/* 설정 패널 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-800">자동 가격 조정 설정</h3>
                <p className="text-gray-600 mt-2">소싱가 변동 시 자동으로 판매가를 조정합니다</p>
              </div>
              <div className="px-4 py-2 rounded-full font-semibold bg-green-100 text-green-800">
                활성화됨
              </div>
            </div>

            {/* 설정 폼 */}
            <form onSubmit={saveAutoPricingSettings} className="space-y-6">
              {/* 목표 마진율 */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    목표 마진율 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={autoPricingSettings.target_margin}
                    onChange={(e) => setAutoPricingSettings({
                      ...autoPricingSettings,
                      target_margin: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="30.0"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    예: 30% 입력 시, 소싱가 10,000원 → 판매가 14,300원
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    최소 마진율 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={autoPricingSettings.min_margin}
                    onChange={(e) => setAutoPricingSettings({
                      ...autoPricingSettings,
                      min_margin: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="15.0"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    이 마진율 이하로 떨어지면 자동 비활성화
                  </p>
                </div>
              </div>

              {/* 가격 단위 */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    가격 올림 단위 (원)
                  </label>
                  <select
                    value={autoPricingSettings.price_unit}
                    onChange={(e) => setAutoPricingSettings({
                      ...autoPricingSettings,
                      price_unit: parseInt(e.target.value)
                    })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value={100}>100원 단위</option>
                    <option value={500}>500원 단위</option>
                    <option value={1000}>1,000원 단위</option>
                    <option value={5000}>5,000원 단위</option>
                    <option value={10000}>10,000원 단위</option>
                  </select>
                  <p className="mt-2 text-sm text-gray-600">
                    판매가를 깔끔하게 올림 처리 (예: 14,380원 → 14,400원)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    최소 마진 미달 시 자동 비활성화
                  </label>
                  <label className="relative inline-flex items-center cursor-pointer mt-3">
                    <input
                      type="checkbox"
                      checked={autoPricingSettings.auto_disable_on_low_margin}
                      onChange={(e) => setAutoPricingSettings({
                        ...autoPricingSettings,
                        auto_disable_on_low_margin: e.target.checked
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-14 h-8 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-6 peer-checked:after:border-white after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-purple-600"></div>
                    <span className="ml-3 text-sm font-medium text-gray-700">
                      {autoPricingSettings.auto_disable_on_low_margin ? '활성화' : '비활성화'}
                    </span>
                  </label>
                  <p className="mt-2 text-sm text-gray-600">
                    마진이 최소 마진율 이하면 상품 판매 중단
                  </p>
                </div>
              </div>

              {/* 저장 버튼 */}
              <button
                type="submit"
                disabled={actionLoading['save-auto-pricing']}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-4 rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading['save-auto-pricing'] ? (
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>저장 중...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <Settings className="w-5 h-5" />
                    <span>설정 저장</span>
                  </div>
                )}
              </button>
            </form>
          </div>

          {/* 수동 실행 패널 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-4">수동 가격 조정</h3>
            <p className="text-gray-600 mb-6">
              모든 활성 상품의 가격을 현재 설정에 맞춰 즉시 조정합니다.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">목표 마진율</h4>
                    <p className="text-2xl font-bold text-blue-600">{autoPricingSettings.target_margin}%</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  소싱가에 이 마진율을 적용하여 판매가를 계산합니다
                </p>
              </div>

              <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl border border-red-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">최소 마진율</h4>
                    <p className="text-2xl font-bold text-red-600">{autoPricingSettings.min_margin}%</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  이 마진율 이하로 떨어지면 판매를 중단합니다
                </p>
              </div>
            </div>

            <button
              onClick={adjustAllPrices}
              disabled={actionLoading['adjust-all-prices']}
              className="w-full mt-6 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-4 rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading['adjust-all-prices'] ? (
                <div className="flex items-center justify-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>가격 조정 중...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <Play className="w-5 h-5" />
                  <span>모든 상품 가격 조정 실행</span>
                </div>
              )}
            </button>
          </div>

          {/* 가격 계산 예시 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-4">가격 계산 예시</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">소싱가</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">목표 마진율</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">계산된 가격</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">조정된 판매가</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">실제 마진율</th>
                  </tr>
                </thead>
                <tbody>
                  {[10000, 25000, 50000, 100000].map((sourcingPrice) => {
                    const targetPrice = sourcingPrice / (1 - autoPricingSettings.target_margin / 100);
                    const adjustedPrice = Math.round(targetPrice / autoPricingSettings.price_unit) * autoPricingSettings.price_unit;
                    const actualMargin = ((adjustedPrice - sourcingPrice) / adjustedPrice) * 100;

                    return (
                      <tr key={sourcingPrice} className="border-b border-gray-200">
                        <td className="px-4 py-3 text-sm text-gray-800">{sourcingPrice.toLocaleString()}원</td>
                        <td className="px-4 py-3 text-sm text-gray-800">{autoPricingSettings.target_margin}%</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{Math.round(targetPrice).toLocaleString()}원</td>
                        <td className="px-4 py-3 text-sm font-semibold text-green-600">{adjustedPrice.toLocaleString()}원</td>
                        <td className="px-4 py-3 text-sm font-semibold text-blue-600">{actualMargin.toFixed(1)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-sm text-gray-600">
              * 계산된 가격을 {autoPricingSettings.price_unit.toLocaleString()}원 단위로 올림하여 조정된 판매가가 결정됩니다.
            </p>
          </div>
        </div>
      )}

      {/* 송장 입력 모달 */}
      {isTrackingModalOpen && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">송장번호 입력</h2>

            {/* 주문 정보 요약 */}
            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-gray-600">주문번호</p>
              <p className="text-lg font-bold text-gray-800">{selectedOrder.order_number}</p>
              <p className="text-sm text-gray-600 mt-2">고객명</p>
              <p className="text-gray-800">{selectedOrder.customer_name}</p>
              <p className="text-sm text-gray-600 mt-2">주문금액</p>
              <p className="text-gray-800 font-bold">{formatCurrency(selectedOrder.total_amount)}</p>
            </div>

            {/* 배송사 선택 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                배송사
              </label>
              <select
                value={trackingInfo.carrier_code}
                onChange={(e) => setTrackingInfo({ ...trackingInfo, carrier_code: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="4">CJ대한통운</option>
                <option value="5">한진택배</option>
                <option value="8">롯데택배</option>
                <option value="1">우체국택배</option>
                <option value="6">로젠택배</option>
              </select>
            </div>

            {/* 송장번호 입력 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                송장번호
              </label>
              <input
                type="text"
                value={trackingInfo.tracking_number}
                onChange={(e) => setTrackingInfo({ ...trackingInfo, tracking_number: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="송장번호를 입력하세요"
                autoFocus
              />
              <p className="mt-2 text-sm text-gray-600">
                💡 소싱처에서 복사 → 붙여넣기
              </p>
            </div>

            {/* 버튼 */}
            <div className="flex gap-3">
              <button
                onClick={closeTrackingModal}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleUpdateTracking}
                disabled={actionLoading['update-tracking']}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-teal-600 text-white rounded-xl hover:shadow-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading['update-tracking'] ? '처리 중...' : '저장 및 출고완료 처리'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
