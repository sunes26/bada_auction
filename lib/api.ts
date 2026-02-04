import type {
  ApiResponse,
  PaginatedResponse,
  Product,
  CreateProductRequest,
  UpdateProductRequest,
  MonitoredProduct,
  Order,
  OrdersResponse,
  CreateOrderRequest,
  UpdateOrderRequest,
  Notification,
  PlayautoConfig,
  PlayautoAccount,
  DashboardStats,
  UrlExtractionResult,
  AccountingDashboardStats,
  ProfitLossStatement,
  ExpensesResponse,
  ExpenseCreate,
  SettlementsResponse,
  SettlementCreate,
  VATCalculation,
  IncomeTaxEstimate,
  MonthlyReport,
} from './types';

// ============================================
// Configuration
// ============================================

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const DEFAULT_CACHE_TTL = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// ============================================
// Cache Implementation
// ============================================

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class ApiCache {
  private cache = new Map<string, CacheEntry<unknown>>();

  set<T>(key: string, data: T, ttl: number = DEFAULT_CACHE_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > entry.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clearPattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

const apiCache = new ApiCache();

// ============================================
// Error Handling
// ============================================

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ============================================
// Core API Client
// ============================================

interface FetchOptions extends RequestInit {
  useCache?: boolean;
  cacheTTL?: number;
  retry?: boolean;
  maxRetries?: number;
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(
  url: string,
  options: FetchOptions,
  retries: number = 0
): Promise<Response> {
  try {
    const response = await fetch(url, options);

    // Retry on 5xx errors
    if (response.status >= 500 && retries < (options.maxRetries || MAX_RETRIES)) {
      await sleep(RETRY_DELAY * (retries + 1));
      return fetchWithRetry(url, options, retries + 1);
    }

    return response;
  } catch (error) {
    if (retries < (options.maxRetries || MAX_RETRIES)) {
      await sleep(RETRY_DELAY * (retries + 1));
      return fetchWithRetry(url, options, retries + 1);
    }
    throw error;
  }
}

export async function apiCall<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const {
    useCache = false,
    cacheTTL = DEFAULT_CACHE_TTL,
    retry = true,
    maxRetries = MAX_RETRIES,
    ...fetchOptions
  } = options;

  const url = `${API_BASE_URL}${path}`;
  const cacheKey = `${fetchOptions.method || 'GET'}:${url}:${JSON.stringify(fetchOptions.body || {})}`;

  // Check cache for GET requests
  if (useCache && (!fetchOptions.method || fetchOptions.method === 'GET')) {
    const cachedData = apiCache.get<T>(cacheKey);
    if (cachedData) {
      return cachedData;
    }
  }

  try {
    const response = retry
      ? await fetchWithRetry(url, { ...fetchOptions, maxRetries })
      : await fetch(url, fetchOptions);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || `API Error: ${response.status}`,
        response.status,
        errorData
      );
    }

    const data: T = await response.json();

    // Cache successful GET responses
    if (useCache && (!fetchOptions.method || fetchOptions.method === 'GET')) {
      apiCache.set(cacheKey, data, cacheTTL);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

// ============================================
// Products API
// ============================================

export const productsApi = {
  list: (cache = true) =>
    apiCall<ApiResponse<Product[]>>('/api/products/list', { useCache: cache, cacheTTL: 30000 }),

  get: (id: number, cache = true) =>
    apiCall<ApiResponse<Product>>(`/api/products/${id}`, { useCache: cache, cacheTTL: 60000 }),

  create: (data: CreateProductRequest) =>
    apiCall<ApiResponse<Product>>('/api/products/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  update: (id: number, data: UpdateProductRequest) =>
    apiCall<ApiResponse<Product>>(`/api/products/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/products/${id}`, {
      method: 'DELETE',
    }),

  toggleStatus: (id: number) =>
    apiCall<ApiResponse<Product>>(`/api/products/${id}/toggle-status`, {
      method: 'POST',
    }),

  extractUrlInfo: (productUrl: string) =>
    apiCall<UrlExtractionResult>('/api/monitor/extract-url-info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_url: productUrl }),
      useCache: false,
    }),

  syncToPlayauto: (id: number) =>
    apiCall<ApiResponse<any>>(`/api/products/${id}/sync-to-playauto`, {
      method: 'POST',
      useCache: false,
    }),
};

// ============================================
// Monitored Products API
// ============================================

export const monitorApi = {
  list: (cache = true) =>
    apiCall<ApiResponse<MonitoredProduct[]>>('/api/monitor/list', { useCache: cache, cacheTTL: 30000 }),

  get: (id: number, cache = true) =>
    apiCall<ApiResponse<MonitoredProduct>>(`/api/monitor/${id}`, { useCache: cache, cacheTTL: 60000 }),

  add: (data: { product_url: string; check_interval_minutes?: number; notes?: string }) =>
    apiCall<ApiResponse<MonitoredProduct>>('/api/monitor/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Partial<MonitoredProduct>) =>
    apiCall<ApiResponse<MonitoredProduct>>(`/api/monitor/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/monitor/${id}`, {
      method: 'DELETE',
    }),

  checkNow: (id: number) =>
    apiCall<ApiResponse<MonitoredProduct>>(`/api/monitor/${id}/check`, {
      method: 'POST',
      useCache: false,
    }),
};

// ============================================
// Orders API
// ============================================

export const ordersApi = {
  list: (limit = 50, cache = true) =>
    apiCall<OrdersResponse>(`/api/orders/list?limit=${limit}`, { useCache: cache, cacheTTL: 15000 }),

  listWithItems: (limit = 50, cache = true) =>
    apiCall<OrdersResponse>(`/api/orders/with-items?limit=${limit}`, { useCache: cache, cacheTTL: 15000 }),

  get: (id: number, cache = true) =>
    apiCall<ApiResponse<Order>>(`/api/orders/${id}`, { useCache: cache, cacheTTL: 30000 }),

  create: (data: CreateOrderRequest) =>
    apiCall<ApiResponse<Order>>('/api/orders/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  update: (id: number, data: UpdateOrderRequest) =>
    apiCall<ApiResponse<Order>>(`/api/orders/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/orders/${id}`, {
      method: 'DELETE',
    }),

  updateStatus: (id: number, status: Order['status']) =>
    apiCall<ApiResponse<Order>>(`/api/orders/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }),

  updateTracking: (id: number, trackingNumber: string) =>
    apiCall<ApiResponse<Order>>(`/api/orders/${id}/tracking`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tracking_number: trackingNumber }),
    }),

  stats: (cache = true) =>
    apiCall<ApiResponse<DashboardStats>>('/api/orders/stats', { useCache: cache, cacheTTL: 30000 }),
};

// ============================================
// Notifications API
// ============================================

export const notificationsApi = {
  list: (limit = 20, cache = true) =>
    apiCall<ApiResponse<Notification[]>>(`/api/monitor/notifications?limit=${limit}`, {
      useCache: cache,
      cacheTTL: 10000,
    }),

  markAsRead: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/monitor/notifications/${id}/read`, {
      method: 'POST',
    }),

  markAllAsRead: () =>
    apiCall<ApiResponse<void>>('/api/monitor/notifications/mark-all-read', {
      method: 'POST',
    }),

  delete: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/monitor/notifications/${id}`, {
      method: 'DELETE',
    }),
};

// ============================================
// Playauto API
// ============================================

export const playautoApi = {
  getConfig: (cache = true) =>
    apiCall<ApiResponse<PlayautoConfig>>('/api/playauto/config', { useCache: cache, cacheTTL: 60000 }),

  saveConfig: (data: PlayautoConfig) =>
    apiCall<ApiResponse<PlayautoConfig>>('/api/playauto/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getAccounts: (cache = true) =>
    apiCall<ApiResponse<PlayautoAccount[]>>('/api/playauto/accounts', { useCache: cache, cacheTTL: 60000 }),

  getOrders: (limit = 50, cache = true) =>
    apiCall<ApiResponse<Order[]>>(`/api/playauto/orders?limit=${limit}`, {
      useCache: cache,
      cacheTTL: 15000,
    }),

  stats: (cache = true) =>
    apiCall<ApiResponse<any>>('/api/playauto/stats', { useCache: cache, cacheTTL: 30000 }),

  syncOrders: () =>
    apiCall<ApiResponse<{ imported_count: number }>>('/api/playauto/sync-orders', {
      method: 'POST',
      useCache: false,
    }),

  syncInventory: () =>
    apiCall<ApiResponse<{ updated_count: number }>>('/api/playauto/sync-inventory', {
      method: 'POST',
      useCache: false,
    }),
};

// ============================================
// Accounting API
// ============================================

export const accountingApi = {
  getDashboard: (period: string = 'this_month', cache = true) =>
    apiCall<AccountingDashboardStats>(`/api/accounting/dashboard/stats?period=${period}`, {
      useCache: cache,
      cacheTTL: 30000,
    }),

  getProfitLoss: (startDate: string, endDate: string, cache = true) =>
    apiCall<ProfitLossStatement>(`/api/accounting/profit-loss?start_date=${startDate}&end_date=${endDate}`, {
      useCache: cache,
      cacheTTL: 60000,
    }),

  getExpenses: (startDate?: string, endDate?: string, category?: string, cache = true) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (category) params.append('category', category);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiCall<ExpensesResponse>(`/api/accounting/expenses${query}`, {
      useCache: cache,
      cacheTTL: 30000,
    });
  },

  createExpense: (data: ExpenseCreate) =>
    apiCall<ApiResponse<{ expense_id: number }>>('/api/accounting/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateExpense: (id: number, data: Partial<ExpenseCreate>) =>
    apiCall<ApiResponse<void>>(`/api/accounting/expenses/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteExpense: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/accounting/expenses/${id}`, {
      method: 'DELETE',
    }),

  getSettlements: (market?: string, cache = true) => {
    const query = market ? `?market=${market}` : '';
    return apiCall<SettlementsResponse>(`/api/accounting/settlements${query}`, {
      useCache: cache,
      cacheTTL: 30000,
    });
  },

  createSettlement: (data: SettlementCreate) =>
    apiCall<ApiResponse<{ settlement_id: number }>>('/api/accounting/settlements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateSettlement: (id: number, data: { settlement_status?: string; memo?: string }) =>
    apiCall<ApiResponse<void>>(`/api/accounting/settlements/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteSettlement: (id: number) =>
    apiCall<ApiResponse<void>>(`/api/accounting/settlements/${id}`, {
      method: 'DELETE',
    }),

  getVAT: (year: number, quarter: number, cache = true) =>
    apiCall<VATCalculation>(`/api/accounting/tax/vat?year=${year}&quarter=${quarter}`, {
      useCache: cache,
      cacheTTL: 60000,
    }),

  getIncomeTax: (year: number, cache = true) =>
    apiCall<IncomeTaxEstimate>(`/api/accounting/tax/income?year=${year}`, {
      useCache: cache,
      cacheTTL: 60000,
    }),

  getMonthlyReport: (year: number, month: number, cache = true) =>
    apiCall<MonthlyReport>(`/api/accounting/report/monthly?year=${year}&month=${month}`, {
      useCache: cache,
      cacheTTL: 60000,
    }),

  getExpenseCategories: (cache = true) =>
    apiCall<ApiResponse<string[]>>('/api/accounting/expense-categories', {
      useCache: cache,
      cacheTTL: 300000, // 5 minutes
    }),
};

// ============================================
// Simplified Fetch API (for direct use)
// ============================================

/**
 * Simplified fetch wrapper with error handling and type safety
 * Use this when you need more control than the pre-built API methods
 */
export async function fetchAPI<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: response.statusText
      }));
      throw new ApiError(
        errorData.detail || errorData.message || `HTTP ${response.status}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error occurred'
    );
  }
}

// ============================================
// Cache Management
// ============================================

export const cache = {
  clear: () => apiCache.clear(),
  delete: (key: string) => apiCache.delete(key),
  clearPattern: (pattern: string) => apiCache.clearPattern(pattern),

  // Clear specific resource caches
  clearProducts: () => apiCache.clearPattern('/api/products'),
  clearOrders: () => apiCache.clearPattern('/api/orders'),
  clearMonitored: () => apiCache.clearPattern('/api/monitor'),
  clearNotifications: () => apiCache.clearPattern('/api/monitor/notifications'),
  clearPlayauto: () => apiCache.clearPattern('/api/playauto'),
  clearAccounting: () => apiCache.clearPattern('/api/accounting'),
};
