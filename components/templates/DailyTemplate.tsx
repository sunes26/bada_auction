import { Star, Check, AlertCircle, Trash2 } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import { TemplateProps } from './TemplateProps';

// 섹션 삭제 버튼 컴포넌트
function SectionDeleteButton({ sectionKey, onSectionDelete }: { sectionKey: string; onSectionDelete?: (key: string) => void }) {
  if (!onSectionDelete) return null;
  return (
    <button
      onClick={() => onSectionDelete(sectionKey)}
      className="absolute top-2 right-2 w-10 h-10 bg-red-500/80 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-colors shadow-lg z-20"
      title="섹션 삭제"
    >
      <Trash2 className="w-5 h-5" />
    </button>
  );
}

export default function DailyTemplate(props: TemplateProps) {
  const {
    content,
    uploadedImages,
    editingField,
    editingValue,
    onImageUpload,
    onImageRefresh,
    onImageDrop,
    onTextEdit,
    onTextSave,
    onTextCancel,
    onValueChange,
    onImageClick,
    editingImage,
    imageStyleSettings,
    onImageDelete,
    onTextStyleClick,
    textStyles = {},
    additionalImageSlots = 0,
    onAddImageSlot,
    onRemoveImageSlot,
    imageSizes = {},
    onImageResize,
    imagePositions = {},
    onImageMove,
    imageAlignments = {},
    onImageAlignment,
    containerWidths = {},
    onContainerWidthChange,
    hiddenSections = {},
    onSectionDelete,
  } = props;
  return (
    <>
      {/* Hero Section */}
      {!hiddenSections['hero'] && (
      <div className="w-full h-[1200px] relative">
        <SectionDeleteButton sectionKey="hero" onSectionDelete={onSectionDelete} />
        <EditableImage
          imageKey="template1_bg"
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
            {/* 제품명 영역 */}
            <div className="absolute top-32 left-1/2 -translate-x-1/2 text-center w-full px-4 z-10">
              <p className="text-2xl font-medium text-white drop-shadow-lg">
                <EditableText
                  field="mainCopy1"
                  value={content.mainCopy1}
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
              <h2 className="text-7xl font-extrabold text-cyan-400 mt-2 drop-shadow-lg">
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
              </h2>
            </div>

            {/* 3 Hooking Points - Hero 하단 내부 */}
            <div className="absolute bottom-0 left-0 right-0 grid grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className={`flex flex-col items-center justify-center p-6 ${i < 3 ? 'border-r border-white/30' : ''}`}
                >
                  <Check className="w-8 h-8 text-white mb-2" />
                  <p className="text-lg font-semibold text-white">
                    <EditableText
                      field={`hooking${i}`}
                      value={content[`hooking${i}`]}
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
              ))}
            </div>
          </div>
        </EditableImage>
      </div>
      )}

      {/* Product Info Section */}
      {!hiddenSections['productInfo'] && (
      <div className="w-full bg-[#f0f0f0] py-20 px-10 text-center relative">
        <SectionDeleteButton sectionKey="productInfo" onSectionDelete={onSectionDelete} />
        <h3 className="text-4xl font-bold text-gray-800">
          <EditableText
            field="hookingTitle2"
            value={content.hookingTitle2}
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
        <p className="text-lg text-gray-600 mt-4 mb-8">
          <EditableText
            field="hookingSentence"
            value={content.hookingSentence}
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

        {/* Tags */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="px-5 py-2 border border-gray-400 rounded-full">
              <span className="text-lg font-medium">
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
            </div>
          ))}
        </div>

        {/* Product Images */}
        <div className="relative w-[600px] h-[600px] mx-auto">
          <EditableImage
            imageKey="template2_main"
            uploadedImages={uploadedImages}
            className="w-full h-full rounded-2xl"
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
          <div className="absolute -bottom-10 -right-10 w-64 h-64">
            <EditableImage
              imageKey="template2_sub"
              uploadedImages={uploadedImages}
              className="w-full h-full rounded-full shadow-lg bg-cover"
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
      )}

      {/* Customer Reviews Section */}
      {!hiddenSections['reviews'] && (
      <div className="w-full bg-black text-white py-20 px-10 text-center relative">
        <SectionDeleteButton sectionKey="reviews" onSectionDelete={onSectionDelete} />
        <h2 className="text-4xl font-bold">
          <EditableText
            field="reviewSectionTitle"
            value={content.reviewSectionTitle || '믿고쓰는 생필품!'}
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
        </h2>
        <p className="text-xl text-gray-400 mt-2 mb-8">
          <EditableText
            field="reviewSectionSubtitle"
            value={content.reviewSectionSubtitle || '추천할 수 밖에 없는 이유!'}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
            onStyleClick={onTextStyleClick}
            textStyles={textStyles}
            className="text-gray-400"
          />
        </p>

        <div className="inline-block px-8 py-4 mb-12 border-2 border-white rounded-lg">
          <div className="flex justify-center">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star key={i} className="w-6 h-6 fill-yellow-400 text-yellow-400" />
            ))}
          </div>
          <p className="font-bold mt-1 text-white">
            <EditableText
              field="satisfactionLabel"
              value={content.satisfactionLabel || '고객만족도'}
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
          </p>
        </div>

        <div className="space-y-6 max-w-2xl mx-auto">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-800 rounded-lg p-8 text-left relative">
              <div className="flex mb-3">
                {[1, 2, 3, 4, 5].map((j) => (
                  <Star key={j} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-xl leading-relaxed">
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
                  className="text-white"
                />
              </p>
              <p className="text-right text-gray-500 mt-6">
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
          ))}
        </div>
      </div>
      )}

      {/* Product Details Section */}
      {!hiddenSections['productDetails'] && (
      <div className="w-full bg-white pt-20 text-center relative">
        <SectionDeleteButton sectionKey="productDetails" onSectionDelete={onSectionDelete} />
        <h3 className="text-4xl font-bold text-cyan-400">
          <EditableText
            field="hookingTitle3"
            value={content.hookingTitle3}
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
        <p className="text-lg text-gray-600 mt-4 mb-8">
          <EditableText
            field="hookingSentence3"
            value={content.hookingSentence3}
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
        <EditableImage
          imageKey="template4_bg"
          uploadedImages={uploadedImages}
          className="w-full h-[600px]"
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
      )}

      {/* Product Guide Section */}
      {!hiddenSections['productGuide'] && (
      <div className="w-full bg-white py-20 px-10 text-center relative">
        <SectionDeleteButton sectionKey="productGuide" onSectionDelete={onSectionDelete} />
        <div className="inline-block bg-black text-white px-8 py-3 rounded-full font-bold text-xl mb-12">
          <EditableText
            field="productGuideLabel"
            value={content.productGuideLabel || '상품안내'}
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

        <div className="max-w-2xl mx-auto space-y-12">
          {[1, 2, 3, 4].map((i) => (
            <div key={i}>
              <EditableImage
                imageKey={`template5_pt${i}`}
                uploadedImages={uploadedImages}
                className="w-full aspect-square rounded-lg bg-contain bg-no-repeat"
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
              <div className="mt-6 text-center">
                <p className="font-medium text-xl">
                  <EditableText
                    field={`point${i}Description`}
                    value={content[`point${i}Description`]}
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
          ))}
        </div>
      </div>
      )}

      {/* Caution Section */}
      {!hiddenSections['caution'] && (
      <div className="w-full bg-white py-20 px-10 text-center relative">
        <SectionDeleteButton sectionKey="caution" onSectionDelete={onSectionDelete} />
        <div className="inline-block bg-black text-white px-8 py-3 rounded-full font-bold text-xl mb-12">
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
        </div>

        <div className="max-w-3xl mx-auto">
          <EditableImage
            imageKey="template6_bg"
            uploadedImages={uploadedImages}
            className="w-full h-[600px] rounded-lg bg-contain bg-no-repeat"
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
          {Array.from({ length: additionalImageSlots }).map((_, index) => {
            const imageKey = `additional_product_image_${index}`;
            return (
              <div key={index} className="relative mt-6 flex justify-center">
                <EditableImage
                  imageKey={imageKey}
                  uploadedImages={uploadedImages}
                  className="rounded-lg"
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

          <div className="max-w-3xl mx-auto mt-8 bg-white p-8 rounded-lg">
            <div className="flex items-center justify-center gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-yellow-500" />
              <h4 className="text-xl font-bold">
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
              </h4>
            </div>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              <EditableText
                field="cautions"
                value={content.cautions}
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
      )}
    </>
  );
}
