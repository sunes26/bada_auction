'use client';

import { useState } from 'react';
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
}

export default function AdvancedFilter({
  onFilterChange,
  onSavePreset,
  availableMarkets = [],
  availableSources = [],
  availableStatuses = [],
}: AdvancedFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
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
        className="px-4 py-2 bg-white/80 backdrop-blur-xl rounded-xl shadow-lg hover:shadow-xl transition-all border border-white/20 flex items-center gap-2 text-gray-700 font-semibold"
      >
        <Filter className="w-4 h-4" />
        고급 필터
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">고급 필터</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Content */}
        <div className="p-6 space-y-6">
          {/* Price Range */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              가격 범위 (원)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={filters.priceRange?.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange!, min: Number(e.target.value) }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="최소 금액"
              />
              <span className="text-gray-500">~</span>
              <input
                type="number"
                value={filters.priceRange?.max}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange!, max: Number(e.target.value) }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="최대 금액"
              />
            </div>
          </div>

          {/* Margin Range */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              마진율 범위 (%)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={filters.marginRange?.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  marginRange: { ...prev.marginRange!, min: Number(e.target.value) }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="최소 마진율"
              />
              <span className="text-gray-500">~</span>
              <input
                type="number"
                value={filters.marginRange?.max}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  marginRange: { ...prev.marginRange!, max: Number(e.target.value) }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="최대 마진율"
              />
            </div>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              날짜 범위
            </label>
            <div className="flex items-center gap-4">
              <input
                type="date"
                value={filters.dateRange?.start}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange!, start: e.target.value }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="text-gray-500">~</span>
              <input
                type="date"
                value={filters.dateRange?.end}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange!, end: e.target.value }
                }))}
                className="flex-1 px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Markets */}
          {availableMarkets.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                마켓
              </label>
              <div className="flex flex-wrap gap-2">
                {availableMarkets.map(market => (
                  <button
                    key={market}
                    onClick={() => toggleMultiSelect('markets', market)}
                    className={`px-4 py-2 rounded-xl font-medium transition-all ${
                      filters.markets?.includes(market)
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
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
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                소싱처
              </label>
              <div className="flex flex-wrap gap-2">
                {availableSources.map(source => (
                  <button
                    key={source}
                    onClick={() => toggleMultiSelect('sources', source)}
                    className={`px-4 py-2 rounded-xl font-medium transition-all ${
                      filters.sources?.includes(source)
                        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
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
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                상태
              </label>
              <div className="flex flex-wrap gap-2">
                {availableStatuses.map(status => (
                  <button
                    key={status}
                    onClick={() => toggleMultiSelect('statuses', status)}
                    className={`px-4 py-2 rounded-xl font-medium transition-all ${
                      filters.statuses?.includes(status)
                        ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg'
                        : 'bg-white/50 text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="flex items-center gap-2">
            {!showSavePreset ? (
              <button
                onClick={() => setShowSavePreset(true)}
                className="px-4 py-2 bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                프리셋 저장
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="프리셋 이름"
                  className="px-4 py-2 bg-white/50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleSavePreset}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                >
                  저장
                </button>
                <button
                  onClick={() => {
                    setShowSavePreset(false);
                    setPresetName('');
                  }}
                  className="px-4 py-2 bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  취소
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="px-6 py-3 bg-white/80 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors font-semibold"
            >
              초기화
            </button>
            <button
              onClick={handleApply}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              적용
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
