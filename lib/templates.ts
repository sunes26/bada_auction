import { Home, Package, Sparkles, Leaf } from 'lucide-react';
import type { Template, TemplateType } from '@/types';

export const templates: Record<TemplateType, Template> = {
  daily: {
    name: '템플릿A',
    description: '일상에 꼭 필요한',
    placeholder: '예: 프리미엄 화장지'
  },
  convenience: {
    name: '템플릿B',
    description: '간편하고 맛있는',
    placeholder: '예: 컵라면, 즉석밥'
  },
  additional: {
    name: '템플릿C',
    description: '특별한 디자인의',
    placeholder: '예: 하우스감귤'
  },
  additional2: {
    name: '템플릿D',
    description: '새로운 스타일의',
    placeholder: '예: 미리 물티슈'
  },
  fresh: {
    name: '신선식품',
    description: '신선하고 건강한',
    placeholder: '예: 유기농 사과'
  },
  simple: {
    name: '심플버전',
    description: '간단하고 깔끔한',
    placeholder: '예: 기본 상품'
  }
};

export const getTemplateIcon = (type: TemplateType) => {
  const iconMap = {
    daily: Home,
    convenience: Package,
    additional: Sparkles,
    additional2: Sparkles,
    fresh: Leaf,
    simple: Package
  };
  return iconMap[type];
};
