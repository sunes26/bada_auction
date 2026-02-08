import { Star } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import OctagonBadge from './OctagonBadge';
import { TemplateProps } from './TemplateProps';

export default function FoodTemplate(props: TemplateProps) {
  const { content, uploadedImages, editingField, editingValue, onImageUpload, onImageRefresh, onImageDrop, onTextEdit, onTextSave, onTextCancel, onValueChange, onImageClick, editingImage, imageStyleSettings, onImageDelete, onTextStyleClick, textStyles = {}, additionalImageSlots = 0, onAddImageSlot, onRemoveImageSlot, imageSizes = {}, onImageResize, imagePositions = {}, onImageMove, imageAlignments = {}, onImageAlignment } = props;

  return (
    <>
      {/* Hero Section */}
      <div className="w-full h-[1200px] relative">
        <EditableImage
          imageKey="food_template1_bg"
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
          imageAlignments={imageAlignments}
          onImageAlignment={onImageAlignment}
          fillContainer={true}
          isResizable={false}
        >
          <div className="absolute inset-0">
            <div className="absolute top-48 left-1/2 -translate-x-1/2 text-center w-full px-4">
              {/* 파란 배지 */}
              <div className="inline-block bg-blue-600 text-white px-6 py-2 rounded-full font-bold text-lg mb-4 shadow-lg">
                <EditableText
                  field="subtitle"
                  value={content.subtitle}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                  onStyleClick={onTextStyleClick}
                  textStyles={textStyles}
                />
              </div>
              {/* 제품명 */}
              <h1 className="text-6xl font-extrabold text-white drop-shadow-2xl">
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

            {/* 100% 정품 배지 - 우하단 */}
            <div className="absolute bottom-10 right-10">
              <OctagonBadge
                topText={content.badgeTop || '100%'}
                bottomText={content.badgeBottom || '정품'}
                topField="badgeTop"
                bottomField="badgeBottom"
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
              />
            </div>
          </div>
        </EditableImage>
      </div>

      {/* Dark Blue Section - 맛과 영양을 모두 갖춘 */}
      <div className="w-full text-white py-16 px-10 text-center" style={{ backgroundColor: 'rgb(39, 57, 93)' }}>
        <h2 className="text-4xl font-bold mb-8 drop-shadow-lg">
          <EditableText
            field="coreMessage1"
            value={content.coreMessage1}
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

        {/* 원형 이미지 */}
        <div className="max-w-md mx-auto mb-8">
          <EditableImage
            imageKey="food_template2_main"
            uploadedImages={uploadedImages}
            className="w-full aspect-square rounded-full shadow-2xl"
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

        {/* Tags */}
        <div className="flex justify-center gap-6">
          {[1, 2, 3].map((i) => (
            <span key={i} className="text-xl font-semibold">
              <EditableText
                field={`tag${i}`}
                value={content[`tag${i}`]}
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
              />
            </span>
          ))}
        </div>
      </div>

      {/* Blue Review Section - 실제 구매자들의 BEST REVIEW */}
      <div className="w-full bg-blue-600 text-white py-20 px-10">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold mb-2">
            <EditableText
              field="reviewSectionTitle"
              value={content.reviewSectionTitle || '실제 구매자들의'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
              className="text-white"
            />
          </h3>
          <h2 className="text-5xl font-bold text-yellow-400">
            <EditableText
              field="reviewSectionSubtitle"
              value={content.reviewSectionSubtitle || 'BEST REVIEW'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
              className="text-yellow-400"
            />
          </h2>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg p-6 shadow-lg flex gap-4">
              {/* 후기 이미지 */}
              <div className="flex-shrink-0">
                <EditableImage
                  imageKey={`food_review${i}`}
                  uploadedImages={uploadedImages}
                  className="w-24 h-24 rounded-lg"
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

              {/* 후기 내용 */}
              <div className="flex-1">
                <div className="flex mb-2">
                  {[1, 2, 3, 4, 5].map((j) => (
                    <Star key={j} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <div className="text-base leading-relaxed mb-3 text-gray-800">
                  <EditableText
                    field={`review${i}`}
                    value={content[`review${i}`]}
                    isTextarea
                    editingField={editingField}
                    editingValue={editingValue}
                    onEdit={onTextEdit}
                    onSave={onTextSave}
                    onCancel={onTextCancel}
                    onValueChange={onValueChange}
                    onStyleClick={onTextStyleClick}
                    textStyles={textStyles}
                    className="text-gray-800"
                  />
                </div>
                <p className="text-sm text-gray-500 text-right">
                  <EditableText
                    field={`reviewer${i}Name`}
                    value={content[`reviewer${i}Name`] || ['ksdfda****', 'Wah5dr****', 'Qhd3gh****'][i - 1]}
                    editingField={editingField}
                    editingValue={editingValue}
                    onEdit={onTextEdit}
                    onSave={onTextSave}
                    onCancel={onTextCancel}
                    onValueChange={onValueChange}
                    onStyleClick={onTextStyleClick}
                    textStyles={textStyles}
                    className="text-gray-500"
                  />님
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Product Image Section - 상품 정보 */}
      <div className="w-full bg-white py-20 px-10 text-center">
        <div className="max-w-3xl mx-auto">
          {/* 상품 정보 배지 */}
          <div className="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold text-xl mb-8 shadow-lg">
            <EditableText
              field="productInfoLabel"
              value={content.productInfoLabel || '상품 정보'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
            />
          </div>

          {/* 제품 이미지 */}
          <EditableImage
            imageKey="food_product_image"
            uploadedImages={uploadedImages}
            className="w-full h-[500px] rounded-lg shadow-xl"
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
                className="w-full h-[500px] rounded-lg shadow-xl"
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

      {/* Caution Section - 주의사항 */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-3xl mx-auto">
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-xl p-8 shadow-md text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
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
