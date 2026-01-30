/**
 * useAPI Hook
 *
 * 커스텀 훅으로 API 호출을 단순화하고 로딩, 에러 상태를 자동으로 관리합니다.
 *
 * @example
 * const { data, loading, error, refetch } = useAPI<DashboardStats>('/api/dashboard/stats');
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchAPI, ApiError } from '@/lib/api';
import { toast } from 'sonner';

export interface UseAPIOptions<T> {
  /** 초기 데이터 */
  initialData?: T | null;
  /** 자동 실행 여부 (false면 수동으로 refetch 호출 필요) */
  enabled?: boolean;
  /** 에러 발생 시 toast 표시 여부 */
  showErrorToast?: boolean;
  /** 성공 시 toast 표시 여부 */
  showSuccessToast?: boolean;
  /** 성공 토스트 메시지 */
  successMessage?: string;
  /** 에러 토스트 메시지 커스터마이징 */
  errorMessage?: string | ((error: Error) => string);
  /** 요청 옵션 */
  fetchOptions?: RequestInit;
  /** 의존성 배열 (변경 시 자동으로 refetch) */
  deps?: any[];
  /** 디바운스 딜레이 (ms) */
  debounceDelay?: number;
}

export interface UseAPIResult<T> {
  /** 응답 데이터 */
  data: T | null;
  /** 로딩 상태 */
  loading: boolean;
  /** 에러 객체 */
  error: Error | null;
  /** 수동으로 다시 요청 */
  refetch: () => Promise<void>;
  /** 로딩 상태인지 여부 */
  isLoading: boolean;
  /** 에러 상태인지 여부 */
  isError: boolean;
  /** 성공 상태인지 여부 */
  isSuccess: boolean;
}

export function useAPI<T = any>(
  url: string | null,
  options: UseAPIOptions<T> = {}
): UseAPIResult<T> {
  const {
    initialData = null,
    enabled = true,
    showErrorToast = true,
    showSuccessToast = false,
    successMessage,
    errorMessage,
    fetchOptions,
    deps = [],
    debounceDelay = 0,
  } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState<boolean>(enabled && !!url);
  const [error, setError] = useState<Error | null>(null);

  // debounce 타이머 ref
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  // abort controller for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (!url) {
      setLoading(false);
      return;
    }

    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 새로운 abort controller 생성
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      setError(null);

      const result = await fetchAPI<T>(url, {
        ...fetchOptions,
        signal: abortControllerRef.current.signal,
      });

      setData(result);
      setError(null);

      if (showSuccessToast && successMessage) {
        toast.success(successMessage);
      }
    } catch (err) {
      // Abort 에러는 무시
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }

      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      setData(null);

      if (showErrorToast) {
        const message = typeof errorMessage === 'function'
          ? errorMessage(error)
          : errorMessage || (err instanceof ApiError ? err.message : '데이터를 불러오는데 실패했습니다');
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  }, [url, fetchOptions, showErrorToast, showSuccessToast, successMessage, errorMessage]);

  const debouncedFetch = useCallback(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (debounceDelay > 0) {
      debounceTimer.current = setTimeout(() => {
        fetchData();
      }, debounceDelay);
    } else {
      fetchData();
    }
  }, [fetchData, debounceDelay]);

  useEffect(() => {
    if (enabled && url) {
      debouncedFetch();
    }

    // cleanup
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [enabled, url, ...deps]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    isLoading: loading,
    isError: !!error,
    isSuccess: !loading && !error && data !== null,
  };
}

/**
 * useMutation Hook
 *
 * POST, PUT, DELETE 등 mutation 작업을 위한 훅
 *
 * @example
 * const { mutate, loading, error } = useMutation('/api/products', {
 *   method: 'POST',
 *   onSuccess: () => toast.success('생성 완료'),
 * });
 *
 * await mutate({ name: '상품명' });
 */

export interface UseMutationOptions<TData = any, TVariables = any> {
  /** HTTP 메서드 */
  method?: 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  /** 성공 시 콜백 */
  onSuccess?: (data: TData) => void;
  /** 에러 시 콜백 */
  onError?: (error: Error) => void;
  /** 에러 발생 시 toast 표시 여부 */
  showErrorToast?: boolean;
  /** 성공 시 toast 표시 여부 */
  showSuccessToast?: boolean;
  /** 성공 토스트 메시지 */
  successMessage?: string;
  /** 에러 토스트 메시지 */
  errorMessage?: string | ((error: Error) => string);
}

export interface UseMutationResult<TData = any, TVariables = any> {
  /** mutation 실행 함수 */
  mutate: (variables: TVariables) => Promise<TData | null>;
  /** 로딩 상태 */
  loading: boolean;
  /** 에러 객체 */
  error: Error | null;
  /** 응답 데이터 */
  data: TData | null;
  /** 초기화 */
  reset: () => void;
}

export function useMutation<TData = any, TVariables = any>(
  url: string,
  options: UseMutationOptions<TData, TVariables> = {}
): UseMutationResult<TData, TVariables> {
  const {
    method = 'POST',
    onSuccess,
    onError,
    showErrorToast = true,
    showSuccessToast = true,
    successMessage = '작업이 완료되었습니다',
    errorMessage,
  } = options;

  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (variables: TVariables): Promise<TData | null> => {
    try {
      setLoading(true);
      setError(null);

      const result = await fetchAPI<TData>(url, {
        method,
        body: JSON.stringify(variables),
      });

      setData(result);

      if (showSuccessToast) {
        toast.success(successMessage);
      }

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);

      if (showErrorToast) {
        const message = typeof errorMessage === 'function'
          ? errorMessage(error)
          : errorMessage || (err instanceof ApiError ? err.message : '작업 중 오류가 발생했습니다');
        toast.error(message);
      }

      if (onError) {
        onError(error);
      }

      return null;
    } finally {
      setLoading(false);
    }
  }, [url, method, onSuccess, onError, showErrorToast, showSuccessToast, successMessage, errorMessage]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    mutate,
    loading,
    error,
    data,
    reset,
  };
}
