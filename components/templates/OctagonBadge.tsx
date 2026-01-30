import EditableText from './EditableText';

interface OctagonBadgeProps {
  topText: string;
  bottomText: string;
  topField: string;
  bottomField: string;
  editingField: string | null;
  editingValue: string;
  onEdit: (field: string, value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onValueChange: (value: string) => void;
  onStyleClick?: (field: string) => void;
  textStyles?: Record<string, { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }>;
  className?: string;
}

export default function OctagonBadge({
  topText,
  bottomText,
  topField,
  bottomField,
  editingField,
  editingValue,
  onEdit,
  onSave,
  onCancel,
  onValueChange,
  onStyleClick,
  textStyles = {},
  className = 'w-40 h-40',
}: OctagonBadgeProps) {
  return (
    <div className={`relative ${className}`}>
      <div
        className="w-full h-full flex items-center justify-center shadow-lg"
        style={{
          background:
            'linear-gradient(135deg, rgb(224, 242, 254) 0%, rgb(243, 229, 245) 25%, rgb(255, 243, 224) 50%, rgb(232, 245, 232) 75%, rgb(224, 242, 254) 100%)',
          clipPath:
            'polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)',
          filter: 'drop-shadow(rgba(0, 0, 0, 0.2) 0px 4px 8px)',
        }}
      >
        <div className="text-center">
          <div className="text-4xl font-bold text-black">
            <EditableText
              field={topField}
              value={topText}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onEdit}
              onSave={onSave}
              onCancel={onCancel}
              onValueChange={onValueChange}
              onStyleClick={onStyleClick}
              textStyles={textStyles}
              style={{ fontSize: '36px', fontWeight: 'bold', color: '#000' }}
            />
          </div>
          <div className="text-lg font-medium text-black">
            <EditableText
              field={bottomField}
              value={bottomText}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onEdit}
              onSave={onSave}
              onCancel={onCancel}
              onValueChange={onValueChange}
              onStyleClick={onStyleClick}
              textStyles={textStyles}
              style={{ fontSize: '18px', fontWeight: '500', color: '#000' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
