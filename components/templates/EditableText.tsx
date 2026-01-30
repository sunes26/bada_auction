import { useState } from 'react';

interface EditableTextProps {
  field: string;
  value: string | undefined;
  editingField: string | null;
  editingValue: string;
  isTextarea?: boolean;
  textStyles?: Record<string, {
    fontSize?: string;
    color?: string;
    fontWeight?: string;
    textAlign?: string;
  }>;
  onEdit: (field: string, value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onValueChange: (value: string) => void;
  onStyleClick?: (field: string) => void;
  className?: string;
  style?: React.CSSProperties;
}

export default function EditableText({
  field,
  value = '',
  editingField,
  editingValue,
  isTextarea = false,
  textStyles = {},
  onEdit,
  onSave,
  onCancel,
  onValueChange,
  onStyleClick,
  className = '',
  style = {},
}: EditableTextProps) {
  const isEditing = editingField === field;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isEditing && onStyleClick) {
      onStyleClick(field);
    }
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isEditing) {
      onEdit(field, value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isTextarea && e.key === 'Enter') {
      e.preventDefault();
      onSave();
    }
    if (e.key === 'Escape') {
      onCancel();
    }
  };

  // 현재 field의 스타일 가져오기
  const currentStyles = textStyles?.[field] || {};

  const combinedStyle = {
    ...style,
    fontSize: currentStyles.fontSize || style.fontSize,
    color: currentStyles.color || style.color,
    fontWeight: currentStyles.fontWeight || style.fontWeight,
    textAlign: (currentStyles.textAlign as any) || style.textAlign,
  };

  if (isEditing) {
    return (
      <div className="relative inline-block" onClick={(e) => e.stopPropagation()}>
        {isTextarea ? (
          <textarea
            value={editingValue}
            onChange={(e) => onValueChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full px-2 py-1 border-2 border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
            style={combinedStyle}
            rows={5}
            autoFocus
          />
        ) : (
          <input
            type="text"
            value={editingValue}
            onChange={(e) => onValueChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="px-2 py-1 border-2 border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
            style={combinedStyle}
            autoFocus
          />
        )}
        <div className="flex gap-2 mt-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSave();
            }}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
          >
            저장
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onCancel();
            }}
            className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
          >
            취소
          </button>
        </div>
      </div>
    );
  }

  return (
    <span
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      className={`cursor-pointer hover:bg-blue-50 hover:ring-2 hover:ring-blue-300 rounded px-2 py-1 transition-all inline-block relative z-40 group ${className}`}
      style={{ ...combinedStyle, minWidth: 'fit-content', wordBreak: 'break-word' }}
      title="클릭: 속성 패널 열기 | 더블클릭: 인라인 편집"
    >
      {value || '텍스트를 입력하세요'}
      {/* 커스텀 툴팁 - Figma 스타일 */}
      <span className="absolute -top-9 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 block shadow-lg">
        클릭: 속성 패널 | 더블클릭: 인라인 편집
      </span>
    </span>
  );
}
