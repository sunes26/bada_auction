'use client';

import { useState, useCallback } from 'react';
import { X, Plus, RefreshCw, Tag } from 'lucide-react';

interface KeywordEditorProps {
  keywords: string[];
  onKeywordsChange: (keywords: string[]) => void;
  productName?: string;
  category?: string;
  disabled?: boolean;
  maxKeywords?: number;
}

export default function KeywordEditor({
  keywords,
  onKeywordsChange,
  productName,
  category,
  disabled = false,
  maxKeywords = 40
}: KeywordEditorProps) {
  const [newKeyword, setNewKeyword] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingValue, setEditingValue] = useState('');

  // GPT로 키워드 생성 (Next.js API Route 사용)
  const generateKeywords = useCallback(async () => {
    if (!productName) {
      alert('상품명이 필요합니다.');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/generate-keywords', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: productName,
          category: category || undefined,
          count: 30
        })
      });

      const data = await response.json();

      if (data.success && data.keywords) {
        // 기존 키워드와 합치고 중복 제거
        const combined = [...keywords, ...data.keywords];
        const unique = [...new Set(combined)].slice(0, maxKeywords);
        onKeywordsChange(unique);
      } else {
        alert('키워드 생성에 실패했습니다: ' + (data.error || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('키워드 생성 실패:', error);
      alert('키워드 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  }, [productName, category, keywords, onKeywordsChange, maxKeywords]);

  // 키워드 추가
  const addKeyword = useCallback(() => {
    const trimmed = newKeyword.trim();
    if (!trimmed) return;

    if (keywords.length >= maxKeywords) {
      alert(`최대 ${maxKeywords}개까지만 추가할 수 있습니다.`);
      return;
    }

    if (keywords.includes(trimmed)) {
      alert('이미 존재하는 키워드입니다.');
      return;
    }

    onKeywordsChange([...keywords, trimmed]);
    setNewKeyword('');
  }, [newKeyword, keywords, onKeywordsChange, maxKeywords]);

  // 키워드 삭제
  const removeKeyword = useCallback((index: number) => {
    const updated = keywords.filter((_, i) => i !== index);
    onKeywordsChange(updated);
  }, [keywords, onKeywordsChange]);

  // 키워드 수정 시작
  const startEditing = useCallback((index: number) => {
    setEditingIndex(index);
    setEditingValue(keywords[index]);
  }, [keywords]);

  // 키워드 수정 완료
  const finishEditing = useCallback(() => {
    if (editingIndex === null) return;

    const trimmed = editingValue.trim();
    if (!trimmed) {
      // 빈 값이면 삭제
      removeKeyword(editingIndex);
    } else if (trimmed !== keywords[editingIndex]) {
      // 중복 체크
      if (keywords.some((k, i) => i !== editingIndex && k === trimmed)) {
        alert('이미 존재하는 키워드입니다.');
        return;
      }
      const updated = [...keywords];
      updated[editingIndex] = trimmed;
      onKeywordsChange(updated);
    }

    setEditingIndex(null);
    setEditingValue('');
  }, [editingIndex, editingValue, keywords, onKeywordsChange, removeKeyword]);

  // 전체 삭제
  const clearAll = useCallback(() => {
    if (window.confirm('모든 키워드를 삭제하시겠습니까?')) {
      onKeywordsChange([]);
    }
  }, [onKeywordsChange]);

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-bold text-blue-800">검색 키워드</h3>
          <span className="text-sm text-gray-600">({keywords.length}/{maxKeywords})</span>
        </div>
        <div className="flex items-center gap-2">
          {keywords.length > 0 && (
            <button
              type="button"
              onClick={clearAll}
              disabled={disabled}
              className="px-3 py-1.5 text-xs font-semibold text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              전체 삭제
            </button>
          )}
          <button
            type="button"
            onClick={generateKeywords}
            disabled={disabled || isGenerating || !productName}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-semibold hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
            {isGenerating ? 'AI 생성중...' : 'AI 키워드 생성'}
          </button>
        </div>
      </div>

      <p className="text-xs text-blue-600 mb-4 bg-white/70 rounded-lg p-2 border border-blue-200">
        상품 등록 시 오픈마켓 검색에 사용되는 키워드입니다. AI가 자동으로 생성하거나 직접 추가할 수 있습니다.
      </p>

      {/* 키워드 입력 */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newKeyword}
          onChange={(e) => setNewKeyword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addKeyword();
            }
          }}
          disabled={disabled || keywords.length >= maxKeywords}
          className="flex-1 px-4 py-2 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          placeholder="키워드를 입력하고 Enter 또는 추가 버튼을 클릭하세요"
        />
        <button
          type="button"
          onClick={addKeyword}
          disabled={disabled || !newKeyword.trim() || keywords.length >= maxKeywords}
          className="px-4 py-2 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          추가
        </button>
      </div>

      {/* 키워드 목록 */}
      {keywords.length > 0 ? (
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 bg-white rounded-lg border border-blue-200">
          {keywords.map((keyword, index) => (
            <div
              key={index}
              className="group flex items-center gap-1 bg-blue-100 hover:bg-blue-200 rounded-full px-3 py-1.5 transition-colors"
            >
              {editingIndex === index ? (
                <input
                  type="text"
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  onBlur={finishEditing}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      finishEditing();
                    } else if (e.key === 'Escape') {
                      setEditingIndex(null);
                      setEditingValue('');
                    }
                  }}
                  autoFocus
                  className="w-24 px-2 py-0.5 text-sm border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              ) : (
                <>
                  <span
                    onClick={() => !disabled && startEditing(index)}
                    className="text-sm text-blue-800 cursor-pointer hover:underline"
                    title="클릭하여 수정"
                  >
                    {keyword}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeKeyword(index)}
                    disabled={disabled}
                    className="ml-1 w-4 h-4 flex items-center justify-center text-blue-600 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                    title="삭제"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500 bg-white rounded-lg border border-blue-200">
          <Tag className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-sm">키워드가 없습니다.</p>
          <p className="text-xs mt-1">AI 키워드 생성 버튼을 클릭하거나 직접 입력하세요.</p>
        </div>
      )}
    </div>
  );
}
