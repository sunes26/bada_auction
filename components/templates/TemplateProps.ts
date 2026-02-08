export interface TemplateProps {
  content: any;
  uploadedImages: Record<string, string>;
  editingField: string | null;
  editingValue: string;
  onImageUpload: (imageKey: string) => void;
  onImageRefresh?: (imageKey: string) => void;
  onImageDrop?: (imageKey: string, file: File) => void;
  onTextEdit: (field: string, value: string) => void;
  onTextSave: () => void;
  onTextCancel: () => void;
  onValueChange: (value: string) => void;
  onImageClick?: (imageKey: string) => void;
  editingImage?: string | null;
  imageStyleSettings?: Record<string, any>;
  onImageDelete?: (imageKey: string) => void;
  onTextStyleClick?: (field: string) => void;
  textStyles?: Record<string, { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }>;
  additionalImageSlots?: number;
  onAddImageSlot?: () => void;
  onRemoveImageSlot?: (index: number) => void;
  imageSizes?: Record<string, number>;
  onImageResize?: (imageKey: string, size: number) => void;
  imagePositions?: Record<string, { x: number; y: number }>;
  onImageMove?: (imageKey: string, position: { x: number; y: number }) => void;
  imageAlignments?: Record<string, 'left' | 'center' | 'right'>;
  onImageAlignment?: (imageKey: string, alignment: 'left' | 'center' | 'right') => void;
}
