/**
 * EmptyState Component
 *
 * 데이터가 없을 때 표시하는 컴포넌트
 */

import { LucideIcon, Package, FileText, Receipt, DollarSign, AlertCircle } from 'lucide-react';

export interface EmptyStateProps {
  /** 아이콘 */
  icon?: LucideIcon;
  /** 제목 */
  title: string;
  /** 설명 */
  description?: string;
  /** 액션 버튼 */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** 크기 */
  size?: 'sm' | 'md' | 'lg';
  /** 커스텀 className */
  className?: string;
}

const sizeClasses = {
  sm: {
    icon: 'w-12 h-12',
    title: 'text-base',
    description: 'text-sm',
    button: 'px-3 py-2 text-sm',
    container: 'py-8',
  },
  md: {
    icon: 'w-16 h-16',
    title: 'text-lg',
    description: 'text-base',
    button: 'px-4 py-2 text-base',
    container: 'py-12',
  },
  lg: {
    icon: 'w-20 h-20',
    title: 'text-xl',
    description: 'text-lg',
    button: 'px-6 py-3 text-lg',
    container: 'py-16',
  },
};

export default function EmptyState({
  icon: Icon = Package,
  title,
  description,
  action,
  size = 'md',
  className = '',
}: EmptyStateProps) {
  const sizes = sizeClasses[size];

  return (
    <div className={`text-center ${sizes.container} ${className}`}>
      <div className="flex justify-center mb-4">
        <Icon className={`${sizes.icon} text-gray-400`} />
      </div>
      <h3 className={`${sizes.title} font-semibold text-gray-900 mb-2`}>
        {title}
      </h3>
      {description && (
        <p className={`${sizes.description} text-gray-600 mb-6 max-w-md mx-auto`}>
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className={`${sizes.button} bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-600 transition-colors duration-200 shadow-md hover:shadow-lg`}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

/**
 * 미리 정의된 Empty State 컴포넌트들
 */

export function EmptyOrders({ onCreateOrder }: { onCreateOrder?: () => void }) {
  return (
    <EmptyState
      icon={Package}
      title="주문이 없습니다"
      description="아직 등록된 주문이 없습니다. 첫 주문을 생성해보세요."
      action={onCreateOrder ? {
        label: '주문 생성하기',
        onClick: onCreateOrder,
      } : undefined}
    />
  );
}

export function EmptyProducts({ onCreateProduct }: { onCreateProduct?: () => void }) {
  return (
    <EmptyState
      icon={Package}
      title="상품이 없습니다"
      description="아직 등록된 상품이 없습니다. 첫 상품을 추가해보세요."
      action={onCreateProduct ? {
        label: '상품 추가하기',
        onClick: onCreateProduct,
      } : undefined}
    />
  );
}

export function EmptyExpenses({ onCreateExpense }: { onCreateExpense?: () => void }) {
  return (
    <EmptyState
      icon={Receipt}
      title="지출 내역이 없습니다"
      description="아직 등록된 지출 내역이 없습니다. 지출을 추가해보세요."
      action={onCreateExpense ? {
        label: '지출 추가하기',
        onClick: onCreateExpense,
      } : undefined}
    />
  );
}

export function EmptySettlements({ onCreateSettlement }: { onCreateSettlement?: () => void }) {
  return (
    <EmptyState
      icon={DollarSign}
      title="정산 내역이 없습니다"
      description="아직 등록된 정산 내역이 없습니다. 정산을 추가해보세요."
      action={onCreateSettlement ? {
        label: '정산 추가하기',
        onClick: onCreateSettlement,
      } : undefined}
    />
  );
}

export function EmptyData({ message = "데이터가 없습니다" }: { message?: string }) {
  return (
    <EmptyState
      icon={FileText}
      title={message}
      size="sm"
    />
  );
}

export function ErrorState({
  title = "오류가 발생했습니다",
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      icon={AlertCircle}
      title={title}
      description={description || "데이터를 불러오는 중 문제가 발생했습니다. 다시 시도해주세요."}
      action={onRetry ? {
        label: '다시 시도',
        onClick: onRetry,
      } : undefined}
    />
  );
}
