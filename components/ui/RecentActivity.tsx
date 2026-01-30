'use client';

import { Package, DollarSign, AlertCircle, TrendingUp, Clock } from 'lucide-react';

interface Activity {
  id: string;
  type: 'order' | 'price_change' | 'alert' | 'sync';
  title: string;
  description: string;
  time: string;
  icon: React.ReactNode;
  color: string;
}

interface RecentActivityProps {
  activities: Activity[];
}

export default function RecentActivity({ activities }: RecentActivityProps) {
  const getIconByType = (type: Activity['type']) => {
    switch (type) {
      case 'order':
        return <Package className="w-4 h-4" />;
      case 'price_change':
        return <DollarSign className="w-4 h-4" />;
      case 'alert':
        return <AlertCircle className="w-4 h-4" />;
      case 'sync':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const getColorByType = (type: Activity['type']) => {
    switch (type) {
      case 'order':
        return 'from-blue-500 to-blue-600';
      case 'price_change':
        return 'from-green-500 to-green-600';
      case 'alert':
        return 'from-red-500 to-red-600';
      case 'sync':
        return 'from-purple-500 to-purple-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-black/5 border border-white/20 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">최근 활동</h3>
      <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar pl-4">
        {activities.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">최근 활동이 없습니다</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className="relative pl-8 pb-3 border-l-2 border-gray-200 last:border-l-0 last:pb-0"
            >
              <div className={`absolute left-[-16px] w-8 h-8 rounded-lg bg-gradient-to-br ${getColorByType(activity.type)} flex items-center justify-center text-white shadow-md`}>
                {getIconByType(activity.type)}
              </div>
              <div className="ml-2">
                <p className="font-semibold text-gray-800 text-sm">{activity.title}</p>
                <p className="text-xs text-gray-600 mt-1">{activity.description}</p>
                <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {activity.time}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #2563eb, #7c3aed);
        }
      `}</style>
    </div>
  );
}
