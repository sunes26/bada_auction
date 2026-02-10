import { Home, Package, Cpu, UtensilsCrossed, ShieldCheck, PenTool } from 'lucide-react';
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
  electronics: {
    name: '전자제품류',
    description: '기술과 혁신의',
    placeholder: '예: 무선 이어폰, 충전기'
  },
  processedFood: {
    name: '가공식품류',
    description: '맛있고 간편한',
    placeholder: '예: 밀키트, 냉동식품'
  },
  hygiene: {
    name: '위생용품류',
    description: '깨끗하고 안전한',
    placeholder: '예: 물티슈, 위생용품'
  },
  stationery: {
    name: '문구류',
    description: '기록과 창작의',
    placeholder: '예: 노트, 다이어리'
  }
};

export const getTemplateIcon = (type: TemplateType) => {
  const iconMap = {
    daily: Home,
    convenience: Package,
    electronics: Cpu,
    processedFood: UtensilsCrossed,
    hygiene: ShieldCheck,
    stationery: PenTool
  };
  return iconMap[type];
};
