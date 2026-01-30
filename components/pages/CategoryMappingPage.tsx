"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface CategoryMapping {
  id: number;
  level1: string;
  info_code: string;
  info_code_name: string;
  notes?: string;
}

interface InfoCode {
  code: string;
  name: string;
  description: string;
}

export default function CategoryMappingPage() {
  const [mappings, setMappings] = useState<CategoryMapping[]>([]);
  const [availableInfoCodes, setAvailableInfoCodes] = useState<InfoCode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 편집/추가 모드
  const [editMode, setEditMode] = useState<'none' | 'add' | 'edit'>('none');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    level1: '',
    info_code: '',
    info_code_name: '',
    notes: ''
  });

  // 데이터 로드
  useEffect(() => {
    loadMappings();
    loadAvailableInfoCodes();
  }, []);

  const loadMappings = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/category-infocode-mappings');
      if (!response.ok) throw new Error('매핑 조회 실패');
      const data = await response.json();
      setMappings(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableInfoCodes = async () => {
    try {
      const response = await fetch('http://localhost:8000/available-infocodes');
      if (!response.ok) throw new Error('infoCode 목록 조회 실패');
      const data = await response.json();
      setAvailableInfoCodes(data);
    } catch (err: any) {
      console.error('infoCode 목록 조회 실패:', err);
    }
  };

  const handleAdd = () => {
    setEditMode('add');
    setFormData({ level1: '', info_code: '', info_code_name: '', notes: '' });
  };

  const handleEdit = (mapping: CategoryMapping) => {
    setEditMode('edit');
    setEditingId(mapping.id);
    setFormData({
      level1: mapping.level1,
      info_code: mapping.info_code,
      info_code_name: mapping.info_code_name,
      notes: mapping.notes || ''
    });
  };

  const handleCancel = () => {
    setEditMode('none');
    setEditingId(null);
    setFormData({ level1: '', info_code: '', info_code_name: '', notes: '' });
  };

  const handleSave = async () => {
    try {
      setLoading(true);

      if (editMode === 'add') {
        // 추가
        const response = await fetch('http://localhost:8000/category-infocode-mappings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || '추가 실패');
        }
      } else if (editMode === 'edit' && editingId) {
        // 수정
        const response = await fetch(`http://localhost:8000/category-infocode-mappings/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            info_code: formData.info_code,
            info_code_name: formData.info_code_name,
            notes: formData.notes
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || '수정 실패');
        }
      }

      await loadMappings();
      handleCancel();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, level1: string) => {
    if (!confirm(`'${level1}' 매핑을 삭제하시겠습니까?`)) return;

    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/category-infocode-mappings/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '삭제 실패');
      }

      await loadMappings();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInfoCodeChange = (code: string) => {
    const selected = availableInfoCodes.find(ic => ic.code === code);
    setFormData({
      ...formData,
      info_code: code,
      info_code_name: selected?.name || ''
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>카테고리 - infoCode 매핑 관리</CardTitle>
            {editMode === 'none' && (
              <Button onClick={handleAdd}>새 매핑 추가</Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* 추가/수정 폼 */}
          {editMode !== 'none' && (
            <div className="bg-gray-50 p-4 rounded-lg mb-6 space-y-4">
              <h3 className="text-lg font-semibold">
                {editMode === 'add' ? '새 매핑 추가' : '매핑 수정'}
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="level1">카테고리 (level1)</Label>
                  <Input
                    id="level1"
                    value={formData.level1}
                    onChange={(e) => setFormData({ ...formData, level1: e.target.value })}
                    disabled={editMode === 'edit'}
                    placeholder="예: 간편식"
                  />
                </div>

                <div>
                  <Label htmlFor="info_code">infoCode</Label>
                  <select
                    id="info_code"
                    value={formData.info_code}
                    onChange={(e) => handleInfoCodeChange(e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="">선택하세요</option>
                    {availableInfoCodes.map(ic => (
                      <option key={ic.code} value={ic.code}>
                        {ic.code} - {ic.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <Label htmlFor="info_code_name">infoCode 이름</Label>
                  <Input
                    id="info_code_name"
                    value={formData.info_code_name}
                    onChange={(e) => setFormData({ ...formData, info_code_name: e.target.value })}
                    placeholder="예: 가공식품"
                  />
                </div>

                <div>
                  <Label htmlFor="notes">메모</Label>
                  <Input
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="예: 즉석밥, 죽, 국/탕/찌개 등"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleSave} disabled={loading}>
                  {loading ? '저장 중...' : '저장'}
                </Button>
                <Button variant="outline" onClick={handleCancel}>
                  취소
                </Button>
              </div>
            </div>
          )}

          {/* 매핑 테이블 */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-4 py-2 text-left">카테고리 (level1)</th>
                  <th className="border px-4 py-2 text-left">infoCode</th>
                  <th className="border px-4 py-2 text-left">infoCode 이름</th>
                  <th className="border px-4 py-2 text-left">메모</th>
                  <th className="border px-4 py-2 text-center">작업</th>
                </tr>
              </thead>
              <tbody>
                {loading && mappings.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="border px-4 py-8 text-center text-gray-500">
                      로딩 중...
                    </td>
                  </tr>
                ) : mappings.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="border px-4 py-8 text-center text-gray-500">
                      등록된 매핑이 없습니다
                    </td>
                  </tr>
                ) : (
                  mappings.map((mapping) => (
                    <tr key={mapping.id} className="hover:bg-gray-50">
                      <td className="border px-4 py-2 font-medium">{mapping.level1}</td>
                      <td className="border px-4 py-2 text-sm font-mono">{mapping.info_code}</td>
                      <td className="border px-4 py-2">{mapping.info_code_name}</td>
                      <td className="border px-4 py-2 text-sm text-gray-600">{mapping.notes || '-'}</td>
                      <td className="border px-4 py-2 text-center">
                        <div className="flex gap-2 justify-center">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(mapping)}
                            disabled={editMode !== 'none'}
                          >
                            수정
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDelete(mapping.id, mapping.level1)}
                            disabled={editMode !== 'none'}
                            className="text-red-600 hover:text-red-700"
                          >
                            삭제
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            총 {mappings.length}개 매핑
          </div>
        </CardContent>
      </Card>

      {/* infoCode 설명 카드 */}
      <Card>
        <CardHeader>
          <CardTitle>사용 가능한 infoCode 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {availableInfoCodes.map((ic) => (
              <div key={ic.code} className="border rounded p-3 bg-gray-50">
                <div className="font-mono text-sm text-blue-600">{ic.code}</div>
                <div className="font-semibold mt-1">{ic.name}</div>
                <div className="text-xs text-gray-600 mt-1">{ic.description}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
