import { Upload, X, RefreshCw } from 'lucide-react';
import { ReactNode, useState, useRef, useEffect } from 'react';

interface EditableImageProps {
  imageKey: string;
  uploadedImages: Record<string, string>;
  className?: string;
  style?: React.CSSProperties;
  children?: ReactNode;
  onImageUpload?: (imageKey: string) => void;
  onImageRefresh?: (imageKey: string) => void;
  onImageClick?: (imageKey: string) => void;
  onImageDelete?: (imageKey: string) => void;
  onImageDrop?: (imageKey: string, file: File) => void;
  imageStyles?: Record<string, any>;
  imageStyleSettings?: Record<string, {
    shadow?: string;
    borderRadius?: string;
    borderWidth?: string;
    borderColor?: string;
    opacity?: number;
    brightness?: number;
    contrast?: number;
    saturate?: number;
  }>;
  editingImage?: string | null;
  imageSizes?: Record<string, number>;
  onImageResize?: (imageKey: string, size: number) => void;
  imagePositions?: Record<string, { x: number; y: number }>;
  onImageMove?: (imageKey: string, position: { x: number; y: number }) => void;
  imageAlignments?: Record<string, 'left' | 'center' | 'right'>;
  onImageAlignment?: (imageKey: string, alignment: 'left' | 'center' | 'right') => void;
  isResizable?: boolean; // 크기 조정 가능 여부
  fillContainer?: boolean; // 컨테이너 꽉 채우기
}

export default function EditableImage({
  imageKey,
  uploadedImages,
  className = '',
  style = {},
  children,
  onImageUpload,
  onImageRefresh,
  onImageClick,
  onImageDelete,
  onImageDrop,
  imageStyles = {},
  imageStyleSettings = {},
  editingImage,
  imageSizes = {},
  onImageResize,
  imagePositions = {},
  onImageMove,
  imageAlignments = {},
  onImageAlignment,
  isResizable = true, // 기본값: 크기 조정 가능
  fillContainer = false, // 기본값: 컨테이너 꽉 채우지 않음
}: EditableImageProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [showPasteToast, setShowPasteToast] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeCorner, setResizeCorner] = useState<'tl' | 'tr' | 'bl' | 'br' | null>(null);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, size: 100 });
  const containerRef = useRef<HTMLDivElement>(null);
  const imageUrl = uploadedImages[imageKey];
  const settings = imageStyleSettings[imageKey] || {};
  const isEditing = editingImage === imageKey;
  const imageSize = imageSizes[imageKey] || 100;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onImageClick) {
      onImageClick(imageKey);
    }
  };

  const handleUploadClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onImageUpload) {
      onImageUpload(imageKey);
    }
  };

  const handleRefreshClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onImageRefresh) {
      onImageRefresh(imageKey);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onImageDelete && window.confirm('이미지를 삭제하시겠습니까?')) {
      onImageDelete(imageKey);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        if (onImageDrop) {
          onImageDrop(imageKey, file);
        }
      } else {
        alert('이미지 파일만 업로드할 수 있습니다.');
      }
    }
  };

  // 클립보드 붙여넣기 핸들러
  const handlePaste = async (e: React.ClipboardEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const items = e.clipboardData.items;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const blob = items[i].getAsFile();
        if (blob && onImageDrop) {
          onImageDrop(imageKey, blob);
          // 붙여넣기 성공 알림
          setShowPasteToast(true);
          setTimeout(() => setShowPasteToast(false), 2000);
        }
        break;
      }
    }
  };

  // 컨테이너 클릭 핸들러 (포커스)
  const handleContainerClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    containerRef.current?.focus();
    setIsFocused(true);
    if (onImageClick) {
      onImageClick(imageKey);
    }
  };

  // 포커스 아웃 핸들러
  const handleBlur = () => {
    setIsFocused(false);
  };

  // 모서리 리사이징 시작
  const handleResizeStart = (corner: 'tl' | 'tr' | 'bl' | 'br', e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeCorner(corner);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      size: imageSize,
    });
  };

  // 리사이징 처리
  useEffect(() => {
    if (!isResizing || !resizeCorner) return;

    // 커서 스타일 설정
    const cursors = {
      tl: 'nwse-resize',
      tr: 'nesw-resize',
      bl: 'nesw-resize',
      br: 'nwse-resize',
    };
    document.body.style.cursor = cursors[resizeCorner];
    document.body.style.userSelect = 'none';

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;

      // 대각선 거리로 크기 계산
      let delta = 0;
      if (resizeCorner === 'br') {
        delta = (deltaX + deltaY) / 2;
      } else if (resizeCorner === 'tl') {
        delta = -(deltaX + deltaY) / 2;
      } else if (resizeCorner === 'tr') {
        delta = (deltaX - deltaY) / 2;
      } else if (resizeCorner === 'bl') {
        delta = (-deltaX + deltaY) / 2;
      }

      const scaleFactor = 0.3;
      const newSize = Math.max(50, Math.min(300, resizeStart.size + delta * scaleFactor));

      if (onImageResize) {
        onImageResize(imageKey, Math.round(newSize));
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      setResizeCorner(null);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, resizeCorner, resizeStart, imageKey, onImageResize]);

  // 컨테이너 스타일 - 가운데 정렬, 이미지가 컨테이너 안에 유지되도록 overflow: hidden
  const containerStyle: React.CSSProperties = {
    ...style,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',  // 이미지가 컨테이너를 벗어나지 않도록
  };

  const imageStyle: React.CSSProperties = {
    backgroundImage: imageUrl ? `url(${imageUrl})` : undefined,
    backgroundSize: fillContainer ? 'cover' : 'contain',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    boxShadow: settings.shadow || undefined,
    borderRadius: settings.borderRadius || undefined,
    borderWidth: settings.borderWidth || undefined,
    borderColor: settings.borderColor || undefined,
    borderStyle: settings.borderWidth ? 'solid' : undefined,
    opacity: settings.opacity !== undefined ? settings.opacity : 1,
    filter: `brightness(${settings.brightness || 1}) contrast(${settings.contrast || 1}) saturate(${settings.saturate || 1})`,
    // 크기 조정: 컨테이너 내에서 비율 적용 (최대 100%)
    width: '100%',
    height: '100%',
    // 이미지 크기 조정은 scale로 처리 (컨테이너 안에서 확대/축소)
    transform: isResizable && !fillContainer ? `scale(${imageSize / 100})` : undefined,
    transition: isResizing ? 'none' : 'all 0.15s ease-out',
    position: 'relative' as const,
  };

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      data-editable="true"
      className={`editable-container relative group ${className} ${isDragging ? 'ring-4 ring-blue-500 ring-opacity-50' : ''} ${isFocused || isResizing ? 'ring-2 ring-blue-400 ring-offset-2' : ''} outline-none transition-all`}
      style={containerStyle}
      onClick={handleContainerClick}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onPaste={handlePaste}
      onBlur={handleBlur}
      title={imageUrl ? "모서리 드래그하여 크기 조정" : "클릭 후 Ctrl+V로 붙여넣기"}
    >
      {/* 실제 이미지 영역 */}
      <div
        className="relative"
        style={imageStyle}
      >
        {children}

        {/* 이미지 편집 컨트롤 */}
        <div className={`absolute top-2 right-2 flex gap-2 ${isEditing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity z-10`}>
          {imageUrl && onImageDelete && (
            <button
              onClick={handleDeleteClick}
              className="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
              title="이미지 삭제"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {imageUrl && onImageRefresh && (
            <button
              onClick={handleRefreshClick}
              className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center hover:bg-green-600 transition-colors shadow-lg"
              title="이미지 새로고침"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          {onImageUpload && (
            <button
              onClick={handleUploadClick}
              className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors shadow-lg"
              title="이미지 업로드"
            >
              <Upload className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Figma 스타일 4개 모서리 핸들 - 크기 조정 가능할 때만 표시 */}
        {imageUrl && onImageResize && isResizable && (
          <>
            {/* 좌상단 핸들 */}
            <div
              onMouseDown={(e) => handleResizeStart('tl', e)}
              className={`resize-handle absolute -top-1 -left-1 w-3 h-3 bg-white border-2 border-blue-500 cursor-nwse-resize shadow-md hover:scale-125 transition-all z-20 ${isEditing || isFocused || isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
              title="좌상단 모서리 드래그"
            />

            {/* 우상단 핸들 */}
            <div
              onMouseDown={(e) => handleResizeStart('tr', e)}
              className={`resize-handle absolute -top-1 -right-1 w-3 h-3 bg-white border-2 border-blue-500 cursor-nesw-resize shadow-md hover:scale-125 transition-all z-20 ${isEditing || isFocused || isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
              title="우상단 모서리 드래그"
            />

            {/* 좌하단 핸들 */}
            <div
              onMouseDown={(e) => handleResizeStart('bl', e)}
              className={`resize-handle absolute -bottom-1 -left-1 w-3 h-3 bg-white border-2 border-blue-500 cursor-nesw-resize shadow-md hover:scale-125 transition-all z-20 ${isEditing || isFocused || isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
              title="좌하단 모서리 드래그"
            />

            {/* 우하단 핸들 */}
            <div
              onMouseDown={(e) => handleResizeStart('br', e)}
              className={`resize-handle absolute -bottom-1 -right-1 w-3 h-3 bg-white border-2 border-blue-500 cursor-nwse-resize shadow-md hover:scale-125 transition-all z-20 ${isEditing || isFocused || isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
              title="우하단 모서리 드래그"
            />

            {/* 크기 표시 */}
            <div className={`absolute top-2 left-2 bg-black/80 backdrop-blur-sm rounded-lg px-3 py-1.5 shadow-lg ${isResizing ? 'opacity-100' : 'opacity-0'} transition-opacity z-10 pointer-events-none`}>
              <span className="text-white text-xs font-bold">
                {imageSize}%
              </span>
            </div>

            {/* 편집 중 오버레이 */}
            {isResizing && (
              <div className="absolute inset-0 border-2 border-blue-500 rounded pointer-events-none z-20">
                <div className="absolute inset-0 bg-blue-500/10"></div>
              </div>
            )}
          </>
        )}

        {/* 이미지가 없을 때 플레이스홀더 */}
        {!imageUrl && (
          <div className={`absolute inset-0 flex flex-col items-center justify-center bg-gray-100 border-2 border-dashed ${isDragging ? 'border-blue-500 bg-blue-50' : isFocused ? 'border-blue-400 bg-blue-50' : 'border-gray-300'} rounded transition-colors`}>
            <Upload className={`w-12 h-12 mb-3 ${isDragging || isFocused ? 'text-blue-500' : 'text-gray-400'}`} />
            <p className={`text-sm font-semibold mb-2 ${isDragging || isFocused ? 'text-blue-600' : 'text-gray-500'}`}>
              {isDragging ? '여기에 놓으세요' : '이미지를 업로드하세요'}
            </p>
            {!isDragging && (
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">클릭 후 <kbd className="px-2 py-1 bg-gray-200 rounded text-xs font-mono">Ctrl+V</kbd>로 붙여넣기</p>
                <p className="text-xs text-gray-400">또는 드래그앤드롭</p>
              </div>
            )}
          </div>
        )}

        {/* 드래그 중 오버레이 (이미지가 있을 때) */}
        {isDragging && imageUrl && (
          <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center rounded pointer-events-none">
            <div className="bg-blue-500 text-white px-4 py-2 rounded-lg font-semibold">
              여기에 놓으세요
            </div>
          </div>
        )}

        {/* 편집 중 표시 */}
        {isEditing && (
          <div className="absolute inset-0 border-4 border-blue-500 rounded pointer-events-none">
            <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
              편집 중
            </div>
          </div>
        )}

        {/* 붙여넣기 성공 토스트 */}
        {showPasteToast && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-2xl font-semibold z-50 animate-bounce">
            ✓ 이미지가 붙여넣기 되었습니다!
          </div>
        )}
      </div>
    </div>
  );
}
