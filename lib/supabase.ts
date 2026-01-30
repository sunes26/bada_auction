/**
 * Supabase 클라이언트 (로컬 모드에서는 사용 안 함)
 * 호환성을 위해 더미 객체 export
 */

export const supabase = {
  from: () => ({
    select: () => Promise.resolve({ data: null, error: null }),
    insert: () => Promise.resolve({ data: null, error: null }),
    update: () => Promise.resolve({ data: null, error: null }),
    delete: () => Promise.resolve({ data: null, error: null }),
  }),
  storage: {
    from: () => ({
      list: () => Promise.resolve({ data: null, error: null }),
      download: () => Promise.resolve({ data: null, error: null }),
      upload: () => Promise.resolve({ data: null, error: null }),
    }),
  },
};

export const isSupabaseConfigured = () => {
  return false; // 로컬 모드에서는 항상 false
};
