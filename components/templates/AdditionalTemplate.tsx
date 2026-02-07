import { AlertCircle } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import { TemplateProps } from './TemplateProps';

export default function AdditionalTemplate(props: TemplateProps) {
  const { content, uploadedImages, editingField, editingValue, onImageUpload, onImageRefresh, onImageDrop, onTextEdit, onTextSave, onTextCancel, onValueChange, onImageClick, editingImage, imageStyleSettings, onImageDelete, onTextStyleClick, textStyles = {}, additionalImageSlots = 0, onAddImageSlot, onRemoveImageSlot, imageSizes = {}, onImageResize, imagePositions = {}, onImageMove } = props;

  return (
    <>
      {/* Hero Section - 배경 이미지 + 브랜드 + 제품명 */}
      <div className="w-full h-[800px] relative">
        <EditableImage
          imageKey="additional_template1_product"
          uploadedImages={uploadedImages}
          className="w-full h-full bg-cover"
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
        >
          <div className="absolute inset-0">
            {/* 좌상단 작은 브랜드명 */}
            <div className="absolute top-12 left-12">
              <p className="text-lg text-gray-600 font-medium">
                <EditableText
                  field="brandName"
                  value={content.brandName}
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

            {/* 중앙 큰 제품명 */}
            <div className="absolute top-1/2 left-12 -translate-y-1/2">
              <h1 className="text-7xl font-bold text-gray-800">
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
            </div>
          </div>
        </EditableImage>
      </div>

      {/* 면도의 새로운 기준 Section */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-5xl mx-auto">
          <p className="text-center text-xl text-gray-600 mb-4">
            <EditableText
              field="seasonTitle"
              value={content.seasonTitle}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
            />
          </p>
          <h2 className="text-5xl font-bold text-center text-gray-800 mb-12">
            <EditableText
              field="mainProductName"
              value={content.mainProductName}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
            />
          </h2>

          <div className="max-w-3xl mx-auto">
            <EditableImage
              imageKey="additional_template2_main"
              uploadedImages={uploadedImages}
              className="w-full h-[600px] rounded-2xl shadow-xl"
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
          </div>
        </div>
      </div>

      {/* Notice Section - 검정 배경 */}
      <div className="w-full bg-black text-white py-16 px-10 text-center">
        <h3 className="text-3xl font-bold mb-4">
          <EditableText
            field="noticeTitle"
            value={content.noticeTitle || 'Notice'}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
          />
        </h3>
        <p className="text-lg leading-relaxed max-w-4xl mx-auto">
          <EditableText
            field="noticeText"
            value={content.noticeText}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
          />
        </p>
      </div>

      {/* 제품명 + 이미지 Section */}
      <div className="w-full bg-white py-20 px-10 text-center">
        <h2 className="text-5xl font-bold text-gray-800 mb-12">
          <EditableText
            field="copywriting1"
            value={content.copywriting1}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
          />
        </h2>
        <div className="max-w-3xl mx-auto">
          <EditableImage
            imageKey="additional_template4_feature"
            uploadedImages={uploadedImages}
            className="w-full h-[600px] rounded-2xl shadow-xl"
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
        </div>
      </div>

      {/* 제품정보 Section */}
      <div className="w-full bg-white py-20 px-10 text-center">
        <h2 className="text-4xl font-bold text-gray-800 mb-12">
          <EditableText
            field="productInfoLabel"
            value={content.productInfoLabel || '제품정보'}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
          />
        </h2>
        <div className="max-w-4xl mx-auto">
          <EditableImage
            imageKey="additional_template4_product"
            uploadedImages={uploadedImages}
            className="w-full h-[500px] rounded-2xl shadow-lg"
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

          {/* 추가 이미지 슬롯 */}
          {Array.from({ length: additionalImageSlots }).map((_, index) => (
            <div key={index} className="relative mt-6">
              <EditableImage
                imageKey={`additional_product_image_${index}`}
                uploadedImages={uploadedImages}
                className="w-full h-[500px] rounded-2xl shadow-lg"
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
                isResizable={true}
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
          ))}

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

      {/* 주의사항 Section */}
      <div className="w-full bg-gray-100 py-16 px-10">
        <div className="max-w-3xl mx-auto">
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-xl p-8">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
              <h4 className="text-xl font-bold text-gray-800">
                <EditableText
                  field="cautionLabel"
                  value={content.cautionLabel || '주의사항'}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                />
              </h4>
            </div>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              <EditableText
                field="cautionContent"
                value={content.cautionContent || '상품 수량과 옵션을 꼭 확인해주세요.'}
                isTextarea
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
              />
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
