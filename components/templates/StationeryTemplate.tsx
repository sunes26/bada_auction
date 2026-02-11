import { PenTool, BookOpen, Layers, Edit3, Check, Bookmark, Trash2 } from 'lucide-react';
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

export default function StationeryTemplate(props: TemplateProps) {
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
          <p className="text-indigo-600 font-bold tracking-widest mb-4 text-sm">
            <EditableText
              field="introSubtitle"
              value={content.introSubtitle || 'RECORD YOUR MOMENTS'}
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
          <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
            <EditableText
              field="introTitle"
              value={content.introTitle || '생각이 머무는 곳,\n영감이 시작되는 공간'}
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
          <p className="text-lg text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            <EditableText
              field="introDescription"
              value={content.introDescription || '스쳐 지나가는 아이디어부터 소중한 하루의 기록까지.\n사각거리는 종이의 질감과 부드러운 필기감으로\n당신의 기록을 더욱 특별하게 만들어보세요.'}
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
          <div className="rounded-2xl overflow-hidden shadow-xl max-w-4xl mx-auto bg-slate-50">
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

      {/* Feature 1: 종이 품질 */}
      {!hiddenSections['feature1'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature1" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
            <div className="w-full md:w-1/2 rounded-2xl overflow-hidden shadow-lg aspect-[4/3] bg-slate-100">
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
              <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center text-xl mb-2">
                <PenTool className="w-6 h-6" />
              </div>
              <h3 className="text-3xl font-bold text-slate-900">
                <EditableText
                  field="feature1Title"
                  value={content.feature1Title || '비침 없이 완벽한\n120g 프리미엄 내지'}
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
              <p className="text-slate-600 leading-relaxed text-lg">
                <EditableText
                  field="feature1Description"
                  value={content.feature1Description || '만년필, 젤펜, 형광펜 어떤 필기구를 사용해도 뒷면 비침 걱정이 없습니다. 눈의 피로를 덜어주는 미색 용지를 사용하여 장시간 필기에도 편안합니다.'}
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
                <div className="px-4 py-2 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="block text-xl font-bold text-slate-900">
                    <EditableText
                      field="feature1Stat1Value"
                      value={content.feature1Stat1Value || '120gsm'}
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
                  <span className="text-xs text-slate-500">
                    <EditableText
                      field="feature1Stat1Label"
                      value={content.feature1Stat1Label || '도톰한 두께감'}
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
                <div className="px-4 py-2 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="block text-xl font-bold text-slate-900">
                    <EditableText
                      field="feature1Stat2Value"
                      value={content.feature1Stat2Value || 'Acid-Free'}
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
                  <span className="text-xs text-slate-500">
                    <EditableText
                      field="feature1Stat2Label"
                      value={content.feature1Stat2Label || '중성지 사용'}
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

      {/* Feature 2: 제본/디자인 (Dark Block) */}
      {!hiddenSections['feature2'] && (
        <section className="w-full bg-slate-800 rounded-3xl mx-auto max-w-5xl p-10 md:p-16 text-white text-center shadow-xl relative overflow-hidden my-8">
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
            <span className="inline-block px-3 py-1 border border-indigo-400 text-indigo-300 rounded-full text-xs font-bold mb-6">
              <EditableText
                field="feature2Badge"
                value={content.feature2Badge || 'SMART DESIGN'}
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
                value={content.feature2Title || '어떤 페이지도 평평하게\n180도 펼침 제본'}
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
            <p className="text-slate-300 text-lg leading-relaxed mb-8">
              <EditableText
                field="feature2Description"
                value={content.feature2Description || '글씨를 쓸 때 손에 걸리는 불편함이 없습니다.\n특수 제본 기술(Lay-flat)을 적용하여\n첫 장부터 마지막 장까지 완벽하게 펼쳐집니다.'}
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
                <BookOpen className="w-6 h-6 text-indigo-300 mb-1 mx-auto" />
                <span className="text-sm font-medium">
                  <EditableText
                    field="feature2Card1"
                    value={content.feature2Card1 || '180° Lay-flat'}
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
                <Layers className="w-6 h-6 text-indigo-300 mb-1 mx-auto" />
                <span className="text-sm font-medium">
                  <EditableText
                    field="feature2Card2"
                    value={content.feature2Card2 || '견고한 하드커버'}
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

      {/* Feature 3: 활용성/라이프스타일 */}
      {!hiddenSections['feature3'] && (
        <section className="w-full py-16 px-8 bg-white relative">
          <SectionDeleteButton sectionKey="feature3" onSectionDelete={onSectionDelete} />
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-10 items-center">
            <div className="order-2 md:order-1 space-y-8">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Edit3 className="w-8 h-8 text-indigo-600" />
                  <h3 className="text-2xl font-bold text-slate-900">
                    <EditableText
                      field="feature3Title"
                      value={content.feature3Title || '당신의 일상을\n디자인하세요'}
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
                <p className="text-slate-600 leading-relaxed">
                  <EditableText
                    field="feature3Description"
                    value={content.feature3Description || '업무 미팅, 학습 노트, 다이어리 꾸미기까지.\n어떤 용도로 사용해도 만족스러운 경험을 드립니다.\n심플한 디자인으로 데스크테리어 소품으로도 훌륭합니다.'}
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
                <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="bg-white p-2 rounded shadow-sm text-indigo-700">
                    <Check className="w-6 h-6" />
                  </div>
                  <div>
                    <strong className="block text-slate-900 mb-1">
                      <EditableText
                        field="feature3Point1Title"
                        value={content.feature3Point1Title || '다양한 내지 구성'}
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
                    <p className="text-sm text-slate-500">
                      <EditableText
                        field="feature3Point1Desc"
                        value={content.feature3Point1Desc || '줄글(Lined), 모눈(Grid), 무지(Plain) 중 선택 가능'}
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
                <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="bg-white p-2 rounded shadow-sm text-indigo-700">
                    <Bookmark className="w-6 h-6" />
                  </div>
                  <div>
                    <strong className="block text-slate-900 mb-1">
                      <EditableText
                        field="feature3Point2Title"
                        value={content.feature3Point2Title || '편리한 디테일'}
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
                    <p className="text-sm text-slate-500">
                      <EditableText
                        field="feature3Point2Desc"
                        value={content.feature3Point2Desc || '가름끈 2개, 뒷면 수납 포켓, 밴드 클로저 포함'}
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
            <div className="order-1 md:order-2 rounded-2xl overflow-hidden shadow-lg h-full min-h-[400px] bg-slate-100">
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
