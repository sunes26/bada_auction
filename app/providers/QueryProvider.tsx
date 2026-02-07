'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // 기본 캐시 시간: 30초
            staleTime: 30 * 1000,
            // 가비지 컬렉션: 5분
            gcTime: 5 * 60 * 1000,
            // 실패 시 재시도 1회
            retry: 1,
            // 윈도우 포커스 시 자동 새로고침
            refetchOnWindowFocus: true,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
