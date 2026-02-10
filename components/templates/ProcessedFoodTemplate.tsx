import { Carrot, Clock, ThumbsUp, Flame, Trash2 } from 'lucide-react';
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

export default function ProcessedFoodTemplate(props: TemplateProps) {
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
      {/* Intro Section */}
      {!hiddenSections['intro'] && (
        <section className="w-full py-16 px-8 text-center bg-white relative">
          <SectionDeleteButton sectionKey="intro" onSectionDelete={onSectionDelete} />
          <p className="text-orange-600 font-bold tracking-widest mb-4 text-sm">
            <EditableText
              field="introSubtitle"
              value={content.introSubtitle || 'PREMIUM RECIPE'}
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
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-6 leading-tight">
            <EditableText
              field="introTitle"
              value={content.introTitle || '집에서 즐기는\n완벽한 한 끼'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
              isTextarea
            />
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            <EditableText
              field="introDescription"
              value={content.introDescription || '엄선된 재료와 쉐프의 비법 레시피로 완성했습니다.\n복잡한 준비 없이, 데우기만 하면 근사한 요리가 됩니다.'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
              isTextarea
            />
          </p>
          <div className="rounded-2xl overflow-hidden shadow-2xl max-w-4xl mx-auto bg-gray-100">
            <EditableImage
              imageKey="intro_main"
              uploadedImages={uploadedImages}
              className="w-full h-[500px]"
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
            />
          </div>
        </section>
      )}

      {/* Feature 1: 재료/품질 강조 */}
      {!hiddenSections['feature1'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature1" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
            <div className="w-full md:w-1/2 rounded-2xl overflow-hidden shadow-lg aspect-[4/3] bg-gray-100">
              <EditableImage
                imageKey="feature1_image"
                uploadedImages={uploadedImages}
                className="w-full h-full"
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
              />
            </div>
            <div className="w-full md:w-1/2 space-y-6">
              <div className="w-12 h-12 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-xl mb-2">
                <Carrot className="w-6 h-6" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">
                <EditableText
                  field="feature1Title"
                  value={content.feature1Title || '타협하지 않는\n신선한 원재료'}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                  onStyleClick={onTextStyleClick}
                  textStyles={textStyles}
                  isTextarea
                />
              </h3>
              <p className="text-gray-600 leading-relaxed text-lg">
                <EditableText
                  field="feature1Description"
                  value={content.feature1Description || '맛의 기본은 좋은 재료에서 시작됩니다. 산지에서 갓 수확한 신선한 야채와 엄격하게 선별된 고품질 육류만을 사용합니다.'}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                  onStyleClick={onTextStyleClick}
                  textStyles={textStyles}
                  isTextarea
                />
              </p>
              <div className="flex gap-4 mt-4">
                <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="block text-xl font-bold text-gray-900">
                    <EditableText
                      field="feature1Stat1Value"
                      value={content.feature1Stat1Value || 'Fresh'}
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
                  <span className="text-xs text-gray-500">
                    <EditableText
                      field="feature1Stat1Label"
                      value={content.feature1Stat1Label || '당일 입고 재료'}
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
                <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="block text-xl font-bold text-gray-900">
                    <EditableText
                      field="feature1Stat2Value"
                      value={content.feature1Stat2Value || 'Clean'}
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
                  <span className="text-xs text-gray-500">
                    <EditableText
                      field="feature1Stat2Label"
                      value={content.feature1Stat2Label || '위생 공정'}
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
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Feature 2: 맛/비법 (Dark Block) */}
      {!hiddenSections['feature2'] && (
        <section className="w-full bg-gray-900 rounded-3xl mx-auto max-w-5xl p-10 md:p-16 text-white text-center shadow-xl relative overflow-hidden my-8">
          <SectionDeleteButton sectionKey="feature2" onSectionDelete={onSectionDelete} />
          <div className="absolute top-0 left-0 w-full h-full opacity-40 mix-blend-overlay pointer-events-none">
            <EditableImage
              imageKey="feature2_bg"
              uploadedImages={uploadedImages}
              className="w-full h-full"
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
            />
          </div>
          <div className="relative z-10 max-w-3xl mx-auto">
            <span className="inline-block px-3 py-1 border border-gray-600 text-gray-300 rounded-full text-xs font-bold mb-6">
              <EditableText
                field="feature2Badge"
                value={content.feature2Badge || 'SECRET SAUCE'}
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
            <h3 className="text-3xl md:text-4xl font-bold mb-6">
              <EditableText
                field="feature2Title"
                value={content.feature2Title || '입안 가득 퍼지는\n깊은 풍미의 비결'}
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
                isTextarea
              />
            </h3>
            <p className="text-gray-300 text-lg leading-relaxed mb-8">
              <EditableText
                field="feature2Description"
                value={content.feature2Description || '수많은 테스트 끝에 완성된 황금 비율 소스.\n자극적인 맛 대신, 재료와 어우러지는 깊은 감칠맛을 냅니다.'}
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
                isTextarea
              />
            </p>
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur px-6 py-3 rounded-full border border-white/20">
              <ThumbsUp className="w-5 h-5 text-orange-400" />
              <span>
                <EditableText
                  field="feature2HighlightText"
                  value={content.feature2HighlightText || '재구매율 1위의 검증된 맛'}
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
          </div>
        </section>
      )}

      {/* Feature 3: 간편 조리 */}
      {!hiddenSections['feature3'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature3" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-10 items-center">
            <div className="order-2 md:order-1 space-y-8">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Clock className="w-8 h-8 text-orange-600" />
                  <h3 className="text-2xl font-bold text-gray-900">
                    <EditableText
                      field="feature3Title"
                      value={content.feature3Title || '바쁜 일상 속\n5분이면 충분합니다'}
                      editingField={editingField}
                      editingValue={editingValue}
                      onEdit={onTextEdit}
                      onSave={onTextSave}
                      onCancel={onTextCancel}
                      onValueChange={onValueChange}
                      onStyleClick={onTextStyleClick}
                      textStyles={textStyles}
                      isTextarea
                    />
                  </h3>
                </div>
                <p className="text-gray-600 leading-relaxed">
                  <EditableText
                    field="feature3Description"
                    value={content.feature3Description || '요리할 시간이 부족해도 걱정하지 마세요.\n라면만큼 쉽지만, 퀄리티는 레스토랑급입니다.'}
                    editingField={editingField}
                    editingValue={editingValue}
                    onEdit={onTextEdit}
                    onSave={onTextSave}
                    onCancel={onTextCancel}
                    onValueChange={onValueChange}
                    onStyleClick={onTextStyleClick}
                    textStyles={textStyles}
                    isTextarea
                  />
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="bg-white p-2 rounded shadow-sm text-gray-800">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <strong className="block text-gray-900 mb-1">
                      <EditableText
                        field="feature3Method1Title"
                        value={content.feature3Method1Title || '전자레인지 조리'}
                        editingField={editingField}
                        editingValue={editingValue}
                        onEdit={onTextEdit}
                        onSave={onTextSave}
                        onCancel={onTextCancel}
                        onValueChange={onValueChange}
                        onStyleClick={onTextStyleClick}
                        textStyles={textStyles}
                      />
                    </strong>
                    <p className="text-sm text-gray-500">
                      <EditableText
                        field="feature3Method1Desc"
                        value={content.feature3Method1Desc || '포장을 살짝 뜯은 후 약 4분간 데워주세요. (700W 기준)'}
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
                <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="bg-white p-2 rounded shadow-sm text-gray-800">
                    <Flame className="w-6 h-6" />
                  </div>
                  <div>
                    <strong className="block text-gray-900 mb-1">
                      <EditableText
                        field="feature3Method2Title"
                        value={content.feature3Method2Title || '직화/냄비 조리'}
                        editingField={editingField}
                        editingValue={editingValue}
                        onEdit={onTextEdit}
                        onSave={onTextSave}
                        onCancel={onTextCancel}
                        onValueChange={onValueChange}
                        onStyleClick={onTextStyleClick}
                        textStyles={textStyles}
                      />
                    </strong>
                    <p className="text-sm text-gray-500">
                      <EditableText
                        field="feature3Method2Desc"
                        value={content.feature3Method2Desc || '내용물을 냄비나 팬에 붓고 중약불에서 3~5분간 볶아주세요.'}
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
            </div>
            <div className="order-1 md:order-2 rounded-2xl overflow-hidden shadow-lg h-full min-h-[400px] bg-gray-100">
              <EditableImage
                imageKey="feature3_image"
                uploadedImages={uploadedImages}
                className="w-full h-full min-h-[400px]"
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
              />
            </div>
          </div>
        </section>
      )}

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
    </>
  );
}
