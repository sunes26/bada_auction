/**
 * 실시간 주문 모니터링 훅
 *
 * 30초마다 새로운 주문을 체크하고 브라우저 알림을 표시합니다.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/lib/api';

interface Order {
  unliq: string;
  order_no: string;
  shop_name: string;
  order_status: string;
  total_amount: number;
  order_date: string;
  customer_name: string;
}

interface OrderMonitoringOptions {
  enabled?: boolean;
  interval?: number; // 체크 간격 (밀리초)
  showNotifications?: boolean; // 브라우저 알림
  showToasts?: boolean; // 토스트 알림
}

interface OrderMonitoringResult {
  recentOrders: Order[];
  newOrderCount: number;
  isChecking: boolean;
  lastCheckTime: string | null;
  checkNow: () => void;
}

export function useOrderMonitoring(
  options: OrderMonitoringOptions = {}
): OrderMonitoringResult {
  const {
    enabled = true,
    interval = 30000, // 30초
    showNotifications = true,
    showToasts = true
  } = options;

  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [newOrderCount, setNewOrderCount] = useState(0);
  const [isChecking, setIsChecking] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState<string | null>(null);

  const previousOrderIds = useRef<Set<string>>(new Set());
  const notificationPermission = useRef<NotificationPermission>('default');

  // 브라우저 알림 권한 요청
  useEffect(() => {
    if (showNotifications && 'Notification' in window) {
      Notification.requestPermission().then((permission) => {
        notificationPermission.current = permission;
      });
    }
  }, [showNotifications]);

  // 주문 체크 함수
  const checkOrders = useCallback(async () => {
    if (!enabled) return;

    try {
      setIsChecking(true);

      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ${API_BASE_URL};
      const response = await fetch(`${apiUrl}/api/playauto/orders/recent?minutes=30`);

      if (!response.ok) {
        throw new Error('주문 조회 실패');
      }

      const data = await response.json();

      if (data.success && Array.isArray(data.orders)) {
        const orders = data.orders as Order[];
        setRecentOrders(orders);
        setLastCheckTime(data.check_time);

        // 신규 주문 감지
        const currentOrderIds = new Set(orders.map(o => o.unliq));
        const newOrders = orders.filter(
          o => !previousOrderIds.current.has(o.unliq)
        );

        if (newOrders.length > 0 && previousOrderIds.current.size > 0) {
          setNewOrderCount(prev => prev + newOrders.length);

          // 토스트 알림
          if (showToasts) {
            newOrders.forEach(order => {
              toast.success(
                `신규 주문 도착!`,
                {
                  description: `${order.shop_name} - ${order.customer_name} (${order.total_amount.toLocaleString()}원)`,
                  duration: 5000,
                }
              );
            });
          }

          // 브라우저 알림
          if (
            showNotifications &&
            'Notification' in window &&
            notificationPermission.current === 'granted'
          ) {
            newOrders.forEach(order => {
              new Notification('신규 주문 도착!', {
                body: `${order.shop_name} - ${order.customer_name}\n${order.total_amount.toLocaleString()}원`,
                icon: '/favicon.ico',
                tag: order.unliq,
                requireInteraction: false,
              });
            });

            // 알림음 재생 (선택사항)
            try {
              const audio = new Audio('/notification.mp3');
              audio.volume = 0.3;
              audio.play().catch(() => {
                // 자동 재생 차단 시 무시
              });
            } catch (e) {
              // 오디오 파일 없으면 무시
            }
          }
        }

        // 현재 주문 ID 저장
        previousOrderIds.current = currentOrderIds;
      }
    } catch (error) {
      console.error('주문 모니터링 오류:', error);
    } finally {
      setIsChecking(false);
    }
  }, [enabled, showNotifications, showToasts]);

  // 수동 체크
  const checkNow = useCallback(() => {
    checkOrders();
  }, [checkOrders]);

  // 주기적 체크
  useEffect(() => {
    if (!enabled) return;

    // 첫 체크
    checkOrders();

    // 주기적 체크
    const intervalId = setInterval(checkOrders, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [enabled, interval, checkOrders]);

  return {
    recentOrders,
    newOrderCount,
    isChecking,
    lastCheckTime,
    checkNow,
  };
}
