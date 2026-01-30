'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, X, Package, ShoppingCart } from 'lucide-react';

interface SearchResult {
  id: string;
  type: 'order' | 'product';
  title: string;
  subtitle: string;
  icon: React.ReactNode;
}

interface GlobalSearchProps {
  onResultClick?: (result: SearchResult) => void;
}

export default function GlobalSearch({ onResultClick }: GlobalSearchProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    // 디바운스 처리 (500ms)
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      searchData(query);
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  const searchData = async (searchQuery: string) => {
    try {
      setIsLoading(true);
      const searchResults: SearchResult[] = [];

      // 주문 검색
      const ordersRes = await fetch(`http://localhost:8000/api/orders/list?limit=50`);
      const ordersData = await ordersRes.json();

      if (ordersData.success && ordersData.orders) {
        ordersData.orders
          .filter((order: any) =>
            order.order_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            order.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            order.market?.toLowerCase().includes(searchQuery.toLowerCase())
          )
          .slice(0, 5)
          .forEach((order: any) => {
            searchResults.push({
              id: `order-${order.id}`,
              type: 'order',
              title: `${order.market} - ${order.order_number}`,
              subtitle: `${order.customer_name} / ${order.total_amount?.toLocaleString()}원`,
              icon: <Package className="w-4 h-4" />,
            });
          });
      }

      // 모니터링 상품 검색
      const productsRes = await fetch(`http://localhost:8000/api/monitor/products`);
      const productsData = await productsRes.json();

      if (productsData.success && productsData.products) {
        productsData.products
          .filter((product: any) =>
            product.product_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            product.source?.toLowerCase().includes(searchQuery.toLowerCase())
          )
          .slice(0, 5)
          .forEach((product: any) => {
            searchResults.push({
              id: `product-${product.id}`,
              type: 'product',
              title: product.product_name,
              subtitle: `${product.source.toUpperCase()} / ${product.current_price?.toLocaleString()}원`,
              icon: <ShoppingCart className="w-4 h-4" />,
            });
          });
      }

      setResults(searchResults);
    } catch (error) {
      console.error('검색 실패:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    if (onResultClick) {
      onResultClick(result);
    }
    setIsOpen(false);
    setQuery('');
  };

  const handleClear = () => {
    setQuery('');
    setResults([]);
  };

  return (
    <div className="relative w-full max-w-md" ref={searchRef}>
      {/* 검색 입력 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="주문번호, 상품명, 고객명 검색..."
          className="w-full pl-10 pr-10 py-3 bg-white/80 backdrop-blur-xl border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* 검색 결과 드롭다운 */}
      {isOpen && (query.length >= 2 || results.length > 0) && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/10 border border-white/20 overflow-hidden z-50 max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-500 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">검색 중...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              검색 결과가 없습니다.
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {results.map((result) => (
                <button
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50/50 transition-colors flex items-start gap-3"
                >
                  <div className={`flex-shrink-0 mt-1 p-2 rounded-lg ${
                    result.type === 'order'
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-green-100 text-green-600'
                  }`}>
                    {result.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-800 truncate">{result.title}</p>
                    <p className="text-sm text-gray-600 truncate">{result.subtitle}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
