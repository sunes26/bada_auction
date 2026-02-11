import { Leaf, Shield, CheckCircle, Wind, Droplets, Sparkles, Trash2 } from 'lucide-react';
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

export default function HygieneTemplate(props: TemplateProps) {
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
          <p className="text-teal-600 font-bold tracking-widest mb-4 text-sm">
            <EditableText
              field="introSubtitle"
              value={content.introSubtitle || 'PURE & SAFE'}
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
              value={content.introTitle || '매일 닿는 피부니까\n더 순수하게, 더 안전하게'}
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
              value={content.introDescription || '불필요한 성분은 빼고, 자연 유래 성분으로 채웠습니다.\n온 가족이 안심하고 사용할 수 있는 데일리 케어.'}
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
          <div className="rounded-2xl overflow-hidden shadow-xl max-w-4xl mx-auto bg-gray-50">
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

      {/* Feature 1: 소재/안전성 */}
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
              <div className="w-12 h-12 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-xl mb-2">
                <Leaf className="w-6 h-6" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">
                <EditableText
                  field="feature1Title"
                  value={content.feature1Title || '피부가 먼저 느끼는\n자연 유래 소재'}
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
                  value={content.feature1Description || '민감한 피부에도 자극 없이 부드럽게 닿습니다. 엄격한 기준의 피부 저자극 테스트를 통과했으며, 형광증백제나 인공 색소를 전혀 사용하지 않았습니다.'}
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
                      value={content.feature1Stat1Value || '100%'}
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
                      value={content.feature1Stat1Label || '천연 펄프/소재'}
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
                      value={content.feature1Stat2Value || 'Zero'}
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
                      value={content.feature1Stat2Label || '유해성분 불검출'}
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

      {/* Feature 2: 인증/신뢰 (Teal Dark Block) */}
      {!hiddenSections['feature2'] && (
        <section className="w-full bg-teal-700 rounded-3xl mx-auto max-w-5xl p-10 md:p-16 text-white text-center shadow-xl relative overflow-hidden my-8">
          <SectionDeleteButton sectionKey="feature2" onSectionDelete={onSectionDelete} />
          <div className="absolute top-0 left-0 w-full h-full opacity-20 mix-blend-overlay pointer-events-none">
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
            <span className="inline-block px-3 py-1 border border-teal-300 text-teal-200 rounded-full text-xs font-bold mb-6">
              <EditableText
                field="feature2Badge"
                value={content.feature2Badge || 'CERTIFIED QUALITY'}
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
                value={content.feature2Title || '깐깐하게 검증받은\n안전한 품질'}
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
            <p className="text-teal-50 text-lg leading-relaxed mb-8">
              <EditableText
                field="feature2Description"
                value={content.feature2Description || "독일 더마테스트 최고 등급 'EXCELLENT' 획득.\n국제 표준 인증 기관의 까다로운 절차를 모두 통과했습니다."}
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
            <div className="inline-flex items-center gap-4">
              <div className="bg-white/10 backdrop-blur px-6 py-3 rounded-xl border border-white/20">
                <Shield className="w-6 h-6 text-teal-200 mb-1 mx-auto" />
                <span className="text-sm font-medium">
                  <EditableText
                    field="feature2Card1"
                    value={content.feature2Card1 || '안전성 인증'}
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
              <div className="bg-white/10 backdrop-blur px-6 py-3 rounded-xl border border-white/20">
                <CheckCircle className="w-6 h-6 text-teal-200 mb-1 mx-auto" />
                <span className="text-sm font-medium">
                  <EditableText
                    field="feature2Card2"
                    value={content.feature2Card2 || '품질 보증'}
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
        </section>
      )}

      {/* Feature 3: 기능성/사용감 */}
      {!hiddenSections['feature3'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature3" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-10 items-center">
            <div className="order-2 md:order-1 space-y-8">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles className="w-8 h-8 text-teal-600" />
                  <h3 className="text-2xl font-bold text-gray-900">
                    <EditableText
                      field="feature3Title"
                      value={content.feature3Title || '탁월한 흡수력과\n산뜻한 마무리감'}
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
                    value={content.feature3Description || '독자적인 3중 레이어 구조로 흡수력은 높이고,\n사용 후 잔여물 걱정 없이 깔끔합니다.'}
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
                  <div className="bg-white p-2 rounded shadow-sm text-teal-700">
                    <Wind className="w-6 h-6" />
                  </div>
                  <div>
                    <strong className="block text-gray-900 mb-1">
                      <EditableText
                        field="feature3Point1Title"
                        value={content.feature3Point1Title || '통기성 & 건조'}
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
                        field="feature3Point1Desc"
                        value={content.feature3Point1Desc || '우수한 통기성으로 눅눅함 없이 언제나 보송보송합니다.'}
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
                  <div className="bg-white p-2 rounded shadow-sm text-teal-700">
                    <Droplets className="w-6 h-6" />
                  </div>
                  <div>
                    <strong className="block text-gray-900 mb-1">
                      <EditableText
                        field="feature3Point2Title"
                        value={content.feature3Point2Title || '강력한 세정/흡수'}
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
                        field="feature3Point2Desc"
                        value={content.feature3Point2Desc || '한 번의 사용으로도 충분한 만족감을 드립니다.'}
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
              containerWidth={containerWidths[imageKey] || 85}
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
