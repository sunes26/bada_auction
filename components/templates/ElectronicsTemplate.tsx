import { Music, Volume2, VolumeX, Feather, Mic, Zap, Headphones, Briefcase, Cable, BookOpen, Check, Trash2 } from 'lucide-react';
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

export default function ElectronicsTemplate(props: TemplateProps) {
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
          <p className="text-indigo-600 font-bold tracking-widest mb-4 uppercase text-sm">
            <EditableText
              field="introSubtitle"
              value={content.introSubtitle || 'SILENCE REDEFINED'}
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
          <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-8 leading-tight">
            <EditableText
              field="introTitle"
              value={content.introTitle || '세상의 소음을 끄고\n오직 음악만 남기다.'}
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
          <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-12 font-light">
            <EditableText
              field="introDescription"
              value={content.introDescription || '압도적인 몰입감을 지금 경험해보세요.'}
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
          <div className="rounded-3xl overflow-hidden shadow-2xl max-w-4xl mx-auto">
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

      {/* Feature 1: Sound Quality */}
      {!hiddenSections['feature1'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature1" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
            <div className="w-full md:w-1/2 rounded-2xl overflow-hidden shadow-lg">
              <EditableImage
                imageKey="feature1_image"
                uploadedImages={uploadedImages}
                className="w-full h-[400px]"
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
              <div className="w-12 h-12 bg-gray-900 text-white rounded-lg flex items-center justify-center">
                <Music className="w-6 h-6" />
              </div>
              <h3 className="text-3xl md:text-4xl font-bold text-gray-900">
                <EditableText
                  field="feature1Title"
                  value={content.feature1Title || '원음 그대로의 감동\n40mm HD 드라이버'}
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
                  value={content.feature1Description || '정밀하게 튜닝된 드라이버가 깊고 풍부한 저음부터 섬세한 고음까지 완벽한 밸런스를 선사합니다.'}
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
              <ul className="space-y-3 mt-4 text-gray-500 font-medium">
                {[1, 2, 3].map((i) => (
                  <li key={i} className="flex items-center gap-2">
                    <Check className="w-5 h-5 text-indigo-600" />
                    <EditableText
                      field={`feature1Point${i}`}
                      value={content[`feature1Point${i}`] || `특징 ${i}`}
                      editingField={editingField}
                      editingValue={editingValue}
                      onEdit={onTextEdit}
                      onSave={onTextSave}
                      onCancel={onTextCancel}
                      onValueChange={onValueChange}
                      onStyleClick={onTextStyleClick}
                      textStyles={textStyles}
                    />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Feature 2: Noise Cancellation (Dark Block) */}
      {!hiddenSections['feature2'] && (
        <section className="w-full bg-gray-900 rounded-3xl mx-auto max-w-5xl p-10 md:p-16 text-white text-center shadow-xl relative overflow-hidden my-8">
          <SectionDeleteButton sectionKey="feature2" onSectionDelete={onSectionDelete} />
          <div className="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none">
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
            <div className="inline-block px-4 py-1 border border-indigo-400 text-indigo-300 rounded-full text-sm font-bold mb-6">
              <EditableText
                field="feature2Badge"
                value={content.feature2Badge || 'ANC PRO TECHNOLOGY'}
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
            <h3 className="text-3xl md:text-5xl font-bold mb-6">
              <EditableText
                field="feature2Title"
                value={content.feature2Title || '주변 소음 99.8% 차단'}
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
            <p className="text-gray-300 text-lg leading-relaxed mb-10">
              <EditableText
                field="feature2Description"
                value={content.feature2Description || '지하철, 비행기, 시끄러운 카페에서도 나만의 공간을 만드세요.'}
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-xl border border-white/10">
                <VolumeX className="w-8 h-8 mb-3 text-indigo-400 mx-auto" />
                <h4 className="text-xl font-bold mb-2">
                  <EditableText
                    field="feature2Card1Title"
                    value={content.feature2Card1Title || '노이즈 캔슬링 모드'}
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
                <p className="text-sm text-gray-400">
                  <EditableText
                    field="feature2Card1Desc"
                    value={content.feature2Card1Desc || '완벽한 몰입이 필요할 때'}
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
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-xl border border-white/10">
                <Volume2 className="w-8 h-8 mb-3 text-indigo-400 mx-auto" />
                <h4 className="text-xl font-bold mb-2">
                  <EditableText
                    field="feature2Card2Title"
                    value={content.feature2Card2Title || '주변 소리 듣기 모드'}
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
                <p className="text-sm text-gray-400">
                  <EditableText
                    field="feature2Card2Desc"
                    value={content.feature2Card2Desc || '대화나 안내방송을 들어야 할 때'}
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
        </section>
      )}

      {/* Feature 3: Comfort */}
      {!hiddenSections['feature3'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature3" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto flex flex-col-reverse md:flex-row items-center gap-12">
            <div className="w-full md:w-1/2 space-y-6">
              <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center">
                <Feather className="w-6 h-6" />
              </div>
              <h3 className="text-3xl md:text-4xl font-bold text-gray-900">
                <EditableText
                  field="feature3Title"
                  value={content.feature3Title || '하루 종일 편안한\n클라우드 핏 착용감'}
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
                  field="feature3Description"
                  value={content.feature3Description || '안경을 써도 불편하지 않습니다. 프리미엄 메모리폼 이어패드가 귀 모양에 맞춰 부드럽게 밀착됩니다.'}
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
              <div className="flex gap-4 mt-6">
                <div className="text-center p-4 bg-gray-50 rounded-xl">
                  <span className="block text-2xl font-black text-indigo-600">
                    <EditableText
                      field="feature3Stat1Value"
                      value={content.feature3Stat1Value || '254g'}
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
                      field="feature3Stat1Label"
                      value={content.feature3Stat1Label || '초경량 무게'}
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
                <div className="text-center p-4 bg-gray-50 rounded-xl">
                  <span className="block text-2xl font-black text-indigo-600">
                    <EditableText
                      field="feature3Stat2Value"
                      value={content.feature3Stat2Value || 'Soft'}
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
                      field="feature3Stat2Label"
                      value={content.feature3Stat2Label || '단백질 가죽'}
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
            <div className="w-full md:w-1/2 rounded-2xl overflow-hidden shadow-lg">
              <EditableImage
                imageKey="feature3_image"
                uploadedImages={uploadedImages}
                className="w-full h-[400px]"
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

      {/* Feature 4: Call Quality & Battery (2-Column Grid) */}
      {!hiddenSections['feature4'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature4" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
            <div className="bg-gray-50 p-10 rounded-3xl">
              <Mic className="w-10 h-10 text-indigo-600 mb-6" />
              <h3 className="text-2xl font-bold mb-4">
                <EditableText
                  field="feature4Card1Title"
                  value={content.feature4Card1Title || '선명한 통화 품질'}
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
              <p className="text-gray-600 mb-6">
                <EditableText
                  field="feature4Card1Desc"
                  value={content.feature4Card1Desc || 'AI 기반의 통화 소음 감소 기술이 목소리만 선명하게 전달합니다.'}
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
              <EditableImage
                imageKey="feature4_image1"
                uploadedImages={uploadedImages}
                className="w-full h-48 rounded-xl"
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
            <div className="bg-gray-50 p-10 rounded-3xl">
              <Zap className="w-10 h-10 text-yellow-500 mb-6" />
              <h3 className="text-2xl font-bold mb-4">
                <EditableText
                  field="feature4Card2Title"
                  value={content.feature4Card2Title || '멈추지 않는 플레이'}
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
              <p className="text-gray-600 mb-6">
                <EditableText
                  field="feature4Card2Desc"
                  value={content.feature4Card2Desc || '한 번 충전으로 최대 30시간 연속 재생이 가능합니다.'}
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
              <div className="flex items-center gap-4 mt-8">
                <div className="h-4 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-400 w-4/5"></div>
                </div>
                <span className="font-bold text-gray-700">
                  <EditableText
                    field="feature4BatteryValue"
                    value={content.feature4BatteryValue || '30H'}
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

      {/* Feature 5: In the Box (구성품) */}
      {!hiddenSections['feature5'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature5" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto">
            <h3 className="text-3xl font-bold text-center mb-12">
              <EditableText
                field="feature5Title"
                value={content.feature5Title || '구성품 (In the Box)'}
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { icon: Headphones, key: 'box1', defaultText: '본체' },
                { icon: Briefcase, key: 'box2', defaultText: '케이스' },
                { icon: Cable, key: 'box3', defaultText: '충전 케이블' },
                { icon: BookOpen, key: 'box4', defaultText: '사용 설명서' },
              ].map((item) => (
                <div key={item.key} className="bg-gray-50 p-6 rounded-xl text-center hover:shadow-md transition-shadow">
                  <div className="h-24 flex items-center justify-center mb-4 text-5xl text-gray-300">
                    <item.icon className="w-16 h-16" />
                  </div>
                  <p className="font-medium">
                    <EditableText
                      field={`feature5${item.key}`}
                      value={content[`feature5${item.key}`] || item.defaultText}
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
