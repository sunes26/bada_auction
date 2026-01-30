'use client';

import { useState, useEffect } from 'react';
import { BookmarkPlus, Trash2, Check } from 'lucide-react';
import { FilterConfig } from './AdvancedFilter';
import { toast } from 'sonner';

interface Preset {
  name: string;
  filters: FilterConfig;
}

interface FilterPresetsProps {
  onLoadPreset: (filters: FilterConfig) => void;
  currentFilters?: FilterConfig;
}

export default function FilterPresets({ onLoadPreset, currentFilters }: FilterPresetsProps) {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = () => {
    try {
      const saved = localStorage.getItem('filter-presets');
      if (saved) {
        setPresets(JSON.parse(saved));
      }
    } catch (error) {
      console.error('프리셋 로드 실패:', error);
      toast.error('프리셋을 불러오는데 실패했습니다.');
    }
  };

  const savePresets = (newPresets: Preset[]) => {
    try {
      localStorage.setItem('filter-presets', JSON.stringify(newPresets));
      setPresets(newPresets);
      toast.success('프리셋이 저장되었습니다.');
    } catch (error) {
      console.error('프리셋 저장 실패:', error);
      toast.error('프리셋 저장에 실패했습니다.');
    }
  };

  const handleSavePreset = (name: string, filters: FilterConfig) => {
    const existingIndex = presets.findIndex(p => p.name === name);
    let newPresets: Preset[];

    if (existingIndex >= 0) {
      // Update existing preset
      newPresets = [...presets];
      newPresets[existingIndex] = { name, filters };
      toast.info(`프리셋 "${name}"이(가) 업데이트되었습니다.`);
    } else {
      // Add new preset
      newPresets = [...presets, { name, filters }];
      toast.success(`프리셋 "${name}"이(가) 추가되었습니다.`);
    }

    savePresets(newPresets);
  };

  const handleLoadPreset = (preset: Preset) => {
    onLoadPreset(preset.filters);
    setSelectedPreset(preset.name);
    toast.success(`프리셋 "${preset.name}"을(를) 적용했습니다.`);
  };

  const handleDeletePreset = (name: string) => {
    const newPresets = presets.filter(p => p.name !== name);
    savePresets(newPresets);
    if (selectedPreset === name) {
      setSelectedPreset(null);
    }
    toast.success(`프리셋 "${name}"이(가) 삭제되었습니다.`);
  };

  if (presets.length === 0) {
    return null;
  }

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-black/5 border border-white/20 p-4">
      <div className="flex items-center gap-2 mb-3">
        <BookmarkPlus className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-gray-800">저장된 필터 프리셋</h3>
      </div>

      <div className="flex flex-wrap gap-2">
        {presets.map((preset) => (
          <div
            key={preset.name}
            className={`group relative px-4 py-2 rounded-xl border transition-all ${
              selectedPreset === preset.name
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white border-transparent shadow-lg'
                : 'bg-white/50 text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <button
              onClick={() => handleLoadPreset(preset)}
              className="flex items-center gap-2 font-medium"
            >
              {selectedPreset === preset.name && (
                <Check className="w-4 h-4" />
              )}
              {preset.name}
            </button>

            <button
              onClick={() => handleDeletePreset(preset.name)}
              className={`absolute -top-2 -right-2 p-1 rounded-full transition-all opacity-0 group-hover:opacity-100 ${
                selectedPreset === preset.name
                  ? 'bg-white text-red-600'
                  : 'bg-red-500 text-white'
              }`}
              title="삭제"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export { type Preset };
export function saveFilterPreset(name: string, filters: FilterConfig) {
  try {
    const saved = localStorage.getItem('filter-presets');
    const presets: Preset[] = saved ? JSON.parse(saved) : [];

    const existingIndex = presets.findIndex(p => p.name === name);
    if (existingIndex >= 0) {
      presets[existingIndex] = { name, filters };
    } else {
      presets.push({ name, filters });
    }

    localStorage.setItem('filter-presets', JSON.stringify(presets));
    return true;
  } catch (error) {
    console.error('프리셋 저장 실패:', error);
    return false;
  }
}
