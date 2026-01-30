/**
 * 실시간 주문 모니터링 위젯
 *
 * 신규 주문을 실시간으로 모니터링하고 알림을 표시합니다.
 */

'use client';

import { useOrderMonitoring } from '@/hooks/useOrderMonitoring';
import { RefreshCw, Bell, Clock, Package } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface OrderMonitorWidgetProps {
  enabled?: boolean;
  interval?: number;
  showRecentOrders?: boolean;
}

export default function OrderMonitorWidget({
  enabled = true,
  interval = 30000,
  showRecentOrders = true,
}: OrderMonitorWidgetProps) {
  const {
    recentOrders,
    newOrderCount,
    isChecking,
    lastCheckTime,
    checkNow,
  } = useOrderMonitoring({
    enabled,
    interval,
    showNotifications: true,
    showToasts: true,
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Bell className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">실시간 주문 모니터링</h3>
            <p className="text-sm text-gray-500">
              {interval / 1000}초마다 자동 확인 중
            </p>
          </div>
        </div>

        <button
          onClick={checkNow}
          disabled={isChecking}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin' : ''}`} />
          <span>{isChecking ? '확인 중...' : '지금 확인'}</span>
        </button>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700 font-medium">신규 주문</p>
              <p className="text-3xl font-bold text-green-900 mt-1">
                {newOrderCount}
              </p>
            </div>
            <div className="p-3 bg-green-200 rounded-full">
              <Package className="w-6 h-6 text-green-700" />
            </div>
          </div>
          {newOrderCount > 0 && (
            <div className="mt-2 flex items-center gap-1 text-xs text-green-700">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>처리 대기 중</span>
            </div>
          )}
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700 font-medium">최근 30분</p>
              <p className="text-3xl font-bold text-blue-900 mt-1">
                {recentOrders.length}
              </p>
            </div>
            <div className="p-3 bg-blue-200 rounded-full">
              <Clock className="w-6 h-6 text-blue-700" />
            </div>
          </div>
          {lastCheckTime && (
            <p className="mt-2 text-xs text-blue-700">
              마지막 확인:{' '}
              {formatDistanceToNow(new Date(lastCheckTime), {
                addSuffix: true,
                locale: ko,
              })}
            </p>
          )}
        </div>
      </div>

      {/* 최근 주문 목록 */}
      {showRecentOrders && recentOrders.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            최근 주문 ({recentOrders.length}건)
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {recentOrders.slice(0, 5).map((order) => (
              <div
                key={order.unliq}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      {order.customer_name}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                      {order.shop_name}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    주문번호: {order.order_no}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">
                    {order.total_amount.toLocaleString()}원
                  </p>
                  <p className="text-xs text-gray-500">
                    {order.order_status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 주문 없을 때 */}
      {recentOrders.length === 0 && (
        <div className="text-center py-8">
          <Package className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500">최근 30분간 신규 주문이 없습니다</p>
        </div>
      )}
    </div>
  );
}
