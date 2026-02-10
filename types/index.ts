export interface Category {
  level1: string;
  level2: string;
  level3: string;
  level4: string;
}

export interface TrendingKeyword {
  id: string;
  category: string;
  keyword: string;
  rank: number;
  change: 'NEW' | 'UP' | 'DOWN' | 'SAME';
  updated_at: string;
}

export interface Assignment {
  id: string;
  student_name: string;
  week: string;
  file_urls: string[];
  memo: string;
  created_at: string;
}

export interface Week {
  id: string;
  week_number: string;
  assignment_content: string;
  created_at: string;
}

export interface ChatbotSettings {
  id: string;
  system_prompt: string;
  updated_at: string;
}

export type TemplateType = 'daily' | 'convenience' | 'electronics' | 'processedFood' | 'hygiene' | 'stationery';

export interface Template {
  name: string;
  description: string;
  placeholder: string;
}
