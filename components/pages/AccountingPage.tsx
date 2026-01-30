'use client';

import { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  Receipt,
  Building2,
  Calculator,
  FileText,
  Plus,
  Download,
  Edit2,
  Trash2,
  CheckCircle,
  Clock,
  PieChart,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import EmptyState, { EmptyExpenses, EmptySettlements } from '@/components/ui/EmptyState';
import { API_BASE_URL } from '@/lib/api';
import type {
  AccountingDashboardStats,
  ProfitLossStatement,
  Expense,
  Settlement,
  VATCalculation,
  IncomeTaxEstimate,
  MonthlyReport,
} from '@/lib/types';

type TabType = 'dashboard' | 'profit-loss' | 'expenses' | 'settlements' | 'tax' | 'report';

const AccountingPage = () => {
  const [currentTab, setCurrentTab] = useState<TabType>('dashboard');
  const [loading, setLoading] = useState(false);

  // Dashboard state
  const [dashboardStats, setDashboardStats] = useState<AccountingDashboardStats | null>(null);
  const [period, setPeriod] = useState('this_month');

  // Profit Loss state
  const [profitLossData, setProfitLossData] = useState<ProfitLossStatement | null>(null);
  const [plStartDate, setPlStartDate] = useState('');
  const [plEndDate, setPlEndDate] = useState('');

  // Expenses state
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseFormData, setExpenseFormData] = useState({
    expense_date: new Date().toISOString().split('T')[0],
    category: '광고비',
    subcategory: '',
    amount: 0,
    description: '',
    payment_method: '카드',
    is_vat_deductible: false
  });

  // Settlements state
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [showSettlementModal, setShowSettlementModal] = useState(false);
  const [settlementFormData, setSettlementFormData] = useState({
    market: '쿠팡',
    settlement_date: new Date().toISOString().split('T')[0],
    period_start: '',
    period_end: '',
    total_sales: 0,
    commission: 0,
    shipping_fee: 0,
    promotion_cost: 0,
    net_amount: 0,
    memo: ''
  });

  // Tax state
  const [vatData, setVatData] = useState<VATCalculation | null>(null);
  const [incomeTaxData, setIncomeTaxData] = useState<IncomeTaxEstimate | null>(null);
  const [taxYear, setTaxYear] = useState(new Date().getFullYear());
  const [taxQuarter, setTaxQuarter] = useState(Math.ceil((new Date().getMonth() + 1) / 3));

  // Report state
  const [monthlyReport, setMonthlyReport] = useState<MonthlyReport | null>(null);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);

  // Load functions
  useEffect(() => {
    if (currentTab === 'dashboard') {
      loadDashboardStats();
    } else if (currentTab === 'profit-loss') {
      const today = new Date();
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
      setPlStartDate(firstDay.toISOString().split('T')[0]);
      setPlEndDate(today.toISOString().split('T')[0]);
    } else if (currentTab === 'expenses') {
      loadExpenses();
    } else if (currentTab === 'settlements') {
      loadSettlements();
    } else if (currentTab === 'tax') {
      loadVatData();
      loadIncomeTaxData();
    } else if (currentTab === 'report') {
      loadMonthlyReport();
    }
  }, [currentTab]);

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/accounting/dashboard/stats?period=${period}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setDashboardStats(data);
      }
    } catch (error) {
      console.error('대시보드 로드 실패:', error);
      toast.error('대시보드 데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadProfitLoss = async () => {
    if (!plStartDate || !plEndDate) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/accounting/profit-loss?start_date=${plStartDate}&end_date=${plEndDate}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setProfitLossData(data);
      }
    } catch (error) {
      console.error('손익계산서 로드 실패:', error);
      toast.error('손익계산서를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadExpenses = async () => {
    try {
      setLoading(true);
      const res = await fetch('${API_BASE_URL}/api/accounting/expenses');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setExpenses(data.expenses);
      }
    } catch (error) {
      console.error('지출 로드 실패:', error);
      toast.error('지출 내역을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadSettlements = async () => {
    try {
      setLoading(true);
      const res = await fetch('${API_BASE_URL}/api/accounting/settlements');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setSettlements(data.settlements);
      }
    } catch (error) {
      console.error('정산 로드 실패:', error);
      toast.error('정산 내역을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadVatData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/accounting/tax/vat?year=${taxYear}&quarter=${taxQuarter}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setVatData(data);
      }
    } catch (error) {
      console.error('부가세 로드 실패:', error);
      toast.error('부가세 데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadIncomeTaxData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/accounting/tax/income?year=${taxYear}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setIncomeTaxData(data);
      }
    } catch (error) {
      console.error('소득세 로드 실패:', error);
      toast.error('소득세 데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadMonthlyReport = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/accounting/report/monthly?year=${reportYear}&month=${reportMonth}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setMonthlyReport(data);
      }
    } catch (error) {
      console.error('월별 리포트 로드 실패:', error);
      toast.error('월별 리포트를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExpense = async () => {
    try {
      const res = await fetch('${API_BASE_URL}/api/accounting/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(expenseFormData)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.success) {
        toast.success('지출이 등록되었습니다');
        setShowExpenseModal(false);
        loadExpenses();
      }
    } catch (error) {
      console.error('지출 등록 실패:', error);
      toast.error('지출 등록에 실패했습니다');
    }
  };

  const handleDeleteExpense = async (id: number) => {
    if (!confirm('이 지출을 삭제하시겠습니까?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/accounting/expenses/${id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        alert('지출이 삭제되었습니다');
        loadExpenses();
      }
    } catch (error) {
      console.error('지출 삭제 실패:', error);
    }
  };

  const handleCreateSettlement = async () => {
    try {
      const res = await fetch('${API_BASE_URL}/api/accounting/settlements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settlementFormData)
      });
      const data = await res.json();
      if (data.success) {
        alert('정산이 등록되었습니다');
        setShowSettlementModal(false);
        loadSettlements();
      }
    } catch (error) {
      console.error('정산 등록 실패:', error);
      alert('정산 등록 실패');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  // Excel 내보내기 함수들
  const exportProfitLossToExcel = async () => {
    if (!profitLossData) {
      alert('먼저 손익계산서를 조회해주세요');
      return;
    }

    const ExcelJS = await import('exceljs');
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('손익계산서');

    // 제목
    worksheet.mergeCells('A1:C1');
    worksheet.getCell('A1').value = '손익계산서';
    worksheet.getCell('A1').font = { size: 16, bold: true };
    worksheet.getCell('A1').alignment = { horizontal: 'center' };

    // 기간
    worksheet.mergeCells('A2:C2');
    worksheet.getCell('A2').value = `기간: ${profitLossData.period.start} ~ ${profitLossData.period.end}`;
    worksheet.getCell('A2').alignment = { horizontal: 'center' };

    // 헤더
    worksheet.addRow([]);
    const headerRow = worksheet.addRow(['항목', '금액', '비율']);
    headerRow.font = { bold: true };
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' }
    };

    // 데이터
    const data = profitLossData.statement;
    worksheet.addRow(['1. 매출', data.revenue.total_sales, '']);
    worksheet.addRow(['2. 매출원가', data.cost_of_sales.total_cost, '']);
    worksheet.addRow(['3. 매출총이익', data.gross_profit.amount, `${data.gross_profit.margin}%`]);

    worksheet.addRow(['4. 판매관리비', data.operating_expenses.total, '']);
    data.operating_expenses.breakdown.forEach((exp: any) => {
      worksheet.addRow([`  - ${exp.category}`, exp.total, '']);
    });

    worksheet.addRow(['5. 영업이익', data.operating_profit.amount, `${data.operating_profit.margin}%`]);
    worksheet.addRow(['6. 순이익', data.net_profit.amount, `${data.net_profit.margin}%`]);

    // 열 너비 조정
    worksheet.getColumn(1).width = 30;
    worksheet.getColumn(2).width = 20;
    worksheet.getColumn(3).width = 15;

    // 숫자 포맷 (B열)
    worksheet.getColumn(2).numFmt = '#,##0';

    // 파일 다운로드
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `손익계산서_${plStartDate}_${plEndDate}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const exportExpensesToExcel = async () => {
    if (expenses.length === 0) {
      alert('내보낼 지출 데이터가 없습니다');
      return;
    }

    const ExcelJS = await import('exceljs');
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('지출 내역');

    // 제목
    worksheet.mergeCells('A1:G1');
    worksheet.getCell('A1').value = '지출 내역';
    worksheet.getCell('A1').font = { size: 16, bold: true };
    worksheet.getCell('A1').alignment = { horizontal: 'center' };

    // 헤더
    worksheet.addRow([]);
    const headerRow = worksheet.addRow(['날짜', '카테고리', '세부분류', '금액', '결제수단', '부가세공제', '설명']);
    headerRow.font = { bold: true };
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' }
    };

    // 데이터
    expenses.forEach((expense) => {
      worksheet.addRow([
        expense.expense_date,
        expense.category,
        expense.subcategory || '-',
        expense.amount,
        expense.payment_method || '-',
        expense.is_vat_deductible ? 'O' : 'X',
        expense.description || '-'
      ]);
    });

    // 합계 행
    const totalRow = worksheet.addRow([
      '',
      '',
      '합계',
      { formula: `SUM(D4:D${3 + expenses.length})` },
      '',
      '',
      ''
    ]);
    totalRow.font = { bold: true };
    totalRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFFFD700' }
    };

    // 열 너비 조정
    worksheet.getColumn(1).width = 12;
    worksheet.getColumn(2).width = 15;
    worksheet.getColumn(3).width = 15;
    worksheet.getColumn(4).width = 15;
    worksheet.getColumn(5).width = 12;
    worksheet.getColumn(6).width = 12;
    worksheet.getColumn(7).width = 30;

    // 금액 열 포맷
    worksheet.getColumn(4).numFmt = '#,##0';

    // 파일 다운로드
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `지출내역_${new Date().toISOString().split('T')[0]}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const exportSettlementsToExcel = async () => {
    if (settlements.length === 0) {
      alert('내보낼 정산 데이터가 없습니다');
      return;
    }

    const ExcelJS = await import('exceljs');
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('마켓별 정산');

    // 제목
    worksheet.mergeCells('A1:H1');
    worksheet.getCell('A1').value = '마켓별 정산 내역';
    worksheet.getCell('A1').font = { size: 16, bold: true };
    worksheet.getCell('A1').alignment = { horizontal: 'center' };

    // 헤더
    worksheet.addRow([]);
    const headerRow = worksheet.addRow([
      '마켓', '정산기간 시작', '정산기간 종료', '정산일',
      '총판매액', '수수료', '배송비', '실정산액', '상태'
    ]);
    headerRow.font = { bold: true };
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' }
    };

    // 데이터
    settlements.forEach((settlement) => {
      worksheet.addRow([
        settlement.market,
        settlement.period_start,
        settlement.period_end,
        settlement.settlement_date,
        settlement.total_sales,
        settlement.commission,
        settlement.shipping_fee,
        settlement.net_amount,
        settlement.settlement_status === 'completed' ? '완료' : '대기'
      ]);
    });

    // 합계 행
    const totalRow = worksheet.addRow([
      '',
      '',
      '',
      '합계',
      { formula: `SUM(E4:E${3 + settlements.length})` },
      { formula: `SUM(F4:F${3 + settlements.length})` },
      { formula: `SUM(G4:G${3 + settlements.length})` },
      { formula: `SUM(H4:H${3 + settlements.length})` },
      ''
    ]);
    totalRow.font = { bold: true };
    totalRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFFFD700' }
    };

    // 열 너비 조정
    worksheet.getColumn(1).width = 12;
    worksheet.getColumn(2).width = 12;
    worksheet.getColumn(3).width = 12;
    worksheet.getColumn(4).width = 12;
    worksheet.getColumn(5).width = 15;
    worksheet.getColumn(6).width = 15;
    worksheet.getColumn(7).width = 15;
    worksheet.getColumn(8).width = 15;
    worksheet.getColumn(9).width = 10;

    // 금액 열 포맷
    for (let col = 5; col <= 8; col++) {
      worksheet.getColumn(col).numFmt = '#,##0';
    }

    // 파일 다운로드
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `마켓별정산_${new Date().toISOString().split('T')[0]}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const exportMonthlyReportToExcel = async () => {
    if (!monthlyReport) {
      alert('먼저 월별 리포트를 조회해주세요');
      return;
    }

    const ExcelJS = await import('exceljs');
    const workbook = new ExcelJS.Workbook();

    // 요약 시트
    const summarySheet = workbook.addWorksheet('요약');
    summarySheet.mergeCells('A1:B1');
    summarySheet.getCell('A1').value = `${reportYear}년 ${reportMonth}월 리포트`;
    summarySheet.getCell('A1').font = { size: 16, bold: true };
    summarySheet.getCell('A1').alignment = { horizontal: 'center' };

    summarySheet.addRow([]);
    summarySheet.addRow(['항목', '값']);
    summarySheet.addRow(['총 주문', `${monthlyReport.summary.order_count}건`]);
    summarySheet.addRow(['총 매출', monthlyReport.summary.total_revenue]);
    summarySheet.addRow(['총 매입', monthlyReport.summary.total_cost]);
    summarySheet.addRow(['총 지출', monthlyReport.summary.total_expenses]);
    summarySheet.addRow(['순이익', monthlyReport.summary.net_profit]);
    summarySheet.addRow(['ROI', `${monthlyReport.summary.roi}%`]);
    summarySheet.addRow(['평균 주문금액', monthlyReport.summary.avg_order_value]);

    summarySheet.getColumn(1).width = 20;
    summarySheet.getColumn(2).width = 20;
    summarySheet.getColumn(2).numFmt = '#,##0';

    // 베스트셀러 시트
    const bestsellerSheet = workbook.addWorksheet('베스트셀러');
    bestsellerSheet.mergeCells('A1:C1');
    bestsellerSheet.getCell('A1').value = '베스트셀러 TOP 5';
    bestsellerSheet.getCell('A1').font = { size: 14, bold: true };
    bestsellerSheet.getCell('A1').alignment = { horizontal: 'center' };

    bestsellerSheet.addRow([]);
    const bsHeaderRow = bestsellerSheet.addRow(['순위', '상품명', '판매액', '판매량']);
    bsHeaderRow.font = { bold: true };

    monthlyReport.bestsellers.forEach((product: any, index: number) => {
      bestsellerSheet.addRow([
        index + 1,
        product.product_name,
        product.total_revenue,
        product.total_quantity
      ]);
    });

    bestsellerSheet.getColumn(1).width = 10;
    bestsellerSheet.getColumn(2).width = 40;
    bestsellerSheet.getColumn(3).width = 15;
    bestsellerSheet.getColumn(4).width = 10;
    bestsellerSheet.getColumn(3).numFmt = '#,##0';

    // 마켓 분석 시트
    const marketSheet = workbook.addWorksheet('마켓 분석');
    marketSheet.mergeCells('A1:C1');
    marketSheet.getCell('A1').value = '마켓별 분석';
    marketSheet.getCell('A1').font = { size: 14, bold: true };
    marketSheet.getCell('A1').alignment = { horizontal: 'center' };

    marketSheet.addRow([]);
    const mHeaderRow = marketSheet.addRow(['마켓', '주문 건수', '매출액']);
    mHeaderRow.font = { bold: true };

    monthlyReport.market_analysis.forEach((market: any) => {
      marketSheet.addRow([
        market.source || market.market,
        market.orders,
        market.revenue
      ]);
    });

    marketSheet.getColumn(1).width = 15;
    marketSheet.getColumn(2).width = 15;
    marketSheet.getColumn(3).width = 20;
    marketSheet.getColumn(3).numFmt = '#,##0';

    // 파일 다운로드
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `월별리포트_${reportYear}년${reportMonth}월.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  // Tab navigation
  const tabs = [
    { id: 'dashboard', label: '대시보드', icon: <PieChart className="w-4 h-4" /> },
    { id: 'profit-loss', label: '손익계산서', icon: <FileText className="w-4 h-4" /> },
    { id: 'expenses', label: '지출 관리', icon: <Receipt className="w-4 h-4" /> },
    { id: 'settlements', label: '마켓별 정산', icon: <Building2 className="w-4 h-4" /> },
    { id: 'tax', label: '세금 계산', icon: <Calculator className="w-4 h-4" /> },
    { id: 'report', label: '월별 리포트', icon: <BarChart3 className="w-4 h-4" /> }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-2">
            <DollarSign className="w-8 h-8 text-green-600" />
            회계 관리
          </h1>
          <p className="text-gray-600">매출, 지출, 정산을 통합 관리하고 세금을 계산합니다</p>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-2 flex-wrap">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id as TabType)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                currentTab === tab.id
                  ? 'bg-green-600 text-white shadow-lg'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          {/* 1. Dashboard Tab */}
          {currentTab === 'dashboard' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">회계 대시보드</h2>
                <select
                  value={period}
                  onChange={(e) => {
                    setPeriod(e.target.value);
                    loadDashboardStats();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="this_month">이번 달</option>
                  <option value="last_month">지난 달</option>
                  <option value="this_year">올해</option>
                </select>
              </div>

              {dashboardStats && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-sm text-blue-600 mb-1">총 매출</div>
                      <div className="text-2xl font-bold text-blue-800">
                        {formatCurrency(dashboardStats.summary.total_revenue)}
                      </div>
                    </div>
                    <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="text-sm text-orange-600 mb-1">총 매입</div>
                      <div className="text-2xl font-bold text-orange-800">
                        {formatCurrency(dashboardStats.summary.total_cost)}
                      </div>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <div className="text-sm text-red-600 mb-1">총 지출</div>
                      <div className="text-2xl font-bold text-red-800">
                        {formatCurrency(dashboardStats.summary.total_expenses)}
                      </div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="text-sm text-green-600 mb-1">순이익</div>
                      <div className="text-2xl font-bold text-green-800">
                        {formatCurrency(dashboardStats.summary.net_profit)}
                      </div>
                      <div className="text-xs text-green-600 mt-1">
                        마진율: {dashboardStats.summary.profit_margin}%
                      </div>
                    </div>
                  </div>

                  {/* Charts */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Monthly Revenue */}
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h3 className="text-lg font-bold mb-4">월별 매출 추이</h3>
                      <div className="space-y-2">
                        {dashboardStats.monthly_revenue.map((item: any) => (
                          <div key={item.month} className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">{item.month}</span>
                            <span className="font-semibold">{formatCurrency(item.revenue)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Expense by Category */}
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h3 className="text-lg font-bold mb-4">지출 카테고리별</h3>
                      <div className="space-y-2">
                        {dashboardStats.expense_by_category.map((item: any) => (
                          <div key={item.category} className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">{item.category}</span>
                            <span className="font-semibold">{formatCurrency(item.total)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* 2. Profit Loss Tab */}
          {currentTab === 'profit-loss' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">손익계산서</h2>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={plStartDate}
                    onChange={(e) => setPlStartDate(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <span className="py-2">~</span>
                  <input
                    type="date"
                    value={plEndDate}
                    onChange={(e) => setPlEndDate(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <button
                    onClick={loadProfitLoss}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    조회
                  </button>
                  {profitLossData && (
                    <button
                      onClick={exportProfitLossToExcel}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Excel 다운로드
                    </button>
                  )}
                </div>
              </div>

              {profitLossData && (
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">1. 매출</span>
                      <span className="text-xl font-bold text-blue-800">
                        {formatCurrency(profitLossData.statement.revenue.total_sales)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      주문 건수: {profitLossData.statement.revenue.order_count}건
                    </div>
                  </div>

                  <div className="p-4 bg-orange-50 rounded-lg">
                    <div className="flex justify-between">
                      <span className="font-semibold">2. 매출원가</span>
                      <span className="text-xl font-bold text-orange-800">
                        {formatCurrency(profitLossData.statement.cost_of_sales.total_cost)}
                      </span>
                    </div>
                  </div>

                  <div className="p-4 bg-green-50 rounded-lg border-2 border-green-300">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold text-lg">3. 매출총이익</span>
                      <span className="text-2xl font-bold text-green-800">
                        {formatCurrency(profitLossData.statement.gross_profit.amount)}
                      </span>
                    </div>
                    <div className="text-sm text-green-600">
                      마진율: {profitLossData.statement.gross_profit.margin}%
                    </div>
                  </div>

                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">4. 판매관리비</span>
                      <span className="text-xl font-bold text-red-800">
                        {formatCurrency(profitLossData.statement.operating_expenses.total)}
                      </span>
                    </div>
                    <div className="ml-4 space-y-1">
                      {profitLossData.statement.operating_expenses.breakdown.map((exp: any) => (
                        <div key={exp.category} className="flex justify-between text-sm">
                          <span className="text-gray-600">- {exp.category}</span>
                          <span>{formatCurrency(exp.total)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg border-2 border-purple-300">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold text-lg">5. 영업이익</span>
                      <span className="text-2xl font-bold text-purple-800">
                        {formatCurrency(profitLossData.statement.operating_profit.amount)}
                      </span>
                    </div>
                    <div className="text-sm text-purple-600">
                      영업이익률: {profitLossData.statement.operating_profit.margin}%
                    </div>
                  </div>

                  <div className="p-6 bg-gradient-to-r from-green-100 to-green-50 rounded-lg border-2 border-green-400">
                    <div className="flex justify-between mb-2">
                      <span className="font-bold text-xl">6. 순이익</span>
                      <span className="text-3xl font-bold text-green-900">
                        {formatCurrency(profitLossData.statement.net_profit.amount)}
                      </span>
                    </div>
                    <div className="text-sm text-green-700">
                      순이익률: {profitLossData.statement.net_profit.margin}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 3. Expenses Tab */}
          {currentTab === 'expenses' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">지출 관리</h2>
                <div className="flex gap-2">
                  <button
                    onClick={exportExpensesToExcel}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Excel 다운로드
                  </button>
                  <button
                    onClick={() => setShowExpenseModal(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    지출 추가
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">날짜</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">카테고리</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">세부분류</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">금액</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">결제수단</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">부가세공제</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">작업</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {expenses.map((expense) => (
                      <tr key={expense.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{expense.expense_date}</td>
                        <td className="px-4 py-3 text-sm">{expense.category}</td>
                        <td className="px-4 py-3 text-sm">{expense.subcategory || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right font-semibold">
                          {formatCurrency(expense.amount)}
                        </td>
                        <td className="px-4 py-3 text-sm">{expense.payment_method || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          {expense.is_vat_deductible ? (
                            <CheckCircle className="w-4 h-4 text-green-600 mx-auto" />
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => handleDeleteExpense(expense.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. Settlements Tab */}
          {currentTab === 'settlements' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">마켓별 정산</h2>
                <div className="flex gap-2">
                  <button
                    onClick={exportSettlementsToExcel}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Excel 다운로드
                  </button>
                  <button
                    onClick={() => setShowSettlementModal(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    정산 추가
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">마켓</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">정산기간</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">정산일</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">총판매액</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">수수료</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">실정산액</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">상태</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {settlements.map((settlement) => (
                      <tr key={settlement.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold">{settlement.market}</td>
                        <td className="px-4 py-3 text-sm">
                          {settlement.period_start} ~ {settlement.period_end}
                        </td>
                        <td className="px-4 py-3 text-sm">{settlement.settlement_date}</td>
                        <td className="px-4 py-3 text-sm text-right">
                          {formatCurrency(settlement.total_sales)}
                        </td>
                        <td className="px-4 py-3 text-sm text-right text-red-600">
                          -{formatCurrency(settlement.commission)}
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-bold text-green-700">
                          {formatCurrency(settlement.net_amount)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {settlement.settlement_status === 'completed' ? (
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">완료</span>
                          ) : (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">대기</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 5. Tax Tab */}
          {currentTab === 'tax' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6">세금 계산</h2>

                {/* VAT */}
                <div className="mb-8">
                  <div className="flex gap-4 items-center mb-4">
                    <h3 className="text-xl font-bold">부가세 (분기별)</h3>
                    <select
                      value={taxYear}
                      onChange={(e) => setTaxYear(Number(e.target.value))}
                      className="px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      {[2026, 2025, 2024].map(y => (
                        <option key={y} value={y}>{y}년</option>
                      ))}
                    </select>
                    <select
                      value={taxQuarter}
                      onChange={(e) => setTaxQuarter(Number(e.target.value))}
                      className="px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      {[1, 2, 3, 4].map(q => (
                        <option key={q} value={q}>{q}분기</option>
                      ))}
                    </select>
                    <button
                      onClick={loadVatData}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      조회
                    </button>
                  </div>

                  {vatData && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <div className="text-sm text-blue-600 mb-1">과세매출</div>
                        <div className="text-xl font-bold">
                          {formatCurrency(vatData.calculation.taxable_sales)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          부가세: {formatCurrency(vatData.calculation.vat_on_sales)}
                        </div>
                      </div>
                      <div className="p-4 bg-orange-50 rounded-lg">
                        <div className="text-sm text-orange-600 mb-1">과세매입</div>
                        <div className="text-xl font-bold">
                          {formatCurrency(vatData.calculation.taxable_purchases)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          부가세: {formatCurrency(vatData.calculation.vat_on_purchases)}
                        </div>
                      </div>
                      <div className="p-4 bg-green-50 rounded-lg border-2 border-green-300">
                        <div className="text-sm text-green-600 mb-1">납부세액</div>
                        <div className="text-2xl font-bold text-green-800">
                          {formatCurrency(vatData.calculation.vat_payable)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Income Tax */}
                <div>
                  <div className="flex gap-4 items-center mb-4">
                    <h3 className="text-xl font-bold">종합소득세 (연간)</h3>
                    <button
                      onClick={loadIncomeTaxData}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      조회
                    </button>
                  </div>

                  {incomeTaxData && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-blue-50 rounded-lg">
                          <div className="text-sm text-blue-600 mb-1">총 매출</div>
                          <div className="text-xl font-bold">
                            {formatCurrency(incomeTaxData.calculation.total_sales)}
                          </div>
                        </div>
                        <div className="p-4 bg-orange-50 rounded-lg">
                          <div className="text-sm text-orange-600 mb-1">총 매입</div>
                          <div className="text-xl font-bold">
                            {formatCurrency(incomeTaxData.calculation.total_purchases)}
                          </div>
                        </div>
                        <div className="p-4 bg-red-50 rounded-lg">
                          <div className="text-sm text-red-600 mb-1">필요경비</div>
                          <div className="text-xl font-bold">
                            {formatCurrency(incomeTaxData.calculation.total_expenses)}
                          </div>
                        </div>
                      </div>
                      <div className="p-6 bg-gradient-to-r from-purple-100 to-purple-50 rounded-lg border-2 border-purple-300">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-sm text-purple-600 mb-1">과세표준</div>
                            <div className="text-2xl font-bold text-purple-800">
                              {formatCurrency(incomeTaxData.calculation.taxable_income)}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-purple-600 mb-1">예상 세액</div>
                            <div className="text-2xl font-bold text-purple-800">
                              {formatCurrency(incomeTaxData.calculation.total_tax)}
                            </div>
                            <div className="text-sm text-purple-600 mt-1">
                              (소득세 + 지방세 / 세율 {incomeTaxData.calculation.effective_tax_rate}%)
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 6. Report Tab */}
          {currentTab === 'report' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">월별 리포트</h2>
                <div className="flex gap-2">
                  <select
                    value={reportYear}
                    onChange={(e) => setReportYear(Number(e.target.value))}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {[2026, 2025, 2024].map(y => (
                      <option key={y} value={y}>{y}년</option>
                    ))}
                  </select>
                  <select
                    value={reportMonth}
                    onChange={(e) => setReportMonth(Number(e.target.value))}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {Array.from({length: 12}, (_, i) => i + 1).map(m => (
                      <option key={m} value={m}>{m}월</option>
                    ))}
                  </select>
                  <button
                    onClick={loadMonthlyReport}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    조회
                  </button>
                  {monthlyReport && (
                    <button
                      onClick={exportMonthlyReportToExcel}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Excel 다운로드
                    </button>
                  )}
                </div>
              </div>

              {monthlyReport && (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="text-sm text-blue-600 mb-1">총 주문</div>
                      <div className="text-2xl font-bold">{monthlyReport.summary.order_count}건</div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="text-sm text-green-600 mb-1">총 매출</div>
                      <div className="text-2xl font-bold">{formatCurrency(monthlyReport.summary.total_revenue)}</div>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <div className="text-sm text-purple-600 mb-1">순이익</div>
                      <div className="text-2xl font-bold">{formatCurrency(monthlyReport.summary.net_profit)}</div>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <div className="text-sm text-yellow-600 mb-1">ROI</div>
                      <div className="text-2xl font-bold">{monthlyReport.summary.roi}%</div>
                    </div>
                  </div>

                  {/* Bestsellers */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-bold mb-4">베스트셀러 TOP 5</h3>
                    <div className="space-y-2">
                      {monthlyReport.bestsellers.map((product: any, index: number) => (
                        <div key={index} className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs">
                              {index + 1}
                            </span>
                            <span className="font-medium">{product.product_name}</span>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold">{formatCurrency(product.total_revenue)}</div>
                            <div className="text-xs text-gray-600">{product.total_quantity}개</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Market Analysis */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-bold mb-4">마켓별 분석</h3>
                    <div className="space-y-2">
                      {monthlyReport.market_analysis.map((market: any) => (
                        <div key={market.source} className="flex justify-between items-center">
                          <span className="font-medium">{market.source}</span>
                          <div className="text-right">
                            <div className="font-semibold">{formatCurrency(market.revenue)}</div>
                            <div className="text-xs text-gray-600">{market.orders}건</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Expense Modal */}
      {showExpenseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">지출 추가</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">지출일자</label>
                <input
                  type="date"
                  value={expenseFormData.expense_date}
                  onChange={(e) => setExpenseFormData({...expenseFormData, expense_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">카테고리</label>
                <select
                  value={expenseFormData.category}
                  onChange={(e) => setExpenseFormData({...expenseFormData, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="광고비">광고비</option>
                  <option value="배송비">배송비</option>
                  <option value="포장재">포장재</option>
                  <option value="수수료">수수료</option>
                  <option value="기타">기타</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">금액</label>
                <input
                  type="number"
                  value={expenseFormData.amount}
                  onChange={(e) => setExpenseFormData({...expenseFormData, amount: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">결제수단</label>
                <select
                  value={expenseFormData.payment_method}
                  onChange={(e) => setExpenseFormData({...expenseFormData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="카드">카드</option>
                  <option value="현금">현금</option>
                  <option value="계좌이체">계좌이체</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={expenseFormData.is_vat_deductible}
                  onChange={(e) => setExpenseFormData({...expenseFormData, is_vat_deductible: e.target.checked})}
                  className="w-4 h-4"
                />
                <label className="text-sm font-medium text-gray-700">부가세 공제 가능</label>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowExpenseModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateExpense}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  추가
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settlement Modal */}
      {showSettlementModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">정산 추가</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">마켓</label>
                <select
                  value={settlementFormData.market}
                  onChange={(e) => setSettlementFormData({...settlementFormData, market: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="쿠팡">쿠팡</option>
                  <option value="네이버">네이버</option>
                  <option value="11번가">11번가</option>
                  <option value="G마켓">G마켓</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">정산 기간</label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={settlementFormData.period_start}
                    onChange={(e) => setSettlementFormData({...settlementFormData, period_start: e.target.value})}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <span className="py-2">~</span>
                  <input
                    type="date"
                    value={settlementFormData.period_end}
                    onChange={(e) => setSettlementFormData({...settlementFormData, period_end: e.target.value})}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">정산일</label>
                <input
                  type="date"
                  value={settlementFormData.settlement_date}
                  onChange={(e) => setSettlementFormData({...settlementFormData, settlement_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">총 판매액</label>
                <input
                  type="number"
                  value={settlementFormData.total_sales}
                  onChange={(e) => setSettlementFormData({...settlementFormData, total_sales: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">수수료</label>
                <input
                  type="number"
                  value={settlementFormData.commission}
                  onChange={(e) => setSettlementFormData({...settlementFormData, commission: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">배송비</label>
                <input
                  type="number"
                  value={settlementFormData.shipping_fee}
                  onChange={(e) => setSettlementFormData({...settlementFormData, shipping_fee: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">프로모션 비용</label>
                <input
                  type="number"
                  value={settlementFormData.promotion_cost}
                  onChange={(e) => setSettlementFormData({...settlementFormData, promotion_cost: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">실 정산액</label>
                <input
                  type="number"
                  value={settlementFormData.net_amount}
                  onChange={(e) => setSettlementFormData({...settlementFormData, net_amount: Number(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowSettlementModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateSettlement}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  추가
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountingPage;
