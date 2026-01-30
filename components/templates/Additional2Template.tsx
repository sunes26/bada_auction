import { Star } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import { TemplateProps } from './TemplateProps';

export default function Additional2Template(props: TemplateProps) {
  const { content, uploadedImages, editingField, editingValue, onImageUpload, onImageRefresh, onImageDrop, onTextEdit, onTextSave, onTextCancel, onValueChange, onImageClick, editingImage, imageStyleSettings, onImageDelete, onTextStyleClick, textStyles = {}, additionalImageSlots = 0, onAddImageSlot, onRemoveImageSlot, imageSizes = {}, onImageResize, imagePositions = {}, onImageMove } = props;

  return (
    <>
      {/* Hero Section - 황금 비누방울 */}
      <div className="w-full bg-gradient-to-b from-amber-50 to-white py-20 px-10 text-center">
        <h1 className="text-6xl font-bold text-gray-800 mb-4">
          <EditableText field="introTitle" value={content.introTitle} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
        </h1>
        <p className="text-3xl text-gray-600 mb-12 uppercase tracking-wider">
          <EditableText field="introCopy" value={content.introCopy} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
        </p>
        <EditableImage imageKey="additional2_template1_main" uploadedImages={uploadedImages} className="w-full max-w-4xl mx-auto h-[600px] rounded-3xl shadow-2xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} fillContainer={true} isResizable={false} />
      </div>

      {/* 고객만족우수 Section */}
      <div className="w-full bg-white py-20 px-10">
        <h2 className="text-4xl font-bold text-center text-gray-800 mb-4">
          <EditableText field="reviewTitle" value={content.reviewTitle || "고객만족우수"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} className="text-gray-800" />
        </h2>
        <p className="text-center text-blue-600 text-xl mb-12">
          <EditableText field="reviewHashtag" value={content.reviewHashtag || "#솔직후기"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} className="text-blue-600" />
        </p>
        <div className="max-w-4xl mx-auto space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-50 rounded-2xl p-8 shadow-lg">
              <div className="flex mb-3">{[1, 2, 3, 4, 5].map((j) => (<Star key={j} className="w-5 h-5 fill-yellow-400 text-yellow-400" />))}</div>
              <div className="text-lg text-gray-700"><EditableText field={`review${i}`} value={content[`review${i}`]} isTextarea editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} className="text-gray-700" /></div>
            </div>
          ))}
        </div>
      </div>

      {/* 자연의 힘으로 건강한 머릿결을 Section */}
      <div className="w-full bg-gray-50 py-20 px-10">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-800 mb-12">
            <EditableText field="healthTitle" value={content.healthTitle || "자연의 힘으로 건강한 머릿결을"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
          </h2>
          <p className="text-center text-xl text-gray-600 mb-12">
            <EditableText field="healthSubtitle" value={content.healthSubtitle || "자연 성분으로 가득한 샴푸, 당신의 머릿결을 부드럽게 돌이 아름다운 기분을 누려보세요"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
          </p>

          {/* 2개 이미지: 큰 이미지 + 작은 이미지 */}
          <div className="relative">
            <EditableImage imageKey="additional2_template2_main" uploadedImages={uploadedImages} className="w-full h-[600px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} fillContainer={true} isResizable={false} />
            <div className="absolute bottom-8 right-8 w-64 h-64">
              <EditableImage imageKey="additional2_template2_small" uploadedImages={uploadedImages} className="w-full h-full rounded-xl shadow-2xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} fillContainer={true} isResizable={false} />
            </div>
          </div>
        </div>
      </div>

      {/* 샴푸 Section - 제품명 + 이미지 */}
      <div className="w-full bg-white py-20 px-10 text-center">
        <h2 className="text-5xl font-bold text-gray-800 mb-12">
          <EditableText field="brandProductName" value={content.brandProductName} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
        </h2>
        <div className="max-w-3xl mx-auto">
          <EditableImage imageKey="additional2_template3_product" uploadedImages={uploadedImages} className="w-full h-[600px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} fillContainer={true} isResizable={false} />
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
          <EditableImage imageKey="additional2_template5_bg" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-lg" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} fillContainer={true} isResizable={false} />

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

      {/* 주의사항 Section - 파란 배경 */}
      <div className="w-full bg-blue-600 text-white py-12 px-10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
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
              />
            </h4>
          </div>
          <p className="text-base leading-relaxed">
            <EditableText field="noticeText1" value={content.noticeText1 || "상품명의 제품명과 수량을 꼭! 확인해주세요."} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} />
          </p>
        </div>
      </div>
    </>
  );
}
