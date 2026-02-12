'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Plus, ExternalLink, TrendingUp, TrendingDown, DollarSign, Package, Eye, Edit, Trash2, RefreshCw, Search, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Line } from 'react-chartjs-2';
// import { categoryStructure } from '@/lib/categories'; // DB에서 동적으로 로드
import type { Category } from '@/types';
import type { Product as ProductType, ProductSortBy } from '@/lib/types';
import { productsApi, monitorApi, cache, API_BASE_URL } from '@/lib/api';
import EditProductModal from '@/components/modals/EditProductModal';
import DailyTemplate from '@/components/templates/DailyTemplate';
import FoodTemplate from '@/components/templates/FoodTemplate';
import ElectronicsTemplate from '@/components/templates/ElectronicsTemplate';
import ProcessedFoodTemplate from '@/components/templates/ProcessedFoodTemplate';
import HygieneTemplate from '@/components/templates/HygieneTemplate';
import StationeryTemplate from '@/components/templates/StationeryTemplate';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ProductType을 사용 (lib/types.ts에서 import)

interface PriceHistory {
  id: number;
  price: number;
  checked_at: string;
}

interface ProductSourcingPageProps {
  isMobile?: boolean;
}

export default function ProductSourcingPage({ isMobile = false }: ProductSourcingPageProps) {
  const [products, setProducts] = useState<ProductType[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<ProductType | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');  // 기본 필터: 전체
  const [sourcingStatusFilter, setSourcingStatusFilter] = useState<'all' | 'available' | 'out_of_stock' | 'discontinued'>('all');  // 소싱처 상태 필터
  const [inputTypeFilter, setInputTypeFilter] = useState<'all' | 'auto' | 'manual'>('all');  // 입력 방식 필터

  // 검색 및 정렬
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<ProductSortBy>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);

  // 일괄 작업
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // 마켓 코드 수집
  const [syncingMarketplaceCodes, setSyncingMarketplaceCodes] = useState(false);

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      const isActive = activeFilter === 'all' ? undefined : activeFilter === 'active';

      // 공통 API 클라이언트 사용 (캐싱 적용)
      const data = await productsApi.list(true);

      if (data.success) {
        // 필터 적용
        let filtered = data.data || [];
        if (isActive !== undefined) {
          filtered = filtered.filter(p => p.is_active === isActive);
        }
        setProducts(filtered);
      }
    } catch (error) {
      console.error('상품 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // 쇼핑몰 상품코드 일괄 수집
  const handleSyncAllMarketplaceCodes = async () => {
    if (syncingMarketplaceCodes) return;

    if (!confirm('PlayAuto에 등록된 모든 상품의 쇼핑몰 상품코드를 수집하시겠습니까?\n\n이미 수집된 상품은 자동으로 건너뜁니다.')) {
      return;
    }

    try {
      setSyncingMarketplaceCodes(true);

      const response = await fetch(`${API_BASE_URL}/api/products/sync-all-marketplace-codes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        toast.success(data.message, {
          description: `총 ${data.total_products}개 상품 중 ${data.synced_products}개 수집 완료`
        });
      } else {
        toast.error('수집 실패: ' + data.message);
      }
    } catch (error) {
      console.error('마켓 코드 수집 실패:', error);
      toast.error('마켓 코드 수집 중 오류가 발생했습니다.');
    } finally {
      setSyncingMarketplaceCodes(false);
    }
  };

  // 검색, 정렬, 필터링 (useMemo로 최적화)
  const filteredProducts = useMemo(() => {
    let result = [...products];

    // 검색
    if (searchQuery) {
      result = result.filter(p =>
        p.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.sourcing_source?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // 소싱처 상태 필터
    if (sourcingStatusFilter !== 'all') {
      result = result.filter(p => p.monitored_status === sourcingStatusFilter);
    }

    // 입력 방식 필터
    if (inputTypeFilter !== 'all') {
      result = result.filter(p => {
        const productInputType = (p as any).input_type || 'auto';
        return productInputType === inputTypeFilter;
      });
    }

    // 정렬
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.product_name.localeCompare(b.product_name);
          break;
        case 'price':
          comparison = a.selling_price - b.selling_price;
          break;
        case 'margin':
          comparison = (a.margin_rate || 0) - (b.margin_rate || 0);
          break;
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [products, searchQuery, sortBy, sortOrder, sourcingStatusFilter, inputTypeFilter]);

  // 페이지네이션된 상품 목록 (useMemo로 최적화)
  const paginatedProducts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredProducts.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredProducts, currentPage, itemsPerPage]);

  const totalPages = useMemo(() => Math.ceil(filteredProducts.length / itemsPerPage), [filteredProducts.length, itemsPerPage]);

  const handleViewDetail = useCallback(async (product: ProductType) => {
    try {
      // 공통 API 클라이언트 사용 (캐싱 적용)
      const data = await productsApi.get(product.id, true);

      if (data.success && data.data) {
        setSelectedProduct(data.data);
        setPriceHistory((data as any).price_history || []);
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('상품 상세 조회 실패:', error);
    }
  }, []);

  const handleDeleteProduct = useCallback(async (productId: number) => {
    if (!confirm('정말로 이 상품을 삭제하시겠습니까?')) return;

    try {
      const data = await productsApi.delete(productId);

      if (data.success) {
        alert('상품이 삭제되었습니다.');
        cache.clearProducts();
        loadProducts();
      }
    } catch (error) {
      console.error('상품 삭제 실패:', error);
      alert('상품 삭제에 실패했습니다.');
    }
  }, [loadProducts]);

  const handleToggleStatus = useCallback(async (productId: number, currentStatus: boolean, productName: string) => {
    try {
      // 확인 다이얼로그
      const action = currentStatus ? '중단' : '판매중';
      const confirmed = window.confirm(
        `"${productName}" 상품을 ${action}으로 변경하시겠습니까?`
      );

      if (!confirmed) {
        return; // 사용자가 취소한 경우
      }

      const newStatus = !currentStatus;
      const data = await productsApi.update(productId, { is_active: newStatus });

      if (data.success) {
        // UI 즉시 업데이트
        setProducts(prev => prev.map(p =>
          p.id === productId ? { ...p, is_active: newStatus } : p
        ));
        cache.clearProducts();

        toast.success(`상품 상태가 ${action}으로 변경되었습니다.`);
      } else {
        toast.error('상태 변경에 실패했습니다.');
      }
    } catch (error) {
      console.error('상태 변경 실패:', error);
      toast.error('상태 변경 중 오류가 발생했습니다.');
    }
  }, []);

  const handleUpdateSourcingPrice = useCallback(async (productId: number, productName: string) => {
    if (!confirm(`${productName}의 소싱가를 업데이트하시겠습니까?\n\n소싱처에서 현재 가격을 다시 확인합니다.`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${productId}/update-sourcing-price`, {
        method: 'POST'
      });

      // HTTP 에러 처리
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '알 수 없는 오류' }));
        alert(`소싱가 업데이트 실패\n\n${errorData.detail || errorData.message || '서버 오류'}`);
        return;
      }

      const data = await response.json();

      if (data.success) {
        // 가격 변동이 없는 경우
        if (!data.price_diff || data.price_diff === 0) {
          alert(`가격 변동이 없습니다.\n\n현재 소싱가: ${data.current_price?.toLocaleString() || '알 수 없음'}원`);
        } else {
          // 가격 변동이 있는 경우
          const priceDiff = data.price_diff || 0;
          const oldPrice = data.old_price || 0;
          const newPrice = data.new_price || 0;
          const marginRate = data.new_margin_rate || 0;

          const message = priceDiff > 0
            ? `⚠️ 소싱가가 ${priceDiff.toLocaleString()}원 인상되었습니다.\n\n기존: ${oldPrice.toLocaleString()}원\n변경: ${newPrice.toLocaleString()}원\n\n새 마진율: ${marginRate}%`
            : `✅ 소싱가가 ${Math.abs(priceDiff).toLocaleString()}원 인하되었습니다!\n\n기존: ${oldPrice.toLocaleString()}원\n변경: ${newPrice.toLocaleString()}원\n\n새 마진율: ${marginRate}%`;
          alert(message);
        }
        cache.clearProducts();
        loadProducts();
      } else {
        alert(`소싱가 업데이트 실패\n\n${data.message || data.detail || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('소싱가 업데이트 실패:', error);
      alert(`소싱가 업데이트 중 오류가 발생했습니다.\n\n${error.message || '네트워크 오류'}\n\n소싱처 URL이 올바른지 확인해주세요.`);
    }
  }, [loadProducts]);

  // PlayAuto 동기화
  const handleSyncToPlayauto = useCallback(async (productId: number, productName: string, cSaleCd: string | null | undefined) => {
    if (!cSaleCd) {
      toast.error('PlayAuto에 등록되지 않은 상품입니다.\n먼저 "상품등록"을 진행해주세요.');
      return;
    }

    const confirmed = window.confirm(
      `"${productName}" 상품 정보를 PlayAuto와 동기화하시겠습니까?\n\n` +
      `마켓플레이스의 상품 정보(상품명, 가격 등)가 현재 정보로 업데이트됩니다.`
    );

    if (!confirmed) return;

    try {
      toast.info('PlayAuto 동기화 중...');
      const response = await productsApi.syncToPlayauto(productId);

      if (response.success) {
        // 타입 assertion: 백엔드가 product_name, selling_price를 직접 반환
        const data = response as any;
        toast.success(
          `PlayAuto 동기화 완료!\n\n` +
          `상품명: ${data.product_name || productName}\n` +
          `판매가: ${data.selling_price?.toLocaleString() || '-'}원`
        );
        cache.clearProducts();
      } else {
        toast.error(`PlayAuto 동기화 실패\n\n${response.message || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('PlayAuto 동기화 실패:', error);
      toast.error(`PlayAuto 동기화 중 오류가 발생했습니다.\n\n${error.message || '네트워크 오류'}`);
    }
  }, []);

  // 일괄 선택/해제
  const handleSelectAll = useCallback(() => {
    if (selectedIds.length === paginatedProducts.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(paginatedProducts.map(p => p.id));
    }
  }, [selectedIds.length, paginatedProducts]);

  const handleSelectProduct = useCallback((productId: number) => {
    setSelectedIds(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  }, []);

  // 일괄 삭제
  const handleBulkDelete = useCallback(async () => {
    if (selectedIds.length === 0) {
      alert('삭제할 상품을 선택해주세요.');
      return;
    }

    if (!confirm(`선택한 ${selectedIds.length}개 상품을 삭제하시겠습니까?`)) return;

    try {
      await Promise.all(selectedIds.map(id => productsApi.delete(id)));
      alert('선택한 상품이 삭제되었습니다.');
      setSelectedIds([]);
      cache.clearProducts();
      loadProducts();
    } catch (error) {
      console.error('일괄 삭제 실패:', error);
      alert('일괄 삭제 중 오류가 발생했습니다.');
    }
  }, [selectedIds, loadProducts]);

  // 일괄 상태 변경
  const handleBulkToggleStatus = useCallback(async (newStatus: boolean) => {
    if (selectedIds.length === 0) {
      alert('상태를 변경할 상품을 선택해주세요.');
      return;
    }

    try {
      await Promise.all(
        selectedIds.map(id => productsApi.update(id, { is_active: newStatus }))
      );
      alert(`선택한 ${selectedIds.length}개 상품의 상태가 변경되었습니다.`);
      setSelectedIds([]);
      cache.clearProducts();
      loadProducts();
    } catch (error) {
      console.error('일괄 상태 변경 실패:', error);
      alert('일괄 상태 변경 중 오류가 발생했습니다.');
    }
  }, [selectedIds, loadProducts]);

  // 플레이오토 상품 등록 (저장된 기본 템플릿 사용)
  const handleRegisterToPlayauto = useCallback(async () => {
    if (selectedIds.length === 0) {
      alert('등록할 상품을 선택해주세요.');
      return;
    }

    const confirmed = confirm(
      `선택한 ${selectedIds.length}개 상품을 기본 쇼핑몰에 등록하시겠습니까?\n\n` +
      `(설정에서 지정한 기본 템플릿이 사용됩니다)`
    );

    if (!confirmed) return;

    try {
      // API 호출 - site_list 없이 호출하면 백엔드에서 기본 템플릿 자동 사용
      const response = await fetch(`${API_BASE_URL}/api/products/register-to-playauto`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_ids: selectedIds
        })
      });

      const data = await response.json();

      // 디버깅: 전체 응답 콘솔 출력
      console.log('=== PlayAuto 상품 등록 응답 ===');
      console.log('전체 응답:', data);

      // 채널 분류 및 쿠팡 디버깅 정보 출력
      if (data.results) {
        data.results.forEach((result: {
          product_name?: string;
          coupang_debug?: { opt_type?: string; std_ol_yn?: string; opts?: unknown; site_list?: unknown; error?: string; api_response?: unknown };
          channel_debug?: { site_list_received?: string[]; single_product_sites?: string[]; coupang_sites?: string[]; smartstore_sites?: string[] }
        }) => {
          // 채널 분류 정보 출력
          if (result.channel_debug) {
            console.log(`\n[채널 분류] 상품: ${result.product_name}`);
            console.log('받은 site_list:', result.channel_debug.site_list_received);
            console.log('옥션/지마켓:', result.channel_debug.single_product_sites);
            console.log('쿠팡:', result.channel_debug.coupang_sites);
            console.log('스마트스토어:', result.channel_debug.smartstore_sites);
          }

          // 쿠팡 디버깅 정보 출력
          if (result.coupang_debug) {
            console.log(`\n[쿠팡 디버그] 상품: ${result.product_name}`);
            console.log('opt_type:', result.coupang_debug.opt_type);
            console.log('std_ol_yn:', result.coupang_debug.std_ol_yn);
            console.log('opts:', result.coupang_debug.opts);
            console.log('site_list:', result.coupang_debug.site_list);
            if (result.coupang_debug.error) {
              console.log('에러:', result.coupang_debug.error);
              console.log('API 응답:', result.coupang_debug.api_response);
            }
          } else {
            console.log(`\n[쿠팡] 쿠팡 등록 시도 안됨 (coupang_sites가 비어있음)`);
          }
        });
      }
      console.log('==============================');

      if (response.ok && data.success) {
        alert(
          `상품 등록 완료!\n\n` +
          `성공: ${data.success_count}개\n` +
          `실패: ${data.fail_count}개\n\n` +
          `등록된 상품은 자동으로 판매중 상태로 변경됩니다.`
        );
        setSelectedIds([]);
        cache.clearProducts();
        loadProducts();
      } else {
        // 기본 템플릿 미설정 오류 처리
        const errorMsg = data.detail || data.error || '상품 등록에 실패했습니다.';
        alert(errorMsg);
      }
    } catch (error) {
      console.error('플레이오토 등록 실패:', error);
      alert('플레이오토 등록 중 오류가 발생했습니다.');
    }
  }, [selectedIds, loadProducts]);

  // Excel 내보내기 (공통 함수) - 이미지 포함
  const exportToExcel = useCallback(async (productsToExport: ProductType[], filename: string) => {
    try {
      // ExcelJS 동적 import
      const ExcelJS = (await import('exceljs')).default;

      // 워크북 생성
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('상품목록');

      // 헤더 행 추가
      worksheet.columns = [
        { header: '번호', key: 'no', width: 8 },
        { header: '썸네일', key: 'thumbnail', width: 15 },
        { header: '상품명', key: 'name', width: 35 },
        { header: '카테고리', key: 'category', width: 25 },
        { header: '판매가', key: 'sellingPrice', width: 12 },
        { header: '소싱가', key: 'sourcingPrice', width: 12 },
        { header: '마진', key: 'margin', width: 12 },
        { header: '마진율', key: 'marginRate', width: 10 },
        { header: '소싱처', key: 'source', width: 12 },
        { header: '상태', key: 'status', width: 10 },
        { header: '등록일', key: 'created', width: 12 },
      ];

      // 헤더 스타일 적용
      worksheet.getRow(1).font = { bold: true };
      worksheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' };
      worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE0E0E0' }
      };

      // 이미지 다운로드 및 추가를 위한 함수
      const downloadImage = async (imageUrl: string): Promise<ArrayBuffer | null> => {
        try {
          const response = await fetch(imageUrl);
          if (!response.ok) return null;
          return await response.arrayBuffer();
        } catch (error) {
          console.error('이미지 다운로드 실패:', imageUrl, error);
          return null;
        }
      };

      // 데이터 및 이미지 추가
      for (let i = 0; i < productsToExport.length; i++) {
        const p = productsToExport[i];
        const sourcingPrice = p.sourcing_price || (p as any).effective_sourcing_price || 0;
        const thumbnailUrl = (p as any).thumbnail_url;
        const fullImageUrl = thumbnailUrl?.startsWith('/static')
          ? `${API_BASE_URL}${thumbnailUrl}`
          : thumbnailUrl;

        // 데이터 행 추가
        const row = worksheet.addRow({
          no: i + 1,
          thumbnail: '', // 이미지는 별도로 추가
          name: p.product_name,
          category: p.category || '-',
          sellingPrice: p.selling_price,
          sourcingPrice: sourcingPrice,
          margin: p.margin || 0,
          marginRate: (p.margin_rate || 0).toFixed(1) + '%',
          source: p.sourcing_source || '-',
          status: p.is_active ? '판매중' : '중단',
          created: new Date(p.created_at).toLocaleDateString()
        });

        // 행 높이 설정 (이미지 크기에 맞게)
        row.height = 80;
        row.alignment = { vertical: 'middle', horizontal: 'center' };

        // 이미지 다운로드 및 추가
        if (fullImageUrl && fullImageUrl !== '-') {
          try {
            const imageBuffer = await downloadImage(fullImageUrl);
            if (imageBuffer) {
              const imageId = workbook.addImage({
                buffer: imageBuffer,
                extension: 'jpeg',
              });

              // 이미지를 셀에 추가 (B열, 해당 행)
              worksheet.addImage(imageId, {
                tl: { col: 1, row: i + 1 }, // B열(1), 데이터 행(+1은 헤더)
                ext: { width: 80, height: 80 },
                editAs: 'oneCell'
              });
            }
          } catch (error) {
            console.error('이미지 추가 실패:', fullImageUrl, error);
          }
        }
      }

      // Excel 파일 생성 및 다운로드
      const buffer = await workbook.xlsx.writeBuffer();
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();

      alert('Excel 파일이 다운로드되었습니다. 썸네일 이미지가 포함되어 있습니다.');
    } catch (error) {
      console.error('Excel 내보내기 실패:', error);
      alert('Excel 내보내기 중 오류가 발생했습니다.');
    }
  }, []);

  // 전체 Excel 내보내기
  const handleExportExcel = useCallback(() => {
    exportToExcel(filteredProducts, `상품목록_전체_${new Date().toISOString().split('T')[0]}.xlsx`);
  }, [filteredProducts, exportToExcel]);

  // 선택 항목 Excel 내보내기
  const handleExportSelected = useCallback(() => {
    if (selectedIds.length === 0) {
      alert('내보낼 상품을 선택해주세요.');
      return;
    }

    const selectedProducts = products.filter(p => selectedIds.includes(p.id));
    exportToExcel(selectedProducts, `상품목록_선택항목_${new Date().toISOString().split('T')[0]}.xlsx`);
  }, [selectedIds, products, exportToExcel]);

  const getMarginColor = useCallback((marginRate: number) => {
    if (marginRate >= 50) return 'text-green-600 bg-green-50';
    if (marginRate >= 30) return 'text-blue-600 bg-blue-50';
    if (marginRate >= 10) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  }, []);

  const getStatusBadge = useCallback((status?: string) => {
    if (!status) return <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">알 수 없음</span>;

    if (status === 'available') {
      return <span className="px-2 py-1 bg-green-100 text-green-600 rounded-full text-xs">판매중</span>;
    } else if (status === 'out_of_stock') {
      return <span className="px-2 py-1 bg-orange-100 text-orange-600 rounded-full text-xs">일시품절</span>;
    } else if (status === 'discontinued') {
      return <span className="px-2 py-1 bg-red-100 text-red-600 rounded-full text-xs">판매종료</span>;
    }
    return <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">{status}</span>;
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <span className="ml-3 text-lg text-gray-600">로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">내 판매 상품</h1>
          <p className="text-gray-600 mt-1">판매 중인 상품과 소싱 정보를 관리하세요</p>
        </div>
        {/* 쇼핑몰 상품코드 수집 버튼 */}
        {!isMobile && (
          <button
            onClick={handleSyncAllMarketplaceCodes}
            disabled={syncingMarketplaceCodes}
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-5 h-5 ${syncingMarketplaceCodes ? 'animate-spin' : ''}`} />
            {syncingMarketplaceCodes ? '수집 중...' : '쇼핑몰 상품코드 수집'}
          </button>
        )}
      </div>

      {/* Search and Filters */}
      <div className={`bg-white rounded-xl shadow-lg border border-gray-200 space-y-4 ${isMobile ? 'p-4' : 'p-6'}`}>
        {/* 검색 및 정렬 */}
        <div className={`flex gap-4 items-center ${isMobile ? 'flex-col' : 'flex-wrap'}`}>
          {/* 검색 */}
          <div className={`${isMobile ? 'w-full' : 'flex-1 min-w-[300px]'}`}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="상품명 검색..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 정렬 + 기타 버튼 */}
          <div className={`flex gap-2 items-center ${isMobile ? 'w-full justify-between' : ''}`}>
            <div className="flex gap-2 items-center">
              {!isMobile && <span className="text-sm font-semibold text-gray-700 whitespace-nowrap">정렬:</span>}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className={`border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 ${isMobile ? 'px-2 py-1.5 text-sm' : 'px-3 py-2'}`}
              >
                <option value="date">등록일</option>
                <option value="name">상품명</option>
                <option value="price">판매가</option>
                <option value="margin">마진율</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className={`border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors ${isMobile ? 'p-1.5' : 'p-2'}`}
                title={sortOrder === 'asc' ? '오름차순' : '내림차순'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>

            {/* Excel 내보내기 - 모바일에서는 숨김 */}
            {!isMobile && (
              <button
                onClick={handleExportExcel}
                className="px-4 py-2 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors whitespace-nowrap"
              >
                Excel 내보내기
              </button>
            )}
          </div>
        </div>

        {/* 필터 및 일괄 작업 */}
        <div className={`flex items-center gap-4 ${isMobile ? 'flex-col items-start' : 'flex-wrap'}`}>
          <div className="flex items-center gap-2">
            {!isMobile && <span className="text-sm font-semibold text-gray-700">판매:</span>}
            <div className="flex gap-2">
              {(['all', 'active', 'inactive'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className={`rounded-lg font-medium transition-all ${
                    activeFilter === filter
                      ? 'bg-blue-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                >
                  {filter === 'all' ? '전체' : filter === 'active' ? '판매중' : '중단'}
                </button>
              ))}
            </div>
          </div>

          {/* 소싱처 상태 필터 */}
          <div className="flex items-center gap-2">
            {!isMobile && <span className="text-sm font-semibold text-gray-700">소싱:</span>}
            <div className="flex gap-2">
              {(['all', 'available', 'out_of_stock', 'discontinued'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setSourcingStatusFilter(filter)}
                  className={`rounded-lg font-medium transition-all ${
                    sourcingStatusFilter === filter
                      ? filter === 'out_of_stock' ? 'bg-orange-500 text-white shadow-md'
                        : filter === 'discontinued' ? 'bg-red-500 text-white shadow-md'
                        : 'bg-green-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                >
                  {filter === 'all' ? '전체' : filter === 'available' ? '정상' : filter === 'out_of_stock' ? '일시품절' : '판매종료'}
                </button>
              ))}
            </div>
          </div>

          {/* 입력 방식 필터 */}
          <div className="flex items-center gap-2">
            {!isMobile && <span className="text-sm font-semibold text-gray-700">입력:</span>}
            <div className="flex gap-2">
              {(['all', 'auto', 'manual'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setInputTypeFilter(filter)}
                  className={`rounded-lg font-medium transition-all ${
                    inputTypeFilter === filter
                      ? filter === 'auto' ? 'bg-blue-500 text-white shadow-md'
                        : filter === 'manual' ? 'bg-purple-500 text-white shadow-md'
                        : 'bg-gray-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } ${isMobile ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}`}
                >
                  {filter === 'all' ? '전체' : filter === 'auto' ? '⚡자동추출' : '🖊️수동입력'}
                </button>
              ))}
            </div>
          </div>

          {/* 일괄 작업 버튼 - 모바일에서는 숨김 */}
          {!isMobile && selectedIds.length > 0 && (() => {
            // 선택된 상품들의 상태 확인
            const selectedProducts = products.filter(p => selectedIds.includes(p.id));
            const allActive = selectedProducts.every(p => p.is_active);
            const allInactive = selectedProducts.every(p => !p.is_active);
            const hasInactive = selectedProducts.some(p => !p.is_active);
            const hasActive = selectedProducts.some(p => p.is_active);

            return (
              <div className="flex gap-2 ml-auto items-center">
                <span className="text-sm text-gray-600">{selectedIds.length}개 선택</span>
                <button
                  onClick={handleExportSelected}
                  className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors whitespace-nowrap"
                >
                  Excel 내보내기
                </button>

                {/* 중단된 상품이 있으면 "상품등록(판매중)" 버튼 표시 */}
                {hasInactive && (
                  <button
                    onClick={handleRegisterToPlayauto}
                    className="px-3 py-1 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors whitespace-nowrap"
                  >
                    상품등록(판매중)
                  </button>
                )}

                {/* 판매중인 상품이 있으면 "판매중지" 버튼 표시 */}
                {hasActive && (
                  <button
                    onClick={() => handleBulkToggleStatus(false)}
                    className="px-3 py-1 bg-gray-500 text-white rounded-lg text-sm hover:bg-gray-600 transition-colors whitespace-nowrap"
                  >
                    판매중지
                  </button>
                )}

                <button
                  onClick={handleBulkDelete}
                  className="px-3 py-1 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
                >
                  삭제
                </button>
              </div>
            );
          })()}

          {/* 통계 */}
          <div className="ml-auto text-sm text-gray-600 flex items-center gap-3">
            <div>
              검색 결과: <span className="font-bold text-blue-600">{filteredProducts.length}</span>개
              {filteredProducts.length !== products.length && (
                <span className="text-gray-400"> / 전체 {products.length}개</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-600 font-semibold">⚡{products.filter(p => (p as any).input_type !== 'manual').length}</span>
              <span className="text-purple-600 font-semibold">🖊️{products.filter(p => (p as any).input_type === 'manual').length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Products Table */}
      {products.length === 0 ? (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center border border-gray-200">
          <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">등록된 상품이 없습니다</h3>
          <p className="text-gray-500">
            상세페이지 생성기에서 상품을 추가해주세요.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          {/* 모바일: 카드 레이아웃 */}
          {isMobile ? (
            <div className="divide-y divide-gray-200">
              {paginatedProducts.map((product) => {
                const marginRate = product.margin_rate || 0;
                const margin = product.margin || 0;
                const sourcingPrice = product.sourcing_price || (product as any).effective_sourcing_price;

                return (
                  <div
                    key={product.id}
                    className="p-4 hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex gap-3">
                      {/* 썸네일 */}
                      {product.thumbnail_url ? (
                        <img
                          src={product.thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${product.thumbnail_url}` : product.thumbnail_url}
                          alt={product.product_name}
                          className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                          <Package className="w-8 h-8 text-gray-400" />
                        </div>
                      )}

                      {/* 상품 정보 */}
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 text-sm truncate mb-1">
                          {product.product_name}
                        </div>

                        {/* 가격 정보 */}
                        <div className="flex items-center gap-2 text-xs mb-2">
                          <span className="font-bold text-gray-900">{product.selling_price.toLocaleString()}원</span>
                          <span className="text-gray-400">|</span>
                          <span className="text-gray-600">{sourcingPrice ? `${sourcingPrice.toLocaleString()}원` : '-'}</span>
                          <span className={`font-bold ${marginRate >= 50 ? 'text-green-600' : marginRate >= 30 ? 'text-blue-600' : marginRate >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
                            ({marginRate.toFixed(0)}%)
                          </span>
                        </div>

                        {/* 상태 + 액션 */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleToggleStatus(product.id, product.is_active, product.product_name)}
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                              product.is_active
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {product.is_active ? '판매중' : '중단'}
                          </button>
                          {/* 입력 방식 배지 */}
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            (product as any).input_type === 'manual'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {(product as any).input_type === 'manual' ? '🖊️수동' : '⚡자동'}
                          </span>
                          {product.sourcing_url && (
                            <a
                              href={product.sourcing_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1.5 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                              title="구매하기"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          )}
                          <button
                            onClick={() => {
                              setSelectedProduct(product);
                              setShowEditModal(true);
                            }}
                            className="p-1.5 text-purple-600 hover:bg-purple-100 rounded-lg transition-colors"
                            title="수정"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleViewDetail(product)}
                            className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                            title="상세보기"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
          /* 데스크톱: 테이블 레이아웃 */
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1200px]">
              <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
                <tr>
                  <th className="px-4 py-4 text-center">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === paginatedProducts.length && paginatedProducts.length > 0}
                      onChange={handleSelectAll}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">상품명</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">카테고리</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">판매가</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">소싱가</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">마진</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">소싱처</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">상태</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider whitespace-nowrap">관리</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedProducts.map((product) => {
                  const marginRate = product.margin_rate || 0;
                  const margin = product.margin || 0;
                  const sourcingPrice = product.sourcing_price || (product as any).effective_sourcing_price;

                  return (
                    <tr
                      key={product.id}
                      className="hover:bg-blue-50 transition-colors"
                    >
                      <td className="px-4 py-4 text-center">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(product.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectProduct(product.id);
                          }}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4 min-w-[300px] cursor-pointer" onClick={() => handleViewDetail(product)}>
                        <div className="flex items-center gap-3">
                          {product.thumbnail_url ? (
                            <img src={product.thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${product.thumbnail_url}` : product.thumbnail_url} alt={product.product_name} className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
                          ) : (
                            <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                              <Package className="w-6 h-6 text-gray-400" />
                            </div>
                          )}
                          <div>
                            <div className="font-semibold text-gray-900">{product.product_name}</div>
                            {/* 입력 방식 배지 */}
                            <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                              (product as any).input_type === 'manual'
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-blue-100 text-blue-700'
                            }`}>
                              {(product as any).input_type === 'manual' ? '🖊️수동입력' : '⚡자동추출'}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 min-w-[200px]">
                        <div className="text-sm text-gray-600">{product.category || '-'}</div>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="font-bold text-gray-900">{product.selling_price.toLocaleString()}원</div>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="text-gray-700">{sourcingPrice ? `${sourcingPrice.toLocaleString()}원` : '-'}</div>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className={`font-bold ${marginRate >= 50 ? 'text-green-600' : marginRate >= 30 ? 'text-blue-600' : marginRate >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {margin.toLocaleString()}원
                          <div className="text-xs mt-1">{marginRate.toFixed(1)}%</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <div className="flex flex-col items-center gap-1">
                          {product.sourcing_source ? (
                            <>
                              <span className="font-semibold text-gray-800 uppercase text-sm">{product.sourcing_source}</span>
                              {product.sourcing_url && (
                                <a
                                  href={product.sourcing_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-500 hover:text-blue-600 transition-colors"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <ExternalLink className="w-4 h-4" />
                                </a>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleStatus(product.id, product.is_active, product.product_name);
                          }}
                          className={`inline-block px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all hover:scale-105 cursor-pointer ${
                            product.is_active
                              ? 'bg-green-100 text-green-700 hover:bg-green-200'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                          title="클릭하여 상태 변경"
                        >
                          {product.is_active ? '판매중' : '중단'}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center justify-center gap-2">
                          {product.sourcing_url && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUpdateSourcingPrice(product.id, product.product_name);
                              }}
                              className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                              title="소싱가 갱신"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewDetail(product);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                            title="상세보기"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedProduct(product);
                              setShowEditModal(true);
                            }}
                            className="p-2 text-purple-600 hover:bg-purple-100 rounded-lg transition-colors"
                            title="수정"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          {product.c_sale_cd && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSyncToPlayauto(product.id, product.product_name, product.c_sale_cd);
                              }}
                              className="p-2 text-orange-600 hover:bg-orange-100 rounded-lg transition-colors"
                              title="PlayAuto 동기화"
                            >
                              <Upload className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm('정말 삭제하시겠습니까?')) {
                                handleDeleteProduct(product.id);
                              }
                            }}
                            className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                            title="삭제"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">페이지당:</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => {
                      setItemsPerPage(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="20">20개</option>
                    <option value="50">50개</option>
                    <option value="100">100개</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    처음
                  </button>
                  <button
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    이전
                  </button>

                  <span className="text-sm text-gray-600 px-4">
                    {currentPage} / {totalPages}
                  </span>

                  <button
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    다음
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    마지막
                  </button>
                </div>

                <div className="text-sm text-gray-600">
                  총 {filteredProducts.length}개 중 {(currentPage - 1) * itemsPerPage + 1}-
                  {Math.min(currentPage * itemsPerPage, filteredProducts.length)}번째 표시
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedProduct && (
        <ProductDetailModal
          product={selectedProduct}
          priceHistory={priceHistory}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedProduct(null);
            setPriceHistory([]);
          }}
        />
      )}

      {/* Add Product Modal */}
      {showAddModal && (
        <AddProductModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            cache.clearProducts(); // 캐시 제거
            loadProducts();
          }}
        />
      )}

      {/* Edit Product Modal */}
      {showEditModal && selectedProduct && (
        <EditProductModal
          product={selectedProduct}
          onClose={() => {
            setShowEditModal(false);
            setSelectedProduct(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedProduct(null);
            cache.clearProducts(); // 캐시 제거
            loadProducts();
          }}
        />
      )}
    </div>
  );
}

// Product Card Component
function ProductCard({ product, onViewDetail, onDelete, getMarginColor, getStatusBadge }: {
  product: ProductType;
  onViewDetail: (product: ProductType) => void;
  onDelete: (id: number) => void;
  getMarginColor: (marginRate: number) => string;
  getStatusBadge: (status?: string) => React.JSX.Element;
}) {
  const marginRate = product.margin_rate || 0;
  const margin = product.margin || 0;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300 group">
      {/* Thumbnail */}
      <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
        {product.thumbnail_url ? (
          <img
            src={product.thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${product.thumbnail_url}` : product.thumbnail_url}
            alt={product.product_name}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <Package className="w-16 h-16 text-gray-300" />
          </div>
        )}
        {!product.is_active && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="text-white font-bold text-lg">판매 중단</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5 space-y-4">
        {/* Product Name */}
        <div>
          <h3 className="text-lg font-bold text-gray-800 mb-1 line-clamp-2">
            {product.product_name}
          </h3>
          {product.category && (
            <span className="text-xs text-gray-500">{product.category}</span>
          )}
        </div>

        {/* Price Info */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">판매가</span>
            <span className="text-lg font-bold text-gray-900">
              {product.selling_price.toLocaleString()}원
            </span>
          </div>
          {(product.sourcing_price || (product as any).effective_sourcing_price) && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">소싱가</span>
              <span className="text-sm font-semibold text-gray-700">
                {(product.sourcing_price || (product as any).effective_sourcing_price).toLocaleString()}원
              </span>
            </div>
          )}
        </div>

        {/* Margin */}
        <div className={`p-3 rounded-lg ${getMarginColor(marginRate)}`}>
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold">마진</span>
            <div className="text-right">
              <div className="font-bold">{margin.toLocaleString()}원</div>
              <div className="text-xs">{marginRate.toFixed(1)}%</div>
            </div>
          </div>
        </div>

        {/* Sourcing Info */}
        {product.sourcing_source && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-600">소싱처</span>
              <span className="text-sm font-bold text-gray-800 uppercase">
                {product.sourcing_source}
              </span>
              {getStatusBadge(product.monitored_status)}
            </div>
            {product.sourcing_url && (
              <a
                href={product.sourcing_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-600 transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={() => onViewDetail(product)}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
          >
            <Eye className="w-4 h-4" />
            상세보기
          </button>
          <button
            onClick={() => onDelete(product.id)}
            className="px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Detail Page Viewer Modal
function DetailPageViewerModal({ htmlContent, onClose }: {
  htmlContent: string;
  onClose: () => void;
}) {
  // JSON인지 HTML인지 확인
  let isJson = false;
  let detailPageData: any = null;

  try {
    detailPageData = JSON.parse(htmlContent);
    isJson = true;
  } catch {
    isJson = false;
  }

  // 템플릿 렌더링 함수
  const renderTemplate = () => {
    if (!isJson || !detailPageData) return null;

    const { template, content, images } = detailPageData;

    // 추가 이미지 슬롯 개수 계산 (additional_product_image_N 형식의 키 개수)
    const additionalImageCount = images
      ? Object.keys(images).filter(key => key.startsWith('additional_product_image_')).length
      : 0;

    // 템플릿에서 사용할 props (편집 기능 비활성화)
    const templateProps = {
      content,
      uploadedImages: images || {},
      editingField: null,
      editingValue: '',
      onImageUpload: () => {},
      onImageRefresh: () => {},
      onImageDrop: () => {},
      onTextEdit: () => {},
      onTextSave: () => {},
      onTextCancel: () => {},
      onValueChange: () => {},
      onImageClick: () => {},
      editingImage: null,
      imageStyleSettings: {},
      onTextStyleClick: () => {},
      textStyles: {},
      additionalImageSlots: additionalImageCount,
      onAddImageSlot: () => {},
      onRemoveImageSlot: () => {},
      onImageDelete: () => {},
    };

    // 템플릿 선택
    if (template === 'daily') return <DailyTemplate {...templateProps} />;
    if (template === 'convenience') return <FoodTemplate {...templateProps} />;
    if (template === 'electronics') return <ElectronicsTemplate {...templateProps} />;
    if (template === 'processedFood') return <ProcessedFoodTemplate {...templateProps} />;
    if (template === 'hygiene') return <HygieneTemplate {...templateProps} />;
    if (template === 'stationery') return <StationeryTemplate {...templateProps} />;

    return null;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {isJson && detailPageData?.content?.productName
              ? `${detailPageData.content.productName} - 상세페이지`
              : '상세페이지 미리보기'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isJson && detailPageData ? (
            <div className="flex justify-center">
              <div className="w-[860px] bg-white shadow-2xl rounded-2xl overflow-hidden border">
                {renderTemplate()}
              </div>
            </div>
          ) : (
            <div
              className="border border-gray-200 rounded-lg overflow-hidden bg-white"
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-500 text-white rounded-xl font-semibold hover:bg-gray-600 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

// Detail Modal Component
function ProductDetailModal({ product, priceHistory, onClose }: {
  product: ProductType;
  priceHistory: PriceHistory[];
  onClose: () => void;
}) {
  const [showDetailPageViewer, setShowDetailPageViewer] = useState(false);
  const [detailPageHtml, setDetailPageHtml] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // 상세페이지 보기 핸들러
  const handleViewDetailPage = useCallback(async () => {
    try {
      setIsGenerating(true);

      // 상세페이지 조회
      const response = await fetch(`${API_BASE_URL}/api/products/detail-page/${product.id}`);
      const data = await response.json();

      if (data.success && data.has_detail_page && data.detail_page_data) {
        // 이미 상세페이지가 있으면 바로 표시
        setDetailPageHtml(data.detail_page_data);
        setShowDetailPageViewer(true);
      } else {
        // 상세페이지가 없으면 생성
        if (confirm('상세페이지가 없습니다. AI로 자동 생성하시겠습니까?\n\n(OpenAI API를 사용하므로 약간의 시간이 소요됩니다)')) {
          const generateResponse = await fetch(`${API_BASE_URL}/api/products/detail-page/${product.id}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_regenerate: false })
          });

          if (!generateResponse.ok) {
            const errorText = await generateResponse.text();
            console.error('API Error:', errorText);
            throw new Error(`서버 오류 (${generateResponse.status}): ${errorText}`);
          }

          const generateData = await generateResponse.json();

          if (generateData.success && generateData.detail_page_data) {
            setDetailPageHtml(generateData.detail_page_data);
            setShowDetailPageViewer(true);
            alert('상세페이지가 생성되었습니다!');
          } else {
            const errorMsg = generateData.detail || generateData.message || '알 수 없는 오류';
            alert(`상세페이지 생성에 실패했습니다.\n\n오류: ${errorMsg}`);
          }
        }
      }
    } catch (error: any) {
      console.error('상세페이지 조회/생성 실패:', error);
      alert(`상세페이지 조회 중 오류가 발생했습니다.\n\n${error.message || error}`);
    } finally {
      setIsGenerating(false);
    }
  }, [product.id]);

  // Chart data
  const chartData = {
    labels: priceHistory.map(h => new Date(h.checked_at).toLocaleDateString()),
    datasets: [
      {
        label: '소싱가 추이',
        data: priceHistory.map(h => h.price),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      title: {
        display: true,
        text: '소싱가 변동 추이 (최근 30일)',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">{product.product_name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Price Chart */}
          {priceHistory.length > 0 && (
            <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
              <Line data={chartData} options={chartOptions} />
            </div>
          )}

          {/* Detail Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-blue-600 font-semibold mb-1">판매가</div>
              <div className="text-2xl font-bold text-blue-700">
                {product.selling_price.toLocaleString()}원
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-purple-600 font-semibold mb-1">소싱가</div>
              <div className="text-2xl font-bold text-purple-700">
                {(product.sourcing_price || (product as any).effective_sourcing_price)?.toLocaleString() || '알 수 없음'}원
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-600 font-semibold mb-1">마진 (금액)</div>
              <div className="text-2xl font-bold text-green-700">
                {(product.margin || 0).toLocaleString()}원
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-600 font-semibold mb-1">마진율</div>
              <div className="text-2xl font-bold text-green-700">
                {(product.margin_rate || 0).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Sourcing Link */}
          {product.sourcing_url && (
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="text-sm font-semibold text-gray-700 mb-2">소싱처 링크</div>
              <a
                href={product.sourcing_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-600 underline break-all flex items-center gap-2"
              >
                {product.sourcing_url}
                <ExternalLink className="w-4 h-4 flex-shrink-0" />
              </a>
            </div>
          )}

          {/* Detail Page Section */}
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-xl border-2 border-purple-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-lg font-bold text-gray-800 mb-1">상세페이지</div>
                <div className="text-sm text-gray-600">
                  {product.detail_page_data
                    ? '상세페이지가 저장되어 있습니다.'
                    : '상세페이지가 없습니다. AI로 자동 생성할 수 있습니다.'}
                </div>
              </div>
              <button
                onClick={handleViewDetailPage}
                disabled={isGenerating}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Eye className="w-5 h-5" />
                {isGenerating ? '처리 중...' : product.detail_page_data ? '상세페이지 보기' : '상세페이지 생성'}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-500 text-white rounded-xl font-semibold hover:bg-gray-600 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>

      {/* Detail Page Viewer Modal */}
      {showDetailPageViewer && detailPageHtml && (
        <DetailPageViewerModal
          htmlContent={detailPageHtml}
          onClose={() => {
            setShowDetailPageViewer(false);
            setDetailPageHtml(null);
          }}
        />
      )}
    </div>
  );
}

// Add Product Modal Component
function AddProductModal({ onClose, onSuccess }: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    product_name: '',
    selling_price: '',
    sourcing_url: '',
    sourcing_price: '',
    sourcing_product_name: '',
    sourcing_source: '',
    thumbnail_url: '',
    notes: '',
  });
  const [category, setCategory] = useState<Category>({ level1: '', level2: '', level3: '', level4: '' });
  const [loading, setLoading] = useState(false);
  const [extractingUrl, setExtractingUrl] = useState(false);
  const [categoryStructure, setCategoryStructure] = useState<any>({});
  const [loadingCategories, setLoadingCategories] = useState(true);

  // 카테고리 구조를 API에서 로드
  useEffect(() => {
    const loadCategoryStructure = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/categories/structure`);
        const data = await res.json();
        if (data.success) {
          setCategoryStructure(data.structure);
        }
      } catch (error) {
        console.error('카테고리 로드 실패:', error);
      } finally {
        setLoadingCategories(false);
      }
    };
    loadCategoryStructure();
  }, []);

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

  const extractUrlInfo = async () => {
    if (!formData.sourcing_url) {
      alert('소싱처 URL을 입력해주세요.');
      return;
    }

    setExtractingUrl(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/monitor/extract-url-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_url: formData.sourcing_url }),
      });

      if (!response.ok) {
        throw new Error('URL 정보 추출 실패');
      }

      const result = await response.json();
      if (result.success && result.data) {
        const { product_name, current_price, source, thumbnail_url } = result.data;

        setFormData(prev => ({
          ...prev,
          sourcing_product_name: product_name || '',
          sourcing_price: current_price ? current_price.toString() : '',
          sourcing_source: source ? source.toUpperCase() : '',
          thumbnail_url: thumbnail_url || '',
          product_name: prev.product_name || product_name || '', // 상품명이 비어있으면 자동 입력
        }));

        // 판매가가 비어있으면 50% 마진으로 자동 계산
        if (!formData.selling_price && current_price) {
          const calculatedSellingPrice = Math.ceil(current_price * 1.5);
          setFormData(prev => ({
            ...prev,
            selling_price: calculatedSellingPrice.toString(),
          }));
        }

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
  };

  const handleSubmit = async (e: React.FormEvent) => {
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
      // 카테고리를 문자열로 조합
      const categoryString = `${category.level1} > ${category.level2} > ${category.level3} > ${category.level4}`;

      const response = await fetch(`${API_BASE_URL}/api/products/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: formData.product_name,
          selling_price: parseFloat(formData.selling_price),
          sourcing_url: formData.sourcing_url || null,
          sourcing_product_name: formData.sourcing_product_name || null,
          sourcing_price: formData.sourcing_price ? parseFloat(formData.sourcing_price) : null,
          sourcing_source: formData.sourcing_source || null,
          thumbnail_url: formData.thumbnail_url || null,
          category: categoryString,
          notes: formData.notes || null,
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert('상품이 추가되었습니다!');
        onSuccess();
      } else {
        alert('상품 추가에 실패했습니다.');
      }
    } catch (error) {
      console.error('상품 추가 실패:', error);
      alert('상품 추가 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">상품 추가</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 소싱처 URL */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              소싱처 URL (선택)
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={formData.sourcing_url}
                onChange={(e) => setFormData({ ...formData, sourcing_url: e.target.value })}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="예: https://www.11st.co.kr/products/... 또는 오뚜기몰 등"
              />
              <button
                type="button"
                onClick={extractUrlInfo}
                disabled={extractingUrl || !formData.sourcing_url}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
                {extractingUrl ? '추출 중...' : '정보 추출'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              소싱처 URL을 입력하고 "정보 추출"을 클릭하면 상품명과 가격이 자동으로 입력됩니다.
            </p>
          </div>

          {/* 소싱 정보 표시 */}
          {formData.sourcing_product_name && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-blue-800">
                <Package className="w-4 h-4" />
                <span className="font-semibold">소싱 정보</span>
              </div>
              <div className="flex gap-4">
                {formData.thumbnail_url && (
                  <div className="flex-shrink-0">
                    <img
                      src={formData.thumbnail_url.startsWith('/static') ? `${API_BASE_URL}${formData.thumbnail_url}` : formData.thumbnail_url}
                      alt="상품 썸네일"
                      className="w-20 h-20 object-cover rounded-lg border border-gray-200"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                )}
                <div className="text-sm text-gray-700 space-y-1 flex-1">
                  <div><span className="font-medium">마켓:</span> {formData.sourcing_source}</div>
                  <div><span className="font-medium">상품명:</span> {formData.sourcing_product_name}</div>
                  <div><span className="font-medium">소싱가:</span> {parseInt(formData.sourcing_price).toLocaleString()}원</div>
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              상품명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: 비비고 만두"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              판매가 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.selling_price}
              onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: 5000"
              required
            />
            {formData.sourcing_price && (
              <p className="text-xs text-gray-500 mt-1">
                마진: {(parseFloat(formData.selling_price) - parseFloat(formData.sourcing_price)).toLocaleString()}원
                ({((parseFloat(formData.selling_price) - parseFloat(formData.sourcing_price)) / parseFloat(formData.sourcing_price) * 100).toFixed(1)}%)
              </p>
            )}
          </div>

          {/* 카테고리 4단계 선택 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              카테고리 <span className="text-red-500">*</span>
            </label>
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

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              메모
            </label>
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
              className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {loading ? '추가 중...' : '상품 추가'}
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
