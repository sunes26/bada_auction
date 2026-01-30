'use client';

import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { BarChart3 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function MarginChart() {
  const [chartData, setChartData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadMarginData();
  }, []);

  const loadMarginData = async () => {
    try {
      setIsLoading(true);

      // 모든 주문 가져오기
      const ordersRes = await fetch(`${API_BASE_URL}/api/orders/list?limit=100`);
      const ordersData = await ordersRes.json();

      // 마진율 구간별 집계
      const marginRanges = {
        '0-10%': 0,
        '10-20%': 0,
        '20-30%': 0,
        '30-40%': 0,
        '40-50%': 0,
        '50%+': 0,
        '역마진': 0,
      };

      if (ordersData.success && ordersData.orders) {
        for (const order of ordersData.orders) {
          try {
            const orderDetailRes = await fetch(`${API_BASE_URL}/api/orders/order/${order.id}`);
            const orderDetail = await orderDetailRes.json();

            if (orderDetail.success && orderDetail.order_items) {
              for (const item of orderDetail.order_items) {
                if (item.selling_price > 0) {
                  const margin = ((item.selling_price - item.sourcing_price) / item.selling_price) * 100;

                  if (margin < 0) {
                    marginRanges['역마진']++;
                  } else if (margin < 10) {
                    marginRanges['0-10%']++;
                  } else if (margin < 20) {
                    marginRanges['10-20%']++;
                  } else if (margin < 30) {
                    marginRanges['20-30%']++;
                  } else if (margin < 40) {
                    marginRanges['30-40%']++;
                  } else if (margin < 50) {
                    marginRanges['40-50%']++;
                  } else {
                    marginRanges['50%+']++;
                  }
                }
              }
            }
          } catch (err) {
            // 개별 주문 조회 실패는 무시
          }
        }
      }

      setChartData({
        labels: Object.keys(marginRanges),
        datasets: [
          {
            label: '상품 수',
            data: Object.values(marginRanges),
            backgroundColor: [
              'rgba(239, 68, 68, 0.8)',   // 역마진 - 빨강
              'rgba(251, 146, 60, 0.8)',  // 0-10% - 주황
              'rgba(253, 224, 71, 0.8)',  // 10-20% - 노랑
              'rgba(163, 230, 53, 0.8)',  // 20-30% - 연두
              'rgba(34, 197, 94, 0.8)',   // 30-40% - 초록
              'rgba(59, 130, 246, 0.8)',  // 40-50% - 파랑
              'rgba(139, 92, 246, 0.8)',  // 50%+ - 보라
            ],
            borderColor: [
              'rgb(239, 68, 68)',
              'rgb(251, 146, 60)',
              'rgb(253, 224, 71)',
              'rgb(163, 230, 53)',
              'rgb(34, 197, 94)',
              'rgb(59, 130, 246)',
              'rgb(139, 92, 246)',
            ],
            borderWidth: 2,
          }
        ]
      });
    } catch (error) {
      console.error('마진 데이터 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `상품 수: ${context.parsed.y}개`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        }
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-500"></div>
      </div>
    );
  }

  if (!chartData) {
    return (
      <div className="flex items-center justify-center h-80 bg-gray-50 rounded-xl">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-500">데이터를 불러올 수 없습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-80">
      <Bar data={chartData} options={options} />
    </div>
  );
}
