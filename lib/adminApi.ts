/**
 * Admin API 헬퍼 함수
 * 프로덕션 환경에서 자동으로 인증 헤더를 추가합니다.
 */

import { API_BASE_URL } from './api';

/**
 * Admin API 인증 헤더 생성
 */
function getAdminHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // 프로덕션 환경 (Railway)에서는 인증 헤더 추가
  const isProduction = API_BASE_URL.includes('railway.app');

  if (isProduction) {
    const adminPassword = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || '8888';
    headers['X-Admin-Password'] = adminPassword;
  }

  return headers;
}

/**
 * Admin API GET 요청
 */
export async function adminGet<T = any>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: getAdminHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Admin API POST 요청
 */
export async function adminPost<T = any>(endpoint: string, body?: any): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: getAdminHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Admin API DELETE 요청
 */
export async function adminDelete<T = any>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers: getAdminHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Admin API PUT 요청
 */
export async function adminPut<T = any>(endpoint: string, body?: any): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: getAdminHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Admin API 파일 업로드
 */
export async function adminUpload(endpoint: string, formData: FormData): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;

  // FormData는 Content-Type을 자동 설정하므로 헤더에서 제외
  const headers: HeadersInit = {};

  // 프로덕션 환경에서는 인증 헤더만 추가
  const isProduction = API_BASE_URL.includes('railway.app');
  if (isProduction) {
    const adminPassword = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || '8888';
    headers['X-Admin-Password'] = adminPassword;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Admin API fetch (커스텀 옵션)
 */
export async function adminFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const url = `${API_BASE_URL}${endpoint}`;

  // 기존 헤더와 Admin 헤더 병합
  const headers = {
    ...getAdminHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}
