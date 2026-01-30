/**
 * 주문 상태별 통계 조회 훅
 */

import { useState, useEffect, useCallback } from 'react';

export interface StatusCount {
  status: string;
  count: number;
}

interface OrderStatusStatsResult {
  statusCounts: StatusCount[];
  totalOrders: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useOrderStatusStats(): OrderStatusStatsResult {
  const [statusCounts, setStatusCounts] = useState<StatusCount[]>([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/playauto/stats/by-status`);

      if (!response.ok) {
        throw new Error('상태별 통계 조회 실패');
      }

      const data = await response.json();

      if (data.success) {
        setStatusCounts(data.status_counts || []);
        setTotalOrders(data.total_orders || 0);
      } else {
        throw new Error(data.message || '통계 조회 실패');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
      setError(errorMessage);
      console.error('상태별 통계 조회 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    statusCounts,
    totalOrders,
    isLoading,
    error,
    refresh: fetchStats,
  };
}
