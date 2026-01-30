/**
 * 마켓별 통합 통계 그리드
 *
 * 마켓별 주문 통계를 카드 형태로 표시하고 필터링 기능을 제공합니다.
 */

'use client';

import { useMarketStats, MarketStat } from '@/hooks/useMarketStats';
import { TrendingUp, TrendingDown, Minus, Store, RefreshCw, Filter } from 'lucide-react';
import { useState } from 'react';

interface MarketStatsGridProps {
  days?: number;
  onMarketClick?: (market: string) => void;
}

export default function MarketStatsGrid({
  days = 7,
  onMarketClick,
}: MarketStatsGridProps) {
  const { markets, totalOrders, isLoading, error, refresh } = useMarketStats(days);
  const [selectedMarket, setSelectedMarket] = useState<string | null>(null);

  const handleMarketClick = (market: string) => {
    const newMarket = selectedMarket === market ? null : market;
    setSelectedMarket(newMarket);
    onMarketClick?.(newMarket || '');
  };

  // 마켓 아이콘 색상 매핑
  const getMarketColor = (index: number) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-green-500 to-green-600',
      'from-purple-500 to-purple-600',
      'from-orange-500 to-orange-600',
      'from-pink-500 to-pink-600',
      'from-indigo-500 to-indigo-600',
    ];
    return colors[index % colors.length];
  };

  const getTrendIcon = (changePercent: number) => {
    if (changePercent > 0) {
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    } else if (changePercent < 0) {
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    } else {
      return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendColor = (changePercent: number) => {
    if (changePercent > 0) {
      return 'text-green-600';
    } else if (changePercent < 0) {
      return 'text-red-600';
    } else {
      return 'text-gray-500';
    }
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <p className="text-red-600">마켓별 통계를 불러오는데 실패했습니다</p>
          <p className="text-sm text-gray-500 mt-1">{error}</p>
          <button
            onClick={refresh}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-50 rounded-lg">
            <Store className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">마켓별 통계</h3>
            <p className="text-sm text-gray-500">최근 {days}일간 주문 현황</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedMarket && (
            <button
              onClick={() => handleMarketClick(selectedMarket)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
            >
              <Filter className="w-4 h-4" />
              필터 해제
            </button>
          )}
          <button
            onClick={refresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">새로고침</span>
          </button>
        </div>
      </div>

      {/* 전체 통계 */}
      <div className="mb-6 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">전체 주문</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{totalOrders}건</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">활성 마켓</p>
            <p className="text-2xl font-semibold text-gray-900 mt-1">{markets.length}개</p>
          </div>
        </div>
      </div>

      {/* 마켓별 카드 그리드 */}
      {isLoading ? (
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-3 animate-spin" />
          <p className="text-gray-500">마켓별 통계 불러오는 중...</p>
        </div>
      ) : markets.length === 0 ? (
        <div className="text-center py-12">
          <Store className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500">최근 {days}일간 주문이 없습니다</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market, index) => (
            <div
              key={market.market}
              onClick={() => handleMarketClick(market.market)}
              className={`
                relative overflow-hidden rounded-lg border-2 transition-all cursor-pointer
                ${
                  selectedMarket === market.market
                    ? 'border-purple-500 shadow-lg scale-105'
                    : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                }
              `}
            >
              {/* 배경 그라데이션 */}
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${getMarketColor(index)} opacity-10 rounded-full -mr-8 -mt-8`} />

              <div className="relative p-5">
                {/* 마켓명 */}
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-bold text-gray-900">{market.market}</h4>
                  <div className={`p-2 bg-gradient-to-br ${getMarketColor(index)} rounded-lg`}>
                    <Store className="w-4 h-4 text-white" />
                  </div>
                </div>

                {/* 주문 수 */}
                <div className="mb-3">
                  <p className="text-sm text-gray-600 mb-1">주문 건수</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-3xl font-bold text-gray-900">
                      {market.order_count}
                    </p>
                    <p className="text-sm text-gray-500">건</p>
                  </div>
                </div>

                {/* 주문 금액 */}
                <div className="mb-3">
                  <p className="text-sm text-gray-600 mb-1">총 금액</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {market.total_amount.toLocaleString()}원
                  </p>
                </div>

                {/* 증감률 */}
                <div className="flex items-center gap-2 pt-3 border-t border-gray-200">
                  {getTrendIcon(market.change_percent)}
                  <span className={`text-sm font-semibold ${getTrendColor(market.change_percent)}`}>
                    {market.change_percent > 0 ? '+' : ''}
                    {market.change_percent}%
                  </span>
                  <span className="text-xs text-gray-500">
                    (전 기간 대비)
                  </span>
                </div>

                {/* 선택 표시 */}
                {selectedMarket === market.market && (
                  <div className="absolute top-3 right-3">
                    <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 클릭 안내 */}
      {markets.length > 0 && !selectedMarket && (
        <p className="text-center text-sm text-gray-500 mt-4">
          카드를 클릭하면 해당 마켓 주문만 필터링됩니다
        </p>
      )}
    </div>
  );
}
