'use client';

import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { PieChart } from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function SourcePieChart() {
  const [chartData, setChartData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSourceData();
  }, []);

  const loadSourceData = async () => {
    try {
      setIsLoading(true);

      // RPA 소싱처별 통계 가져오기
      const statsRes = await fetch('http://localhost:8000/api/orders/rpa/stats/by-source');
      const statsData = await statsRes.json();

      if (statsData.success && statsData.stats && statsData.stats.length > 0) {
        const labels = statsData.stats.map((s: any) => s.source.toUpperCase());
        const data = statsData.stats.map((s: any) => s.total_executions || 0);

        // 색상 배열
        const colors = [
          'rgba(59, 130, 246, 0.8)',   // 파랑
          'rgba(139, 92, 246, 0.8)',   // 보라
          'rgba(236, 72, 153, 0.8)',   // 핑크
          'rgba(251, 146, 60, 0.8)',   // 주황
          'rgba(34, 197, 94, 0.8)',    // 초록
          'rgba(234, 179, 8, 0.8)',    // 노랑
        ];

        const borderColors = [
          'rgb(59, 130, 246)',
          'rgb(139, 92, 246)',
          'rgb(236, 72, 153)',
          'rgb(251, 146, 60)',
          'rgb(34, 197, 94)',
          'rgb(234, 179, 8)',
        ];

        setChartData({
          labels,
          datasets: [
            {
              label: '주문 수',
              data,
              backgroundColor: colors.slice(0, labels.length),
              borderColor: borderColors.slice(0, labels.length),
              borderWidth: 2,
            }
          ]
        });
      } else {
        // 데이터가 없을 경우 기본값
        setChartData({
          labels: ['데이터 없음'],
          datasets: [
            {
              label: '주문 수',
              data: [1],
              backgroundColor: ['rgba(209, 213, 219, 0.8)'],
              borderColor: ['rgb(209, 213, 219)'],
              borderWidth: 2,
            }
          ]
        });
      }
    } catch (error) {
      console.error('소싱처 데이터 로드 실패:', error);
      setChartData({
        labels: ['데이터 없음'],
        datasets: [
          {
            label: '주문 수',
            data: [1],
            backgroundColor: ['rgba(209, 213, 219, 0.8)'],
            borderColor: ['rgb(209, 213, 219)'],
            borderWidth: 2,
          }
        ]
      });
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
        position: 'bottom' as const,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value}건 (${percentage}%)`;
          }
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
          <PieChart className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-500">데이터를 불러올 수 없습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-80">
      <Pie data={chartData} options={options} />
    </div>
  );
}
