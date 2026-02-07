import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '@/lib/api';

interface DashboardData {
  success: boolean;
  rpa_stats: {
    total: number;
    pending: number;
    completed: number;
    failed: number;
  };
  playauto_stats: {
    total_products: number;
    active_products: number;
  };
  monitor_stats: {
    total: number;
    active: number;
    margin_issues: number;
  };
  recent_orders: any[];
  all_orders: any[];
}

async function fetchDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/all`);
  if (!response.ok) {
    throw new Error('대시보드 데이터 로드 실패');
  }
  return response.json();
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    staleTime: 30 * 1000, // 30초
    gcTime: 5 * 60 * 1000, // 5분
    refetchOnWindowFocus: true,
  });
}

// 주문 목록 훅
export function useOrders(limit: number = 100) {
  return useQuery({
    queryKey: ['orders', limit],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/orders/list?limit=${limit}`);
      if (!response.ok) throw new Error('주문 데이터 로드 실패');
      return response.json();
    },
    staleTime: 15 * 1000, // 15초
  });
}

// 상품 목록 훅
export function useProducts(isActive?: boolean, limit: number = 100) {
  return useQuery({
    queryKey: ['products', isActive, limit],
    queryFn: async () => {
      let url = `${API_BASE_URL}/api/products/list?limit=${limit}`;
      if (isActive !== undefined) {
        url += `&is_active=${isActive}`;
      }
      const response = await fetch(url);
      if (!response.ok) throw new Error('상품 데이터 로드 실패');
      return response.json();
    },
    staleTime: 30 * 1000, // 30초
  });
}

// 회계 통계 훅
export function useAccountingStats(period: string = 'this_month') {
  return useQuery({
    queryKey: ['accounting', 'stats', period],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/accounting/dashboard/stats?period=${period}`);
      if (!response.ok) throw new Error('회계 데이터 로드 실패');
      return response.json();
    },
    staleTime: 60 * 1000, // 1분
  });
}
