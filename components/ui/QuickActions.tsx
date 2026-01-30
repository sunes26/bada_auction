'use client';

import { Plus, ShoppingCart, Upload, Settings } from 'lucide-react';

interface QuickAction {
  icon: React.ReactNode;
  label: string;
  description: string;
  color: string;
  onClick: () => void;
}

interface QuickActionsProps {
  onCreateOrder: () => void;
  onCollectProducts: () => void;
  onUploadTracking: () => void;
  onSettings: () => void;
}

export default function QuickActions({
  onCreateOrder,
  onCollectProducts,
  onUploadTracking,
  onSettings,
}: QuickActionsProps) {
  const actions: QuickAction[] = [
    {
      icon: <Plus className="w-6 h-6" />,
      label: '주문 생성',
      description: '새 주문 추가',
      color: 'from-blue-500 to-blue-600',
      onClick: onCreateOrder,
    },
    {
      icon: <ShoppingCart className="w-6 h-6" />,
      label: '상품 수집',
      description: '상품 검색 및 모니터링',
      color: 'from-green-500 to-green-600',
      onClick: onCollectProducts,
    },
    {
      icon: <Upload className="w-6 h-6" />,
      label: '송장 업로드',
      description: '송장 일괄 업로드',
      color: 'from-purple-500 to-purple-600',
      onClick: onUploadTracking,
    },
    {
      icon: <Settings className="w-6 h-6" />,
      label: '설정',
      description: 'Playauto 설정',
      color: 'from-orange-500 to-orange-600',
      onClick: onSettings,
    },
  ];

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-black/5 border border-white/20 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">빠른 액션</h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={action.onClick}
            className="group relative overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] text-left"
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
            <div className="relative">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${action.color} flex items-center justify-center text-white mb-2 shadow-md`}>
                {action.icon}
              </div>
              <p className="font-semibold text-gray-800 text-sm mb-1">{action.label}</p>
              <p className="text-xs text-gray-600">{action.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
