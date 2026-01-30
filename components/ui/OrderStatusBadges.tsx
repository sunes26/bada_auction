/**
 * 주문 상태별 카운트 뱃지
 *
 * 주문 상태별 건수를 뱃지 형태로 표시합니다.
 */

'use client';

import { useOrderStatusStats } from '@/hooks/useOrderStatusStats';
import {
  Package,
  Clock,
  Truck,
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

interface OrderStatusBadgesProps {
  onStatusClick?: (status: string) => void;
}

export default function OrderStatusBadges({ onStatusClick }: OrderStatusBadgesProps) {
  const { statusCounts, totalOrders, isLoading, error, refresh } = useOrderStatusStats();

  // 상태별 아이콘 및 색상 매핑
  const getStatusConfig = (status: string) => {
    const configs: Record<string, { icon: any; color: string; bgColor: string }> = {
      '신규주문': {
        icon: Package,
        color: 'text-blue-700',
        bgColor: 'bg-blue-50 border-blue-200 hover:bg-blue-100',
      },
      '발주확인': {
        icon: Clock,
        color: 'text-yellow-700',
        bgColor: 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100',
      },
      '상품준비중': {
        icon: AlertCircle,
        color: 'text-orange-700',
        bgColor: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
      },
      '배송중': {
        icon: Truck,
        color: 'text-purple-700',
        bgColor: 'bg-purple-50 border-purple-200 hover:bg-purple-100',
      },
      '배송완료': {
        icon: CheckCircle,
        color: 'text-green-700',
        bgColor: 'bg-green-50 border-green-200 hover:bg-green-100',
      },
      '취소': {
        icon: XCircle,
        color: 'text-red-700',
        bgColor: 'bg-red-50 border-red-200 hover:bg-red-100',
      },
      '반품': {
        icon: RefreshCw,
        color: 'text-gray-700',
        bgColor: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
      },
      '교환': {
        icon: RefreshCw,
        color: 'text-indigo-700',
        bgColor: 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100',
      },
    };

    return (
      configs[status] || {
        icon: Package,
        color: 'text-gray-700',
        bgColor: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
      }
    );
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="text-center">
          <p className="text-red-600 text-sm">상태별 통계를 불러오는데 실패했습니다</p>
          <button
            onClick={refresh}
            className="mt-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
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
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">주문 상태</h3>
          <p className="text-sm text-gray-500">최근 30일간 주문 상태별 현황</p>
        </div>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50"
          title="새로고침"
        >
          <RefreshCw className={`w-5 h-5 text-gray-600 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* 전체 주문 수 */}
      <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">전체 주문</span>
          <span className="text-2xl font-bold text-gray-900">{totalOrders}건</span>
        </div>
      </div>

      {/* 상태별 뱃지 그리드 */}
      {isLoading ? (
        <div className="text-center py-8">
          <RefreshCw className="w-6 h-6 text-gray-400 mx-auto mb-2 animate-spin" />
          <p className="text-sm text-gray-500">불러오는 중...</p>
        </div>
      ) : statusCounts.length === 0 ? (
        <div className="text-center py-8">
          <Package className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-500">주문이 없습니다</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {statusCounts.map((item) => {
            const config = getStatusConfig(item.status);
            const Icon = config.icon;
            const percentage = totalOrders > 0 ? ((item.count / totalOrders) * 100).toFixed(1) : 0;

            return (
              <button
                key={item.status}
                onClick={() => onStatusClick?.(item.status)}
                className={`
                  relative overflow-hidden rounded-lg border-2 p-4 transition-all
                  ${config.bgColor}
                `}
              >
                {/* 아이콘 */}
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`w-5 h-5 ${config.color}`} />
                  <span className="text-xs text-gray-500">{percentage}%</span>
                </div>

                {/* 상태명 */}
                <p className={`text-sm font-medium ${config.color} mb-1`}>
                  {item.status}
                </p>

                {/* 카운트 */}
                <p className="text-2xl font-bold text-gray-900">{item.count}</p>

                {/* 호버 효과 */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-current to-transparent opacity-0 hover:opacity-20 transition-opacity" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
