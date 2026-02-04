/**
 * WebSocket 실시간 알림 클라이언트
 */

import { API_BASE_URL } from './api';

export interface NotificationMessage {
  type: 'order_created' | 'order_updated' | 'tracking_uploaded' | 'product_registered' | 'price_alert' | 'pong';
  data: any;
  timestamp: string;
}

export type NotificationHandler = (message: NotificationMessage) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private handlers: NotificationHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3초

  constructor() {
    this.connect();
  }

  private getWebSocketUrl(): string {
    // HTTP → WS, HTTPS → WSS
    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const baseUrl = API_BASE_URL.replace('http://', '').replace('https://', '');
    return `${wsProtocol}://${baseUrl}/ws/notifications`;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] 이미 연결됨');
      return;
    }

    const url = this.getWebSocketUrl();
    console.log('[WebSocket] 연결 시도:', url);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[WebSocket] 연결 성공');
        this.reconnectAttempts = 0;

        // Ping 전송 (30초마다)
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 30000);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: NotificationMessage = JSON.parse(event.data);
          console.log('[WebSocket] 메시지 수신:', message);

          // 모든 핸들러에 알림
          this.handlers.forEach(handler => {
            try {
              handler(message);
            } catch (error) {
              console.error('[WebSocket] 핸들러 오류:', error);
            }
          });
        } catch (error) {
          console.error('[WebSocket] 메시지 파싱 오류:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] 오류:', error);
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] 연결 종료');
        this.cleanup();

        // 재연결 시도
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`[WebSocket] 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} (${this.reconnectDelay}ms 후)`);
          this.reconnectTimeout = setTimeout(() => {
            this.connect();
          }, this.reconnectDelay);
        } else {
          console.error('[WebSocket] 최대 재연결 횟수 초과');
        }
      };
    } catch (error) {
      console.error('[WebSocket] 연결 생성 실패:', error);
    }
  }

  disconnect() {
    console.log('[WebSocket] 수동 연결 해제');
    this.cleanup();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * 알림 핸들러 등록
   */
  onNotification(handler: NotificationHandler) {
    this.handlers.push(handler);

    // 핸들러 제거 함수 반환
    return () => {
      const index = this.handlers.indexOf(handler);
      if (index > -1) {
        this.handlers.splice(index, 1);
      }
    };
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 싱글톤 인스턴스
let wsClient: WebSocketClient | null = null;

/**
 * WebSocket 클라이언트 가져오기 (싱글톤)
 */
export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient();
  }
  return wsClient;
}

/**
 * WebSocket 연결 해제
 */
export function disconnectWebSocket() {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
}
