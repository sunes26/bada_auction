// 로컬 트렌딩 키워드 데이터
export interface TrendingKeyword {
  id: string;
  keyword: string;
  rank: number;
  category: string;
  change: 'NEW' | 'UP' | 'DOWN' | 'SAME';
  created_at: string;
  updated_at: string;
}

export const trendingKeywords: TrendingKeyword[] = [
  { id: '1', keyword: '유기농 사과', rank: 1, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '2', keyword: '프리미엄 화장지', rank: 2, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '3', keyword: '컵라면', rank: 3, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '4', keyword: '즉석밥', rank: 4, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '5', keyword: '물티슈', rank: 5, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '6', keyword: '하우스감귤', rank: 6, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '7', keyword: '생수', rank: 7, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '8', keyword: '초콜릿', rank: 8, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '9', keyword: '과자', rank: 9, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '10', keyword: '우유', rank: 10, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '11', keyword: '샴푸', rank: 11, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '12', keyword: '치약', rank: 12, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '13', keyword: '커피', rank: 13, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '14', keyword: '녹차', rank: 14, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '15', keyword: '홍차', rank: 15, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '16', keyword: '쥬스', rank: 16, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '17', keyword: '식빵', rank: 17, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '18', keyword: '케이크', rank: 18, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '19', keyword: '쿠키', rank: 19, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '20', keyword: '사탕', rank: 20, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '21', keyword: '젤리', rank: 21, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '22', keyword: '요구르트', rank: 22, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '23', keyword: '치즈', rank: 23, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '24', keyword: '버터', rank: 24, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '25', keyword: '계란', rank: 25, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '26', keyword: '햄', rank: 26, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '27', keyword: '소시지', rank: 27, category: '식품', change: 'UP', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '28', keyword: '베이컨', rank: 28, category: '식품', change: 'DOWN', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '29', keyword: '참치캔', rank: 29, category: '식품', change: 'SAME', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: '30', keyword: '김치', rank: 30, category: '식품', change: 'NEW', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
];
