'use client';

import { useState, useCallback, useEffect } from 'react';
import { Search, Package, RefreshCw } from 'lucide-react';
import { categoryStructure } from '@/lib/categories';
import type { Category } from '@/types';
import { productsApi, monitorApi, API_BASE_URL } from '@/lib/api';

interface Product {
  id: number;
  product_name: string;
  selling_price: number;
  sourcing_url?: string;
  sourcing_product_name?: string;
  sourcing_price?: number;
  sourcing_source?: string;
  category?: string;
  notes?: string;
  c_sale_cd?: string;
  c_sale_cd_gmk?: string;  // 지마켓/옥션용
  c_sale_cd_smart?: string;  // 스마트스토어용
}

// 마켓 코드 -> 한글 이름 변환
const getMarketName = (shopCd: string): string => {
  const marketNames: { [key: string]: string } = {
    'A001': '옥션',
    'A006': '쿠팡',
    'A112': '네이버 스마트스토어',
    'A027': '11번가',
    'A077': '지마켓',
    'A524': 'SSG.COM',
    'A113': '롯데ON',
    'A522': 'GS SHOP',
    'A419': 'CJ온스타일',
    'A900': '카페24',
  };
  return marketNames[shopCd] || shopCd;
};

export default function EditProductModal({ product, onClose, onSuccess }: {
  product: Product;
  onClose: () => void;
  onSuccess: () => void;
}) {
  // 카테고리 파싱
  const parseCategory = (categoryString?: string): Category => {
    if (!categoryString) return { level1: '', level2: '', level3: '', level4: '' };
    const parts = categoryString.split(' > ').map(s => s.trim());
    return {
      level1: parts[0] || '',
      level2: parts[1] || '',
      level3: parts[2] || '',
      level4: parts[3] || ''
    };
  };

  const [formData, setFormData] = useState({
    product_name: product.product_name,
    selling_price: product.selling_price.toString(),
    sourcing_url: product.sourcing_url || '',
    sourcing_product_name: product.sourcing_product_name || '',
    sourcing_price: product.sourcing_price?.toString() || '',
    sourcing_source: product.sourcing_source || '',
    thumbnail_url: (product as any).thumbnail_url || '',
    notes: product.notes || '',
    c_sale_cd_gmk: product.c_sale_cd_gmk || '',
    c_sale_cd_smart: product.c_sale_cd_smart || '',
  });
  const [category, setCategory] = useState<Category>(parseCategory(product.category));
  const [loading, setLoading] = useState(false);
  const [extractingUrl, setExtractingUrl] = useState(false);

  // 마켓 코드 관련 상태
  const [marketplaceCodes, setMarketplaceCodes] = useState<any[]>([]);
  const [loadingMarketplaceCodes, setLoadingMarketplaceCodes] = useState(false);
  const [syncingMarketplaceCodes, setSyncingMarketplaceCodes] = useState(false);

  const level1Options = Object.keys(categoryStructure);
  const level2Options = category.level1 ? Object.keys((categoryStructure as any)[category.level1] || {}) : [];
  const level3Options = category.level1 && category.level2 ? Object.keys((categoryStructure as any)[category.level1]?.[category.level2] || {}) : [];
  const level4Options = category.level1 && category.level2 && category.level3 ? (categoryStructure as any)[category.level1]?.[category.level2]?.[category.level3] || [] : [];

  const handleCategoryChange = (level: keyof Category, value: string) => {
    setCategory(prev => {
      const updated = { ...prev, [level]: value };
      if (level === 'level1') {
        updated.level2 = '';
        updated.level3 = '';
        updated.level4 = '';
      } else if (level === 'level2') {
        updated.level3 = '';
        updated.level4 = '';
      } else if (level === 'level3') {
        updated.level4 = '';
      }
      return updated;
    });
  };

  const extractUrlInfo = useCallback(async () => {
    if (!formData.sourcing_url) {
      alert('소싱처 URL을 입력해주세요.');
      return;
    }

    setExtractingUrl(true);
    try {
      // 공통 API 클라이언트 사용
      const result = await productsApi.extractUrlInfo(formData.sourcing_url);

      if (result.success && result.data) {
        const { product_name, current_price, source, thumbnail_url } = result.data;

        setFormData(prev => ({
          ...prev,
          sourcing_product_name: product_name || '',
          sourcing_price: current_price ? current_price.toString() : '',
          sourcing_source: source ? source.toUpperCase() : '',
          thumbnail_url: thumbnail_url || prev.thumbnail_url,
        }));

        alert('소싱처 정보를 불러왔습니다!');
      } else {
        alert('URL에서 정보를 추출할 수 없습니다.');
      }
    } catch (error) {
      console.error('URL 정보 추출 실패:', error);
      alert('URL 정보 추출 중 오류가 발생했습니다.');
    } finally {
      setExtractingUrl(false);
    }
  }, [formData.sourcing_url]);

  // 마켓 코드 조회
  const loadMarketplaceCodes = useCallback(async () => {
    setLoadingMarketplaceCodes(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${product.id}/marketplace-codes`);
      const data = await response.json();

      if (data.success) {
        setMarketplaceCodes(data.marketplace_codes || []);
      }
    } catch (error) {
      console.error('마켓 코드 조회 실패:', error);
    } finally {
      setLoadingMarketplaceCodes(false);
    }
  }, [product.id]);

  // 마켓 코드 동기화
  const handleSyncMarketplaceCodes = async () => {
    if (syncingMarketplaceCodes) return;

    setSyncingMarketplaceCodes(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${product.id}/sync-marketplace-codes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ ${data.synced_count}개 마켓 코드 수집 완료`);
        await loadMarketplaceCodes(); // 재조회
      } else {
        alert('수집 실패: ' + data.message);
      }
    } catch (error) {
      console.error('마켓 코드 동기화 실패:', error);
      alert('마켓 코드 동기화 중 오류가 발생했습니다.');
    } finally {
      setSyncingMarketplaceCodes(false);
    }
  };

  // 모달 열릴 때 마켓 코드 조회
  useEffect(() => {
    loadMarketplaceCodes();
  }, [loadMarketplaceCodes]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_name || !formData.selling_price) {
      alert('상품명과 판매가는 필수입니다.');
      return;
    }

    if (!category.level1 || !category.level2 || !category.level3 || !category.level4) {
      alert('카테고리를 모두 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      const categoryString = `${category.level1} > ${category.level2} > ${category.level3} > ${category.level4}`;

      // 공통 API 클라이언트 사용
      const data = await productsApi.update(product.id, {
        product_name: formData.product_name,
        selling_price: parseFloat(formData.selling_price),
        sourcing_url: formData.sourcing_url || undefined,
        sourcing_product_name: formData.sourcing_product_name || undefined,
        sourcing_price: formData.sourcing_price ? parseFloat(formData.sourcing_price) : undefined,
        sourcing_source: formData.sourcing_source || undefined,
        thumbnail_url: formData.thumbnail_url || undefined,
        category: categoryString,
        notes: formData.notes || undefined,
        c_sale_cd_gmk: formData.c_sale_cd_gmk || undefined,
        c_sale_cd_smart: formData.c_sale_cd_smart || undefined,
      });

      if (data.success) {
        alert('상품이 수정되었습니다!');
        onSuccess();
      } else {
        alert('상품 수정에 실패했습니다.');
      }
    } catch (error) {
      console.error('상품 수정 실패:', error);
      alert('상품 수정 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [product.id, formData, category, onSuccess]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">상품 수정</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 소싱처 변경 섹션 */}
          <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border-2 border-orange-300 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-5 h-5 text-orange-600" />
              <h3 className="text-lg font-bold text-orange-800">소싱처 변경</h3>
            </div>
            <p className="text-sm text-orange-700 mb-4">
              더 저렴한 소싱처를 찾으셨나요? 새로운 소싱처 URL을 입력하고 "정보 추출"을 클릭하세요.
            </p>

            {/* 기존 소싱 정보 표시 */}
            {product.sourcing_source && (
              <div className="bg-white/70 rounded-lg p-3 mb-4 border border-orange-200">
                <div className="text-xs font-semibold text-gray-600 mb-2">현재 소싱처</div>
                <div className="flex items-center gap-3">
                  {(product as any).thumbnail_url && (
                    <img
                      src={(product as any).thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${(product as any).thumbnail_url}` : (product as any).thumbnail_url}
                      alt="현재 상품"
                      className="w-16 h-16 object-cover rounded-lg border border-gray-200"
                    />
                  )}
                  <div className="text-sm space-y-1">
                    <div><span className="font-medium text-gray-700">마켓:</span> <span className="font-bold text-blue-600 uppercase">{product.sourcing_source}</span></div>
                    <div><span className="font-medium text-gray-700">소싱가:</span> <span className="font-bold text-green-600">{product.sourcing_price?.toLocaleString()}원</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* 새 소싱처 URL 입력 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                새 소싱처 URL
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={formData.sourcing_url}
                  onChange={(e) => setFormData({ ...formData, sourcing_url: e.target.value })}
                  className="flex-1 px-4 py-3 border-2 border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="예: https://www.11st.co.kr/products/... 또는 G마켓, 쿠팡 등"
                />
                <button
                  type="button"
                  onClick={extractUrlInfo}
                  disabled={extractingUrl || !formData.sourcing_url}
                  className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap font-semibold"
                >
                  <Search className="w-4 h-4" />
                  {extractingUrl ? '추출 중...' : '정보 추출'}
                </button>
              </div>
              <p className="text-xs text-orange-600 mt-2">
                💡 팁: 다른 마켓에서 더 저렴한 상품을 찾으셨다면 URL을 입력하고 정보를 추출하세요!
              </p>
            </div>

            {/* 수동 입력 옵션 */}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">소싱처 (수동)</label>
                <input
                  type="text"
                  value={formData.sourcing_source}
                  onChange={(e) => setFormData({ ...formData, sourcing_source: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"
                  placeholder="예: 11ST, GMARKET"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">소싱가 (수동)</label>
                <input
                  type="number"
                  value={formData.sourcing_price}
                  onChange={(e) => setFormData({ ...formData, sourcing_price: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"
                  placeholder="예: 3000"
                />
              </div>
            </div>

            {/* 추출된 새 소싱 정보 표시 */}
            {formData.sourcing_product_name && formData.sourcing_source && formData.sourcing_source !== product.sourcing_source && (
              <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4 mt-4">
                <div className="flex items-center gap-2 text-sm text-green-800 mb-3">
                  <Package className="w-4 h-4" />
                  <span className="font-bold">✨ 새로운 소싱 정보</span>
                </div>
                <div className="flex gap-4">
                  {formData.thumbnail_url && (
                    <div className="flex-shrink-0">
                      <img
                        src={formData.thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${formData.thumbnail_url}` : formData.thumbnail_url}
                        alt="새 상품 썸네일"
                        className="w-20 h-20 object-cover rounded-lg border-2 border-green-300"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div className="text-sm text-gray-700 space-y-1 flex-1">
                    <div><span className="font-medium">마켓:</span> <span className="font-bold text-blue-600 uppercase">{formData.sourcing_source}</span></div>
                    <div><span className="font-medium">상품명:</span> {formData.sourcing_product_name}</div>
                    {formData.sourcing_price && (
                      <div>
                        <span className="font-medium">소싱가:</span> <span className="font-bold text-green-600">{parseInt(formData.sourcing_price).toLocaleString()}원</span>
                        {product.sourcing_price && (
                          <span className="ml-2 text-xs">
                            {parseInt(formData.sourcing_price) < product.sourcing_price ? (
                              <span className="text-green-600 font-bold">
                                ▼ {(product.sourcing_price - parseInt(formData.sourcing_price)).toLocaleString()}원 절감!
                              </span>
                            ) : parseInt(formData.sourcing_price) > product.sourcing_price ? (
                              <span className="text-red-600 font-bold">
                                ▲ {(parseInt(formData.sourcing_price) - product.sourcing_price).toLocaleString()}원 증가
                              </span>
                            ) : (
                              <span className="text-gray-600">동일</span>
                            )}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">상품명 <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: 비비고 만두"
              required
            />
          </div>

          {/* 판매가 섹션 - 개선됨 */}
          <div className="bg-blue-50 border-2 border-blue-300 rounded-xl p-5">
            <label className="block text-sm font-semibold text-blue-800 mb-3">
              판매가 설정 <span className="text-red-500">*</span>
            </label>

            <div className="space-y-3">
              {/* 판매가 입력 */}
              <div>
                <input
                  type="number"
                  value={formData.selling_price}
                  onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg font-bold"
                  placeholder="예: 5000"
                  required
                />
              </div>

              {/* 마진 정보 */}
              {formData.sourcing_price && formData.selling_price && parseFloat(formData.selling_price) > 0 && (
                <div className="bg-white rounded-lg p-3 border border-blue-200">
                  <div className="text-xs text-gray-600 mb-1">마진 정보</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="text-sm font-medium text-gray-700">마진:</span>
                      <span className="ml-2 text-lg font-bold text-green-600">
                        {(parseFloat(formData.selling_price) - parseFloat(formData.sourcing_price)).toLocaleString()}원
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">마진율:</span>
                      <span className="ml-2 text-lg font-bold text-blue-600">
                        {((parseFloat(formData.selling_price) - parseFloat(formData.sourcing_price)) / parseFloat(formData.sourcing_price) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* 빠른 마진율 적용 버튼 */}
              {formData.sourcing_price && parseFloat(formData.sourcing_price) > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-700 mb-2">빠른 마진율 적용</div>
                  <div className="grid grid-cols-4 gap-2">
                    {[30, 40, 50, 60].map((rate) => {
                      const calculatedPrice = Math.round(parseFloat(formData.sourcing_price) * (1 + rate / 100) / 100) * 100;
                      return (
                        <button
                          key={rate}
                          type="button"
                          onClick={() => setFormData({ ...formData, selling_price: calculatedPrice.toString() })}
                          className="px-3 py-2 bg-white border-2 border-blue-300 rounded-lg hover:bg-blue-100 hover:border-blue-500 transition-all text-sm font-semibold text-blue-700"
                        >
                          {rate}%
                          <div className="text-xs text-gray-600 mt-1">{calculatedPrice.toLocaleString()}원</div>
                        </button>
                      );
                    })}
                  </div>
                  <p className="text-xs text-blue-600 mt-2">
                    💡 버튼을 클릭하면 해당 마진율로 판매가가 자동 계산됩니다
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* 카테고리 4단계 선택 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">카테고리 <span className="text-red-500">*</span></label>
            <div className="grid grid-cols-2 gap-3">
              <select
                value={category.level1}
                onChange={(e) => handleCategoryChange('level1', e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">1단계 선택</option>
                {level1Options.map((option: string) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>

              <select
                value={category.level2}
                onChange={(e) => handleCategoryChange('level2', e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!category.level1}
                required
              >
                <option value="">2단계 선택</option>
                {level2Options.map((option: string) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>

              <select
                value={category.level3}
                onChange={(e) => handleCategoryChange('level3', e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!category.level2}
                required
              >
                <option value="">3단계 선택</option>
                {level3Options.map((option: string) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>

              <select
                value={category.level4}
                onChange={(e) => handleCategoryChange('level4', e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!category.level3}
                required
              >
                <option value="">4단계 선택</option>
                {level4Options.map((option: string) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
            {category.level4 && (
              <p className="text-xs text-blue-600 mt-2">
                선택된 카테고리: {category.level1} &gt; {category.level2} &gt; {category.level3} &gt; {category.level4}
              </p>
            )}
          </div>

          {/* PlayAuto 판매자 관리코드 */}
          <div className="bg-purple-50 border-2 border-purple-300 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-bold text-purple-800">PlayAuto 연동 정보</h3>
            </div>

            <p className="text-xs text-purple-600 mb-4 bg-white/70 rounded-lg p-3 border border-purple-200">
              💡 상품이 채널별로 2번 등록되므로 판매자 관리코드도 2개입니다.
              PlayAuto 관리자 페이지에서 각 채널의 코드를 확인하여 입력하세요.
            </p>

            <div className="space-y-4">
              {/* 지마켓/옥션용 c_sale_cd */}
              <div>
                <label className="block text-sm font-semibold text-purple-800 mb-2">
                  🛒 지마켓/옥션용 판매자 관리코드
                </label>
                <input
                  type="text"
                  value={formData.c_sale_cd_gmk}
                  onChange={(e) => setFormData({ ...formData, c_sale_cd_gmk: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent font-mono text-sm"
                  placeholder="예: m20260204a54899b72"
                />
                <p className="text-xs text-gray-600 mt-1">
                  단일상품(std_ol_yn=Y)으로 등록된 상품의 코드
                </p>
              </div>

              {/* 스마트스토어용 c_sale_cd */}
              <div>
                <label className="block text-sm font-semibold text-purple-800 mb-2">
                  🏪 스마트스토어 등용 판매자 관리코드
                </label>
                <input
                  type="text"
                  value={formData.c_sale_cd_smart}
                  onChange={(e) => setFormData({ ...formData, c_sale_cd_smart: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent font-mono text-sm"
                  placeholder="예: m20260204b98765c43"
                />
                <p className="text-xs text-gray-600 mt-1">
                  일반상품(std_ol_yn=N)으로 등록된 상품의 코드
                </p>
              </div>
            </div>

            {(formData.c_sale_cd_gmk || formData.c_sale_cd_smart) && (
              <div className="mt-4 bg-green-50 border border-green-300 rounded-lg p-3">
                <p className="text-xs text-green-700 font-semibold">
                  ✅ 상품 수정 시 입력된 채널의 PlayAuto 상품이 함께 업데이트됩니다.
                </p>
                {formData.c_sale_cd_gmk && (
                  <p className="text-xs text-gray-600 mt-1">• 지마켓/옥션 상품 동기화됨</p>
                )}
                {formData.c_sale_cd_smart && (
                  <p className="text-xs text-gray-600">• 스마트스토어 등 상품 동기화됨</p>
                )}
              </div>
            )}

            {/* 마켓별 상품코드 정보 */}
            <div className="mt-6 border-t border-purple-200 pt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-purple-600" />
                  <h4 className="text-sm font-bold text-purple-800">쇼핑몰 상품코드</h4>
                </div>
                <button
                  type="button"
                  onClick={handleSyncMarketplaceCodes}
                  disabled={syncingMarketplaceCodes || loadingMarketplaceCodes}
                  className="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg text-xs font-semibold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 ${syncingMarketplaceCodes ? 'animate-spin' : ''}`} />
                  {syncingMarketplaceCodes ? '수집 중...' : '수집'}
                </button>
              </div>

              {loadingMarketplaceCodes ? (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-purple-600">로딩 중...</p>
                </div>
              ) : marketplaceCodes.length > 0 ? (
                <div className="space-y-2">
                  {marketplaceCodes.map((code, idx) => (
                    <div
                      key={idx}
                      className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-purple-900">
                          {getMarketName(code.shop_cd)}
                        </p>
                        <p className="text-xs text-gray-600 font-mono mt-0.5">
                          {code.shop_sale_no}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">
                          {code.shop_cd}
                        </p>
                        {code.transmitted_at && (
                          <p className="text-xs text-gray-400 mt-0.5">
                            {new Date(code.transmitted_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-600">
                    아직 수집된 쇼핑몰 상품코드가 없습니다.
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    PlayAuto에서 마켓 전송 후 &quot;수집&quot; 버튼을 클릭하세요.
                  </p>
                </div>
              )}

              <p className="text-xs text-purple-600 mt-2 bg-white/70 rounded-lg p-2 border border-purple-100">
                💡 PlayAuto에서 마켓 전송 시 자동으로 부여되는 각 쇼핑몰의 고유 상품번호입니다.
                주문 수집 시 자동으로 매칭됩니다.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">메모</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="상품에 대한 메모를 입력하세요"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {loading ? '수정 중...' : '상품 수정'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 bg-gray-500 text-white rounded-xl font-semibold hover:bg-gray-600 transition-colors"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
