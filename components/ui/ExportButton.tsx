'use client';

import { Download } from 'lucide-react';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';

interface ExportButtonProps {
  data: any[];
  filename: string;
  sheetName?: string;
  buttonText?: string;
  className?: string;
}

export default function ExportButton({
  data,
  filename,
  sheetName = '데이터',
  buttonText = '엑셀 내보내기',
  className = '',
}: ExportButtonProps) {
  const handleExport = () => {
    try {
      if (!data || data.length === 0) {
        toast.warning('내보낼 데이터가 없습니다.');
        return;
      }

      // 엑셀 워크북 생성
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, sheetName);

      // 현재 날짜를 파일명에 추가
      const date = new Date().toISOString().split('T')[0];
      const fullFilename = `${filename}_${date}.xlsx`;

      // 파일 다운로드
      XLSX.writeFile(wb, fullFilename);

      toast.success(`${fullFilename} 파일이 다운로드되었습니다.`);
    } catch (error) {
      console.error('엑셀 내보내기 실패:', error);
      toast.error('엑셀 내보내기에 실패했습니다.');
    }
  };

  return (
    <button
      onClick={handleExport}
      className={`px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300 flex items-center gap-2 ${className}`}
    >
      <Download className="w-4 h-4" />
      {buttonText}
    </button>
  );
}
