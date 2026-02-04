/**
 * 실시간 알림 컴포넌트
 */

'use client';

import { useEffect, useState } from 'react';
import { getWebSocketClient, NotificationMessage } from '@/lib/websocket';
import { Bell, Package, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RealtimeNotifications() {
  const [isConnected, setIsConnected] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    const wsClient = getWebSocketClient();

    // 연결 상태 확인 (1초마다)
    const intervalId = setInterval(() => {
      setIsConnected(wsClient.isConnected());
    }, 1000);

    // 알림 핸들러 등록
    const unsubscribe = wsClient.onNotification((message: NotificationMessage) => {
      setNotificationCount(prev => prev + 1);
      handleNotification(message);
    });

    return () => {
      clearInterval(intervalId);
      unsubscribe();
    };
  }, []);

  const handleNotification = (message: NotificationMessage) => {
    switch (message.type) {
      case 'order_created':
        toast.success(
          <div>
            <div className="font-bold">📦 새 주문</div>
            <div className="text-sm">
              {message.data.order_number} - {message.data.market}
              <br />
              {message.data.total_amount?.toLocaleString()}원
            </div>
          </div>,
          { duration: 5000, icon: '🔔' }
        );
        break;

      case 'order_updated':
        toast(
          <div>
            <div className="font-bold">📝 주문 상태 변경</div>
            <div className="text-sm">
              {message.data.order_number} → {message.data.status}
            </div>
          </div>,
          { duration: 4000, icon: '🔔' }
        );
        break;

      case 'tracking_uploaded':
        toast.success(
          <div>
            <div className="font-bold">🚚 송장 업로드</div>
            <div className="text-sm">
              {message.data.order_number}
              <br />
              송장: {message.data.tracking_number}
            </div>
          </div>,
          { duration: 5000, icon: '🔔' }
        );
        break;

      case 'product_registered':
        toast.success(
          <div>
            <div className="font-bold">✅ 상품 등록</div>
            <div className="text-sm">
              {message.data.product_name}
              <br />
              {message.data.market}
            </div>
          </div>,
          { duration: 5000, icon: '🔔' }
        );
        break;

      case 'price_alert':
        const isMarginIssue = message.data.margin < 0;
        toast(
          <div>
            <div className="font-bold">
              {isMarginIssue ? '⚠️ 역마진 경고' : '💰 가격 변동'}
            </div>
            <div className="text-sm">
              {message.data.product_name}
              <br />
              {message.data.old_price?.toLocaleString()}원 → {message.data.new_price?.toLocaleString()}원
              <br />
              마진: {message.data.margin?.toFixed(1)}%
            </div>
          </div>,
          {
            duration: 6000,
            icon: isMarginIssue ? '⚠️' : '📊',
            style: isMarginIssue ? { background: '#fee' } : undefined
          }
        );
        break;

      case 'pong':
        // Ping 응답 (로그만)
        console.log('[WebSocket] Pong received');
        break;

      default:
        console.log('[WebSocket] 알 수 없는 메시지:', message);
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* 연결 상태 표시 */}
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg backdrop-blur-xl border shadow-lg transition-all ${
          isConnected
            ? 'bg-green-50/90 border-green-300 text-green-700'
            : 'bg-gray-50/90 border-gray-300 text-gray-500'
        }`}
        title={isConnected ? '실시간 알림 연결됨' : '실시간 알림 연결 중...'}
      >
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          }`}
        />
        <Bell className="w-4 h-4" />
        <span className="text-xs font-medium">
          {isConnected ? '실시간 알림' : '연결 중...'}
        </span>
        {notificationCount > 0 && (
          <span className="px-1.5 py-0.5 text-xs font-bold bg-green-500 text-white rounded-full">
            {notificationCount}
          </span>
        )}
      </div>
    </div>
  );
}
