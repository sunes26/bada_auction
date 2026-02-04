'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Package, DollarSign, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import MetricCard from '@/components/ui/MetricCard';
import QuickActions from '@/components/ui/QuickActions';
import RecentActivity from '@/components/ui/RecentActivity';
import RevenueChart from '@/components/ui/charts/RevenueChart';
import MarginChart from '@/components/ui/charts/MarginChart';
import SourcePieChart from '@/components/ui/charts/SourcePieChart';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ordersApi, playautoApi, monitorApi } from '@/lib/api';
import type { Order } from '@/lib/types';
import { API_BASE_URL } from '@/lib/api';

interface DashboardStats {
  totalOrders: number;
  todayOrders: number;
  totalRevenue: number;
  avgMargin: number;
  marginAlerts: number;
  ordersTrend: number;
  revenueTrend: number;
}

interface Activity {
  id: string;
  type: 'order' | 'price_change' | 'alert' | 'sync';
  title: string;
  description: string;
  time: string;
  icon: React.ReactNode;
  color: string;
}

export default function HomePage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalOrders: 0,
    todayOrders: 0,
    totalRevenue: 0,
    avgMargin: 0,
    marginAlerts: 0,
    ordersTrend: 0,
    revenueTrend: 0,
  });
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState<number>(0); // 0: 끄기, 30: 30초, 60: 1분, 300: 5분
  const [activeChartTab, setActiveChartTab] = useState<'revenue' | 'margin' | 'source'>('revenue');

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      // 통합 API 호출 (성능 최적화: 5개 API → 1개 API)
      const response = await fetch(`${API_BASE_URL}/api/dashboard/all`);
      const data = await response.json();

      if (!data.success) {
        throw new Error('대시보드 데이터 로드 실패');
      }

      const { rpa_stats, playauto_stats, monitor_stats, recent_orders, all_orders } = data;

      // 통계 계산 - 실제 주문 데이터 사용
      const totalOrders = all_orders?.length || 0;

      // 오늘 생성된 주문 수 계산
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const todayOrders = all_orders
        ? all_orders.filter((order: any) => {
            const orderDate = new Date(order.created_at);
            orderDate.setHours(0, 0, 0, 0);
            return orderDate.getTime() === today.getTime();
          }).length
        : 0;

      // 매출 계산 (전체 주문에서)
      let totalRevenue = 0;
      if (all_orders) {
        totalRevenue = all_orders.reduce((sum: number, order: any) => sum + (order.total_amount || 0), 0);
      }

      // 평균 마진율 계산 (주문 상품이 이미 포함되어 있음 - N+1 쿼리 제거!)
      let avgMargin = 0;
      let totalMarginSum = 0;
      let itemCount = 0;

      if (all_orders) {
        for (const order of all_orders) {
          // order.items는 이미 포함되어 있음 (with-items 엔드포인트 사용)
          if (order.items && order.items.length > 0) {
            for (const item of order.items) {
              if (item.selling_price > 0) {
                const margin = ((item.selling_price - item.sourcing_price) / item.selling_price) * 100;
                totalMarginSum += margin;
                itemCount++;
              }
            }
          }
        }
      }

      if (itemCount > 0) {
        avgMargin = totalMarginSum / itemCount;
      }

      // 역마진 경고
      const marginAlerts = monitor_stats.margin_issues || 0;

      // 트렌드 계산 (최근 7일 vs 이전 7일)
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const fourteenDaysAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

      let recentOrdersCount = 0;
      let previousOrdersCount = 0;
      let recentRevenue = 0;
      let previousRevenue = 0;

      if (all_orders) {
        all_orders.forEach((order: any) => {
          const orderDate = new Date(order.created_at);
          if (orderDate >= sevenDaysAgo) {
            recentOrdersCount++;
            recentRevenue += order.total_amount || 0;
          } else if (orderDate >= fourteenDaysAgo) {
            previousOrdersCount++;
            previousRevenue += order.total_amount || 0;
          }
        });
      }

      const ordersTrend = previousOrdersCount > 0
        ? ((recentOrdersCount - previousOrdersCount) / previousOrdersCount) * 100
        : 0;
      const revenueTrend = previousRevenue > 0
        ? ((recentRevenue - previousRevenue) / previousRevenue) * 100
        : 0;

      setStats({
        totalOrders,
        todayOrders,
        totalRevenue,
        avgMargin,
        marginAlerts,
        ordersTrend,
        revenueTrend,
      });

      // 최근 활동 생성
      const recentActivities: Activity[] = [];
      if (recent_orders) {
        recent_orders.slice(0, 5).forEach((order: any) => {
          recentActivities.push({
            id: `order-${order.id}`,
            type: 'order',
            title: `새 주문 - ${order.market}`,
            description: `${order.customer_name} / ${order.total_amount?.toLocaleString()}원`,
            time: formatTimeAgo(order.created_at),
            icon: <Package className="w-4 h-4" />,
            color: 'from-blue-500 to-blue-600',
          });
        });
      }

      setActivities(recentActivities);
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
      toast.error('대시보드 데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, []); // 의존성 없음

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // 자동 새로고침
  useEffect(() => {
    if (autoRefresh === 0) return;

    const interval = setInterval(() => {
      loadDashboardData();
    }, autoRefresh * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, loadDashboardData]);

  const formatTimeAgo = useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    return date.toLocaleDateString();
  }, []);

  const handleQuickAction = useCallback((action: string) => {
    // 페이지 전환은 부모 컴포넌트(app/page.tsx)에서 처리해야 하므로
    // 여기서는 임시로 알림만 표시
    console.log(`Quick action: ${action}`);
  }, []);

  return (
    <div className="space-y-8">
      {/* 헤더 및 자동 새로고침 옵션 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            대시보드
          </h1>
          <p className="text-gray-600 mt-2">전체 비즈니스 현황을 한눈에 확인하세요</p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">자동 새로고침:</label>
          <select
            value={autoRefresh}
            onChange={(e) => setAutoRefresh(Number(e.target.value))}
            className="px-4 py-2 bg-white/80 backdrop-blur-xl border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-sm"
          >
            <option value={0}>끄기</option>
            <option value={30}>30초</option>
            <option value={60}>1분</option>
            <option value={300}>5분</option>
          </select>
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="p-2 bg-white/80 backdrop-blur-xl rounded-xl hover:shadow-lg transition-all border border-white/20 disabled:opacity-50"
            title="새로고침"
          >
            <RefreshCw className={`w-5 h-5 text-blue-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 지표 카드 그리드 */}
      {loading && !stats.totalOrders ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="총 주문 수"
            value={`${stats.totalOrders.toLocaleString()}건`}
            icon={<Package className="w-6 h-6" />}
            trend={{ value: stats.ordersTrend, isPositive: true }}
            color="blue"
          />
          <MetricCard
            title="총 매출액"
            value={`${Math.floor(stats.totalRevenue / 10000).toLocaleString()}만원`}
            icon={<DollarSign className="w-6 h-6" />}
            trend={{ value: stats.revenueTrend, isPositive: true }}
            color="green"
          />
          <MetricCard
            title="평균 마진율"
            value={`${stats.avgMargin.toFixed(1)}%`}
            icon={<TrendingUp className="w-6 h-6" />}
            color="purple"
          />
          <MetricCard
            title="재고 알림"
            value={`${stats.marginAlerts}건`}
            icon={<AlertCircle className="w-6 h-6" />}
            color="red"
          />
        </div>
      )}

      {/* 메인 콘텐츠 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 차트 섹션 (2/3 너비) */}
        <div className="lg:col-span-2">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-black/5 border border-white/20 p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">데이터 분석</h3>

            {/* 차트 탭 */}
            <div className="flex gap-2 mb-6 border-b border-gray-200">
              <button
                onClick={() => setActiveChartTab('revenue')}
                className={`px-4 py-2 font-semibold text-sm transition-all ${
                  activeChartTab === 'revenue'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                매출 추이
              </button>
              <button
                onClick={() => setActiveChartTab('margin')}
                className={`px-4 py-2 font-semibold text-sm transition-all ${
                  activeChartTab === 'margin'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                마진 분포
              </button>
              <button
                onClick={() => setActiveChartTab('source')}
                className={`px-4 py-2 font-semibold text-sm transition-all ${
                  activeChartTab === 'source'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                소싱처 비율
              </button>
            </div>

            {/* 차트 */}
            {activeChartTab === 'revenue' && <RevenueChart />}
            {activeChartTab === 'margin' && <MarginChart />}
            {activeChartTab === 'source' && <SourcePieChart />}
          </div>
        </div>

        {/* 최근 활동 (1/3 너비) */}
        <div className="lg:col-span-1">
          <RecentActivity activities={activities} />
        </div>
      </div>

      {/* 빠른 액션 */}
      <QuickActions
        onCreateOrder={() => handleQuickAction('create-order')}
        onCollectProducts={() => handleQuickAction('collect-products')}
        onUploadTracking={() => handleQuickAction('upload-tracking')}
        onSettings={() => handleQuickAction('settings')}
      />
    </div>
  );
}
