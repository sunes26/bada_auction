'use client';

import { Type, Image as ImageIcon, X, AlignLeft, AlignCenter, AlignRight } from 'lucide-react';
import { useState, useEffect } from 'react';

interface PropertiesPanelProps {
  selectedElement: {
    type: 'text' | 'image' | null;
    field: string | null;
  };
  content: any;
  textStyles: Record<string, { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }>;
  imageSizes: Record<string, number>;
  imagePositions: Record<string, { x: number; y: number }>;
  uploadedImages: Record<string, string>;
  onTextChange: (field: string, value: string) => void;
  onStyleChange: (field: string, styles: { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }) => void;
  onImageResize: (imageKey: string, size: number) => void;
  onImageMove: (imageKey: string, position: { x: number; y: number }) => void;
  onClose: () => void;
}

export default function PropertiesPanel({
  selectedElement,
  content,
  textStyles,
  imageSizes,
  imagePositions,
  uploadedImages,
  onTextChange,
  onStyleChange,
  onImageResize,
  onImageMove,
  onClose,
}: PropertiesPanelProps) {
  // 빈 상태
  if (!selectedElement.field) {
    return (
      <div className="properties-panel w-[350px] bg-white border-l border-gray-200 p-6 flex flex-col items-center justify-center text-center min-h-screen">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Type className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">요소를 선택하세요</h3>
        <p className="text-sm text-gray-500">텍스트나 이미지를 클릭하면<br/>속성을 편집할 수 있습니다</p>
      </div>
    );
  }

  // 텍스트 속성 패널
  if (selectedElement.type === 'text') {
    const field = selectedElement.field;
    const value = content[field] || '';
    const styles = textStyles[field] || {};
    const fontSize = parseInt(styles.fontSize || '16');
    const color = styles.color || '#000000';
    const fontWeight = styles.fontWeight || '400';
    const textAlign = styles.textAlign || 'left';

    return (
      <div className="properties-panel w-[350px] bg-white border-l border-gray-200 min-h-screen overflow-y-auto">
        {/* 헤더 */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Type className="w-4 h-4 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-800">Text</h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>

        {/* 내용 */}
        <div className="p-4 space-y-6">
          {/* 텍스트 내용 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">내용</label>
            <textarea
              value={value}
              onChange={(e) => onTextChange(field, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
              placeholder="텍스트를 입력하세요"
            />
          </div>

          {/* 폰트 크기 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              폰트 크기
              <span className="ml-2 text-blue-600 font-mono">{fontSize}px</span>
            </label>
            <input
              type="range"
              min="10"
              max="100"
              value={fontSize}
              onChange={(e) => onStyleChange(field, { ...styles, fontSize: e.target.value + 'px' })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10px</span>
              <span>100px</span>
            </div>
          </div>

          {/* 색상 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">색상</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={color}
                onChange={(e) => onStyleChange(field, { ...styles, color: e.target.value })}
                className="w-12 h-10 rounded-lg border border-gray-300 cursor-pointer"
              />
              <input
                type="text"
                value={color}
                onChange={(e) => onStyleChange(field, { ...styles, color: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                placeholder="#000000"
              />
            </div>
          </div>

          {/* 굵기 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">굵기</label>
            <div className="flex gap-2">
              <button
                onClick={() => onStyleChange(field, { ...styles, fontWeight: '400' })}
                className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                  fontWeight === '400'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Regular
              </button>
              <button
                onClick={() => onStyleChange(field, { ...styles, fontWeight: '700' })}
                className={`flex-1 px-4 py-2 rounded-lg border transition-colors font-bold ${
                  fontWeight === '700'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Bold
              </button>
            </div>
          </div>

          {/* 정렬 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">정렬</label>
            <div className="flex gap-2">
              <button
                onClick={() => onStyleChange(field, { ...styles, textAlign: 'left' })}
                className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                  textAlign === 'left'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <AlignLeft className="w-4 h-4 mx-auto" />
              </button>
              <button
                onClick={() => onStyleChange(field, { ...styles, textAlign: 'center' })}
                className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                  textAlign === 'center'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <AlignCenter className="w-4 h-4 mx-auto" />
              </button>
              <button
                onClick={() => onStyleChange(field, { ...styles, textAlign: 'right' })}
                className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                  textAlign === 'right'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <AlignRight className="w-4 h-4 mx-auto" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 이미지 속성 패널
  if (selectedElement.type === 'image') {
    const imageKey = selectedElement.field;
    const imageSize = imageSizes[imageKey] || 100;
    const imagePosition = imagePositions[imageKey] || { x: 0, y: 0 };
    const imageUrl = uploadedImages[imageKey];

    return (
      <div className="properties-panel w-[350px] bg-white border-l border-gray-200 min-h-screen overflow-y-auto">
        {/* 헤더 */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
              <ImageIcon className="w-4 h-4 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-800">Image</h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>

        {/* 내용 */}
        <div className="p-4 space-y-6">
          {/* 미리보기 */}
          {imageUrl && (
            <div className="w-full aspect-video bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
              <div
                className="w-full h-full bg-cover bg-center bg-no-repeat"
                style={{ backgroundImage: `url(${imageUrl})`, backgroundSize: 'contain' }}
              />
            </div>
          )}

          {/* 크기 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              크기
              <span className="ml-2 text-purple-600 font-mono">{imageSize}%</span>
            </label>
            <input
              type="range"
              min="50"
              max="300"
              value={imageSize}
              onChange={(e) => onImageResize(imageKey, parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>50%</span>
              <span>300%</span>
            </div>
          </div>

          {/* 위치 */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-3">위치</label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">X</label>
                <input
                  type="number"
                  value={Math.round(imagePosition.x)}
                  onChange={(e) => onImageMove(imageKey, { ...imagePosition, x: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Y</label>
                <input
                  type="number"
                  value={Math.round(imagePosition.y)}
                  onChange={(e) => onImageMove(imageKey, { x: imagePosition.x, y: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
            <button
              onClick={() => onImageMove(imageKey, { x: 0, y: 0 })}
              className="w-full mt-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-lg transition-colors"
            >
              위치 초기화
            </button>
          </div>

          {/* 이미지 키 정보 */}
          <div className="pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 break-all">
              <span className="font-semibold">Image Key:</span> {imageKey}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
