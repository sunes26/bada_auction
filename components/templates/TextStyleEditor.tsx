import { X } from 'lucide-react';

interface TextStyleEditorProps {
  field: string;
  styles: {
    fontSize?: string;
    color?: string;
    fontWeight?: string;
  };
  onStyleChange: (field: string, styles: { fontSize?: string; color?: string; fontWeight?: string }) => void;
  onClose: () => void;
}

export default function TextStyleEditor({ field, styles, onStyleChange, onClose }: TextStyleEditorProps) {
  const handleFontSizeChange = (size: string) => {
    onStyleChange(field, { ...styles, fontSize: size });
  };

  const handleColorChange = (color: string) => {
    onStyleChange(field, { ...styles, color });
  };

  const handleFontWeightChange = (weight: string) => {
    onStyleChange(field, { ...styles, fontWeight: weight });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl p-6 shadow-2xl max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-800">텍스트 스타일 편집</h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="space-y-6">
          {/* 글자 크기 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">글자 크기</label>
            <div className="grid grid-cols-4 gap-2">
              {['12px', '16px', '20px', '24px', '32px', '40px', '48px', '64px'].map((size) => (
                <button
                  key={size}
                  onClick={() => handleFontSizeChange(size)}
                  className={`px-3 py-2 rounded-lg border-2 transition-all ${
                    styles.fontSize === size
                      ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          {/* 글자 색상 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">글자 색상</label>
            <div className="grid grid-cols-5 gap-2">
              {[
                { name: '검정', value: '#000000' },
                { name: '흰색', value: '#FFFFFF' },
                { name: '빨강', value: '#EF4444' },
                { name: '파랑', value: '#3B82F6' },
                { name: '초록', value: '#10B981' },
                { name: '노랑', value: '#F59E0B' },
                { name: '보라', value: '#8B5CF6' },
                { name: '분홍', value: '#EC4899' },
                { name: '회색', value: '#6B7280' },
                { name: '남색', value: '#1E40AF' },
              ].map((color) => (
                <button
                  key={color.value}
                  onClick={() => handleColorChange(color.value)}
                  className={`h-12 rounded-lg border-2 transition-all flex items-center justify-center ${
                    styles.color === color.value
                      ? 'border-blue-500 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                >
                  {styles.color === color.value && (
                    <svg className="w-6 h-6" fill={color.value === '#FFFFFF' ? '#000' : '#FFF'} viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* 글자 굵기 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">글자 굵기</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { name: '얇게', value: '300' },
                { name: '보통', value: '400' },
                { name: '중간', value: '500' },
                { name: '굵게', value: '600' },
                { name: '매우 굵게', value: '700' },
                { name: '극굵게', value: '800' },
              ].map((weight) => (
                <button
                  key={weight.value}
                  onClick={() => handleFontWeightChange(weight.value)}
                  className={`px-3 py-2 rounded-lg border-2 transition-all ${
                    styles.fontWeight === weight.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                  style={{ fontWeight: parseInt(weight.value) }}
                >
                  {weight.name}
                </button>
              ))}
            </div>
          </div>

          {/* 미리보기 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">미리보기</label>
            <div className="bg-gray-50 rounded-lg p-6 text-center border-2 border-gray-200">
              <p
                style={{
                  fontSize: styles.fontSize || '16px',
                  color: styles.color || '#000000',
                  fontWeight: styles.fontWeight || '400',
                }}
              >
                텍스트 미리보기
              </p>
            </div>
          </div>

          {/* 완료 버튼 */}
          <button
            onClick={onClose}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            완료
          </button>
        </div>
      </div>
    </div>
  );
}
