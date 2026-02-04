// ============================================
// Core Data Types
// ============================================

export interface Category {
  level1: string;
  level2: string;
  level3: string;
  level4: string;
}

export interface Product {
  id: number;
  product_name: string;
  selling_price: number;
  sourcing_url?: string;
  sourcing_product_name?: string;
  sourcing_price?: number;
  sourcing_source?: string;
  monitored_product_id?: number;
  detail_page_data?: string;
  category?: string;
  thumbnail_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  notes?: string;

  // PlayAuto fields
  c_sale_cd?: string;
  playauto_product_no?: string;
  sol_cate_no?: number;

  // Computed fields from backend
  effective_sourcing_price?: number;
  margin?: number;
  margin_rate?: number;

  // From monitored products join
  monitored_product_name?: string;
  monitored_product_url?: string;
  monitored_source?: string;
  monitored_price?: number;
  monitored_status?: string;
}

export interface MonitoredProduct {
  id: number;
  product_name: string;
  product_url: string;
  source: string;
  current_price: number;
  original_price?: number;
  current_status: 'available' | 'out_of_stock' | 'price_changed' | 'error';
  last_checked: string;
  created_at: string;
  check_interval_minutes: number;
  notes?: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_name: string;
  product_url: string;
  source: string;
  quantity: number;
  sourcing_price: number;
  selling_price: number;
  profit?: number;
  rpa_status: string;
  tracking_number?: string;
  monitored_product_id?: number;
  created_at: string;
  updated_at: string;
}

export interface Order {
  id: number;
  order_number: string;
  customer_name: string;
  customer_phone?: string;
  customer_address?: string;
  customer_request?: string;
  total_amount: number;
  order_date: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  market: string;
  tracking_number?: string;
  created_at: string;
  updated_at: string;
  notes?: string;

  // Relations
  items?: OrderItem[];

  // Playauto specific fields
  source?: 'manual' | 'playauto';
  playauto_order_id?: string;
  playauto_market?: string;
  original_order_data?: string;
}

export interface Notification {
  id: number;
  type: 'price_change' | 'stock_alert' | 'order_update' | 'system';
  title: string;
  message: string;
  related_id?: number;
  is_read: boolean;
  created_at: string;
}

export interface PlayautoConfig {
  id?: number;
  api_key?: string;
  is_active: boolean;
  check_interval_minutes: number;
  auto_import_orders: boolean;
  auto_update_inventory: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PlayautoAccount {
  market_code: string;
  market_name: string;
  shop_name: string;
  user_id: string;
  is_connected: boolean;
}

// ============================================
// API Response Types
// ============================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface OrdersResponse {
  success: boolean;
  orders: Order[];
  total: number;
}

// ============================================
// Statistics Types
// ============================================

export interface DashboardStats {
  total_orders: number;
  pending_orders: number;
  total_revenue: number;
  total_products: number;
  active_products: number;
  monitored_products: number;
  recent_orders: Order[];
  revenue_trend?: RevenueData[];
}

export interface RevenueData {
  date: string;
  revenue: number;
}

export interface OrderStats {
  total: number;
  pending: number;
  processing: number;
  shipped: number;
  delivered: number;
  cancelled: number;
  total_revenue: number;
}

// ============================================
// Form Types
// ============================================

export interface CreateProductRequest {
  product_name: string;
  selling_price: number;
  sourcing_url?: string;
  sourcing_product_name?: string;
  sourcing_price?: number;
  sourcing_source?: string;
  monitored_product_id?: number;
  detail_page_data?: string;
  category?: string;
  thumbnail_url?: string;
  notes?: string;
}

export interface UpdateProductRequest extends Partial<CreateProductRequest> {
  is_active?: boolean;
  c_sale_cd?: string;
}

export interface CreateOrderRequest {
  order_number: string;
  customer_name: string;
  customer_phone?: string;
  customer_address?: string;
  customer_request?: string;
  total_amount: number;
  order_date: string;
  status: Order['status'];
  market: string;
  tracking_number?: string;
  notes?: string;
  items: CreateOrderItemRequest[];
}

export interface CreateOrderItemRequest {
  product_name: string;
  quantity: number;
  unit_price: number;
  options?: string;
}

export interface UpdateOrderRequest extends Partial<Omit<CreateOrderRequest, 'items'>> {
  items?: CreateOrderItemRequest[];
}

// ============================================
// URL Extraction Types
// ============================================

export interface UrlExtractionResult {
  success: boolean;
  data?: {
    product_name: string;
    current_price: number;
    original_price?: number;
    source: string;
    status: string;
    thumbnail_url?: string;
  };
  message?: string;
}

// ============================================
// Sort and Filter Types
// ============================================

export type SortOrder = 'asc' | 'desc';

export type ProductSortBy = 'name' | 'price' | 'margin' | 'date';
export type OrderSortBy = 'date' | 'amount' | 'status' | 'customer';

export interface SortConfig<T extends string> {
  sortBy: T;
  sortOrder: SortOrder;
}

// ============================================
// Utility Types
// ============================================

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>> &
  {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

// ============================================
// Accounting System Types
// ============================================

export interface AccountingDashboardStats {
  success: boolean;
  period: {
    start: string;
    end: string;
  };
  summary: {
    total_revenue: number;
    total_cost: number;
    total_expenses: number;
    gross_profit: number;
    net_profit: number;
    profit_margin: number;
    order_count: number;
  };
  monthly_revenue: Array<{
    month: string;
    revenue: number;
  }>;
  market_revenue: Array<{
    market: string;
    revenue: number;
    orders: number;
  }>;
  expense_by_category: Array<{
    category: string;
    total: number;
  }>;
}

export interface ProfitLossStatement {
  success: boolean;
  period: {
    start: string;
    end: string;
  };
  statement: {
    revenue: {
      total_sales: number;
      order_count: number;
    };
    cost_of_sales: {
      total_cost: number;
    };
    gross_profit: {
      amount: number;
      margin: number;
    };
    operating_expenses: {
      breakdown: Array<{
        category: string;
        total: number;
      }>;
      total: number;
    };
    operating_profit: {
      amount: number;
      margin: number;
    };
    net_profit: {
      amount: number;
      margin: number;
    };
  };
}

export interface Expense {
  id: number;
  expense_date: string;
  category: string;
  subcategory?: string;
  amount: number;
  description?: string;
  payment_method?: string;
  receipt_url?: string;
  is_vat_deductible: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  expense_date: string;
  category: string;
  subcategory?: string;
  amount: number;
  description?: string;
  payment_method?: string;
  receipt_url?: string;
  is_vat_deductible: boolean;
}

export interface Settlement {
  id: number;
  market: string;
  settlement_date: string;
  period_start: string;
  period_end: string;
  total_sales: number;
  commission: number;
  shipping_fee: number;
  promotion_cost: number;
  net_amount: number;
  settlement_status: 'pending' | 'completed';
  memo?: string;
  created_at: string;
  updated_at: string;
}

export interface SettlementCreate {
  market: string;
  settlement_date: string;
  period_start: string;
  period_end: string;
  total_sales: number;
  commission: number;
  shipping_fee: number;
  promotion_cost: number;
  net_amount: number;
  settlement_status: 'pending' | 'completed';
  memo?: string;
}

export interface VATCalculation {
  success: boolean;
  year: number;
  quarter: number;
  period: {
    start: string;
    end: string;
  };
  calculation: {
    taxable_sales: number;
    vat_on_sales: number;
    taxable_purchases: number;
    deductible_expenses: number;
    vat_on_purchases: number;
    vat_payable: number;
  };
}

export interface IncomeTaxEstimate {
  success: boolean;
  year: number;
  calculation: {
    total_sales: number;
    total_purchases: number;
    total_expenses: number;
    taxable_income: number;
    income_tax: number;
    local_tax: number;
    total_tax: number;
    effective_tax_rate: number;
  };
}

export interface MonthlyReport {
  success: boolean;
  period: {
    year: number;
    month: number;
  };
  summary: {
    order_count: number;
    total_revenue: number;
    total_cost: number;
    total_expenses: number;
    net_profit: number;
    roi: number;
    avg_order_value: number;
  };
  best_day: {
    date: string;
    daily_revenue: number;
  } | null;
  bestsellers: Array<{
    product_name: string;
    total_quantity: number;
    total_revenue: number;
  }>;
  market_analysis: Array<{
    market: string;
    orders: number;
    revenue: number;
  }>;
}

export interface ExpensesResponse {
  success: boolean;
  expenses: Expense[];
  total: number;
}

export interface SettlementsResponse {
  success: boolean;
  settlements: Settlement[];
  total: number;
}
