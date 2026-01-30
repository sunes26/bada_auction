/**
 * 통합 주문 관리 페이지 (Unified Order Management Page)
 *
 * 이 컴포넌트는 플레이오토 연동 주문과 수동 입력 주문을 통합하여 관리합니다.
 *
 * 주요 기능:
 * - 6개 탭: 대시보드, 주문 목록(통합), 주문 생성, 플레이오토 설정, 송장 관리, 소싱처 계정
 * - 플레이오토 API 연동 (주문 동기화, 송장 업로드)
 * - 수동 주문 생성 및 관리
 * - RPA 관련 기능은 제외됨
 *
 * @author onbaek-ai
 * @version 1.0.0
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
interface PlayautoSettings {
  api_key: string;
  email: string;
  password: string;
  api_base_url: string;
  enabled: boolean;
  auto_sync_enabled: boolean;
  auto_sync_interval: number;
  encrypt_credentials: boolean;
}

interface PlayautoSettingsResponse {
  api_key_masked: string;
  api_base_url: string;
  enabled: boolean;
  auto_sync_enabled: boolean;
  auto_sync_interval: number;
  last_sync_at: string | null;
}

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

// 소싱처 계정 인터페이스
interface SourcingAccount {
  id: number;
  source: string;
  account_id: string;
  account_password: string;
  is_active: boolean;
  created_at: string;
}

// 탭 타입 정의
type TabType = 'dashboard' | 'orders' | 'create' | 'playauto' | 'tracking' | 'scheduler' | 'accounts';

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

  // 주문 생성 탭 상태
  const [orderForm, setOrderForm] = useState({
    order_number: '',
    market: 'coupang',
    customer_name: '',
    customer_phone: '',
    customer_address: '',
    customer_zipcode: '',
    total_amount: 0,
    notes: ''
  });
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [itemForm, setItemForm] = useState({
    product_name: '',
    product_url: '',
    source: 'ssg',
    quantity: 1,
    sourcing_price: 0,
    selling_price: 0
  });

  // 플레이오토 설정 탭 상태
  const [settings, setSettings] = useState<PlayautoSettings>({
    api_key: '',
    email: '',
    password: '',
    api_base_url: 'https://openapi.playauto.io/api',
    enabled: true,
    auto_sync_enabled: false,
    auto_sync_interval: 30,
    encrypt_credentials: true
  });
  const [settingsInfo, setSettingsInfo] = useState<PlayautoSettingsResponse | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<{
    tested: boolean;
    success: boolean;
    message: string;
  } | null>(null);
  const [showApiSecret, setShowApiSecret] = useState(false);

  // 송장 관리 탭 상태
  const [trackingHistory, setTrackingHistory] = useState<SyncLog[]>([]);
  const [trackingStats, setTrackingStats] = useState({
    total_uploaded: 0,
    success_rate: 0,
    last_upload_at: null as string | null
  });

  // 소싱처 계정 탭 상태
  const [accounts, setAccounts] = useState<SourcingAccount[]>([]);
  const [accountForm, setAccountForm] = useState({
    source: 'ssg',
    account_id: '',
    account_password: '',
    notes: ''
  });

  // ============= API 호출 함수 =============

  // 대시보드 관련
  const loadStats = useCallback(async () => {
    try {
      const data = await fetch((process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/playauto/stats').then(r => r.json());
      setStats(data);
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  }, []);

  const loadRecentLogs = useCallback(async () => {
    try {
      const data = await fetch((process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/playauto/sync-logs?limit=10').then(r => r.json());
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
        const playautoData = await playautoApi.getOrders(50, true);

        if (playautoData.success && playautoData.data) {
          playautoOrders = (playautoData.data as any[]).map((o: any) => ({
            id: o.playauto_order_id || o.id,
            order_number: o.order_number,
            market: o.market,
            customer_name: o.customer_name,
            customer_phone: o.customer_phone,
            customer_address: o.customer_address,
            total_amount: o.total_amount,
            order_date: o.order_date || o.created_at,
            status: (o.order_status || o.status || 'pending') as 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled',
            order_status: o.order_status || o.status || 'pending',
            source: 'playauto' as const,
            order_source: 'playauto',
            created_at: o.created_at,
            updated_at: o.updated_at || o.created_at
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

  // 주문 생성
  const createOrder = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 공통 API 클라이언트 사용
      const data = await fetch((process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/orders/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderForm)
      }).then(r => r.json());

      if (data.success) {
        toast.success(`주문이 생성되었습니다. ID: ${data.order_id}`);
        setSelectedOrderId(data.order_id);
        setOrderForm({
          order_number: '',
          market: 'coupang',
          customer_name: '',
          customer_phone: '',
          customer_address: '',
          customer_zipcode: '',
          total_amount: 0,
          notes: ''
        });
        cache.clearOrders();
      }
    } catch (error) {
      console.error('주문 생성 실패:', error);
      toast.error('주문 생성에 실패했습니다.');
    }
  }, [orderForm]);

  const addOrderItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderId) {
      toast.warning('먼저 주문을 생성하세요.');
      return;
    }

    try {
      const res = await fetch(`http://localhost:8000/api/orders/order/${selectedOrderId}/add-item`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itemForm)
      });
      const data = await res.json();
      if (data.success) {
        toast.success('주문 상품이 추가되었습니다.');
        setItemForm({
          product_name: '',
          product_url: '',
          source: 'ssg',
          quantity: 1,
          sourcing_price: 0,
          selling_price: 0
        });
      }
    } catch (error) {
      console.error('상품 추가 실패:', error);
      toast.error('상품 추가에 실패했습니다.');
    }
  };

  /**
   * URL에서 소싱처 자동 감지
   * @param url - 상품 URL
   * @returns 감지된 소싱처 (ssg, traders, 11st, gmarket, smartstore)
   */
  const detectSourceFromUrl = (url: string): string => {
    if (url.includes('ssg.com') || url.includes('emart.ssg.com') || url.includes('traders.ssg.com')) {
      return 'ssg';
    } else if (url.includes('homeplus.co.kr')) {
      return 'traders';
    } else if (url.includes('11st.co.kr')) {
      return '11st';
    } else if (url.includes('gmarket.co.kr')) {
      return 'gmarket';
    } else if (url.includes('smartstore.naver.com')) {
      return 'smartstore';
    }
    return 'ssg'; // 기본값
  };

  // 플레이오토 설정 관련
  const loadSettings = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/playauto/settings');
      if (!res.ok) throw new Error('설정 조회 실패');
      const data = await res.json();
      setSettingsInfo(data);
    } catch (error) {
      console.error('설정 로드 실패:', error);
    }
  };

  const saveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionLoading({ ...actionLoading, 'save-settings': true });
      const res = await fetch('http://localhost:8000/api/playauto/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      if (data.success) {
        toast.success('설정이 저장되었습니다');
        await loadSettings();
        setSettings({
          ...settings,
          api_key: '',
          email: '',
          password: ''
        });
      } else {
        throw new Error(data.message || '설정 저장 실패');
      }
    } catch (error) {
      console.error('설정 저장 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      toast.error(`설정 저장 실패: ${errorMessage}`);
    } finally {
      setActionLoading({ ...actionLoading, 'save-settings': false });
    }
  };

  const testConnection = async () => {
    try {
      setActionLoading({ ...actionLoading, 'test-connection': true });
      const res = await fetch('http://localhost:8000/api/playauto/test-connection', {
        method: 'POST'
      });
      const data = await res.json();
      setConnectionStatus({
        tested: true,
        success: data.success,
        message: data.message
      });
      if (data.success) {
        toast.success('연결 성공!');
      } else {
        toast.error(`연결 실패: ${data.message}`);
      }
    } catch (error) {
      console.error('연결 테스트 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      setConnectionStatus({
        tested: true,
        success: false,
        message: errorMessage
      });
      toast.error('연결 테스트 중 오류가 발생했습니다');
    } finally {
      setActionLoading({ ...actionLoading, 'test-connection': false });
    }
  };

  // 송장 관련
  const autoUploadTracking = async (days: number = 7) => {
    try {
      setActionLoading({ ...actionLoading, 'auto-upload': true });
      const res = await fetch(`http://localhost:8000/api/playauto/upload-tracking/auto?days=${days}`, {
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
      const res = await fetch('http://localhost:8000/api/playauto/tracking-upload-history?limit=20');
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
  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/orders/sourcing-accounts');
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
      }
    } catch (error) {
      console.error('계정 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const addAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8000/api/orders/sourcing-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountForm)
      });
      const data = await res.json();
      if (data.success) {
        toast.success('소싱처 계정이 등록되었습니다.');
        setAccountForm({
          source: 'ssg',
          account_id: '',
          account_password: '',
          notes: ''
        });
        fetchAccounts();
      }
    } catch (error) {
      console.error('계정 등록 실패:', error);
      toast.error('계정 등록에 실패했습니다.');
    }
  };

  // ============= useEffect 훅 =============

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadStats();
      loadRecentLogs();
    } else if (activeTab === 'orders') {
      fetchOrders();
    } else if (activeTab === 'playauto') {
      loadSettings();
    } else if (activeTab === 'tracking') {
      loadTrackingHistory();
    } else if (activeTab === 'accounts') {
      fetchAccounts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // 주문 소스 필터 변경 시 클라이언트 사이드 필터링 (API 호출 없음)
  useEffect(() => {
    let combinedOrders: Order[] = [];

    // 필터에 따라 주문 병합
    if (orderSourceFilter === 'all') {
      combinedOrders = [...rawManualOrders, ...rawPlayautoOrders];
    } else if (orderSourceFilter === 'manual') {
      combinedOrders = rawManualOrders;
    } else if (orderSourceFilter === 'playauto') {
      combinedOrders = rawPlayautoOrders;
    }

    // 날짜 기준으로 정렬 (최신순)
    combinedOrders.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    setOrders(combinedOrders);
    setFilteredOrders(combinedOrders);
    setPagination(prev => ({ ...prev, total: combinedOrders.length }));
  }, [orderSourceFilter, rawManualOrders, rawPlayautoOrders]);

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
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
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
            { key: 'create', label: '주문 생성', icon: <Plus className="w-4 h-4" /> },
            { key: 'playauto', label: '플레이오토 설정', icon: <Settings className="w-4 h-4" /> },
            { key: 'tracking', label: '송장 관리', icon: <Truck className="w-4 h-4" /> },
            { key: 'scheduler', label: '송장 스케줄러', icon: <Clock className="w-4 h-4" /> },
            { key: 'accounts', label: '소싱처 계정', icon: <Settings className="w-4 h-4" /> }
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
                onClick={() => setActiveTab('create')}
                className="flex items-center gap-3 p-4 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:shadow-lg transition-all"
              >
                <Plus className="w-6 h-6" />
                <div className="text-left">
                  <div className="font-semibold">주문 생성</div>
                  <div className="text-sm opacity-90">수동 주문 입력</div>
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
            <h3 className="text-xl font-bold text-gray-800 mb-6">
              주문 목록 ({filteredOrders.length}건 / 전체 {orders.length}건)
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

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">주문 금액:</span>
                        <p className="text-gray-800 font-bold">{formatCurrency(order.total_amount)}</p>
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
                        <p className="text-gray-800">{formatDate(order.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 주문 생성 탭 */}
      {activeTab === 'create' && (
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
          <h3 className="text-2xl font-bold text-gray-800 mb-6">주문 생성</h3>

          {/* 주문 생성 폼 */}
          <form onSubmit={createOrder} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">주문번호</label>
                <input
                  type="text"
                  value={orderForm.order_number}
                  onChange={(e) => setOrderForm({ ...orderForm, order_number: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="COUPANG-20260109-001"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">마켓</label>
                <select
                  value={orderForm.market}
                  onChange={(e) => setOrderForm({ ...orderForm, market: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="coupang">쿠팡</option>
                  <option value="naver">네이버 스마트스토어</option>
                  <option value="11st">11번가</option>
                  <option value="gmarket">G마켓</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">고객명</label>
                <input
                  type="text"
                  value={orderForm.customer_name}
                  onChange={(e) => setOrderForm({ ...orderForm, customer_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="홍길동"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">전화번호</label>
                <input
                  type="text"
                  value={orderForm.customer_phone}
                  onChange={(e) => setOrderForm({ ...orderForm, customer_phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="010-1234-5678"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">배송 주소</label>
              <input
                type="text"
                value={orderForm.customer_address}
                onChange={(e) => setOrderForm({ ...orderForm, customer_address: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="서울시 강남구 테헤란로 123, 101동 101호"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">우편번호</label>
                <input
                  type="text"
                  value={orderForm.customer_zipcode}
                  onChange={(e) => setOrderForm({ ...orderForm, customer_zipcode: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="06000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">주문 금액</label>
                <input
                  type="number"
                  value={orderForm.total_amount}
                  onChange={(e) => setOrderForm({ ...orderForm, total_amount: Number(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="15900"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">메모</label>
              <textarea
                value={orderForm.notes}
                onChange={(e) => setOrderForm({ ...orderForm, notes: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                rows={3}
                placeholder="배송 요청사항 등"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              <Plus className="w-5 h-5 inline mr-2" />
              주문 생성
            </button>
          </form>

          {/* 주문 상품 추가 폼 */}
          {selectedOrderId && (
            <div className="mt-12 border-t border-gray-200 pt-8">
              <h4 className="text-xl font-bold text-gray-800 mb-6">주문 상품 추가 (주문 ID: {selectedOrderId})</h4>
              <form onSubmit={addOrderItem} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">상품명</label>
                  <input
                    type="text"
                    value={itemForm.product_name}
                    onChange={(e) => setItemForm({ ...itemForm, product_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="[물바다] 햇반 흰밥 210g x 10개"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">상품 URL (소싱처)</label>
                  <input
                    type="url"
                    value={itemForm.product_url}
                    onChange={(e) => {
                      const url = e.target.value;
                      const detectedSource = detectSourceFromUrl(url);
                      setItemForm({
                        ...itemForm,
                        product_url: url,
                        source: detectedSource
                      });
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="https://emart.ssg.com/item/itemView.ssg?itemId=..."
                    required
                  />
                  {itemForm.product_url && (
                    <p className="mt-1 text-sm text-gray-500">
                      자동 감지된 소싱처: <strong className="text-purple-600">{itemForm.source.toUpperCase()}</strong>
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">소싱처</label>
                    <select
                      value={itemForm.source}
                      onChange={(e) => setItemForm({ ...itemForm, source: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-50"
                    >
                      <option value="ssg">SSG</option>
                      <option value="traders">홈플러스/Traders</option>
                      <option value="11st">11번가</option>
                      <option value="gmarket">G마켓</option>
                      <option value="smartstore">스마트스토어</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">수량</label>
                    <input
                      type="number"
                      value={itemForm.quantity}
                      onChange={(e) => setItemForm({ ...itemForm, quantity: Number(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      min="1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">소싱가</label>
                    <input
                      type="number"
                      value={itemForm.sourcing_price}
                      onChange={(e) => {
                        const sourcing = Number(e.target.value);
                        setItemForm({
                          ...itemForm,
                          sourcing_price: sourcing,
                          selling_price: Math.round(sourcing * 1.5)
                        });
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="10900"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    판매가 (50% 마진 자동 계산)
                  </label>
                  <input
                    type="number"
                    value={itemForm.selling_price}
                    onChange={(e) => setItemForm({ ...itemForm, selling_price: Number(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-50"
                    placeholder="16350"
                    required
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    예상 이익: <strong className="text-green-600">
                      {((itemForm.selling_price - itemForm.sourcing_price) * itemForm.quantity).toLocaleString()}원
                    </strong>
                  </p>
                </div>

                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all"
                >
                  <Plus className="w-5 h-5 inline mr-2" />
                  상품 추가
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* 플레이오토 설정 탭 */}
      {activeTab === 'playauto' && (
        <div className="space-y-6">
          {/* 현재 설정 상태 */}
          {settingsInfo && (
            <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
              <h3 className="text-xl font-bold text-gray-800 mb-4">현재 연동 상태</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">API 키</p>
                  <p className="text-gray-800 font-mono">{settingsInfo.api_key_masked || '설정 안됨'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">활성화 상태</p>
                  {settingsInfo.enabled ? (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                      <CheckCircle className="w-4 h-4" />
                      활성화됨
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                      <XCircle className="w-4 h-4" />
                      비활성화됨
                    </span>
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">마지막 동기화</p>
                  <p className="text-gray-800">
                    {settingsInfo.last_sync_at ? formatDate(settingsInfo.last_sync_at) : '없음'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 연결 테스트 결과 */}
          {connectionStatus && connectionStatus.tested && (
            <div className={`p-6 rounded-2xl ${
              connectionStatus.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center gap-3">
                {connectionStatus.success ? (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-600" />
                )}
                <div>
                  <p className={`font-semibold ${connectionStatus.success ? 'text-green-800' : 'text-red-800'}`}>
                    {connectionStatus.success ? '연결 성공' : '연결 실패'}
                  </p>
                  <p className={`text-sm ${connectionStatus.success ? 'text-green-700' : 'text-red-700'}`}>
                    {connectionStatus.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* API 설정 폼 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-6">API 설정</h3>

            <form onSubmit={saveSettings} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API 키 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={settings.api_key}
                  onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                  placeholder="plto_xxxxxxxxxxxxxxxx"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일 <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={settings.email}
                  onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                  placeholder="your-email@example.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showApiSecret ? 'text' : 'password'}
                    value={settings.password}
                    onChange={(e) => setSettings({ ...settings, password: e.target.value })}
                    placeholder="••••••••••••••••"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent pr-12"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiSecret(!showApiSecret)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showApiSecret ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API URL
                </label>
                <input
                  type="text"
                  value={settings.api_base_url}
                  onChange={(e) => setSettings({ ...settings, api_base_url: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={settings.enabled}
                    onChange={(e) => setSettings({ ...settings, enabled: e.target.checked })}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                  />
                  <label htmlFor="enabled" className="ml-3 text-sm text-gray-700">
                    플레이오토 연동 활성화
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="auto_sync"
                    checked={settings.auto_sync_enabled}
                    onChange={(e) => setSettings({ ...settings, auto_sync_enabled: e.target.checked })}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                  />
                  <label htmlFor="auto_sync" className="ml-3 text-sm text-gray-700">
                    자동 동기화 활성화
                  </label>
                </div>
              </div>

              {settings.auto_sync_enabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    동기화 간격 (분)
                  </label>
                  <input
                    type="number"
                    value={settings.auto_sync_interval}
                    onChange={(e) => setSettings({ ...settings, auto_sync_interval: parseInt(e.target.value) })}
                    min="10"
                    max="1440"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-600 mt-1">
                    권장: 30분 (최소 10분, 최대 1440분)
                  </p>
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="encrypt"
                  checked={settings.encrypt_credentials}
                  onChange={(e) => setSettings({ ...settings, encrypt_credentials: e.target.checked })}
                  className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                />
                <label htmlFor="encrypt" className="ml-3 text-sm text-gray-700">
                  자격증명 암호화 (권장)
                </label>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={testConnection}
                  disabled={actionLoading['test-connection'] || !settings.api_key || !settings.email || !settings.password}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading['test-connection'] ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      테스트 중...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      연결 테스트
                    </>
                  )}
                </button>

                <button
                  type="submit"
                  disabled={actionLoading['save-settings'] || !settings.api_key || !settings.email || !settings.password}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading['save-settings'] ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      저장 중...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      설정 저장
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 송장 관리 탭 */}
      {activeTab === 'tracking' && (
        <div className="space-y-6">
          {/* 자동 업로드 섹션 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <h3 className="text-xl font-bold text-gray-800 mb-4">송장 자동 업로드</h3>
            <p className="text-gray-600 mb-6">완료된 주문의 송장번호를 플레이오토에 일괄 업로드합니다</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => autoUploadTracking(7)}
                disabled={actionLoading['auto-upload']}
                className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                {actionLoading['auto-upload'] ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    업로드 중...
                  </>
                ) : (
                  <>
                    <Truck className="w-5 h-5" />
                    최근 7일 자동 업로드
                  </>
                )}
              </button>

              <button
                onClick={() => autoUploadTracking(14)}
                disabled={actionLoading['auto-upload']}
                className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                <Truck className="w-5 h-5" />
                최근 14일 자동 업로드
              </button>

              <button
                onClick={() => autoUploadTracking(30)}
                disabled={actionLoading['auto-upload']}
                className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                <Truck className="w-5 h-5" />
                최근 30일 자동 업로드
              </button>
            </div>
          </div>

          {/* 업로드 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <CheckCircle className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{trackingStats.total_uploaded}</div>
                  <div className="text-sm opacity-90">총 업로드 수</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <TrendingUp className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-3xl font-bold">{trackingStats.success_rate.toFixed(1)}%</div>
                  <div className="text-sm opacity-90">성공률</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Clock className="w-8 h-8 opacity-80" />
                <div className="text-right">
                  <div className="text-lg font-bold truncate">
                    {trackingStats.last_upload_at ? formatDate(trackingStats.last_upload_at) : '없음'}
                  </div>
                  <div className="text-sm opacity-90">마지막 업로드</div>
                </div>
              </div>
            </div>
          </div>

          {/* 업로드 이력 */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">업로드 이력</h3>
              <button
                onClick={loadTrackingHistory}
                className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                새로고침
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">이력 조회 중...</p>
              </div>
            ) : trackingHistory.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Truck className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>업로드 이력이 없습니다</p>
                <p className="text-sm mt-2">자동 업로드를 실행해보세요</p>
              </div>
            ) : (
              <div className="space-y-3">
                {trackingHistory.map((log) => (
                  <div key={log.id} className="border border-gray-200 rounded-xl p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold text-gray-800">{formatDate(log.created_at)}</p>
                        <p className="text-sm text-gray-600">송장번호 일괄 업로드</p>
                      </div>
                      {getSyncStatusBadge(log.status)}
                    </div>

                    <div className="grid grid-cols-4 gap-4 text-sm">
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
                      <div className="mt-3 p-3 bg-red-50 rounded-lg text-sm text-red-700">
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

      {/* 송장 스케줄러 탭 */}
      {activeTab === 'scheduler' && (
        <TrackingSchedulerPage />
      )}

      {/* 소싱처 계정 탭 */}
      {activeTab === 'accounts' && (
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
          <h3 className="text-2xl font-bold text-gray-800 mb-6">소싱처 계정 관리</h3>

          {/* 계정 추가 폼 */}
          <form onSubmit={addAccount} className="space-y-6 mb-12 p-6 bg-gray-50 rounded-xl">
            <h4 className="text-lg font-semibold text-gray-800">새 계정 등록</h4>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">소싱처</label>
                <select
                  value={accountForm.source}
                  onChange={(e) => setAccountForm({ ...accountForm, source: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="ssg">SSG.COM</option>
                  <option value="traders">홈플러스/Traders</option>
                  <option value="11st">11번가</option>
                  <option value="gmarket">G마켓</option>
                  <option value="smartstore">스마트스토어</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">로그인 ID</label>
                <input
                  type="text"
                  value={accountForm.account_id}
                  onChange={(e) => setAccountForm({ ...accountForm, account_id: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="your_id"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">비밀번호</label>
              <input
                type="password"
                value={accountForm.account_password}
                onChange={(e) => setAccountForm({ ...accountForm, account_password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="your_password"
                required
              />
              <p className="mt-2 text-sm text-red-600">비밀번호는 평문으로 저장됩니다. 실제 운영 환경에서는 암호화 필수!</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">메모</label>
              <input
                type="text"
                value={accountForm.notes}
                onChange={(e) => setAccountForm({ ...accountForm, notes: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="메인 계정"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              <Settings className="w-5 h-5 inline mr-2" />
              계정 등록
            </button>
          </form>

          {/* 등록된 계정 목록 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-800 mb-4">등록된 계정</h4>
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600 mx-auto"></div>
              </div>
            ) : accounts.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                등록된 계정이 없습니다.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {accounts.map((account) => (
                  <div key={account.id} className="border border-gray-200 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-lg font-bold text-gray-800">{account.source.toUpperCase()}</h5>
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        account.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {account.is_active ? '활성' : '비활성'}
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-600">ID:</span>
                        <p className="font-semibold text-gray-800">{account.account_id}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">비밀번호:</span>
                        <p className="font-semibold text-gray-800">****</p>
                      </div>
                      <div className="text-xs text-gray-500 mt-4">
                        등록일: {new Date(account.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
