'use client';

import { useState, useEffect } from 'react';
import { Filter, X, Save } from 'lucide-react';

export interface FilterConfig {
  priceRange?: { min: number; max: number };
  marginRange?: { min: number; max: number };
  dateRange?: { start: string; end: string };
  markets?: string[];
  sources?: string[];
  statuses?: string[];
}

interface AdvancedFilterProps {
  onFilterChange: (filters: FilterConfig) => void;
  onSavePreset?: (name: string, filters: FilterConfig) => void;
  availableMarkets?: string[];
  availableSources?: string[];
  availableStatuses?: string[];
  isMobile?: boolean;
}

export default function AdvancedFilter({
  onFilterChange,
  onSavePreset,
  availableMarkets = [],
  availableSources = [],
  availableStatuses = [],
  isMobile: isMobileProp,
}: AdvancedFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(isMobileProp ?? false);
  const [filters, setFilters] = useState<FilterConfig>({
    priceRange: { min: 0, max: 1000000 },
    marginRange: { min: -100, max: 100 },
    dateRange: { start: '', end: '' },
    markets: [],
    sources: [],
    statuses: [],
  });
  const [presetName, setPresetName] = useState('');
  const [showSavePreset, setShowSavePreset] = useState(false);

  // 모바일 감지 (prop이 없을 경우 자동 감지)
  useEffect(() => {
    if (isMobileProp !== undefined) {
      setIsMobile(isMobileProp);
      return;
    }
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [isMobileProp]);

  const handleApply = () => {
    onFilterChange(filters);
    setIsOpen(false);
  };

  const handleReset = () => {
    const resetFilters: FilterConfig = {
      priceRange: { min: 0, max: 1000000 },
      marginRange: { min: -100, max: 100 },
      dateRange: { start: '', end: '' },
      markets: [],
      sources: [],
      statuses: [],
    };
    setFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  const handleSavePreset = () => {
    if (presetName.trim() && onSavePreset) {
      onSavePreset(presetName, filters);
      setPresetName('');
      setShowSavePreset(false);
    }
  };

  const toggleMultiSelect = (category: 'markets' | 'sources' | 'statuses', value: string) => {
    setFilters(prev => {
      const current = prev[category] || [];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [category]: updated };
    });
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`bg-white/80 backdrop-blur-xl rounded-xl shadow-lg hover:shadow-xl transition-all border border-white/20 flex items-center gap-2 text-gray-700 font-semibold whitespace-nowrap ${
          isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
        }`}
      >
        <Filter className={isMobile ? 'w-3 h-3' : 'w-4 h-4'} />
        {isMobile ? '필터' : '고급 필터'}
      </button>
    );
  }

  return (
    <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center ${isMobile ? 'p-0' : 'p-4'}`}>
      <div className={`bg-white/90 backdrop-blur-xl shadow-2xl border border-white/20 w-full overflow-y-auto ${
        isMobile ? 'h-full rounded-none' : 'rounded-2xl max-w-4xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className={`flex items-center justify-between border-b border-gray-200 ${isMobile ? 'p-4' : 'p-6'}`}>
          <h2 className={`font-bold text-gray-800 ${isMobile ? 'text-lg' : 'text-2xl'}`}>고급 필터</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className={isMobile ? 'w-4 h-4' : 'w-5 h-5'} />
          </button>
        </div>

        {/* Filter Content */}
        <div className={`space-y-5 ${isMobile ? 'p-4' : 'p-6 space-y-6'}`}>
          {/* Price Range */}
          <div>
            <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
              가격 범위 (원)
            </label>
            <div className={`flex items-center ${isMobile ? 'gap-2' : 'gap-4'}`}>
              <input
                type="number"
                value={filters.priceRange?.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange!, min: Number(e.target.value) }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                }`}
                placeholder="최소"
              />
              <span className="text-gray-500 text-sm">~</span>
              <input
                type="number"
                value={filters.priceRange?.max}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange!, max: Number(e.target.value) }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                }`}
                placeholder="최대"
              />
            </div>
          </div>

          {/* Margin Range */}
          <div>
            <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
              마진율 범위 (%)
            </label>
            <div className={`flex items-center ${isMobile ? 'gap-2' : 'gap-4'}`}>
              <input
                type="number"
                value={filters.marginRange?.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  marginRange: { ...prev.marginRange!, min: Number(e.target.value) }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                }`}
                placeholder="최소"
              />
              <span className="text-gray-500 text-sm">~</span>
              <input
                type="number"
                value={filters.marginRange?.max}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  marginRange: { ...prev.marginRange!, max: Number(e.target.value) }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                }`}
                placeholder="최대"
              />
            </div>
          </div>

          {/* Date Range */}
          <div>
            <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
              날짜 범위
            </label>
            <div className={`flex items-center ${isMobile ? 'gap-2' : 'gap-4'}`}>
              <input
                type="date"
                value={filters.dateRange?.start}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange!, start: e.target.value }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-2 py-2 text-sm' : 'px-4 py-2'
                }`}
              />
              <span className="text-gray-500 text-sm">~</span>
              <input
                type="date"
                value={filters.dateRange?.end}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange!, end: e.target.value }
                }))}
                className={`flex-1 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isMobile ? 'px-2 py-2 text-sm' : 'px-4 py-2'
                }`}
              />
            </div>
          </div>

          {/* Markets */}
          {availableMarkets.length > 0 && (
            <div>
              <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
                마켓
              </label>
              <div className="flex flex-wrap gap-2">
                {availableMarkets.map(market => (
                  <button
                    key={market}
                    onClick={() => toggleMultiSelect('markets', market)}
                    className={`rounded-xl font-medium transition-all ${
                      filters.markets?.includes(market)
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                  >
                    {market}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          {availableSources.length > 0 && (
            <div>
              <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
                소싱처
              </label>
              <div className="flex flex-wrap gap-2">
                {availableSources.map(source => (
                  <button
                    key={source}
                    onClick={() => toggleMultiSelect('sources', source)}
                    className={`rounded-xl font-medium transition-all ${
                      filters.sources?.includes(source)
                        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                  >
                    {source}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Statuses */}
          {availableStatuses.length > 0 && (
            <div>
              <label className={`block font-semibold text-gray-700 ${isMobile ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
                상태
              </label>
              <div className="flex flex-wrap gap-2">
                {availableStatuses.map(status => (
                  <button
                    key={status}
                    onClick={() => toggleMultiSelect('statuses', status)}
                    className={`rounded-xl font-medium transition-all ${
                      filters.statuses?.includes(status)
                        ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`border-t border-gray-200 ${isMobile ? 'p-4' : 'p-6'}`}>
          {/* 모바일에서는 세로 배치 */}
          <div className={`${isMobile ? 'flex flex-col gap-3' : 'flex items-center justify-between'}`}>
            {/* 프리셋 저장 */}
            <div className={`flex items-center gap-2 ${isMobile ? 'flex-wrap' : ''}`}>
              {!showSavePreset ? (
                <button
                  onClick={() => setShowSavePreset(true)}
                  className={`bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors flex items-center gap-2 ${
                    isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                  }`}
                >
                  <Save className={isMobile ? 'w-3 h-3' : 'w-4 h-4'} />
                  프리셋 저장
                </button>
              ) : (
                <div className={`flex items-center gap-2 ${isMobile ? 'flex-wrap w-full' : ''}`}>
                  <input
                    type="text"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    placeholder="프리셋 이름"
                    className={`bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      isMobile ? 'px-3 py-2 text-sm flex-1' : 'px-4 py-2'
                    }`}
                  />
                  <button
                    onClick={handleSavePreset}
                    className={`bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all ${
                      isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                    }`}
                  >
                    저장
                  </button>
                  <button
                    onClick={() => {
                      setShowSavePreset(false);
                      setPresetName('');
                    }}
                    className={`bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors ${
                      isMobile ? 'px-3 py-2 text-sm' : 'px-4 py-2'
                    }`}
                  >
                    취소
                  </button>
                </div>
              )}
            </div>

            {/* 초기화/적용 버튼 */}
            <div className={`flex items-center gap-2 ${isMobile ? 'justify-end' : ''}`}>
              <button
                onClick={handleReset}
                className={`bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors font-semibold ${
                  isMobile ? 'px-4 py-2 text-sm' : 'px-6 py-3'
                }`}
              >
                초기화
              </button>
              <button
                onClick={handleApply}
                className={`bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all ${
                  isMobile ? 'px-4 py-2 text-sm' : 'px-6 py-3'
                }`}
              >
                적용
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
