/**
 * LoadingSpinner Component
 *
 * 로딩 상태를 표시하는 재사용 가능한 컴포넌트
 */

import { RefreshCw, Loader2 } from 'lucide-react';

export interface LoadingSpinnerProps {
  /** 로딩 텍스트 */
  text?: string;
  /** 크기 */
  size?: 'sm' | 'md' | 'lg';
  /** 아이콘 타입 */
  variant?: 'spinner' | 'refresh';
  /** 전체 화면 중앙 표시 */
  fullscreen?: boolean;
  /** 커스텀 className */
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

const textSizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
};

export default function LoadingSpinner({
  text = '데이터 로딩 중...',
  size = 'md',
  variant = 'spinner',
  fullscreen = false,
  className = '',
}: LoadingSpinnerProps) {
  const Icon = variant === 'spinner' ? Loader2 : RefreshCw;

  const content = (
    <div className={`flex flex-col items-center justify-center ${fullscreen ? '' : 'py-12'} ${className}`}>
      <Icon className={`${sizeClasses[size]} animate-spin text-blue-500 mb-3`} />
      {text && (
        <span className={`${textSizeClasses[size]} text-gray-600 font-medium`}>
          {text}
        </span>
      )}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
}

/**
 * Inline Spinner
 * 텍스트 옆에 표시하는 작은 스피너
 */
export function InlineSpinner({ className = '' }: { className?: string }) {
  return (
    <Loader2 className={`w-4 h-4 animate-spin ${className}`} />
  );
}

/**
 * Button Spinner
 * 버튼 안에 표시하는 스피너
 */
export function ButtonSpinner({ text = '처리 중...' }: { text?: string }) {
  return (
    <span className="flex items-center gap-2">
      <Loader2 className="w-4 h-4 animate-spin" />
      {text}
    </span>
  );
}
