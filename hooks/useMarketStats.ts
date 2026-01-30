/**
 * 마켓별 통계 조회 훅
 */

import { useState, useEffect, useCallback } from 'react';

export interface MarketStat {
  market: string;
  order_count: number;
  total_amount: number;
  change_percent: number;
  prev_count: number;
}

interface MarketStatsResult {
  markets: MarketStat[];
  totalOrders: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useMarketStats(days: number = 7): MarketStatsResult {
  const [markets, setMarkets] = useState<MarketStat[]>([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/playauto/stats/by-market?days=${days}`);

      if (!response.ok) {
        throw new Error('마켓별 통계 조회 실패');
      }

      const data = await response.json();

      if (data.success) {
        setMarkets(data.markets || []);
        setTotalOrders(data.total_orders || 0);
      } else {
        throw new Error(data.message || '통계 조회 실패');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
      setError(errorMessage);
      console.error('마켓별 통계 조회 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    markets,
    totalOrders,
    isLoading,
    error,
    refresh: fetchStats,
  };
}
