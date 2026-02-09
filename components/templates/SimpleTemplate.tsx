import { AlertCircle } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import { TemplateProps } from './TemplateProps';

export default function SimpleTemplate(props: TemplateProps) {
  const { content, uploadedImages, editingField, editingValue, onImageUpload, onImageRefresh, onImageDrop, onTextEdit, onTextSave, onTextCancel, onValueChange, onImageClick, editingImage, imageStyleSettings, onImageDelete, onTextStyleClick, textStyles = {}, additionalImageSlots = 0, onAddImageSlot, onRemoveImageSlot, imageSizes = {}, onImageResize, imagePositions = {}, onImageMove, imageAlignments = {}, onImageAlignment, containerWidths = {}, onContainerWidthChange } = props;

  return (
    <>
      {/* Hero Section - Simple and Clean */}
      <div className="w-full bg-white py-16 px-10 text-center">
        <h1 className="text-6xl font-bold text-gray-800 mb-8">
          <EditableText
            field="productName"
            value={content.productName}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
            onStyleClick={onTextStyleClick}
            textStyles={textStyles}
          />
        </h1>
        <p className="text-3xl text-gray-600 font-light">
          <EditableText
            field="copywriting"
            value={content.copywriting}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
            onStyleClick={onTextStyleClick}
            textStyles={textStyles}
          />
        </p>
      </div>

      {/* Main Product Image */}
      <div className="w-full px-10">
        <div className="max-w-5xl mx-auto">
          <EditableImage
            imageKey="simple_main_image"
            uploadedImages={uploadedImages}
            className="w-full h-[700px] rounded-3xl shadow-2xl"
            onImageUpload={onImageUpload}
            onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop}
            onImageClick={onImageClick}
            editingImage={editingImage}
            imageStyleSettings={imageStyleSettings}
            onImageDelete={onImageDelete}
            imageSizes={imageSizes}
            onImageResize={onImageResize}
            imagePositions={imagePositions}
            onImageMove={onImageMove}
            imageAlignments={imageAlignments}
            onImageAlignment={onImageAlignment}
            fillContainer={true}
            isResizable={false}
          />
        </div>
      </div>

      {/* Product Information Section - 상품정보 */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-800 mb-12 text-center">
            <EditableText
              field="productInfoLabel"
              value={content.productInfoLabel || '상품정보'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
            />
          </h2>

          {/* 10개 이미지 그리드 */}
          <div className="grid grid-cols-2 gap-8">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
              <EditableImage
                key={i}
                imageKey={`simple_product_info_${i}`}
                uploadedImages={uploadedImages}
                className="w-full h-[400px] rounded-xl shadow-lg"
                onImageUpload={onImageUpload}
                onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop}
                onImageClick={onImageClick}
                editingImage={editingImage}
                imageStyleSettings={imageStyleSettings}
                onImageDelete={onImageDelete}
                imageSizes={imageSizes}
                onImageResize={onImageResize}
                imagePositions={imagePositions}
                onImageMove={onImageMove}
                fillContainer={true}
                isResizable={false}
              />
            ))}
          </div>

          {/* 추가 이미지 슬롯 */}
          {Array.from({ length: additionalImageSlots }).map((_, index) => {
            const imageKey = `additional_product_image_${index}`;
            return (
              <div key={index} className="relative mt-6 flex justify-center">
                <EditableImage
                  imageKey={imageKey}
                  uploadedImages={uploadedImages}
                  className="rounded-lg shadow-xl"
                  onImageUpload={onImageUpload}
                  onImageRefresh={onImageRefresh}
                  onImageDrop={onImageDrop}
                  onImageClick={onImageClick}
                  editingImage={editingImage}
                  imageStyleSettings={imageStyleSettings}
                  onImageDelete={onImageDelete}
                  imageSizes={imageSizes}
                  onImageResize={onImageResize}
                  imagePositions={imagePositions}
                  onImageMove={onImageMove}
                  fillContainer={false}
                  isResizable={false}
                  autoFitHeight={true}
                  containerWidth={containerWidths[imageKey] || 100}
                  onContainerWidthChange={onContainerWidthChange}
                />
                {onRemoveImageSlot && (
                  <button
                    onClick={() => onRemoveImageSlot(index)}
                    className="absolute top-2 left-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg z-10"
                    title="이미지 슬롯 삭제"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}

          {/* + 버튼 */}
          {onAddImageSlot && (
            <div className="flex justify-center mt-6">
              <button
                onClick={onAddImageSlot}
                className="w-16 h-16 bg-gray-200 hover:bg-gray-300 rounded-full flex items-center justify-center text-gray-600 hover:text-gray-800 transition-colors shadow-md"
                title="이미지 추가"
              >
                <span className="text-4xl font-light">+</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Caution Section */}
      <div className="w-full bg-gray-50 py-20 px-10">
        <div className="max-w-4xl mx-auto">
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-2xl p-10">
            <div className="flex items-center gap-3 mb-6">
              <AlertCircle className="w-8 h-8 text-yellow-600" />
              <h3 className="text-3xl font-bold text-gray-800">
                <EditableText
                  field="cautionLabel"
                  value={content.cautionLabel || '주의사항'}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                  onStyleClick={onTextStyleClick}
                  textStyles={textStyles}
                />
              </h3>
            </div>
            <p className="text-lg text-gray-700 leading-relaxed whitespace-pre-wrap">
              <EditableText
                field="cautionContent"
                value={content.cautionContent}
                isTextarea
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
              />
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
