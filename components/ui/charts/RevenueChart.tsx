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
import { TrendingUp } from 'lucide-react';
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

export default function RevenueChart() {
  const [chartData, setChartData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  useEffect(() => {
    loadRevenueData();
  }, [period]);

  const loadRevenueData = async () => {
    try {
      setIsLoading(true);

      // RPA 일별 통계 + 주문 목록 가져오기
      const [dailyStatsRes, ordersRes] = await Promise.all([
        fetch('http://localhost:8000/api/orders/rpa/daily-stats?days=30'),
        fetch('http://localhost:8000/api/orders/list?limit=100'),
      ]);

      const dailyStats = await dailyStatsRes.json();
      const ordersData = await ordersRes.json();

      // 날짜별 매출 집계
      const revenueByDate: Record<string, number> = {};

      if (ordersData.success && ordersData.orders) {
        ordersData.orders.forEach((order: any) => {
          const date = new Date(order.created_at).toISOString().split('T')[0];
          revenueByDate[date] = (revenueByDate[date] || 0) + (order.total_amount || 0);
        });
      }

      // 최근 30일 데이터 생성
      const labels: string[] = [];
      const data: number[] = [];
      const now = new Date();

      for (let i = 29; i >= 0; i--) {
        const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        const dateStr = date.toISOString().split('T')[0];
        const label = `${date.getMonth() + 1}/${date.getDate()}`;

        labels.push(label);
        data.push(Math.floor((revenueByDate[dateStr] || 0) / 10000)); // 만원 단위
      }

      setChartData({
        labels,
        datasets: [
          {
            label: '매출 (만원)',
            data,
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: 'rgb(59, 130, 246)',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
          }
        ]
      });
    } catch (error) {
      console.error('매출 데이터 로드 실패:', error);
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
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `매출: ${context.parsed.y.toLocaleString()}만원`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            return value.toLocaleString() + '만원';
          }
        }
      },
      x: {
        grid: {
          display: false,
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
          <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-500">데이터를 불러올 수 없습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-80">
      <Line data={chartData} options={options} />
    </div>
  );
}
