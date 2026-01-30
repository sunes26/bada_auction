'use client';

import { useEffect, useState } from 'react';
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
import { Line } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

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

interface PriceChartProps {
  productId: number;
  productName: string;
}

interface PriceHistory {
  checked_at: string;
  price: number;
}

export default function PriceChart({ productId, productName }: PriceChartProps) {
  const [chartData, setChartData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [priceChange, setPriceChange] = useState<{ value: number; percent: number } | null>(null);

  useEffect(() => {
    loadPriceHistory();
  }, [productId]);

  const loadPriceHistory = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/monitor/product/${productId}/price-history?limit=30`);

      if (!response.ok) throw new Error('가격 이력 로드 실패');

      const data = await response.json();

      if (data.chart_data && data.chart_data.labels.length > 0) {
        // 날짜 포맷팅
        const formattedLabels = data.chart_data.labels.map((dateStr: string) => {
          const date = new Date(dateStr);
          return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
        });

        // 가격 변동 계산
        const prices = data.chart_data.prices;
        if (prices.length >= 2) {
          const firstPrice = prices[0];
          const lastPrice = prices[prices.length - 1];
          const change = lastPrice - firstPrice;
          const changePercent = (change / firstPrice) * 100;
          setPriceChange({ value: change, percent: changePercent });
        }

        setChartData({
          labels: formattedLabels,
          datasets: [
            {
              label: '소싱가 (원)',
              data: prices,
              borderColor: 'rgb(59, 130, 246)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              fill: true,
              tension: 0.4,
              pointRadius: 4,
              pointHoverRadius: 6,
              pointBackgroundColor: 'rgb(59, 130, 246)',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
            }
          ]
        });
      }
    } catch (error) {
      console.error('가격 이력 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${productName} - 가격 변동 추이`,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `가격: ${context.parsed.y.toLocaleString()}원`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value: any) {
            return value.toLocaleString() + '원';
          }
        }
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">가격 이력 로딩 중...</div>
      </div>
    );
  }

  if (!chartData || chartData.datasets[0].data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-center">
          <Minus className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-500">아직 가격 이력이 없습니다</p>
          <p className="text-sm text-gray-400 mt-1">모니터링을 시작하면 가격 변동을 추적할 수 있습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 가격 변동 요약 */}
      {priceChange && (
        <div className="flex items-center justify-center gap-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
          <div className="flex items-center gap-2">
            {priceChange.value > 0 ? (
              <>
                <TrendingUp className="w-5 h-5 text-red-600" />
                <span className="font-semibold text-red-600">
                  +{priceChange.value.toLocaleString()}원 ({priceChange.percent.toFixed(1)}%)
                </span>
              </>
            ) : priceChange.value < 0 ? (
              <>
                <TrendingDown className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-600">
                  {priceChange.value.toLocaleString()}원 ({priceChange.percent.toFixed(1)}%)
                </span>
              </>
            ) : (
              <>
                <Minus className="w-5 h-5 text-gray-600" />
                <span className="font-semibold text-gray-600">변동 없음</span>
              </>
            )}
          </div>
          <span className="text-sm text-gray-600">
            (최근 {chartData.labels.length}회 체크 기준)
          </span>
        </div>
      )}

      {/* 차트 */}
      <div className="h-80">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
